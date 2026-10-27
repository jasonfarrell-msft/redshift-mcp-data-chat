# Approved synthetic POC deployment

## Analytics release v3 — deployed; hosted acceptance BLOCKED

The user-approved, independently reviewed and officially validated frozen release
was deployed on 2026-10-26. MCP v3 passed actual independent numerical/source
acceptance on revision `ca-redshift-bs01--0000003`, digest
`sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`.
2025 totals matched fresh Data API references: oil 21,157,564.26 bbl,
gas 44,177,025.20 Mcf, cost 213,367,864.95 USD. All five physical-source
comparisons passed. Exact preservation hash, identities, secret references,
CORS, resources and min/max remained unchanged; existing runtime roles passed.

The reviewed chat ZIP and registered agent version 2 are also deployed, but
actual hosted oil answers fail closed with HTTP 503 / `AGENT_UNAVAILABLE`.
Overall release acceptance is **not verified**; no gas continuation passed.
See `CHAT-README.md` and
`.squad/decisions/inbox/st-brown-analytics-v3-deployment.md` for full evidence.
Do not rerun builds, overwrite v3, loosen grounding or bootstrap resources.
Prior v2/v1 rollback artifacts remain intact; rollback needs separate approval.

The original approved image-only execution sequence is retained for reference:

```sh
deploy/.venv/bin/python deploy/deploy.py --check --stage update --image-tag v3
# Record/review the printed source_sha256 and app_sha256, then:
deploy/.venv/bin/python deploy/deploy.py --apply --stage build --image-tag v3 --approved-source-sha256 "$SOURCE_SHA"
deploy/.venv/bin/python deploy/deploy.py --apply --stage update --image-tag v3 --approved-source-sha256 "$SOURCE_SHA" --approved-app-sha256 "$APP_SHA"
deploy/.venv/bin/python deploy/deploy.py --apply --stage verify --image-tag v3
```

Use the actual reviewed hashes; do not copy placeholders as evidence. Do not run
`all`, `configure` or bootstrap resource/grant/credential stages. Preserve image,
revision and chat ZIP/version rollback evidence. `verify` now requires independent
read-only Data API reference values and real MCP numerical results across all five
sources, not metadata discovery alone. See `CHAT-README.md` for the registered
analytics agent and App Service release; no new identities/resources are needed.

**Historical release: v2 metadata correction, deployed and verified 2026-10-26.**
Revision `ca-redshift-bs01--0000002` uses immutable digest
`sha256:474fa8cb2fd7d9a3b35c2c918911f3c4c2d7474fe576455d3b1b4bb87ee5fa13`
from successful ACR Linux/AMD64 build `cq2`. The image-only update preserved
configuration, identities, secret references, CORS, resources and scaling.
Native Redshift metadata discovery now finds both dataset schemas, all five
`oge_synthetic` tables and five `wells` columns through the deployed MCP.
The registered-agent schema/table answers and continuation passed the strengthened
chat verifier. This is historical v2 evidence: the updated numerical verifier
requires the new analytics runtime and will correctly fail against unchanged v2.
Original v1 image
and revision remain recorded for rollback; no grants or credentials changed.

## Initial deployment history

**Deployed and externally verified on 2026-10-26.** ACR Linux/AMD64 build `cq1`
succeeded before app creation, and full infrastructure/MCP/Redshift acceptance
passed. The parent completed prerequisite validation and independent/security
review before approved execution. The approved root
`.azure/deployment-plan.md` governs the exact subscription, tenant, Brazil South
resources and public POC exceptions. These are historical bootstrap results;
the schema-discovery fix/release below still requires independent review and execution.

- MCP: https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp
- Health: https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/healthz
- Immutable deployed digest: `sha256:1f7c40921f16cafb9d08df09fe98034098cf797cf43d006426993716c84a5a80`.
- Sole active revision: `ca-redshift-bs01--0000001`, Healthy,
  `RunningAtMaxScale`, one replica at 0.25 CPU / 0.5 GiB and min/max 1/1.
  The maximum-scale status is intentional; no restart was needed.

## Image-only release of the schema-discovery fix (v2)

For the subsequent request **“deploy all changes”**, do **not** run `all`, `app`
or `configure` against the configured app. `all` remains the original bootstrap
sequence and deliberately excludes the new `update` stage. `configure` reloads
dotenv/password and synthesizes settings; it is not an image release operation.
This code change alone does not deploy anything.

After the MCP fix and release tooling pass independent/security review, collect
the live, read-only review evidence from the workspace root:

