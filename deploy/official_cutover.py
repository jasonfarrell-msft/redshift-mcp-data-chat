#!/usr/bin/env python3
"""Narrow review artifacts and snapshot-guarded chat revision update/rollback.

ACA Update has no documented If-Match contract. A local operator lock and fresh
snapshots detect observed drift, NOT atomic CAS; an external-writer window remains.
"""

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

import chat_aca
import chat_deploy

import deploy as shared

CANDIDATE = "ca-redshift-official-bs01"
CANDIDATE_ID = f"{shared.GROUP}/providers/Microsoft.App/containerApps/{CANDIDATE}"
CANDIDATE_URL = f"https://{CANDIDATE}.{chat_aca.DOMAIN}/mcp"
OLD_URL = f"https://ca-redshift-bs01.{chat_aca.DOMAIN}/mcp"
CHAT_PRINCIPAL = "92f43c89-a02c-4636-b7c5-775067c221d5"
CHAT_IMAGE = (f"{chat_aca.REPOSITORY}@sha256:"
              "1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593")
CHAT_RELEASE_IMAGE = (f"{chat_aca.REPOSITORY}@sha256:"
                      "7eff76f081d526ac3ae0870240b01b938edbf1c1f42647f2d3ddcdd7057a59df")
CHAT_REVISION = "ca-redshift-chat-bs01--sr9ms4f"
REPOSITORY = f"{shared.ACR}.azurecr.io/redshift-official-candidate"
BINDING_KEYS = {"FOUNDRY_AGENT_VERSION", "MCP_SERVER_URL"}
SAFE_ENV = BINDING_KEYS | {"NODE_ENV", "PORT", "PUBLIC_ORIGIN",
                           "FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_AGENT_NAME"}
LOCK = shared.DEPLOY_DIR / ".official-chat-cutover.lock"
READ_ONLY_PROPERTIES = {
    "customDomainVerificationId", "eventStreamEndpoint", "latestReadyRevisionName",
    "latestRevisionFqdn", "latestRevisionName", "outboundIpAddresses", "provisioningState",
    "runningStatus", "deploymentErrors",
}


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def candidate_definition(image):
    shared.require(bool(re.fullmatch(re.escape(REPOSITORY) + r"@sha256:[a-f0-9]{64}", image)),
                   "Candidate requires immutable reviewed adapter repository digest.")
    return {
        "location": shared.LOCATION,
        "identity": {"type": "SystemAssigned, UserAssigned",
                     "userAssignedIdentities": {shared.IDENTITY: {}}},
        "properties": {
            "environmentId": shared.ENV_ID,
            "configuration": {
                "activeRevisionsMode": "Single",
                "ingress": {"external": True, "targetPort": 8000, "transport": "http",
                            "allowInsecure": False},
                "registries": [{"server": f"{shared.ACR}.azurecr.io", "identity": shared.IDENTITY}],
            },
            "template": {
                "containers": [{
                    "name": "redshift-official", "image": image,
                    "resources": {"cpu": 0.25, "memory": "0.5Gi"},
                    # Credential/budget configuration is a separate reviewed step after
                    # provisioning system MI and inspecting its real audience claims.
                    "env": [{"name": "REDSHIFT_WORKGROUP", "value": "default-workgroup"},
                            {"name": "REDSHIFT_DATABASE", "value": "dev"},
                            {"name": "AWS_REGION", "value": "us-east-2"},
                            {"name": "REDSHIFT_MCP_ALLOWED_HOSTS",
                             "value": f"{CANDIDATE}.{chat_aca.DOMAIN}"}],
                    "probes": [{"type": kind, "httpGet": {
                        "path": "/healthz", "port": 8000, "scheme": "HTTP"},
                        "periodSeconds": 10, "timeoutSeconds": 2,
                        "failureThreshold": 30 if kind == "Startup" else 3}
                        for kind in ("Startup", "Readiness", "Liveness")],
                }],
                "scale": {"minReplicas": 1, "maxReplicas": 1},
            },
        },
    }


def new_agent_definition():
    """Reuse only the established pure business definition, never legacy stages."""
    desired = copy.deepcopy(chat_deploy.agent_definition())
    shared.require(len(desired["tools"]) == 1 and
                   desired["tools"][0]["server_url"] == OLD_URL and
                   desired["tools"][0]["allowed_tools"] ==
                   {"tool_names": ["get_data_context", "analyze_data"]},
                   "Business tool protocol changed; review before migration.")
    desired["tools"][0]["server_url"] = CANDIDATE_URL
    return desired


