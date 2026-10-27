import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from redshift_mcp_server import server
from redshift_mcp_server.config import ConfigurationError, Settings, load_environment


def test_startup_loads_default_file_before_running(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text(
        "REDSHIFT_HOST=example.invalid\nREDSHIFT_DATABASE=fixture_db\n"
        "REDSHIFT_USER=fixture_user\nREDSHIFT_PASSWORD='synthetic-only'\n",
        encoding="utf-8",
    )
    run = MagicMock(side_effect=lambda **kwargs: Settings.from_env())
    connect = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    monkeypatch.setattr(server.database, "OfficialCursor", connect)
    server.main([])
    assert Settings.from_env().database == "fixture_db"
    run.assert_called_once_with(transport="streamable-http")
    connect.assert_not_called()


def test_exported_environment_wins_even_when_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("REDSHIFT_USER", "exported-user")
    monkeypatch.setenv("REDSHIFT_PASSWORD", "")
    (tmp_path / ".env").write_text(
        "REDSHIFT_USER=file-user\nREDSHIFT_PASSWORD='synthetic-only'\n",
        encoding="utf-8",
    )
    load_environment()
    assert os.environ["REDSHIFT_USER"] == "exported-user"
    assert os.environ["REDSHIFT_PASSWORD"] == ""


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("'synthetic # $ ${REDSHIFT_USER} spaces'", "synthetic # $ ${REDSHIFT_USER} spaces"),
        ('"synthetic # $ ${REDSHIFT_USER} spaces"', "synthetic # $ ${REDSHIFT_USER} spaces"),
        ("synthetic$${REDSHIFT_USER}#suffix", "synthetic$${REDSHIFT_USER}#suffix"),
        (r"""'synthetic\'quote\\slash'""", "synthetic'quote\\slash"),
    ],
)
def test_password_characters_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, literal: str, expected: str
) -> None:
    monkeypatch.setenv("REDSHIFT_USER", "must-not-interpolate")
    (tmp_path / ".env").write_text(f"REDSHIFT_PASSWORD={literal}\n", encoding="utf-8")
    load_environment()
    assert os.environ["REDSHIFT_PASSWORD"] == expected


def test_absent_default_does_not_search_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("REDSHIFT_USER=parent-only\n", encoding="utf-8")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    load_environment()
    assert "REDSHIFT_USER" not in os.environ


def test_startup_without_default_file_needs_no_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    server.main([])
    run.assert_called_once_with(transport="streamable-http")
    assert "REDSHIFT_HOST" not in os.environ


def test_explicit_file_is_used_instead_of_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("REDSHIFT_USER=default-user\n", encoding="utf-8")
    selected = tmp_path / "fixture.config"
    selected.write_text("REDSHIFT_USER=selected-user\n", encoding="utf-8")
    monkeypatch.setattr(server.mcp, "run", MagicMock())
    server.main(["--env-file", str(selected)])
    assert os.environ["REDSHIFT_USER"] == "selected-user"


@pytest.mark.parametrize("explicit", [False, True])
def test_startup_loads_file_when_dotenv_is_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
) -> None:
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    selected = tmp_path / ("fixture.config" if explicit else ".env")
    selected.write_text("REDSHIFT_USER='literal ${USER} # $'\n", encoding="utf-8")
    run = MagicMock(side_effect=lambda **kwargs: os.environ["REDSHIFT_USER"])
    connect = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    monkeypatch.setattr(server.database, "OfficialCursor", connect)
    server.main(["--env-file", str(selected)] if explicit else [])
    assert os.environ["REDSHIFT_USER"] == "literal ${USER} # $"
    run.assert_called_once_with(transport="streamable-http")
    connect.assert_not_called()


def test_missing_explicit_file_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    with pytest.raises(SystemExit) as error:
        server.main(["--env-file", str(tmp_path / "nonexistent.config")])
    assert error.value.code == 2
    assert "requested --env-file does not exist" in capsys.readouterr().err
    run.assert_not_called()


@pytest.mark.parametrize(
    "content",
    [
        "REDSHIFT_USER=must-not-apply\nREDSHIFT_PASSWORD='synthetic-secret\n",
        "'invalid=key'=synthetic-secret\n",
        "REDSHIFT_PASSWORD=synthetic-secret\x00\n",
        "invalid\x00key=synthetic-secret\n",
    ],
)
def test_invalid_file_is_sanitized_and_not_partially_applied(
    content: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    (tmp_path / ".env").write_text(content, encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid environment file syntax") as error:
        load_environment()
    assert "synthetic-secret" not in str(error.value)
    assert "REDSHIFT_USER" not in os.environ
    assert "REDSHIFT_PASSWORD" not in os.environ
    output = capsys.readouterr()
    assert "synthetic-secret" not in output.out + output.err + caplog.text


def test_read_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(Path, "open", MagicMock(side_effect=PermissionError("synthetic-secret")))
    monkeypatch.setattr(server.mcp, "run", MagicMock())
    with pytest.raises(SystemExit) as error:
        server.main([])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert "Check file permissions and UTF-8 encoding" in output.err
    assert "synthetic-secret" not in output.out + output.err + caplog.text
    server.mcp.run.assert_not_called()


def test_invalid_utf8_is_sanitized(tmp_path: Path) -> None:
    (tmp_path / ".env").write_bytes(b"REDSHIFT_PASSWORD=synthetic-secret\xff")
    with pytest.raises(ConfigurationError, match="UTF-8 encoding") as error:
        load_environment()
    assert "synthetic-secret" not in str(error.value)


def test_directory_is_not_silently_ignored(tmp_path: Path) -> None:
    (tmp_path / ".env").mkdir()
    with pytest.raises(ConfigurationError, match="Cannot read the environment file"):
        load_environment()