```bash
deploy/.venv/bin/python deploy/deploy.py --check --stage update --image-tag v2
```

Review the exact source and current configured app represented by the printed
`source_sha256` and `app_sha256`. Confirm the old image is the digest above and
approve these fingerprints before continuing. Set the following shell variables
to those **reviewed** values (they are hashes, not credentials):

```bash
SOURCE_SHA256='<reviewed source_sha256>'
APP_SHA256='<reviewed app_sha256>'
deploy/.venv/bin/python deploy/deploy.py --apply --stage build --image-tag v2 --approved-source-sha256 "$SOURCE_SHA256"
deploy/.venv/bin/python deploy/deploy.py --apply --stage update --image-tag v2 --approved-source-sha256 "$SOURCE_SHA256" --approved-app-sha256 "$APP_SHA256"
deploy/.venv/bin/python deploy/deploy.py --apply --stage verify --image-tag v2
```

`--image-tag` defaults to `v1` for bootstrap compatibility. Tags permit 1–64
simple alphanumeric/underscore/dot/hyphen characters (not a leading dot/hyphen);
registry/repository overrides are forbidden. New release builds require the
reviewed source hash. A tag already present without matching local source/digest
evidence is rejected, and a recorded tag cannot be reused for different source.
Thus `v2` does not overwrite `v1`. Build history retains the old source/digest
record. Serialize releases/builds: ACR's existence check is not a registry-wide
transaction against another publisher. Do not run other publishers concurrently.

`update` requires explicit `--apply` to mutate. It confirms the selected tag's
registry digest and reviewed source, exact approved app fingerprint, environment,
region, system identity/tenant, live image-pull identity principal/client, HTTPS
single-revision ingress and existing Key Vault/password references. It captures
the full existing template and PATCHes **only** that template with the named MCP
container's digest-pinned image changed; it removes the old revision suffix to
allow ACA to generate the new revision name. All other containers/sidecars, env,
secret refs, resources, probes, volumes and scaling remain unchanged.
Identity, configuration (including exact CORS), networking and tags are not sent
or reconstructed. There are no dotenv reads, secret uploads, role grants, AWS
rule changes or new resources.

A fresh read detects concurrent drift before PATCH, with `If-Match` when ARM
returns an ETag. If this API supplies no ETag, there is no atomic compare-and-swap:
serialize all app writers; full normalized post-read comparison still rejects
drift rather than silently repairing it. Fingerprints ignore only ETag,
system-data and known service-generated revision/status bookkeeping, plus the
intended MCP image difference when testing preservation.
Any identity/config/source/tag/digest drift, failed provisioning or readiness
timeout stops the stage without broad recovery or automatic restart.

Before PATCH, metadata records the previous digest-pinned image and revision
and preservation fingerprint; it stores no secret values or app snapshots.
Retries require the **same** tag/digest/source and original app approval hash,
and accept only the previous or intended image with unchanged configuration.
An unfinished release blocks a different build/release. Readiness requires a
new latest revision to be the sole active Healthy Running/RunningAtMaxScale
revision before saving its actual revision/FQDN. `verify --image-tag v2` then
runs the existing full security and external MCP/Redshift acceptance, also
checking release-preservation evidence. Custom preserved resources/scaling do
not relax the original verification policy; deviations from the approved
0.25 CPU/0.5Gi and 1/1 deployment still fail full verification.

Retain `deploy/state.json` and `v1`; `release.previous_image` and
`release.previous_revision` are rollback evidence even if readiness fails.
Rollback execution requires separate approval; this stage does not activate an
old revision or delete/recreate any resource. Never “recover” a failed update by
running bootstrap/configure/all or by editing the approval fingerprints.

## Setup and read-only validation

Requires Azure CLI 2.86 (with Container Apps extension), AWS CLI already signed in
using the approved default credentials, and Python 3.13. The application agent
owns the Dockerfile, ignore file, runtime code and hashed dependency locks.
No local Docker daemon is required.

From the workspace root (context checks require both application lockfiles):

```bash
python3.13 -m venv deploy/.venv
deploy/.venv/bin/python -m pip install -r deploy/requirements.txt
deploy/.venv/bin/python deploy/deploy.py --check
python3 -m unittest discover -s deploy -p 'test_*.py'
```

`--validate` aliases `--check`; omitting either also defaults to read-only.
`--check --offline` validates the context/Dockerfile without cloud calls or SDK
dependencies. **All check modes avoid loading `.env` and cannot provision.**
Online checks inspect authenticated account/provider/API metadata and AWS caller
identity; they are not a replacement for the parent's policy/permission,
name-availability and deployment approval gates.

