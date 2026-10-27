#!/usr/bin/env python3
"""Approved synthetic POC only. Default is read-only; mutations require --apply."""

import argparse
import asyncio
import copy
import hashlib
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "src/redshift-mcp-server"
DEPLOY_DIR = ROOT / "deploy"
STATE = DEPLOY_DIR / "state.json"
SUB = "bb4b2781-6739-4fa1-994e-4ad6ce55c59c"
TENANT = "e90bd921-0e00-4e6f-b87c-713670ee27bf"
LOCATION = "brazilsouth"
RG = "rg-redshift-bs01"
ACR = "acrredshiftbs01bb4b2781"
VAULT = "kv-redshift-bs01"
UMI = "umi-redshift-imagepull-mx01"
ENV = "cae-redshift-bs01"
APP = "ca-redshift-bs01"
IMAGE = f"{ACR}.azurecr.io/redshift-mcp-server:v1"
IMAGE_REPOSITORY = f"{ACR}.azurecr.io/redshift-mcp-server"
BASE = f"/subscriptions/{SUB}"
GROUP = f"{BASE}/resourceGroups/{RG}"
REGISTRY = f"{GROUP}/providers/Microsoft.ContainerRegistry/registries/{ACR}"
VAULT_ID = f"{GROUP}/providers/Microsoft.KeyVault/vaults/{VAULT}"
IDENTITY = f"{GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{UMI}"
ENV_ID = f"{GROUP}/providers/Microsoft.App/managedEnvironments/{ENV}"
APP_ID = f"{GROUP}/providers/Microsoft.App/containerApps/{APP}"
SECRET_SCOPE = f"{VAULT_ID}/secrets/redshift-password"
SECRET_URL = f"https://{VAULT}.vault.azure.net/secrets/redshift-password"
PULL = "7f951dda-4ed3-4680-a7ca-43fe172d538d"
READER = "4633458b-17de-408a-b874-0445c86b69e6"
OFFICER = "b86a8fe4-44ce-4948-aee5-eccb2c155cd7"
APP_API = "2026-07-01"
ACR_API = "2025-11-01"
KV_API = "2026-05-15"
ID_API = "2024-11-30"
ROLE_API = "2022-04-01"
SG = "sg-c2bac6ae"
STAGES = ("prerequisites", "build", "app", "configure", "verify")
NONSECRET = {
    "REDSHIFT_HOST": "host", "REDSHIFT_PORT": "port",
    "REDSHIFT_DATABASE": "database", "REDSHIFT_USER": "user",
    "REDSHIFT_AUTH_MODE": "auth_mode", "REDSHIFT_CONNECT_TIMEOUT": "timeout",
    "AWS_REGION": "region", "REDSHIFT_CLUSTER_IDENTIFIER": "cluster_identifier",
}
# Only these source files can enter the build context, irrespective of ignore behavior.
RUNTIME_FILES = (
    "Dockerfile", ".dockerignore", "pyproject.toml", "requirements.lock",
    "requirements-build.lock", "README.md",
    "redshift_mcp_server/__init__.py", "redshift_mcp_server/__main__.py",
    "redshift_mcp_server/config.py", "redshift_mcp_server/database.py",
    "redshift_mcp_server/analytics.py",
    "redshift_mcp_server/server.py",
)


class DeploymentError(Exception):
    """Only fixed, non-sensitive messages may cross the process boundary."""


def require(condition, message):
    if not condition:
        raise DeploymentError(message)


def quiet_logging():
    # Disable dependency logs, including bodies, tokens, endpoints and exception reprs.
    logging.disable(logging.CRITICAL)


def cli(*args, azure=True):
    command = ["az" if azure else "aws", *args]
    if azure:
        command += ["--only-show-errors"]
        if args[:1] != ("ad",):
            command += ["--subscription", SUB]
    else:
        command += ["--region", "us-east-2"]
    command += ["--output", "json"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("REDSHIFT_")}
    # az acr build uses tempfile internally; confine its archive to our owned directory.
    env["TMPDIR"] = str(DEPLOY_DIR)
    env["AWS_PAGER"] = ""
    result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    require(result.returncode == 0, f"CLI operation failed ({args[0]}; exit {result.returncode}); details suppressed.")
    if args[:3] == ("containerapp", "logs", "show"):
        return result.stdout  # Logs are JSON-lines; classify in memory, never emit them.
    return json.loads(result.stdout) if result.stdout.strip() else None


def read_state():
    require(not STATE.is_symlink(), "Linked deployment metadata is forbidden.")
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(**metadata):
    allowed = {"digest", "source_sha256", "build_run", "fqdn", "revision",
               "owned_officer", "owned_aws_rule", "resource_ids", "image_tag",
               "image_builds", "release"}
    require(metadata.keys() <= allowed, "Refusing unrecognized state fields.")
    state = read_state()
    require(state.keys() <= allowed, "Unexpected state fields; inspect metadata manually.")
    state.update(metadata)
    pending = STATE.with_suffix(".next.json")
    require(not pending.is_symlink() and not STATE.is_symlink(), "Linked state file is forbidden.")
    pending.write_text(json.dumps(state, indent=2) + "\n")
    pending.chmod(0o600)
    pending.replace(STATE)


def credential():
    from azure.identity import AzureCliCredential
    return AzureCliCredential(tenant_id=TENANT, process_timeout=60)


