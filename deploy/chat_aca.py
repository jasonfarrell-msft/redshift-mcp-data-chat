#!/usr/bin/env python3
"""Target-specific ACA migration. Defaults are local/read-only; never repairs App Service."""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

import deploy as shared

SOURCE = shared.ROOT / "src/redshift-chat"
APP = "ca-redshift-chat-bs01"
APP_ID = f"{shared.GROUP}/providers/Microsoft.App/containerApps/{APP}"
DOMAIN = "happygrass-e982f5d6.brazilsouth.azurecontainerapps.io"
ORIGIN = f"https://{APP}.{DOMAIN}"
REPOSITORY = f"{shared.ACR}.azurecr.io/redshift-chat"
PROJECT_ID = (f"{shared.BASE}/resourceGroups/rg-client-sandbox-eus2-mx01/providers/"
              "Microsoft.CognitiveServices/accounts/foundry-sandbox-swc-mx01/projects/redshift-test-project")
ROLES = ("eed3b665-ab3a-47b6-8f48-c9382fb1dad6", "a97b65f3-24c7-4388-baec-2e87135dc908")
FIXED_FILES = (
    "Dockerfile", ".dockerignore", "package.json", "package-lock.json",
    "tsconfig.json", "tsconfig.server.json", "vite.config.ts",
)
CONTEXT = shared.DEPLOY_DIR / ".chat-aca-context"
EVIDENCE = shared.DEPLOY_DIR / ".chat-aca-image.json"


def source_files(source=SOURCE):
    files = list(FIXED_FILES)
    for folder, extensions in (("server", {".ts"}), ("client", {".ts", ".tsx", ".css", ".html"})):
        directory = source / folder
        shared.require(not directory.is_symlink(), "Linked source directory forbidden.")
        files.extend(str(p.relative_to(source)) for p in directory.iterdir()
                     if not p.name.startswith(".") and p.suffix in extensions and p.is_file())
    for name in files:
        path = source / name
        shared.require(path.is_file() and not path.is_symlink(), "Missing or linked build input.")
    return sorted(files)


def source_hash(source=SOURCE):
    digest = hashlib.sha256()
    for name in source_files(source):
        digest.update(name.encode() + b"\0" + (source / name).read_bytes() + b"\0")
    return digest.hexdigest()


def image_reference(value):
    shared.require(isinstance(value, str) and
                   re.fullmatch(re.escape(REPOSITORY) + r"@sha256:[a-f0-9]{64}", value),
                   "An immutable digest in the chat repository is required.")
    return value


def definition(image):
    image_reference(image)
    return {
        "location": "brazilsouth",
        "identity": {"type": "SystemAssigned, UserAssigned",
                     "userAssignedIdentities": {shared.IDENTITY: {}}},
        "properties": {
            "environmentId": shared.ENV_ID,
            "configuration": {
                "activeRevisionsMode": "Single",
                "ingress": {"external": True, "targetPort": 8080, "transport": "http",
                            "allowInsecure": False},
                "registries": [{"server": f"{shared.ACR}.azurecr.io", "identity": shared.IDENTITY}],
            },
            "template": {
                "containers": [{
                    "name": "chat", "image": image,
                    "resources": {"cpu": 0.25, "memory": "0.5Gi"},
                    "env": [{"name": key, "value": value} for key, value in {
                        "NODE_ENV": "production", "PORT": "8080", "PUBLIC_ORIGIN": ORIGIN,
                        "FOUNDRY_PROJECT_ENDPOINT": "https://foundry-sandbox-swc-mx01.services.ai.azure.com/api/projects/redshift-test-project",
                        "FOUNDRY_AGENT_NAME": "redshift-chat-agent", "FOUNDRY_AGENT_VERSION": "2",
                        "MCP_SERVER_URL": "https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp",
                    }.items()],
                    "probes": [{
                        "type": kind, "httpGet": {"path": "/healthz", "port": 8080, "scheme": "HTTP"},
                        "periodSeconds": 10, "timeoutSeconds": 2,
                        "failureThreshold": 30 if kind == "Startup" else 3,
                    } for kind in ("Startup", "Readiness", "Liveness")],
                }],
                "scale": {"minReplicas": 1, "maxReplicas": 1},
            },
        },
    }


def check_context():
    env = shared.arm("GET", shared.ENV_ID, shared.APP_API)
    props = env.get("properties", {})
    shared.require(env["location"].replace(" ", "").lower() == "brazilsouth"
                   and props["defaultDomain"] == DOMAIN, "Existing environment differs from reviewed target.")
    registry = shared.arm("GET", shared.REGISTRY, shared.ACR_API)
    shared.require(registry["properties"]["loginServer"] == f"{shared.ACR}.azurecr.io"
                   and registry["properties"]["adminUserEnabled"] is False,
                   "Registry differs from reviewed keyless target.")
    shared.arm("GET", shared.IDENTITY, shared.ID_API)