The subscription-scoped `infra/redshift-bs01.bicep` and its RG module describe the real
prerequisite creation surface for the shared ARM validation/what-if gate:
RG, ACR, image-pull UMI and registry-scoped AcrPull, Key Vault and Consumption-only
environment. From the workspace root, the parent runs:

```bash
bash /Users/jasonfarrell/.agents/skills/azure-validate/references/recipes/scripts/validate-deployment.sh --scope sub --location brazilsouth --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c --template infra/redshift-bs01.bicep --parameters infra/main.parameters.json
```

There is no parameters file or secret input. This preflight does **not** validate
later app/image/bootstrap, system-identity, secret-reference or AWS stages;
actual cloud build and postdeployment verification are recorded separately below,
not as a full-template workload preflight. `deploy.py` stays the actual
deployment engine. The template is repeatable on its own, but its deterministic
role-assignment name differs from the imperative engine's equivalent-role reuse;
do not switch to applying the template over an imperative-created assignment.
Compilation alone does not establish policy/permission approval or capacity.
The user's later vault-only `SecurityControl: Ignore` policy exclusion is
persisted in the imperative vault creation payload, not this preflight template;
review/revalidate the template before any future use. Do not apply it over the
existing vault or broaden that tag to the resource group.

## Explicit deployment after parent gates

One command executes in the necessary order:

```bash
deploy/.venv/bin/python deploy/deploy.py --apply --stage all
```

Alternatively, resume with the same command replacing `all` by exactly one of:

1. `prerequisites`: RG, Basic RBAC ACR, UMI, registry-scoped AcrPull, public RBAC
   Standard Key Vault, Consumption-only/no-VNet/no-logs environment. Rejects
   unexpected environment managed RG/network resources and new RG delta.
   Accepts absent/null/empty legacy workload profiles, or exactly one profile
   named `Consumption` with type `Consumption` and absent/null/zero
   `minimumCount`/`maximumCount`; rejects dedicated, multiple, renamed or
   nonzero-capacity profiles. All region, subnet/internal-network, infrastructure
   RG, log-destination and resource-inventory checks remain mandatory.
   Only a newly created vault receives the exact tag `SecurityControl: Ignore`,
   as explicitly directed by the user after confirming the inherited policy's
   tag exclusion. Verification requires that exact vault tag and public access;
   an existing vault is not retagged or updated by this stage.
2. `build`: validates and stages **only the hard-coded runtime allowlist** from
   `src/redshift-mcp-server`, then uses ACR Tasks `linux/amd64`. All dotenv files
   are absent regardless of ignore implementation. Rechecks the staged content
   hash before upload, records the immutable digest, and removes the owned
   staging directory in `finally`. Same tag/source plus same registry digest
   skips rebuilding; changed source requires a fresh tag.
   ACR CLI archive work is confined to `deploy/` using `TMPDIR`.
3. `app`: requires >=0.5 available Consumption cores on the **new environment**.
   Creates our real digest-pinned image with both identities, no password, three
   `/healthz` probes, public HTTPS only, 0.25 CPU/0.5Gi, min/max 1. Existing apps
   are not downgraded to credential-free bootstrap.
4. `configure`: uses the application's explicit `load_environment(app_dir/'.env')`
   and `Settings.from_env()` only at execution. Transfers the password directly
   through `SecretClient` and `AzureCliCredential`; whitelist-only nonsecret
   settings enter the app's ARM body **in memory**, not process arguments/disk.
   Preserves the calling environment after loading. Password mode and port 5439
   are required; existing IAM/ECS roles are not migrated. Adds secret-scoped
   Secrets User, waits 60 seconds on a new role, then configures a system-identity
   Key Vault reference and `REDSHIFT_PASSWORD.secretRef`. New runtime configuration
   creates the revision. Uses the actual FQDN as `REDSHIFT_MCP_ALLOWED_HOSTS`; the
   Dockerfile supplies `--host 0.0.0.0 --port 8000`.
   Finally adds **only TCP5439 from 0.0.0.0/0** on the approved AWS SG/region if
   an equivalent rule does not exist, recording only a newly created rule ID.
5. `verify`: read-only acceptance: exact infrastructure, image/resources/probes,
   identities/least-privilege role scopes, vault reference, sole healthy running
   revision, external HTTPS health, rejected hostile host/origin, exact AWS rule,
   official external MCP initialization/tools/list, live `test_connection`
   (`SELECT 1`) and bounded `list_schemas(limit=1)`. Success is emitted only if all
   pass. Run verify separately to recheck a completed deployment.