def arm(method, resource, api, body=None, missing=False, if_match=None):
    token = credential().get_token("https://management.azure.com/.default").token
    request = Request(
        f"https://management.azure.com{resource}?api-version={api}",
        data=None if body is None else json.dumps(body).encode(),
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    if if_match is not None:
        request.add_header("If-Match", if_match)
    try:
        with urlopen(request, timeout=90) as response:
            data = response.read()
            result = json.loads(data) if data else {}
            if method == "GET" and response.headers.get("ETag"):
                result["etag"] = response.headers["ETag"]
            return result
    except HTTPError as exc:
        if missing and exc.code == 404:
            return None
        # Never read/print the response body, request body or exception.
        raise DeploymentError(f"ARM {method} failed (HTTP {exc.code}); details suppressed.") from None


def wait_resource(resource, api):
    for _ in range(80):
        current = arm("GET", resource, api)
        state = current.get("properties", {}).get("provisioningState", "Succeeded")
        if state == "Succeeded":
            return current
        require(state not in ("Failed", "Canceled"), "Resource provisioning failed; inspect sanitized diagnostics.")
        time.sleep(15)
    raise DeploymentError("Resource provisioning timed out; rerun the same stage after investigation.")


def role(principal, scope, definition, principal_type="ServicePrincipal"):
    name = uuid.uuid5(uuid.NAMESPACE_URL, f"{scope.lower()}:{principal}:{definition}")
    resource = f"{scope}/providers/Microsoft.Authorization/roleAssignments/{name}"
    # Reuse pre-existing equivalent assignments, not only our deterministic name.
    assignments = arm("GET", f"{scope}/providers/Microsoft.Authorization/roleAssignments", ROLE_API)
    for assignment in assignments.get("value", []):
        props = assignment["properties"]
        if (props["principalId"].lower() == principal.lower()
                and props["scope"].lower() == scope.lower()
                and props["roleDefinitionId"].endswith(definition)):
            return assignment["id"], False
    arm("PUT", resource, ROLE_API, {"properties": {
        "principalId": principal, "principalType": principal_type,
        "roleDefinitionId": f"{BASE}/providers/Microsoft.Authorization/roleDefinitions/{definition}",
    }})
    return resource, True


def source_manifest(directory=APP_DIR):
    """Never open dotenv files. Reject links and non-allowlisted COPY/ADD sources."""
    for name in RUNTIME_FILES:
        path = directory / name
        require(path.is_file() and not path.is_symlink(), f"Missing/linked runtime file: {name}.")
        require(not any(p.is_symlink() for p in path.parents if p != directory.parent),
                "Linked build context is forbidden.")
    ignore = (directory / ".dockerignore").read_text().splitlines()
    rules = [s.strip() for s in ignore if s.strip() and not s.startswith("#")]
    # Final unconditional denies cannot be undone by earlier allowlist exceptions.
    require("**/.env*" in rules and "**" in rules,
            "Dockerignore must default-deny context and deny every .env*.")
    last_env = max(i for i, value in enumerate(rules) if value in (".env*", "**/.env*"))
    require(not any(r.startswith("!") for r in rules[last_env + 1:]),
            "Dockerignore can re-include secret paths after final denies.")
    require(not (directory / "Dockerfile.dockerignore").exists(),
            "Dockerfile-specific ignore override needs explicit review.")
    dockerfile = (directory / "Dockerfile").read_text()
    require(not re.search(r"(?im)^\s*(ADD|ARG)\s", dockerfile),
            "ADD and build ARG are not permitted in this audited image.")
    copies = re.findall(r"(?im)^\s*COPY\s+(.+)$", dockerfile)
    require(copies, "Dockerfile has no explicit runtime sources.")
    for copy in copies:
        tokens = shlex.split(copy)
        if tokens[0] == "--from=wheel":
            require(tokens == ["--from=wheel", "/wheels/", "/wheels/"],
                    "Unreviewed cross-stage COPY source.")
        else:
            require(all(t in {*RUNTIME_FILES, "redshift_mcp_server/*.py"} for t in tokens[:-1]),
                    "Dockerfile COPY must use allowlisted runtime sources, never COPY . or secrets.")
    require(re.search(r"(?m)^USER (?:10001:10001|10001|mcp)$", dockerfile)
            and "--host" in dockerfile and "0.0.0.0" in dockerfile,
            "Dockerfile must select nonroot USER and explicit public bind.")
    env_keys = {"PIP_NO_CACHE_DIR", "PIP_DISABLE_PIP_VERSION_CHECK",
                "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED"}
    for line in re.findall(r"(?m)^ENV (.+)$", dockerfile):
        require(all(t.split("=", 1)[0] in env_keys and "=" in t for t in shlex.split(line)),
                "Dockerfile ENV contains an unreviewed configuration key.")
    bases = re.findall(r"(?m)^FROM\s+(\S+)", dockerfile)
    require(bases and all(re.fullmatch(r"[^ \n]+@sha256:[a-f0-9]{64}", b) for b in bases),
            "Docker base image must be digest pinned.")
    digest = hashlib.sha256()
    for name in RUNTIME_FILES:
        digest.update(name.encode())
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def check(offline=False):
    require((ROOT / ".azure/deployment-plan.md").is_file(), "Approved plan missing.")
    source_manifest()
    if not offline:
        account = cli("account", "show")
        require(account["id"] == SUB and account["tenantId"] == TENANT,
                "Azure subscription/tenant does not match approved plan.")
        for namespace, kind, version in (
            ("Microsoft.App", "containerApps", APP_API),
            ("Microsoft.App", "managedEnvironments", APP_API),
            ("Microsoft.ContainerRegistry", "registries", ACR_API),
            ("Microsoft.KeyVault", "vaults", KV_API),
            ("Microsoft.ManagedIdentity", "userAssignedIdentities", ID_API),
        ):
            provider = cli("provider", "show", "--namespace", namespace)
            require(provider["registrationState"] == "Registered", "Required provider not registered.")
            resource = next(r for r in provider["resourceTypes"] if r["resourceType"] == kind)
            require(version in resource["apiVersions"], "Approved GA API unavailable.")
            stable = [v for v in resource["apiVersions"] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v)]
            require(stable and max(stable) == version,
                    "A newer GA API requires parent schema review before execution.")
        # A read-only lookup; an absent group is expected before initial provisioning.
        cli("group", "exists", "--name", RG)
        cli("sts", "get-caller-identity", azure=False)
    print("Read-only checks passed: allowlisted context excludes every dotenv path; no settings loaded.")