def snapshot(current, *, require_ready=True):
    """Persist validated nonsecret template; hash all other mutable configuration."""
    shared.require(current.get("id", "").lower() == chat_aca.APP_ID.lower(),
                   "Unexpected cutover resource.")
    identity = current["identity"]
    props = current["properties"]
    shared.require(identity.get("principalId") == CHAT_PRINCIPAL and
                   {key.lower() for key in identity.get("userAssignedIdentities", {})} ==
                   {shared.IDENTITY.lower()},
                   "Chat identity drift; do not repair.")
    shared.require(props["environmentId"].lower() == shared.ENV_ID.lower() and
                   props["configuration"]["activeRevisionsMode"] == "Single" and
                   props["configuration"]["ingress"]["fqdn"] == chat_aca.ORIGIN[8:] and
                   props["configuration"]["ingress"].get("allowInsecure") is False,
                   "Chat environment/HTTPS/revision-mode drift.")
    template = props["template"]
    shared.require(len(template["containers"]) == 1 and
                   template["containers"][0]["image"] in {CHAT_IMAGE, CHAT_RELEASE_IMAGE} and
                   template["scale"].get("minReplicas") == 1 and
                   template["scale"].get("maxReplicas") == 1,
                   "Chat image/container/scale drift.")
    env = template["containers"][0]["env"]
    shared.require(len({e["name"] for e in env}) == len(env) and
                   {e["name"] for e in env} == SAFE_ENV and
                   all(set(e) == {"name", "value"} and isinstance(e["value"], str) for e in env),
                   "Unexpected env/secret; snapshot requires separate review.")
    values = {e["name"]: e["value"] for e in env}
    shared.require(values["FOUNDRY_AGENT_NAME"] == "redshift-chat-agent" and
                   values["PUBLIC_ORIGIN"] == chat_aca.ORIGIN and
                   values["FOUNDRY_PROJECT_ENDPOINT"] ==
                   "https://foundry-sandbox-swc-mx01.services.ai.azure.com/api/projects/redshift-test-project",
                   "Chat project/origin drift.")
    if require_ready:
        shared.require(props.get("provisioningState") == "Succeeded" and
                       props.get("runningStatus") == "Running" and
                       props.get("latestRevisionName") == props.get("latestReadyRevisionName") and
                       bool(props.get("latestReadyRevisionName")) and
                       current.get("_ready_revision") == props["latestReadyRevisionName"],
                       "Exactly one active healthy ready revision/replica must be proven.")
    unrelated = {k: v for k, v in current.items()
                 if k not in {"id", "name", "type", "systemData", "etag", "properties",
                              "_ready_revision", "_revision_names"}}
    unrelated["properties"] = {k: v for k, v in props.items()
                               if k not in READ_ONLY_PROPERTIES | {"template"}}
    return {"id": chat_aca.APP_ID,
            "identity_sha256": fingerprint(identity), "template": copy.deepcopy(template),
            "template_sha256": fingerprint(template),
            "unrelated_sha256": fingerprint(unrelated),
            "revision": props.get("latestReadyRevisionName")}


def read_live(*, require_ready=True):
    current = shared.arm("GET", chat_aca.APP_ID, shared.APP_API)
    if require_ready:
        revision = current["properties"].get("latestReadyRevisionName")
        shared.require(isinstance(revision, str) and
                       bool(re.fullmatch(re.escape(chat_aca.APP) + r"--[a-z0-9-]+", revision)),
                       "Unexpected ready revision identifier.")
        values = shared.arm("GET", chat_aca.APP_ID + "/revisions", shared.APP_API)
        shared.require(not values.get("nextLink"),
                       "Revision listing ambiguous; no paging fallback.")
        current["_revision_names"] = [r["name"] for r in values["value"]]
        active = [r for r in values["value"] if r["properties"].get("active")]
        shared.require(len(active) == 1 and active[0]["name"] == revision,
                       "Expected exactly one active ready revision.")
        state = active[0]["properties"]
        shared.require(state.get("trafficWeight") == 100, "Revision traffic drift.")
        shared.require(state.get("healthState") == "Healthy" and
                       state.get("provisioningState") == "Provisioned" and
                       state.get("runningState") in {"Running", "RunningAtMaxScale"},
                       "Revision readiness pending.")
        replicas = shared.arm("GET", f"{chat_aca.APP_ID}/revisions/{revision}/replicas",
                              shared.APP_API)
        shared.require(not replicas.get("nextLink") and len(replicas["value"]) <= 1,
                       "Expected exactly one replica.")
        shared.require(len(replicas["value"]) == 1, "Replica readiness pending.")
        replica = replicas["value"][0]["properties"]
        containers = replica.get("containers", [])
        shared.require(replica.get("runningState") == "Running" and len(containers) == 1 and
                       containers[0].get("ready") is True and containers[0].get("started") is True,
                       "Replica readiness pending.")
        traffic = current["properties"]["configuration"]["ingress"].get("traffic")
        shared.require(traffic == [{"weight": 100, "latestRevision": True}],
                       "Unexpected traffic configuration; no mode/traffic repair.")
        current["_ready_revision"] = revision
    snapshot(current, require_ready=require_ready)
    return current


