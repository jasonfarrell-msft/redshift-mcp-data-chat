import io
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename", [
    "requirements.lock", "requirements-build.lock", "requirements-official.lock",
])
def test_container_locks_pin_and_hash_every_dependency(filename: str) -> None:
    text = (PROJECT / filename).read_text(encoding="utf-8")
    requirements = text.replace("\\\n", "").splitlines()
    names = set()
    for line in requirements:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert re.fullmatch(
            r"[\w.-]+(?:\[[\w,-]+\])?==[\w.]+(?:\s+--hash=sha256:[a-f0-9]{64})+",
            line,
        )
        names.add(line.split("==")[0].split("[")[0])
    assert names
    assert not names & {"pytest", "pytest-asyncio", "ruff", "pip-tools", "uv"}
    if filename == "requirements.lock":
        assert {"mcp", "python-dotenv", "azure-identity", "boto3"} <= names
        assert "redshift-connector" not in names
        assert "hatchling" not in names
    elif filename == "requirements-official.lock":
        assert {"awslabs-redshift-mcp-server", "mcp"} <= names
        assert "03a3fff27161cf0bd3e75765eb9c8ef5f1cfe920811015dcb2c543d712826b40" in text
    else:
        assert "hatchling" in names


def test_dockerfile_uses_immutable_base_nonroot_and_allowlisted_sources() -> None:
    dockerfile = (PROJECT / "Dockerfile").read_text(encoding="utf-8")
    bases = re.findall(r"^FROM (\S+)", dockerfile, re.M)
    assert len(bases) == 2
    assert bases[0] == bases[1]
    assert re.fullmatch(r"python:3\.13\.\d+-slim-trixie@sha256:[a-f0-9]{64}", bases[0])
    assert "USER 10001:10001" in dockerfile
    assert 'CMD ["redshift-mcp-server", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile
    assert "COPY . " not in dockerfile
    assert "COPY ./" not in dockerfile
    assert "ARG " not in dockerfile
    assert ".env" not in dockerfile
    assert dockerfile.count("--require-hashes --only-binary=:all:") == 3
    assert "python -m venv /opt/adapter" in dockerfile
    assert "python -m venv /opt/official" in dockerfile
    sources = [
        line
        for line in dockerfile.splitlines()
        if line.startswith("COPY ") and "--from" not in line
    ]
    assert sources == [
        "COPY requirements-build.lock ./",
        "COPY pyproject.toml README.md ./",
        "COPY redshift_mcp_server/*.py ./redshift_mcp_server/",
        "COPY requirements.lock ./",
        "COPY requirements-official.lock ./",
        "COPY aws-config ./",
    ]


def test_build_context_is_deny_by_default_and_has_explicit_sensitive_exclusions() -> None:
    rules = (PROJECT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert rules[0] == "**"
    assert {rule for rule in rules if rule.startswith("!")} == {
        "!Dockerfile",
        "!.dockerignore",
        "!pyproject.toml",
        "!README.md",
        "!requirements.lock",
        "!requirements-build.lock",
        "!requirements-official.lock",
        "!aws-config",
        "!redshift_mcp_server/",
        "!redshift_mcp_server/**/*.py",
        "!redshift_mcp_server/aws_credentials.py",
    }
    assert {
        "**/.env*",
        "**/.venv",
        "**/.aws",
        "**/.azure",
        "**/.squad",
        "**/.git",
        "**/tests",
        "**/deploy",
        "**/*.pem",
        "**/*.key",
    } <= set(rules)
    assert rules[-1] == "!redshift_mcp_server/aws_credentials.py"


def test_docker_context_keeps_required_credential_module_only() -> None:
    if not shutil.which("docker"):
        pytest.skip("Docker is required to verify actual build-context filtering")
    probe = subprocess.run(
        ["docker", "info"], capture_output=True, timeout=30, check=False,
    )
    if probe.returncode:
        pytest.skip("Docker daemon is required to verify actual build-context filtering")

    with tempfile.TemporaryDirectory(prefix=".packaging-context-", dir=PROJECT) as directory:
        context = Path(directory)
        shutil.copyfile(PROJECT / ".dockerignore", context / ".dockerignore")
        module = "redshift_mcp_server/aws_credentials.py"
        (context / "redshift_mcp_server").mkdir()
        shutil.copyfile(PROJECT / module, context / module)
        excluded = [
            "credentials",
            "credentials.py",
            "redshift_mcp_server/other_credentials.py",
            "redshift_mcp_server/aws_credentials_backup.py",
            ".aws/credentials",
        ]
        for name in excluded:
            path = context / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("excluded fixture\n", encoding="utf-8")
        result = subprocess.run(
            [
                "docker", "build", "--network=none", "--output=type=tar,dest=-",
                "-f", "-", str(context),
            ],
            input=b"FROM scratch\nCOPY . /\n",
            capture_output=True, timeout=60, check=True,
        )
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
            names = {name.removeprefix("./") for name in archive.getnames()}
            assert module in names
            assert not names.intersection(excluded)
            packaged_module = archive.extractfile(module)
            assert packaged_module is not None
            assert packaged_module.read() == (PROJECT / module).read_bytes()