def prerequisites():
    groups_before = {g["id"].lower() for g in cli("group", "list")}
    existing = arm("GET", GROUP, "2023-07-01", missing=True)
    require(existing is None or existing["location"] == LOCATION, "Existing RG location mismatch.")
    if existing is None:
        arm("PUT", GROUP, "2023-07-01", {"location": LOCATION})
    registry = arm("GET", REGISTRY, ACR_API, missing=True)
    if registry is None:
        arm("PUT", REGISTRY, ACR_API, {
            "location": LOCATION, "sku": {"name": "Basic"}, "properties": {
                "adminUserEnabled": False, "anonymousPullEnabled": False,
                "publicNetworkAccess": "Enabled", "roleAssignmentMode": "LegacyRegistryPermissions",
                "policies": {"azureADAuthenticationAsArmPolicy": {"status": "enabled"}},
            }})
    identity = arm("GET", IDENTITY, ID_API, missing=True)
    if identity is None:
        arm("PUT", IDENTITY, ID_API, {"location": LOCATION, "properties": {}})
    identity = wait_resource(IDENTITY, ID_API)
    role(identity["properties"]["principalId"], REGISTRY, PULL)
    vault = arm("GET", VAULT_ID, KV_API, missing=True)
    if vault is None:
        arm("PUT", VAULT_ID, KV_API, {"location": LOCATION,
            "tags": {"SecurityControl": "Ignore"}, "properties": {
            "tenantId": TENANT, "sku": {"family": "A", "name": "standard"},
            "enableRbacAuthorization": True, "enableSoftDelete": True,
            "enablePurgeProtection": True, "softDeleteRetentionInDays": 90,
            "publicNetworkAccess": "Enabled", "accessPolicies": [],
        }})
    wait_resource(REGISTRY, ACR_API)
    wait_resource(VAULT_ID, KV_API)
    if arm("GET", ENV_ID, APP_API, missing=True) is None:
        cli("containerapp", "env", "create", "--name", ENV, "--resource-group", RG,
            "--location", LOCATION, "--enable-workload-profiles", "false", "--logs-destination", "none")
    wait_resource(ENV_ID, APP_API)
    groups_after = {g["id"].lower() for g in cli("group", "list")}
    require(groups_after - groups_before <= {GROUP.lower()},
            "Unexpected new resource group during provisioning; inspect subscription delta before continuing.")
    verify_infrastructure()
    quota()
    save_state(resource_ids=[GROUP, REGISTRY, VAULT_ID, IDENTITY, ENV_ID, APP_ID])


def verify_infrastructure():
    for resource, api in ((REGISTRY, ACR_API), (VAULT_ID, KV_API),
                          (IDENTITY, ID_API), (ENV_ID, APP_API)):
        obj = arm("GET", resource, api)
        require(obj["location"].lower().replace(" ", "") == LOCATION, "Resource outside approved region.")
        props = obj["properties"]
        if resource == REGISTRY:
            require(obj["sku"]["name"] == "Basic" and not props.get("adminUserEnabled")
                    and not props.get("anonymousPullEnabled")
                    and props.get("publicNetworkAccess") == "Enabled"
                    and props.get("roleAssignmentMode") == "LegacyRegistryPermissions"
                    and props.get("policies", {}).get("azureADAuthenticationAsArmPolicy", {}).get("status") == "enabled",
                    "ACR configuration drift; do not continue.")
        elif resource == VAULT_ID:
            require(props.get("enableRbacAuthorization") and props.get("enablePurgeProtection")
                    and props.get("enableSoftDelete") and props["sku"]["name"].lower() == "standard"
                    and props.get("publicNetworkAccess") == "Enabled"
                    and (obj.get("tags") or {}).get("SecurityControl") == "Ignore",
                    "Vault configuration drift.")
        elif resource == ENV_ID:
            profiles = props.get("workloadProfiles")
            consumption_only = profiles is None or profiles == []
            if isinstance(profiles, list) and len(profiles) == 1:
                profile = profiles[0]
                consumption_only = (
                    isinstance(profile, dict)
                    and profile.get("name") == "Consumption"
                    and profile.get("workloadProfileType") == "Consumption"
                    and profile.get("minimumCount") in (None, 0)
                    and profile.get("maximumCount") in (None, 0)
                )
            require(consumption_only and not props.get("infrastructureResourceGroup")
                    and not (props.get("vnetConfiguration") or {}).get("infrastructureSubnetId")
                    and not (props.get("vnetConfiguration") or {}).get("internal")
                    and (props.get("appLogsConfiguration") or {}).get("destination") in (None, "", "none"),
                    "Environment differs from single-RG Consumption/default-network/no-logs plan.")
    inventory = cli("resource", "list", "--resource-group", RG)
    forbidden = ("microsoft.network/", "microsoft.operationalinsights/")
    require(not any(r["type"].lower().startswith(forbidden) for r in inventory),
            "Unexpected network/log workspace in deployment RG.")


def quota():
    usages = cli("containerapp", "env", "list-usages", "--name", ENV, "--resource-group", RG)
    usages = usages.get("value", []) if isinstance(usages, dict) else usages
    candidates = [u for u in usages if "consumption" in json.dumps(u.get("name", {})).lower()
                  and "core" in json.dumps(u.get("name", {})).lower()]
    require(len(candidates) == 1, "Cannot identify Consumption core quota; inspect read-only usage metadata.")
    usage = candidates[0]
    require(float(usage["limit"]) - float(usage["currentValue"]) >= 0.5,
            "New environment requires at least 0.5 available Consumption cores; no quota increase authorized.")


def validate_image_tag(tag):
    require(isinstance(tag, str) and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}", tag),
            "Image tag must be 1-64 simple tag characters; repository overrides are forbidden.")
    return tag