The deployer is the existing signed-in **Entra user** (Graph user-read required),
not a new service principal. If existing vault authority is insufficient, a
uniquely named vault-scoped Secrets Officer assignment is tracked **before**
creation and removed in `finally`, including SDK failures. Interrupted process
cleanup resumes on the next `configure`; stored assignment identity/scope/role
are checked before removal. Pre-existing permissions are not removed.
No Azure/AWS credentials or `.env` contents are displayed, passed in command
arguments or written as deployment configuration. SDK logging is disabled;
exceptions show only fixed operation/status messages, never bodies/tracebacks.

## Failures and handoff

No automatic quota increases, broad role grants, VNet/egress reconciliation, AWS
identity changes or RG deletes occur. The root AWS CLI principal and open
TCP5439 are known user-approved POC risks, not production recommendations.
`deploy/state.json` contains only resource IDs, hashes, image tags/build history,
release/previous-image/revision/FQDN evidence and owned permission/rule
identifiers; treat it as resumable local metadata.
Keep it until any owned temporary permission is cleaned up.

RBAC propagation may exceed the bounded upload retries or app-role wait; on a
sanitized failure inspect the cause and rerun `configure`, not the bootstrap.
Do not call this deployed based on health alone.

For failed revision verification, the script first classifies console/system
logs **in memory** and prints only fixed diagnostic categories. An explicit
`--apply --stage verify --restart-once` permits one targeted latest-revision
restart, then re-verifies; it never loops restarts or kills processes. Correct
the diagnosed configuration and resume the relevant stage if it still fails.
No general rollback deletes resources or touches unrelated/pre-existing rules.
For a requested AWS rollback, use only the recorded `owned_aws_rule` after
checking that its SG, protocol, ports and CIDR still match; no automatic removal
of pre-existing rules is authorized.

Execution evidence (2026-10-26, reported by the coordinator): inherited
`KeyVault_PublicNetwork_Modify` originally forced public access off. After policy
definition inspection and the user's explicit “Use the tag SecurityControl:
Ignore to override this”, the coordinator merged that tag onto **only the vault**
and enabled public access successfully; no policy change or RG tag was applied.
The environment returned `Succeeded`, `Brazil South`, null infrastructure RG
and VNet configuration, no log destination, and one built-in Consumption profile
(`enableFips: false`, no min/max counts). The old empty-profile-only guard rejected
this representation; the corrected strict guard covers it without changing
environment creation or allowing dedicated capacity.

The vault-tag/Consumption correction passed 17 synthetic deployment tests; the
unsupported-subscription exclusion narrowed to `az ad` calls passed 18; the
healthy `RunningAtMaxScale` guard correction passed 22. Goff's independent
infrastructure/authentication security reviews found no actionable vulnerabilities,
and the Devils Advocate review approved the state predicate. Earlier application
tests passed 102. The historical local Docker PyPI TLS failure remains a failed
local attempt, resolved operationally by successful cloud build `cq1`.

All five regional resources and `rg-redshift-bs01` are in Brazil South. Registry
Basic/admin-off/anonymous-pull-off and Consumption-only/no-VNet/no-managed-infra-RG/
no-log-workspace checks passed. The vault's public access and exact
`SecurityControl: Ignore` tag were verified. Persistent roles are exactly
registry-scoped UMI `AcrPull` and secret-scoped system-identity
`Key Vault Secrets User`, with no extra roles. Password upload stayed in SDK
memory; the app uses a system-identity vault reference and environment `secretRef`.
Temporary upload authority was removed (`owned_officer: null`), and supported
nonsecret connection settings independently matched local settings in memory.
No secret was printed. Approved AWS rule `sgr-041636c02c8e1089b` permits public
IPv4 TCP5439 only; existing rules were preserved.

`deploy/.venv/bin/python deploy/deploy.py --apply --stage verify` completed
successfully with the verified URL, revision and digest. It checked infrastructure,
exact roles, probes, secret references, image, scaling, HTTPS 200, hostile
host/origin rejection, AWS rule and official external MCP initialize/`tools/list`,
`test_connection` (`connected: true`, `SELECT 1`) and `list_schemas(limit=1)`.
The first MCP attempt had a transient `ExceptionGroup`; an isolated sanitized
retry passed, then the entire verification passed. This does not claim that the
first attempt passed. No unresolved deployment blocker remains. Anonymous public
MCP and public Redshift are accepted synthetic-POC scope, not production guidance.