def build(approved_source):
    shared.require(source_hash() == approved_source, "Reviewed source fingerprint changed.")
    shared.require(not CONTEXT.exists() and not CONTEXT.is_symlink(), "Build context already exists.")
    shared.require(not EVIDENCE.is_symlink(), "Linked evidence forbidden.")
    tag = "aca-" + approved_source
    repositories = shared.cli("acr", "repository", "list", "--name", shared.ACR)
    if "redshift-chat" in repositories:
        tags = shared.cli("acr", "repository", "show-tags", "--name", shared.ACR,
                          "--repository", "redshift-chat")
        shared.require(tag not in tags, "Build tag already exists; preserve evidence; do not overwrite.")
    CONTEXT.mkdir(mode=0o700)
    try:
        for name in source_files():
            path = CONTEXT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, path)
        shared.require(source_hash(CONTEXT) == approved_source, "Staged source changed.")
        result = shared.cli("acr", "build", "--registry", shared.ACR, "--resource-group", shared.RG,
                            "--image", f"redshift-chat:{tag}", "--platform", "linux/amd64",
                            "--no-logs", str(CONTEXT))
        shared.require(result and result.get("status") == "Succeeded"
                       and result.get("platform", {}).get("os") == "linux"
                       and result.get("platform", {}).get("architecture") == "amd64",
                       "ACR Linux/AMD64 build not confirmed.")
        manifest = shared.cli("acr", "repository", "show", "--name", shared.ACR,
                              "--image", f"redshift-chat:{tag}")
        image = image_reference(f"{REPOSITORY}@{manifest['digest']}")
        EVIDENCE.write_text(json.dumps({
            "source_sha256": approved_source, "image": image, "tag": tag,
            "build_run": result["runId"], "platform": "linux/amd64",
        }, indent=2) + "\n")
        print(image)
    finally:
        shutil.rmtree(CONTEXT)


def create(image, approved_source):
    shared.require(source_hash() == approved_source, "Reviewed source changed.")
    shared.require(EVIDENCE.is_file() and not EVIDENCE.is_symlink(), "Build evidence required.")
    evidence = json.loads(EVIDENCE.read_text())
    shared.require(evidence["source_sha256"] == approved_source and evidence["image"] == image,
                   "Image/source evidence mismatch.")
    manifest = shared.cli("acr", "repository", "show", "--name", shared.ACR,
                          "--image", f"redshift-chat:{evidence['tag']}")
    shared.require(image == f"{REPOSITORY}@{manifest['digest']}", "Registry digest drift.")
    shared.require(shared.arm("GET", APP_ID, shared.APP_API, missing=True) is None,
                   "Chat app already exists; this creation helper never overwrites it.")
    shared.arm("PUT", APP_ID, shared.APP_API, definition(image))
    grant_roles(image)


def grant_roles(image):
    current = shared.wait_resource(APP_ID, shared.APP_API)
    shared.require(current["properties"]["environmentId"].lower() == shared.ENV_ID.lower()
                   and current["properties"]["template"]["containers"][0]["image"] == image,
                   "Existing chat target/image mismatch.")
    shared.require(current["properties"]["configuration"]["ingress"]["fqdn"] == ORIGIN[8:],
                   "Actual HTTPS origin differs; review before role grants.")
    for role in ROLES:
        shared.role(current["identity"]["principalId"], PROJECT_ID, role)
    print(f"Chat identity roles ready: {ORIGIN}; live acceptance still required.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("plan", "check", "build", "create", "roles"))
    parser.add_argument("--image")
    parser.add_argument("--approved-source-sha256")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.stage == "plan":
        print(json.dumps({"source_sha256": source_hash(), "origin": ORIGIN,
                          "environment": shared.ENV_ID, "role_scope": PROJECT_ID, "roles": ROLES,
                          "definition": definition(args.image or f"{REPOSITORY}@sha256:{'0' * 64}")}, indent=2))
        return
    check_context()
    if args.stage == "check":
        print("Existing ACA environment/registry/identity match; no writes performed.")
        return
    shared.require(args.execute, "Cloud mutation requires --execute after independent review/validation.")
    if args.stage in ("build", "create"):
        shared.require(bool(re.fullmatch(r"[a-f0-9]{64}", args.approved_source_sha256 or "")),
                       "Reviewed source SHA256 required.")
    if args.stage == "build":
        build(args.approved_source_sha256)
    else:
        image_reference(args.image)
        if args.stage == "create":
            create(args.image, args.approved_source_sha256)
        else:
            grant_roles(args.image)


if __name__ == "__main__":
    try:
        main()
    except shared.DeploymentError as exc:
        raise SystemExit(str(exc)) from None