def build(image_tag="v1", approved_source=None):
    validate_image_tag(image_tag)
    source_hash = source_manifest()
    require(approved_source is None or approved_source == source_hash,
            "Reviewed source fingerprint changed; stop and obtain a new review.")
    require(image_tag == "v1" or approved_source == source_hash,
            "A release build requires --approved-source-sha256 from reviewed source.")
    state = read_state()
    pending = state.get("release") or {}
    if pending and pending.get("status") != "complete":
        require(pending.get("image_tag") == image_tag
                and pending.get("source_sha256") == source_hash
                and pending.get("digest") == state.get("digest"),
                "Unfinished release evidence must not be replaced by another build.")
    records = dict(state.get("image_builds", {}))
    if state.get("digest"):
        records.setdefault(state.get("image_tag", "v1"), {
            "digest": state["digest"], "source_sha256": state.get("source_sha256"),
            "build_run": state.get("build_run"),
        })
    record = records.get(image_tag)
    if record:
        require(record.get("source_sha256") == source_hash,
                "Tag is already bound to different source; use a new reviewed tag.")
        if state.get("image_tag", "v1") == image_tag:
            require(record.get("digest") == state.get("digest")
                    and record.get("source_sha256") == state.get("source_sha256"),
                    "Recorded tag/source/digest evidence is inconsistent.")
        digest = cli("acr", "repository", "show", "--name", ACR,
                     "--image", f"redshift-mcp-server:{image_tag}")["digest"]
        require(digest == record["digest"], "Mutable image tag drift; review before rebuilding.")
        if state.get("image_tag", "v1") != image_tag:
            save_state(**record, image_tag=image_tag, image_builds=records)
        return
    tags = cli("acr", "repository", "list", "--name", ACR)
    if "redshift-mcp-server" in tags:
        tags = cli("acr", "repository", "show-tags", "--name", ACR,
                   "--repository", "redshift-mcp-server")
        require(image_tag not in tags, "Tag already exists without matching source evidence; never overwrite it.")
    context = DEPLOY_DIR / ".build-context"
    require(not context.exists(), "Owned build context already exists; inspect/remove it before retry.")
    context.mkdir(mode=0o700)
    try:
        for name in RUNTIME_FILES:
            destination = context / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(APP_DIR / name, destination)
        require(source_manifest(context) == source_hash, "Context changed during staging.")
        require({str(p.relative_to(context)) for p in context.rglob("*") if p.is_file()}
                == set(RUNTIME_FILES), "Context contains an unexpected path.")
        result = cli("acr", "build", "--registry", ACR, "--resource-group", RG,
                     "--image", f"redshift-mcp-server:{image_tag}", "--platform", "linux/amd64",
                     "--no-logs", str(context))
        require(result and result.get("status") == "Succeeded", "ACR build did not succeed.")
        platform = result.get("platform") or {}
        require(platform.get("os", "").lower() == "linux"
                and platform.get("architecture", "").lower() == "amd64",
                "ACR build did not confirm the approved Linux/AMD64 platform.")
        manifest = cli("acr", "repository", "show", "--name", ACR,
                       "--image", f"redshift-mcp-server:{image_tag}")
        require(re.fullmatch(r"sha256:[a-f0-9]{64}", manifest["digest"]), "Invalid built image digest.")
        record = {"digest": manifest["digest"], "source_sha256": source_hash,
                  "build_run": result.get("runId")}
        records[image_tag] = record
        save_state(**record, image_tag=image_tag, image_builds=records)
    finally:
        shutil.rmtree(context)


def settings():
    # The only legitimate dotenv read, at explicitly authorized app/configure execution.
    sys.path.insert(0, str(APP_DIR))
    from redshift_mcp_server.config import Settings, load_environment
    before = dict(os.environ)
    try:
        load_environment(APP_DIR / ".env")
        result = Settings.from_env()
        require(result.auth_mode == "password", "This approval covers password auth only; IAM is deferred.")
        require(result.port == 5439, "Approved firewall permits only TCP5439.")
        return result
    finally:
        os.environ.clear()
        os.environ.update(before)


def app_document(config, configured=False, fqdn=None):
    digest = read_state().get("digest")
    require(digest is not None, "Build stage and immutable image digest required.")
    environment = [{"name": key, "value": str(getattr(config, attr))}
                   for key, attr in NONSECRET.items() if getattr(config, attr) is not None]
    if fqdn:
        environment.append({"name": "REDSHIFT_MCP_ALLOWED_HOSTS", "value": fqdn})
    secrets = []
    if configured:
        secrets = [{"name": "redshift-password", "keyVaultUrl": SECRET_URL, "identity": "system"}]
        environment.append({"name": "REDSHIFT_PASSWORD", "secretRef": "redshift-password"})
    probes = [{"type": kind, "httpGet": {"path": "/healthz", "port": 8000, "scheme": "HTTP"},
               "periodSeconds": 10, "timeoutSeconds": 3, "failureThreshold": 12}
              for kind in ("Startup", "Liveness", "Readiness")]
    return {
        "location": LOCATION,
        "identity": {"type": "SystemAssigned,UserAssigned", "userAssignedIdentities": {IDENTITY: {}}},
        "properties": {"environmentId": ENV_ID, "configuration": {
            "activeRevisionsMode": "Single",
            "ingress": {"external": True, "targetPort": 8000, "allowInsecure": False,
                        "transport": "auto"},
            "registries": [{"server": f"{ACR}.azurecr.io", "identity": IDENTITY}],
            "secrets": secrets,
        }, "template": {
            "containers": [{"name": "redshift-mcp-server",
                            "image": f"{ACR}.azurecr.io/redshift-mcp-server@{digest}",
                            "resources": {"cpu": 0.25, "memory": "0.5Gi"},
                            "env": environment, "probes": probes}],
            "scale": {"minReplicas": 1, "maxReplicas": 1},
        }},
    }