def revision_suffix(value):
    shared.require(isinstance(value, str) and
                   bool(re.fullmatch(r"[a-z][a-z0-9-]{0,40}[a-z0-9]", value)) and "--" not in value,
                   "Explicit unique lowercase revision suffix required.")
    return value


def without_suffix(template):
    value = copy.deepcopy(template)
    value.pop("revisionSuffix", None)
    return value


def binding(template):
    return {entry["name"]: entry["value"] for entry in template["containers"][0]["env"]
            if entry["name"] in BINDING_KEYS}


def prepare_cutover(current, agent_version, suffix):
    shared.require(bool(re.fullmatch(r"[1-9][0-9]{0,8}", agent_version)) and agent_version != "2",
                   "Exact new agent version required; never overwrite agent2.")
    before = snapshot(current)
    desired = {"FOUNDRY_AGENT_VERSION": agent_version, "MCP_SERVER_URL": CANDIDATE_URL}
    existing = binding(before["template"])
    shared.require(existing == {"FOUNDRY_AGENT_VERSION": "2", "MCP_SERVER_URL": OLD_URL} and
                   before["revision"] == CHAT_REVISION and
                   before["template"]["containers"][0]["image"] == CHAT_IMAGE,
                   "Original binding/revision drift; retain existing baseline, do not overwrite.")
    template = copy.deepcopy(before["template"])
    template["containers"][0]["image"] = CHAT_RELEASE_IMAGE
    template["revisionSuffix"] = revision_suffix(suffix)
    for entry in template["containers"][0]["env"]:
        if entry["name"] in desired:
            entry["value"] = desired[entry["name"]]
    return {"before": before, "patch": {"properties": {"template": template}},
            "after_template_sha256": fingerprint(template),
            "expected_revision": f"{chat_aca.APP}--{suffix}", "direction": "cutover"}


def prepare_rollback(current, release, suffix):
    live = snapshot(current)
    before = release["before"]
    shared.require(before["id"] == chat_aca.APP_ID and
                   fingerprint(before["template"]) == before["template_sha256"] and
                   before["identity_sha256"] == live["identity_sha256"] and
                   before["unrelated_sha256"] == live["unrelated_sha256"] and
                   binding(before["template"]) ==
                   {"FOUNDRY_AGENT_VERSION": "2", "MCP_SERVER_URL": OLD_URL},
                   "Rollback snapshot invalid or identity changed.")
    shared.require(live["template_sha256"] == release["after_template_sha256"] and
                   live["revision"] == release["expected_revision"],
                   "Concurrent template change; rollback must not overwrite it.")
    shared.require(fingerprint(release["patch"]["properties"]["template"]) ==
                   release["after_template_sha256"], "Release artifact corrupt.")
    template = copy.deepcopy(before["template"])
    template["revisionSuffix"] = revision_suffix(suffix)
    shared.require(template["revisionSuffix"] != live["template"].get("revisionSuffix"),
                   "Rollback requires a distinct explicit revision suffix.")
    return {"before": live, "rollback_baseline": copy.deepcopy(before),
            "patch": {"properties": {"template": template}},
            "after_template_sha256": fingerprint(template),
            "expected_revision": f"{chat_aca.APP}--{suffix}", "direction": "rollback"}