def app():
    verify_infrastructure()
    quota()
    current = arm("GET", APP_ID, APP_API, missing=True)
    if current is not None:
        require(current["properties"]["environmentId"].lower() == ENV_ID.lower(),
                "Existing app belongs to a different environment.")
        # Never downgrade a configured deployment back to credential-free bootstrap.
        require(current["identity"].get("principalId"), "Existing app has no system identity.")
        return
    arm("PUT", APP_ID, APP_API, app_document(settings()))
    current = wait_resource(APP_ID, APP_API)
    save_state(fqdn=current["properties"]["configuration"]["ingress"]["fqdn"])


def fingerprint(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def release_container(current):
    containers = current["properties"]["template"]["containers"]
    matches = [c for c in containers if c.get("name") == "redshift-mcp-server"]
    require(len(matches) == 1, "Expected exactly one named MCP container; no update performed.")
    return matches[0]


def app_fingerprint(current, ignore_image=False):
    """Keep all configuration/identity fields; ignore only ARM revision bookkeeping."""
    document = copy.deepcopy(current)
    for name in ("etag", "systemData"):
        document.pop(name, None)
    props = document["properties"]
    for name in ("provisioningState", "runningStatus", "latestRevisionName",
                 "latestReadyRevisionName", "latestRevisionFqdn", "eventStreamEndpoint"):
        props.pop(name, None)
    props["template"].pop("revisionSuffix", None)
    if ignore_image:
        release_container(document)["image"] = "<intended-image-change>"
    return fingerprint(document)


def configured_release_app(current):
    require(current.get("id", "").lower() == APP_ID.lower()
            and current.get("name") == APP
            and current.get("type", "").lower() == "microsoft.app/containerapps"
            and current.get("location", "").lower().replace(" ", "") == LOCATION,
            "Update target differs from approved app/region.")
    props = current["properties"]
    require(props.get("environmentId", "").lower() == ENV_ID.lower()
            and props.get("provisioningState") == "Succeeded",
            "Update requires the existing provisioned approved environment/app.")
    identity = current.get("identity") or {}
    require(identity.get("type", "").replace(" ", "") == "SystemAssigned,UserAssigned"
            and identity.get("principalId") and identity.get("tenantId") == TENANT,
            "Update requires the existing system identity and approved tenant.")
    identities = identity.get("userAssignedIdentities") or {}
    require({key.lower() for key in identities} == {IDENTITY.lower()},
            "Update image-pull identity differs from approval.")
    assigned = next(iter(identities.values()))
    live = arm("GET", IDENTITY, ID_API)["properties"]
    require(assigned.get("principalId") and assigned.get("clientId")
            and assigned["principalId"] == live.get("principalId")
            and assigned["clientId"] == live.get("clientId"),
            "Image-pull identity principal/client changed or missing.")
    config = props["configuration"]
    ingress = config.get("ingress") or {}
    require(config.get("activeRevisionsMode") == "Single"
            and ingress.get("external") and ingress.get("allowInsecure") is False
            and ingress.get("targetPort") == 8000 and ingress.get("fqdn"),
            "Update requires configured single-revision HTTPS ingress.")
    registries = config.get("registries") or []
    require(len(registries) == 1 and registries[0].get("server") == f"{ACR}.azurecr.io"
            and registries[0].get("identity", "").lower() == IDENTITY.lower()
            and not registries[0].get("passwordSecretRef") and not registries[0].get("username"),
            "Update requires only the approved identity-based registry reference.")
    secrets = config.get("secrets") or []
    require(all(not s.get("value") for s in secrets),
            "Secret values are forbidden in release snapshots.")
    secret = next((s for s in secrets if s.get("name") == "redshift-password"), {})
    require(secret.get("keyVaultUrl") == SECRET_URL and secret.get("identity") == "system",
            "Update requires the configured system-identity Key Vault reference.")
    container = release_container(current)
    require(any(e.get("name") == "REDSHIFT_PASSWORD"
                and e.get("secretRef") == "redshift-password" and not e.get("value")
                for e in container.get("env", [])),
            "Update requires the existing password secret reference.")
    require(re.fullmatch(re.escape(IMAGE_REPOSITORY) + r"@sha256:[a-f0-9]{64}",
                         container.get("image", "")),
            "Existing image must be pinned to the approved repository digest.")
    return current


def release_evidence(image_tag, approved_source):
    validate_image_tag(image_tag)
    state = read_state()
    require(state.get("image_tag", "v1") == image_tag,
            "Selected tag does not match built metadata.")
    require(re.fullmatch(r"sha256:[a-f0-9]{64}", state.get("digest", "")),
            "A confirmed built digest is required.")
    require(approved_source and approved_source == state.get("source_sha256")
            and source_manifest() == approved_source,
            "Reviewed source differs from built/current source; rebuild with a new tag.")
    record = (state.get("image_builds") or {}).get(image_tag)
    require(record is None or (record.get("digest") == state["digest"]
                              and record.get("source_sha256") == approved_source),
            "Recorded tag/source/digest evidence is inconsistent.")
    manifest = cli("acr", "repository", "show", "--name", ACR,
                   "--image", f"redshift-mcp-server:{image_tag}")
    require(manifest.get("digest") == state["digest"],
            "Registry tag/digest drift; no app update permitted.")
    return state


def update(image_tag="v1", approved_source=None, approved_app=None, apply=False):
    """Only PATCH the captured template. Never call bootstrap, secret or grant stages."""
    validate_image_tag(image_tag)
    current = configured_release_app(arm("GET", APP_ID, APP_API))
    if not apply:
        print(f"Release review: source_sha256={source_manifest()} "
              f"app_sha256={app_fingerprint(current)} image_tag={image_tag}")
        print(f"Current image={release_container(current)['image']} "
              f"revision={current['properties'].get('latestRevisionName')}")
        return
    state = release_evidence(image_tag, approved_source)
    desired = f"{IMAGE_REPOSITORY}@{state['digest']}"
    release = state.get("release") or {}
    same_release = (release.get("image_tag") == image_tag
                    and release.get("digest") == state["digest"]
                    and release.get("source_sha256") == approved_source)
    if release and release.get("status") != "complete":
        require(same_release, "An unfinished release has different source/tag/digest; investigate manually.")
    if same_release:
        require(approved_app == release.get("approved_app_sha256"),
                "Retry requires the original approved app fingerprint.")
        require(app_fingerprint(current, True) == release["preserved_sha256"],
                "Existing identity/configuration drift from release snapshot; stop.")
        require(release_container(current)["image"] in (desired, release["previous_image"]),
                "Existing image drift from release snapshot; stop.")
    else:
        require(approved_app and app_fingerprint(current) == approved_app,
                "Current app does not match the reviewed app fingerprint.")
        require(release_container(current)["image"] != desired,
                "New release must change the image; missing matching retry evidence.")
        release = {
            "image_tag": image_tag, "digest": state["digest"], "source_sha256": approved_source,
            "approved_app_sha256": approved_app,
            "preserved_sha256": app_fingerprint(current, True),
            "previous_image": release_container(current)["image"],
            "previous_revision": current["properties"].get("latestRevisionName"),
            "status": "pending",
        }
        require(release["previous_revision"], "Previous revision is missing; no update permitted.")
        save_state(release=release)
    if release_container(current)["image"] != desired:
        fresh = configured_release_app(arm("GET", APP_ID, APP_API))
        require(app_fingerprint(fresh) == app_fingerprint(current),
                "Concurrent app change before update; no mutation performed.")
        require(source_manifest() == approved_source
                and read_state() == {**state, "release": release},
                "Local release evidence changed before update; stop.")
        release_evidence(image_tag, approved_source)
        template = copy.deepcopy(fresh["properties"]["template"])
        template.pop("revisionSuffix", None)
        document = {"properties": {"template": template}}
        release_container(document)["image"] = desired
        arm("PATCH", APP_ID, APP_API, document, if_match=fresh.get("etag"))
    for _ in range(80):
        current = arm("GET", APP_ID, APP_API)
        require(app_fingerprint(current, True) == release["preserved_sha256"]
                and release_container(current)["image"] == desired,
                "Post-update image/identity/configuration drift; investigate without broad recovery.")
        props = current["properties"]
        require(props.get("provisioningState") not in ("Failed", "Canceled"),
                "Image revision failed; previous image/revision retained in release metadata.")
        revision = props.get("latestRevisionName")
        revisions = cli("containerapp", "revision", "list", "--name", APP, "--resource-group", RG)
        if (props.get("provisioningState") == "Succeeded"
                and revision != release["previous_revision"]
                and sole_healthy_running_revision(revisions, revision)):
            require(read_state() == {**state, "release": release},
                    "Local release metadata changed while waiting for readiness; stop.")
            release_evidence(image_tag, approved_source)
            release["status"] = "complete"
            save_state(release=release, revision=revision,
                       fqdn=props["configuration"]["ingress"]["fqdn"])
            print(f"Image update ready: revision={revision} digest={state['digest']} "
                  f"rollback_image={release['previous_image']} "
                  f"rollback_revision={release['previous_revision']}; run full verify.")
            return
        time.sleep(15)
    raise DeploymentError("Image revision readiness timed out; retain evidence and retry only the same release.")


def upload_password(config):
    from azure.core.exceptions import HttpResponseError
    from azure.keyvault.secrets import SecretClient
    # Principal discovery uses signed-in CLI metadata, never decoding/printing tokens.
    principal = cli("ad", "signed-in-user", "show")["id"]
    owned = read_state().get("owned_officer")
    if owned:
        require(owned.startswith(f"{VAULT_ID}/providers/Microsoft.Authorization/roleAssignments/"),
                "Invalid owned temporary role metadata.")
        previous = arm("GET", owned, ROLE_API, missing=True)
        if previous:
            props = previous["properties"]
            require(props["principalId"] == principal and props["scope"].lower() == VAULT_ID.lower()
                    and props["roleDefinitionId"].endswith(OFFICER),
                    "Stored role ownership mismatch; no permission removed.")
            arm("DELETE", owned, ROLE_API, missing=True)
        save_state(owned_officer=None)
    client = SecretClient(f"https://{VAULT}.vault.azure.net", credential(),
                          logging_enable=False, retry_total=0)
    temporary = None
    try:
        # Try existing authority first; do not unnecessarily grant extra permission.
        for attempt in range(13):
            try:
                try:
                    previous = client.get_secret("redshift-password", logging_enable=False)
                except HttpResponseError as exc:
                    if exc.status_code != 404:
                        raise
                    previous = None
                if previous is not None and previous.value == config.password:
                    return
                written = client.set_secret("redshift-password", config.password, logging_enable=False)
                require(written.value == config.password, "Vault transfer equality check failed.")
                return
            except HttpResponseError as exc:
                if exc.status_code != 403:
                    raise DeploymentError(f"Vault upload failed (HTTP {exc.status_code}); details suppressed.") from None
                if attempt == 0:
                    assignments = arm("GET",
                        f"{VAULT_ID}/providers/Microsoft.Authorization/roleAssignments", ROLE_API)
                    existing = any(
                        a["properties"]["principalId"].lower() == principal.lower()
                        and a["properties"]["scope"].lower() == VAULT_ID.lower()
                        and a["properties"]["roleDefinitionId"].endswith(OFFICER)
                        for a in assignments.get("value", [])
                    )
                    if not existing:
                        temporary = f"{VAULT_ID}/providers/Microsoft.Authorization/roleAssignments/{uuid.uuid4()}"
                        # Record ownership BEFORE mutation, so interruption is recoverable.
                        save_state(owned_officer=temporary)
                        arm("PUT", temporary, ROLE_API, {"properties": {
                            "principalId": principal, "principalType": "User",
                            "roleDefinitionId": f"{BASE}/providers/Microsoft.Authorization/roleDefinitions/{OFFICER}",
                        }})
                time.sleep(10)
        raise DeploymentError("Vault RBAC propagation timed out; no password printed.")
    finally:
        try:
            client.close()
        finally:
            if temporary:
                arm("DELETE", temporary, ROLE_API, missing=True)
                save_state(owned_officer=None)


def aws_rule():
    print("WARNING: approved POC exposes TCP5439 to all IPv4; default AWS principal may be root.")
    rules = cli("ec2", "describe-security-group-rules", "--filters",
                f"Name=group-id,Values={SG}", azure=False)["SecurityGroupRules"]
    if any(not r["IsEgress"] and r.get("IpProtocol") == "tcp"
           and r.get("FromPort") == 5439 and r.get("ToPort") == 5439
           and r.get("CidrIpv4") == "0.0.0.0/0" for r in rules):
        return
    result = cli("ec2", "authorize-security-group-ingress", "--group-id", SG,
                 "--protocol", "tcp", "--port", "5439", "--cidr", "0.0.0.0/0", azure=False)
    created = result.get("SecurityGroupRules", [])
    require(len(created) == 1, "AWS did not return exactly one created rule; inspect metadata.")
    save_state(owned_aws_rule=created[0]["SecurityGroupRuleId"])


def configure():
    current = arm("GET", APP_ID, APP_API)
    config = settings()
    upload_password(config)
    principal = current["identity"]["principalId"]
    _, created = role(principal, SECRET_SCOPE, READER)
    if created:
        time.sleep(60)
    fqdn = current["properties"]["configuration"]["ingress"]["fqdn"]
    document = app_document(config, configured=True, fqdn=fqdn)
    # ACA resolves a newly granted secret role asynchronously; only retry known 403s
    # is unsafe here because ARM can wrap that status. Fail safely and resume stage.
    arm("PUT", APP_ID, APP_API, document)
    current = wait_resource(APP_ID, APP_API)
    save_state(fqdn=fqdn, revision=current["properties"].get("latestRevisionName"))
    aws_rule()


async def mcp_acceptance(fqdn):
    import chat_deploy
    try:
        reference = await asyncio.to_thread(chat_deploy.analytics_reference)
        await chat_deploy.mcp_acceptance(reference, f"https://{fqdn}/mcp")
    except chat_deploy.DeploymentError:
        raise DeploymentError("Live MCP numerical acceptance failed; details suppressed.") from None


def sole_healthy_running_revision(revisions, latest_revision):
    active = [r for r in revisions if r["properties"].get("active")]
    return (len(active) == 1 and active[0]["name"] == latest_revision
            and active[0]["properties"].get("healthState") == "Healthy"
            and active[0]["properties"].get("runningState") in ("Running", "RunningAtMaxScale"))


def verify(image_tag="v1"):
    validate_image_tag(image_tag)
    state = read_state()
    require(state.get("image_tag", "v1") == image_tag,
            "Verification tag differs from built metadata.")
    if state.get("release"):
        release_evidence(image_tag, state.get("source_sha256"))
    verify_infrastructure()
    current = arm("GET", APP_ID, APP_API)
    props = current["properties"]
    if state.get("release"):
        require(state["release"].get("status") == "complete"
                and state["release"].get("image_tag") == image_tag
                and state["release"].get("digest") == state.get("digest")
                and state["release"].get("source_sha256") == state.get("source_sha256")
                and app_fingerprint(current, True) == state["release"]["preserved_sha256"],
                "Release image/identity/configuration evidence differs; full verification stopped.")
    require(current["location"].lower().replace(" ", "") == LOCATION,
            "App is outside Brazil South.")
    require(current["identity"]["type"] == "SystemAssigned, UserAssigned"
            or current["identity"]["type"].replace(" ", "") == "SystemAssigned,UserAssigned",
            "App must retain both identities.")
    require({k.lower() for k in current["identity"]["userAssignedIdentities"]} == {IDENTITY.lower()},
            "App has an unexpected user-assigned identity.")
    config = props["configuration"]
    require(config["activeRevisionsMode"] == "Single"
            and config["ingress"]["external"] and not config["ingress"]["allowInsecure"],
            "HTTPS ingress/revision configuration mismatch.")
    require(len(config["registries"]) == 1
            and config["registries"][0]["server"] == f"{ACR}.azurecr.io"
            and config["registries"][0]["identity"].lower() == IDENTITY.lower()
            and not config["registries"][0].get("passwordSecretRef"),
            "Registry pull identity mismatch.")
    secret = next((s for s in config["secrets"] if s["name"] == "redshift-password"), {})
    require(secret.get("identity") == "system" and secret.get("keyVaultUrl") == SECRET_URL
            and not secret.get("value"), "Vault secret reference identity mismatch.")
    container = release_container(current)
    require(container["image"] == f"{ACR}.azurecr.io/redshift-mcp-server@{read_state()['digest']}"
            and container["resources"]["cpu"] == 0.25
            and container["resources"]["memory"] == "0.5Gi"
            and props["template"]["scale"]["minReplicas"] == 1
            and props["template"]["scale"]["maxReplicas"] == 1,
            "App image, resources or scaling do not match the approved deployment.")
    require({p["type"] for p in container["probes"]} == {"Startup", "Liveness", "Readiness"}
            and all(p.get("httpGet", {}).get("path") == "/healthz"
                    and p["httpGet"]["port"] == 8000 for p in container["probes"]),
            "No-DB health probes are missing or incorrect.")
    require(any(e["name"] == "REDSHIFT_PASSWORD" and e.get("secretRef") == "redshift-password"
                and not e.get("value")
                for e in container["env"]), "Password is not a secretRef.")
    for principal, scope, definition in (
        (current["identity"]["principalId"], SECRET_SCOPE, READER),
        (arm("GET", IDENTITY, ID_API)["properties"]["principalId"], REGISTRY, PULL),
    ):
        assignments = cli("role", "assignment", "list", "--assignee-object-id", principal,
                          "--all", "--include-inherited")
        require(any(a["scope"].lower() == scope.lower()
                    and a["roleDefinitionId"].endswith(definition) for a in assignments),
                "Required exact-scope identity role missing.")
        require(all(a["scope"].lower() == scope.lower()
                    and a["roleDefinitionId"].endswith(definition) for a in assignments),
                "Managed identity has unexpected extra role; inspect least privilege.")
    revision = props["latestRevisionName"]
    revisions = cli("containerapp", "revision", "list", "--name", APP, "--resource-group", RG)
    require(sole_healthy_running_revision(revisions, revision),
            "Latest revision is not the sole healthy running revision; use sanitized diagnostics.")
    fqdn = config["ingress"]["fqdn"]
    with urlopen(f"https://{fqdn}/healthz", timeout=15) as response:
        require(response.status == 200, "Public HTTPS health failed.")
    for headers, statuses in (
        ({"Origin": "https://untrusted.invalid"}, {400, 403}),
        ({"Host": "untrusted.invalid"}, {400, 403, 404, 421}),
    ):
        request = Request(f"https://{fqdn}/mcp", data=b"{}", headers={
            "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
            **headers,
        })
        try:
            with urlopen(request, timeout=15):
                raise DeploymentError("Untrusted MCP host/origin was not rejected.")
        except HTTPError as exc:
            require(exc.code in statuses, "Unexpected result for MCP host/origin rejection.")
    rules = cli("ec2", "describe-security-group-rules", "--filters",
                f"Name=group-id,Values={SG}", azure=False)["SecurityGroupRules"]
    require(any(not r["IsEgress"] and r.get("IpProtocol") == "tcp"
                and r.get("FromPort") == 5439 and r.get("ToPort") == 5439
                and r.get("CidrIpv4") == "0.0.0.0/0" for r in rules),
            "Approved AWS TCP5439 IPv4 rule missing.")
    asyncio.run(mcp_acceptance(fqdn))
    save_state(fqdn=fqdn, revision=revision)
    print(f"VERIFIED https://{fqdn}/mcp revision={revision} digest={read_state()['digest']}")


def diagnose():
    """Classify console/system logs in memory; never emit log lines."""
    categories = set()
    for kind in ("system", "console"):
        try:
            logs = cli("containerapp", "logs", "show", "--name", APP, "--resource-group", RG,
                       "--type", kind, "--tail", "30")
            text = json.dumps(logs).lower()
            for label, pattern in (
                ("image-pull", "imagepull|unauthorized|manifest unknown"),
                ("vault-authorization", "keyvault|key vault|forbidden"),
                ("host-config", "invalid host|invalid origin|421"),
                ("startup-config", "argument|configuration|traceback"),
            ):
                if re.search(pattern, text):
                    categories.add(label)
        except Exception:  # noqa: BLE001 -- Logs must never leak through exception formatting.
            categories.add("logs-unavailable")
    print("Sanitized diagnostics: " + (", ".join(sorted(categories)) or "unclassified; no raw logs emitted"))


def main(argv=None):
    quiet_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Cloud mutations; only after parent gates.")
    mode.add_argument("--check", "--validate", action="store_true", help="Read-only validation (default).")
    parser.add_argument("--offline", action="store_true", help="Only source/build-context checks.")
    parser.add_argument("--stage", choices=(*STAGES, "update", "all"))
    parser.add_argument("--image-tag", default="v1",
                        help="Approved repository tag (default v1); use a fresh tag for changed source.")
    parser.add_argument("--approved-source-sha256", help="Independently reviewed runtime fingerprint.")
    parser.add_argument("--approved-app-sha256", help="Reviewed current-app fingerprint for image-only update.")
    parser.add_argument("--restart-once", action="store_true",
                        help="For apply verify only: classify logs, then restart latest revision once.")
    args = parser.parse_args(argv)
    validate_image_tag(args.image_tag)
    for value in (args.approved_source_sha256, args.approved_app_sha256):
        require(value is None or re.fullmatch(r"[a-f0-9]{64}", value),
                "Approval fingerprints must be 64 lowercase hex characters.")
    require(not args.apply or args.stage, "--apply requires an explicit --stage.")
    require(not args.apply or not args.offline, "--offline cannot mutate.")
    require(not args.restart_once or (args.apply and args.stage == "verify"),
            "--restart-once requires --apply --stage verify.")
    check(args.offline)
    if not args.apply:
        if args.stage == "update":
            require(not args.offline, "Update review requires a live read-only app snapshot.")
            update(args.image_tag)
        return
    stages = STAGES if args.stage == "all" else (args.stage,)
    try:
        for stage in stages:
            print(f"Stage: {stage}")
            if stage == "build":
                build(args.image_tag, args.approved_source_sha256)
            elif stage == "update":
                update(args.image_tag, args.approved_source_sha256,
                       args.approved_app_sha256, apply=True)
            elif stage == "verify":
                verify(args.image_tag)
            else:
                globals()[stage]()
    except Exception:
        if args.stage == "verify" or args.stage == "all":
            diagnose()
            if args.restart_once:
                current = arm("GET", APP_ID, APP_API)
                cli("containerapp", "revision", "restart", "--name", APP, "--resource-group", RG,
                    "--revision", current["properties"]["latestRevisionName"])
                time.sleep(30)
                verify(args.image_tag)
                return
        raise


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except DeploymentError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except BaseException as exc:  # noqa: BLE001 -- Security boundary: no unsanitized exceptions.
        # No traceback, repr, dependency diagnostics, request bodies, or settings.
        print(f"FAILED: operation interrupted ({type(exc).__name__}); details suppressed.", file=sys.stderr)
        sys.exit(1)