@contextmanager
def operator_lock():
    """Coordinates this tool only, not portal/CLI/other external resource writers."""
    descriptor = os.open(LOCK, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise shared.DeploymentError("Another tool operation owns the chat lock.") from None
        yield
    finally:
        os.close(descriptor)


def verify_applied(prepared, *, deadline_seconds=300):
    deadline = time.monotonic() + deadline_seconds
    while True:
        current = read_live(require_ready=False)
        state = snapshot(current, require_ready=False)
        shared.require(state["unrelated_sha256"] == prepared["before"]["unrelated_sha256"] and
                       state["identity_sha256"] == prepared["before"]["identity_sha256"] and
                       state["template_sha256"] in {prepared["before"]["template_sha256"],
                                                    prepared["after_template_sha256"]},
                       "Observed post-update drift; stop, no overwrite or automatic retry.")
        props = current["properties"]
        shared.require(props.get("latestRevisionName") in {
            prepared["before"]["revision"], prepared["expected_revision"]},
            "Unexpected revision observed; stop without retry.")
        shared.require(props.get("provisioningState") not in {"Failed", "Canceled"},
                       "Revision provisioning failed; explicit rollback review required.")
        if (state["template_sha256"] == prepared["after_template_sha256"] and
                props.get("latestRevisionName") == prepared["expected_revision"] and
                props.get("latestReadyRevisionName") == prepared["expected_revision"] and
                props.get("provisioningState") == "Succeeded"):
            try:
                verified = snapshot(read_live())
            except shared.DeploymentError as exc:
                if str(exc) not in {"Revision readiness pending.", "Replica readiness pending."}:
                    raise
            else:
                shared.require(verified["template_sha256"] == prepared["after_template_sha256"] and
                               verified["unrelated_sha256"] ==
                               prepared["before"]["unrelated_sha256"] and
                               verified["revision"] == prepared["expected_revision"],
                               "Post-readiness resource drift; stop without retry.")
                return {"status": "verified", "revision": verified["revision"],
                        "template_sha256": verified["template_sha256"]}
        shared.require(time.monotonic() < deadline,
                       "Readiness deadline exceeded; no write retry. Inspect before rollback.")
        time.sleep(5)


def apply_prepared(prepared, *, reviewed_artifact_sha256, gates):
    """One supported PATCH after immediate recheck; snapshots are NOT atomic CAS."""
    shared.require(fingerprint(prepared) == reviewed_artifact_sha256,
                   "Reviewed cutover/rollback artifact mismatch.")
    required = {"independent_security_review", "independent_correctness_review",
                "azure_validate_current", "azure_deploy_current", "actual_candidate_proof",
                "new_agent_candidate_binding", "sts_expiry_refresh", "db_budget_10s"}
    shared.require(set(gates) == required and all(v is True for v in gates.values()),
                   "Release gates incomplete; no chat mutation.")
    desired = prepared["patch"]
    shared.require(set(desired) == {"properties"} and
                   set(desired["properties"]) == {"template"}, "Only template patch permitted.")
    template = copy.deepcopy(desired["properties"]["template"])
    shared.require(fingerprint(template) == prepared["after_template_sha256"],
                   "Prepared template fingerprint mismatch.")
    suffix = revision_suffix(template.get("revisionSuffix"))
    shared.require(prepared["expected_revision"] == f"{chat_aca.APP}--{suffix}" and
                   prepared["direction"] in {"cutover", "rollback"},
                   "Explicit revision/direction mismatch.")
    intended = binding(template)
    expected_image = CHAT_RELEASE_IMAGE if prepared["direction"] == "cutover" else CHAT_IMAGE
    shared.require(template["containers"][0]["image"] == expected_image,
                   "Only the reviewed release or original rollback image is permitted.")
    shared.require(set(intended) == BINDING_KEYS and
                   ((intended["FOUNDRY_AGENT_VERSION"] == "2" and
                     intended["MCP_SERVER_URL"] == OLD_URL) or
                    (bool(re.fullmatch(r"[1-9][0-9]{0,8}", intended["FOUNDRY_AGENT_VERSION"])) and
                     intended["FOUNDRY_AGENT_VERSION"] != "2" and
                     intended["MCP_SERVER_URL"] == CANDIDATE_URL)),
                   "Only old or candidate business endpoint binding permitted.")
    original = binding(prepared["before"]["template"])
    template["containers"][0]["image"] = prepared["before"]["template"]["containers"][0]["image"]
    for entry in template["containers"][0]["env"]:
        if entry["name"] in BINDING_KEYS:
            entry["value"] = original[entry["name"]]
    shared.require(without_suffix(template) == without_suffix(prepared["before"]["template"]),
                   "Unrelated template mutation forbidden.")
    with operator_lock():
        live = snapshot(read_live())
        if (live["template_sha256"] == prepared["after_template_sha256"] and
                live["revision"] == prepared["expected_revision"] and
                live["unrelated_sha256"] == prepared["before"]["unrelated_sha256"]):
            return verify_applied(prepared)
        shared.require(live == prepared["before"], "Observed resource drift; no overwrite.")
        # Re-read every guarded field immediately before the single write.
        recheck = read_live()
        shared.require(snapshot(recheck) == live,
                       "Immediate pre-write drift; no overwrite or automatic retry.")
        shared.require(prepared["expected_revision"] not in recheck["_revision_names"],
                       "Requested revision already exists; no overwrite/retry.")
        shared.arm("PATCH", chat_aca.APP_ID, shared.APP_API, prepared["patch"])
        return verify_applied(prepared)


def artifact_path(value):
    shared.require(isinstance(value, str) and
                   bool(re.fullmatch(r"\.azure/official-chat-[a-zA-Z0-9._-]+\.json", value)),
                   "Use an explicit .azure/official-chat-*.json artifact path.")
    path = shared.ROOT / value
    shared.require(not path.parent.is_symlink() and path.parent.is_dir() and
                   not path.is_symlink(), "Linked/missing artifact directory forbidden.")
    return path


def read_artifact(value):
    path = artifact_path(value)
    shared.require(path.is_file() and path.stat().st_size <= 262144,
                   "Missing or oversized review artifact.")
    return json.loads(path.read_text())


def save_artifact(value, body):
    path = artifact_path(value)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(json.dumps(body, indent=2) + "\n")
    print(json.dumps({"artifact": value, "sha256": fingerprint(body)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("candidate-plan", "agent-plan", "chat-preflight",
                                          "prepare-cutover", "prepare-rollback", "apply"))
    parser.add_argument("--image")
    parser.add_argument("--agent-version")
    parser.add_argument("--revision-suffix")
    parser.add_argument("--output")
    parser.add_argument("--artifact")
    parser.add_argument("--reviewed-artifact-sha256")
    parser.add_argument("--reviewed-helper-sha256")
    parser.add_argument("--gates-file")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.stage == "candidate-plan":
        shared.require(args.image, "Exact candidate image digest required.")
        print(json.dumps(candidate_definition(args.image), indent=2))
    elif args.stage == "agent-plan":
        print(json.dumps({"definition": new_agent_definition(),
                          "sha256": fingerprint(new_agent_definition()),
                          "operation": "CREATE NEW VERSION ONLY; do not overwrite agent2"},
                         indent=2))
    elif args.stage in {"chat-preflight", "prepare-cutover", "prepare-rollback"}:
        with operator_lock():
            current = read_live()
            if args.stage == "prepare-rollback":
                release = read_artifact(args.artifact)
                shared.require(fingerprint(release) == args.reviewed_artifact_sha256,
                               "Original release artifact hash mismatch.")
                artifact = prepare_rollback(current, release, args.revision_suffix)
            else:
                artifact = prepare_cutover(current, args.agent_version or "", args.revision_suffix)
            if args.stage == "chat-preflight":
                print(json.dumps({"artifact": artifact, "sha256": fingerprint(artifact)}, indent=2))
            else:
                save_artifact(args.output, artifact)
    else:
        shared.require(args.execute,
                       "Cloud mutation requires --execute after current release gates.")
        shared.require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() ==
                       args.reviewed_helper_sha256, "Reviewed helper source changed.")
        artifact = read_artifact(args.artifact)
        gates = read_artifact(args.gates_file)
        print(json.dumps(apply_prepared(
            artifact, reviewed_artifact_sha256=args.reviewed_artifact_sha256, gates=gates)))


if __name__ == "__main__":
    try:
        main()
    except shared.DeploymentError as exc:
        raise SystemExit(str(exc)) from None
    except (OSError, KeyError, TypeError, ValueError):
        message = "Malformed/missing artifact or local operation unavailable; no retry."
        raise SystemExit(message) from None
