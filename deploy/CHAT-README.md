# Redshift React chat extension

## Current: Container Apps verified; obsolete App Service retired

**2026-10-27 02:00:10 UTC:** The React chat is deployed and verified at
https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io.
The separately user-approved, Goff-reviewed cleanup completed: deleted obsolete
`app-redshift-chat-bs01-bb4b2781`, confirmed-empty B1 plan
`asp-redshift-chat-bs01`, and exactly its old identity's two Foundry project
assignments. Direct ARM confirms both resources **ResourceNotFound**; old role
IDs are absent and the new runtime's roles are unchanged.

Exactly six resources remain in `rg-redshift-bs01`, all Brazil South:
`ca-redshift-chat-bs01`, `ca-redshift-bs01`, `cae-redshift-bs01`,
`acrredshiftbs01bb4b2781`, `kv-redshift-bs01`, `umi-redshift-imagepull-mx01`.
Retained metadata/tags, identities and chat/MCP revision/image pins are unchanged,
including the vault-only policy exception. No other external resources changed.
Postcleanup HTML, chat process/fresh connected health and MCP `/healthz`
all HTTP200; connected `checkedAt=2026-10-27T02:00:06.253Z`.

See [current ACA operations and acceptance](CHAT-ACA.md) and
`.chat-artifacts/obsolete-appservice-cleanup-proof.json` (all 12 final checks pass).
Do not run the legacy App Service repair/deployment/verification helpers.
The following outage and blocked-release records are historical, superseded
by the completed ACA deployment and cleanup; they are retained as evidence.

## Historical final speaker-label copy release — App Service deployment BLOCKED

### Current priority: outage startup cause established, 2026-10-27T01:05:43Z

Bounded read-only ARM/SCM diagnosis found actual Node24 startup failing with
**ERR_MODULE_NOT_FOUND: `@azure/ai-projects`**, imported from
`dist/server/providers.js`, before server listen. Oryx reports its build
manifest missing. Shared-root dependency archive/manifest and package path
return ENOENT; node_modules remains a link to worker-ephemeral `/node_modules`.
SCM's namespace is not proof of the worker tree; actual application logs
independently establish failed resolution. Physical deletion/SMB cause is
still unproven. Current package pins2.9.0 and compiled startup files match.

ARM Running/ResourceHealth Available is not application readiness. Public
routes503 at01:02:25; final01:05:34 requests timed out. No second restart,
deployment, package install or source/config/security change. Cosmetic release
is deferred. A matched production dependency archive + authentic Oryx manifest
recovery via narrowly scoped supported delivery is **proposed for review only**;
archive alone is insufficient. No mutation before concrete independent review
and official validation/deploy gates; no second explicit restart authorized.
Support correlation: `5ffe6c98-f754-43cb-b5ba-ae1c807e9f4d`.
See top plan/St. Brown inbox and
`deploy/.chat-artifacts/outage-startup-diagnosis-proof.json`,
`outage-startup-dependency-layout-proof.json`, `outage-startup-final-evidence.json`.
State/failed history/null markers preserved; **NOT Validated or recovered**.

### One user-approved restart — recovery NOT established, 2026-10-27T00:57:19Z

After disclosed UI interruption/in-memory conversation and rate-state reset,
the user explicitly approved one restart; Goff's scoped approval was supplied
by the coordinator. Exactly one explicitly targeted App Service restart ran
**00:48:10Z**, CLI accepted00:48:12Z. No second restart, upload, old repair
executor, rollback or configuration/security/resource change.

Public health briefly recovered00:49:03 (connected, checkedAt00:48:50.676Z),
then transport failures; **final00:57:19Z HTML, health and known asset requests
all returned HTTP503**. Actual BFF replacement is **unproven**: last observed
PID/start identity was unchanged00:49:44, later worker SSH unreachable. Fresh
SCM namespace changed, but actual absolute AND dirfd `O_NOFOLLOW` HTML opens
still fail **ENOENT2**. Metadata is not read convergence. Physical cause
remains unproven; do not describe the application as currently healthy.

Bounded read-only checks finished before the fixed00:58:10Z maximum; no
pending wait/mutation. Actual post-call source20/backend8/config/agent2/MCPv3/
deployment-history preservation passed at its recorded time. State unchanged,
verified markers null, failed deployments still FAILED, approved repair files
untouched and backup absent. **NOT Validated; no final release/numerical proof.**
Next safe avenue is platform-assisted exact-leaf storage/worker-startup
diagnosis, not another restart or blind delivery. Proof:
`deploy/.chat-artifacts/appservice-restart-final-proof.json`; precise findings
and authorization are in the top deployment plan and St. Brown's repair inbox.

### Approved filesystem repair — live validation BLOCKED, 2026-10-27T00:36Z

The exact Sewell R1–R3 revision approved by Goff was not modified. Its actual
read-only worker probe failed **before any repair**: the mandatory
`openat(client_fd, 'index.html', O_RDONLY|O_NOFOLLOW)` returns **ENOENT2**,
although worker absolute reads return the old623-byte HTML and relative stat
reports regular/inode5418. Parent relative opens succeed; SCM remains
unopenable. This is not PID/mount drift: PID1928, exact argv, fresh observed
start ticks1811687 and the original worker namespace/parent inodes remain.

Official focused validation records actual proof but stops at **ResolveErrors,
NOT Validated**. No apply gate/journal, repair write, conditional upload,
cleanup/restart/revert, fingerprint reconciliation or new numerical verifier.
Backup absent; source/ZIP/agent2/MCPv3/state unchanged, verification fields null.
All20 remote sources/eight compiled files/configuration/scoped roles/policy
checks passed; prior101/68/build and exact47+3 review evidence retained.

Final public `/`, `/index.html`, `/healthz` and expected assets remain200/old
HTML. Fresh DB health **healthy, connected=true**, checkedAt
**2026-10-27T00:36:32.572Z**. The earlier transient503 observations remain
historical, not erased. No release or repair success is claimed.
Proof: `deploy/.chat-artifacts/path-repair-focused-validation-blocked-proof.json`,
`path-repair-current-syscall-boundary-proof.json` and
`path-repair-final-public-preservation-proof.json`. Exact commands/current
facts are in `.azure/deployment-plan.md` Section7 and St. Brown's repair inbox.

### Latest approved static recovery — terminal FAILED, 2026-10-26T23:26Z

Goff independently approved a bounded one-file static HTML delivery with **no
restart**. Official focused azure-validate completed **23:22:31Z** before
azure-deploy and the exact supported Entra-only static upload. Existing source,
ZIP, 623-byte HTML and agent/MCP pins were unchanged; prior 101/68 suite proof
was retained, not wastefully rerun. No Oryx/npm build/restore/prune occurred.

Its OWN operation **e0607d31-6943-4878-9f17-be9f401fcf1c** terminal failed
**23:23:28.224922Z**, Kudu **status 3, complete=true, active=false**:
rsync receiver **open** of `/home/site/wwwroot/dist/client/index.html` failed
with **No such file or directory (2)**; rsync **exit 23**. This is a destination
path/open failure, not a compilation failure; deeper filesystem cause is
unproven. No additional attempt, cleanup/filesystem hack, restart or rollback.

Postfailure: public `/`, `/index.html`, `/healthz` remain HTTP **200**, but both
HTML routes still use old HTML/Explorer JS. New JS/CSS are public/exact; direct
Kudu target HTML remains **404**. All **20 source files / eight compiled server
files** remain exact. A postfailure health HTTP 503 is retained; later actual DB
health recovered **healthy, connected=true**, checkedAt **23:25:40.775Z**.
App settings/TLS/basic-publishing/project roles, agent **2** and MCP **v3**
remain unchanged.

**No deployed-fingerprint reconciliation or full new-bundle verifier was run**:
terminal static success/target/public gates failed. Entire existing state equals
its pre-static snapshot; both verification fields stay **null**. Original ZIP
failures stay FAILED; prior decoder numerical success is not new-copy proof.
Separate proof: `deploy/.chat-artifacts/static-recovery-upload-proof.json` and
`static-recovery-terminal-live-proof.json`; prior state retained alongside them.
This bounded attempt is terminal failed, not merely initiated/pending.

### Earlier source ZIP attempts and diagnosis — retained history

The new source-only speaker label correction was independently approved and
completed official azure-validate **2026-10-26T22:52:57Z**: **101 chat tests**,
**68 deployment-helper tests**, Node 24 typecheck/build passed. Only
`client/components.tsx` differs across the 20 runtime files; no behavior change.

- Reviewed source:
  `2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c`.
- Frozen ZIP:
  `cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429`
  (**20 entries / 49,113 bytes**); old ZIP/state preserved.
- Initial deployment and sole identical-ZIP recovery **both terminal failed**.
  Recovery ended **2026-10-26T22:59:33.6210633Z**, Kudu status **3**,
  complete=true, active=false. Oryx build completed; final rsync output copy
  failed renaming generated HTML into `dist/client/index.html`:
  **ENOENT (2), rsync exit 23**. No overlapping/further retry or rollback.
- https://app-redshift-chat-bs01-bb4b2781.azurewebsites.net remains responsive:
  public `/` and `/healthz` HTTP **200**. Final actual DB health
  **healthy, connected=true**, checkedAt **2026-10-26T23:01:47.081Z**.
  All 20 Kudu source files match new source, but public HTML still serves old
  `/assets/index-Cp4GJAH3.js`, which contains **Redshift Explorer**.
  It does **not** match the reviewed new build. Kudu generated HTML GET is 404.
- Agent **2** and MCP **v3** remain unchanged; fresh exact-role/settings/policy
  preservation checks passed. New-bundle full hosted numerical acceptance
  **not run** because deployed-source/asset gates remain closed.
  No success marker: both current verification fields remain **null**.
  Earlier oil/gas success below does not verify the new copy release.

Authoritative current outcome:
`.squad/decisions/inbox/st-brown-ui-copy-release.md`,
top `.azure/deployment-plan.md`, and
`deploy/.chat-artifacts/ui-copy-recovery-terminal-proof.json`.
Further Oryx recovery requires separate authorization/review, not an unchecked
third deployment, source/configuration change or verification override.

### User-directed retry diagnosis — 2026-10-26T23:11Z

The user explicitly authorized a retry at **23:04:39.769Z**. Reconfirmed official
validation and exact frozen source/ZIP/agent pins. No third blind ZIP attempt:
although the HTML appears in a directory listing, actual Kudu GET is **404** and
read-only `stat` reports **ENOENT** while its directory and new JS exist.
The same rsync target failure is not demonstrated cleared.

The new JS `/assets/index-BB76jn9J.js` is already publicly HTTP **200** and exactly
matches the reviewed build; only HTML still points at the old JS. All 20 actual
source files and compiled grounding match reviewed bytes. Latest observed
database health is **healthy, connected=true**, checkedAt
**2026-10-26T23:11:07.603Z**; process remains HTTP 200.

Proposed, **not executed**, alternative: Microsoft's supported single static-file
deployment of the existing reviewed 623-byte HTML to its existing target, with
clean=false/restart=false and no configuration changes. This may still fail at
the same filesystem fault; in-place HTML failure risks root-page availability.
Independent approval of the delivery mechanism and truthful state-evidence
reconciliation is required before execution. Exact command, file hash, risks and
full unchanged-verifier gates are in the top deployment plan.
No new acceptance/verified marker. Agent 2/MCP v3 remain unchanged.

## Previous CHAT-ONLY decoder release — live acceptance passed

Deployed and verified:
https://app-redshift-chat-bs01-bb4b2781.azurewebsites.net.
The official azure-validate workflow completed **2026-10-26T22:26:03Z** before
azure-deploy executed only the existing App Service application stage.
Full hosted acceptance passed **2026-10-26T22:43:40.817798Z**.

- New source SHA-256:
  `77005490f46fe33177ebec38dd45585d01343f8e05f125b799b19303eecaff25`.
- New immutable ZIP SHA-256:
  `1e094ff7c8cfca6fdfce66c3c96013923ebd8bc62d9b7ea9a846ad1b637ec985`;
  `deploy/.chat-artifacts/redshift-chat-77005490f46fe33177ebec38dd45585d01343f8e05f125b799b19303eecaff25.zip`
  contains **20 exact allowlisted entries / 49,113 bytes**.
- Actual App Service managed identity returned **21,157,564.26 bbl** oil for
  2025-01-01 through 2025-12-31 using `get_data_context,analyze_data`.
  Fresh same-cookie gas continuation returned **44,177,025.20 Mcf** for the
  same period using a new `analyze_data`, with `continued=true`.
  Exact unrounded totals/units/period agree with a fresh independent Data API
  reference, not source constants or operator inference replay.
- Full direct MCP numerical acceptance passed all five physical sources,
  including **213,367,864.95 USD** operating cost. Actual current database
  health was `healthy,connected=true`; strict decoder/execution/final-JSON/
  plaintext-answer guards and Secure/HttpOnly/SameSite=Strict session passed.
- Registered agent **2** and definition
  `8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20`,
  MCP **v3** digest
  `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`
  and revision `ca-redshift-bs01--0000003` remain unchanged. No new registration,
  image build, provisioning, grants, credentials, network or CORS change.
- Kudu build completed active/success **2026-10-26T22:29:15.8525189Z**; application
  stage exited 0. All actual remote source files, compiled decoder, public HTML
  and referenced business-UX JS/CSS matched reviewed build bytes.
- First full verification failed at no-Origin MCP acceptance; second full attempt
  returned HTTP 503 without precise phase capture. Isolated hosted oil then
  succeeded, and a final bounded full run passed. Heavy probes were serialized
  with 65-second rolling-window waits. No retry deployment or guard relaxation.
  Browser interaction testing is not claimed by HTTP and byte-match acceptance.

Authoritative proof: `.squad/decisions/inbox/st-brown-decoder-correction-release.md`,
new CHAT-ONLY sections in `.azure/deployment-plan.md`, and ignored
`deploy/.chat-artifacts/decoder-{validation,hosted-artifact,hosted-acceptance}-proof.json`.
Existing strict state has matching deployed/verified source and ZIP fingerprints;
old source ZIP and rollback state remain retained.

## Historical analytics v3 failure and diagnosis

The following blocked-release/local-fix descriptions predate the verified
CHAT-ONLY correction above. They are retained as historical evidence.

The structured analytics artifacts are **deployed, but overall hosted numerical
acceptance is BLOCKED**, as of 2026-10-26T21:59:36Z:
https://app-redshift-chat-bs01-bb4b2781.azurewebsites.net.
Registered agent version **2** matches reviewed definition
`8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20`.
App settings pin that version. Source
`900997e9fa54ba68ceb88ee43159211c5d733ebd0bc9f606fc3d4bfefa806a22`
and ZIP `99496c928e6b49f45f26afb0be57e0787f35589da17435715d3b6294a858a66f`
are deployed: Kudu active/success completion at
`2026-10-26T21:37:53.8306061Z`, all 20 actual remote source files match, and
downloaded HTML plus referenced JS/CSS are HTTP 200 and byte-identical to the
reviewed built bundle. Existing project-only Consumer/User roles and TLS/runtime
protections passed post-release inspection.

The first source deployment failed during the remote build; its terminal failure
was confirmed before the sole retry. The identical frozen retry built successfully
but CLI tracking failed. Read-only Kudu success plus exact remote source/bundle
verification reconciled deployed fingerprints through existing allowlisted state
fields; no verification guard or source was changed.
Process/database health subsequently recovered, but full verification reached
the real hosted `/api/chat` and failed HTTP 503. A literal 2025 oil question
returned public `AGENT_UNAVAILABLE` after 17.2 seconds. Secure cookie attributes
passed; an oil numerical answer and same-cookie fresh gas continuation did **not**.
No provider/grounding field can be inferred from that generic public error.
Both current verification fields are null. Stop for narrow independent diagnosis
and review, not prose fallback, relaxed grounding, permission changes or rollback.
Full proof: `.squad/decisions/inbox/st-brown-analytics-v3-deployment.md`.

### GA serialization compatibility — local fix pending review

Actual operator-identity registered-agent v2 diagnosis identified successful MCP
outputs encoded as business JSON plus LF plus `{structuredResponse: payload}`.
The local BFF now strictly normalizes exactly those two object documents only
when the second has that sole key and both business objects deeply agree.
Multiline/escaped JSON and reordered object keys work; extra keys/documents,
nonobjects, nested envelopes, malformed/mismatched data and prose are rejected.
The original 256 KiB total UTF-8 bound and all execution/final-answer guards remain.

Local Node 24.22.1 chat tests (**100 passed**), typecheck and build passed.
This is **pending Goff review**, not Ready for Validation or a deployment.
Hosted acceptance remains BLOCKED, and the App Service managed identity must
still pass actual hosted oil plus fresh same-cookie gas acceptance against fresh
independent references after an approved release. The fix changes only the chat
serialization adapter: preserve MCP image **v3**, registered agent **v2**, frozen
artifacts, grants/settings and null verification markers. After review, the
parent must revalidate and freeze a **new chat-only immutable ZIP**; no agent
definition update or MCP rebuild is required for this fix.
Record: `.squad/decisions/inbox/sewell-foundry-result-serialization-fix.md`.

### Historical implementation and metadata context

The user approved implementation and deployment on existing infrastructure and
explicitly accepted keeping the current admin identity for the synthetic POC.
Independent implementation/security review and numerical runtime acceptance
remain gates. No credentials, grants, identities or networks change.
Goff rejected the first consumer-grounding artifact: empty/context-only tool
calls could still return invented numerical text. St. Brown's independent
revision now enforces the strict final-text JSON protocol documented in
`src/redshift-chat/README.md`. Data answers require this response's valid executed
`analyze_data`, including continuations; clarification/refusal reasons select only
server-owned text. Invalid output or tool failures fail closed. Empty results
receive a fixed notice; partial/null results have mandatory server-owned caveats.
The agent definition and BFF must be
released together; no new response-format API or preview dependency is assumed.
Goff subsequently approved the independent revision, official Azure validation
passed, and the artifacts were deployed as recorded above. The following
implementation-era and metadata verification descriptions are historical.
The following early metadata diagnosis is historical context:
After independent peer/security review and assignment-only validation, the
user-approved project-scoped Cognitive Services User assignment was deployed.
The earlier acceptance observed the actual App Service managed identity executing
`list_schemas` and continuing a same-cookie conversation, but accepted an empty
schema answer. Connection success and tool invocation did not prove discovery.
Live diagnosis confirmed `information_schema.schemata` filters schemas by owner;
the configured admin and data owner differ. Native `SVV_ALL_*` discovery fixes
this without broader grants, credential changes, business-row queries or new tools.

The earlier verifier passed process health, Redshift, CORS, original no-Origin MCP,
registered-agent, role, source-fingerprint and continuation gates; successful
verification metadata was persisted in ignored `deploy/chat-state.json`. That
historical marker does not prove the stronger dataset gates now implemented.
An earlier no-Origin MCP probe failed; the subsequent full retry passed without
provisioning changes. Interactive browser UX acceptance remains outstanding.
Earlier local correction validation: **56 chat + 22 original = 78 deployment unit
tests** passed; both Bicep entry points compiled (existing Web `BCP081` warnings only).
Compiled inventory confirms the assignment-only mode excludes Consumer updates.

## Exact approved scope

- Subscription `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, tenant
  `e90bd921-0e00-4e6f-b87c-713670ee27bf`.
- New child project **`redshift-test-project`**, system identity, under existing
  **`foundry-sandbox-swc-mx01`**, `rg-client-sandbox-eus2-mx01`, Sweden Central.
  The account itself is an **existing** Bicep reference.
- New Linux **B1 / one instance** plan `asp-redshift-chat-bs01` and app
  `app-redshift-chat-bs01-bb4b2781`, **East US 2**, in existing `rg-redshift-bs01`
  (resource-group metadata remains Brazil South). Existing names are unchanged.
  Node **24 LTS**, HTTPS only, minimum TLS 1.2 for site/SCM, FTPS disabled,
  Always On, system-assigned identity, SCM/FTP basic publishing disabled.
- Exactly two runtime assignments, both direct to App Service system identity
  **`ebcf9b66-cca4-46a6-a344-3f100ea7eb0d`** at **new-project scope only**:
  retain **Foundry Agent Consumer** `eed3b665-ab3a-47b6-8f48-c9382fb1dad6`;
  add explicitly approved **Cognitive Services User**
  `a97b65f3-24c7-4388-baec-2e87135dc908`. The latter has broader project
  data/connection-secret permissions accepted by the user, not minimal
  inference-only privileges.
  No project-identity/account grants, custom role, account/RG/subscription
  runtime roles, new model, Foundry account, capability host, ACR or storage.
- Reuse unchanged model deployment `gpt-5.4-mini`, model version `2026-03-17`,
  `GlobalStandard`, capacity 950. Global inference is not Sweden-only.
- Registered prompt agent `redshift-chat-agent`: exactly
  `get_data_context` and `analyze_data` at the existing remote MCP.
  The allowed-tools filter uses Foundry's canonical object form; the approval
  exemption is filtered to those same two names:

  ```json
  {"allowed_tools":{"tool_names":["get_data_context","analyze_data"]},"require_approval":{"never":{"tool_names":["get_data_context","analyze_data"]}}}
  ```

This is structured, data-backed analytics, **never arbitrary SQL**. MCP retains
four legacy metadata/health tools for compatibility, but the agent cannot call
them. The BFF health probe still calls only `test_connection`.
B1 retains the approved **$14.60/month at 730 hours ceiling** based on the earlier
Brazil South $0.020/hour estimate; recheck East US 2 pricing before provisioning.
Inference/agent/tool/transfer and existing Azure/AWS costs remain additional.
The public request/session controls are resettable POC protections, not a spending
cap. No budget is created. Private endpoints/network isolation are deliberately
not provisioned under the user's public synthetic-POC exception.

## Dependencies and preparation

Use the existing deployment environment; no additional Python dependency file is
needed. It already includes `azure-identity==1.26.0` and `mcp==1.30.0`.
Install/restore using `deploy/requirements.txt` only if the environment is missing.
Node 24 and npm must be available locally. The frontend owns its lockfile and SDK
pins (`@azure/ai-projects` 2.9.0, `@azure/identity` 4.14.0).

```bash
export PATH="$PWD/src/redshift-chat/.runtime/node-v24.22.1-darwin-arm64/bin:$PATH"
deploy/.venv/bin/python -m unittest discover -s deploy -p 'test_chat_deploy.py' -v
az bicep build --file infra/chat.bicep --stdout > deploy/.chat-preflight.json
deploy/.venv/bin/python deploy/chat_deploy.py
```

The default `check` is **read-only**: verify the exact subscription/tenant,
required GA provider APIs, Node 24, account/model metadata and existing MCP.
It does not deploy, create agents, invoke inference, read dotenv files, retrieve
keys, list secrets, or print raw settings/error bodies.
Local `build` is also non-cloud-mutating, but runs `npm ci`, typecheck, tests,
and build before producing a source ZIP:

```bash
deploy/.venv/bin/python deploy/chat_deploy.py --stage build
```

Analytics release sequence after independent review/validation: MCP image-only
`v3` build/update first (see `README.md`), then chat `--stage agent`, `--stage build`,
`--stage app`, `--stage verify`. Cloud stages require `--apply --gates-approved`.
No `prerequisites`, `configure` or `all` stage is needed: existing resources,
grants, credential references and CORS must remain unchanged. Record the current
agent version and retain the previous ignored `chat-state.json` before agent/build;
rollback must restore the previous ZIP and pinned version together. New ZIP names
are source-addressed (`redshift-chat-<source_sha256>.zip`); an existing matching
ZIP is checked and reused, never overwritten. The previous static ZIP is retained.
These commands have NOT been executed for analytics.

The retained numerical `verify` gate still compares exact independently computed
oil/gas totals and units/period against the actual managed-identity app's decoded
plain-text replies, with a fresh analysis on same-cookie continuation. It also
rejects leaked protocol objects and over-budget tool evidence. Server-owned
clarification/unsupported/empty/partial notices cannot satisfy numerical release
acceptance. Confirm actual GA service serialization of MCP output matches the
reviewed direct-JSON, official MCP envelope or strict equal two-document encoding
(the latter is locally implemented but still awaiting review) and that the pinned
agent emits complete protocol JSON within the unchanged output budget. A
serialization/compliance failure blocks release; do not weaken validation or
substitute a direct model call.

The ZIP is constructed from an explicit filename/directory/extension allowlist:
package manifests, TypeScript/Vite configuration, `client/index.html`, and runtime
`server`/`client`/`src`/`public` sources. It excludes dotenv/hidden files,
`.git`, `.squad`, tests, `node_modules`, generated `dist`, caches and other
unlisted files. It rejects links and scans only selected files for credential
patterns. This scan is a defense, not proof that every possible secret format is
absent; independent source/bundle review remains mandatory. It never opens `.env`.
Source and ZIP SHA-256 fingerprints are stored, and stale artifacts are rejected.

### Build/deploy strategy

The ZIP has application files at its root. App Service builds on **Linux Oryx**;
macOS `node_modules` are never uploaded. `SCM_DO_BUILD_DURING_DEPLOYMENT=true`,
`ENABLE_ORYX_BUILD=true` and `NPM_CONFIG_PRODUCTION=false` enable dependency
restore including build-time Vite/TypeScript dependencies despite the runtime
`NODE_ENV=production`. Oryx runs the package's `build` script; the post-build
command prunes development dependencies explicitly. The startup command is
`npm start` (`node dist/server/index.js`). Deployment uses `az webapp deploy`
with Entra authentication, never publishing-profile/basic credentials. If
disabled SCM basic publishing prevents deployment, **stop**; don't re-enable it
silently.

## Review and actual ARM preflight

The full template is subscription-scoped only to combine modules in the **two existing**
resource groups. New resources are limited to project, plan, site, publishing
policies and the two project-scoped roles. No existing MCP resource is in the template.
The template does not propagate the earlier vault-only `SecurityControl=Ignore`
tag. The parameter file pins the actual approved subscription and `appLocation`
to `eastus2`; both Bicep parameter constraints and actual site/plan inventory checks
reject other regions. Subscription deployment-record location stays `brazilsouth`
to preserve existing name/location consistency; it does not place the new app there.

Actual ARM validation previously failed with `InternalSubscriptionIsOverQuotaForSku`:
Brazil South B1 limit 0, usage 0, required 1. The minimum quota request failed with
`QuotaNotAvailableForResource` (request `ec9d9495-e3da-4602-ae9e-4610d235992b`).
East US 2 B1 limit 11, usage 0 was verified using Azure quota CLI. The user selected
**“Deploy the chat App Service in East US 2 (Recommended)”**. Only the new plan/site
move: existing MCP remains Brazil South and Foundry remains Sweden Central.
Read-only ARM validation of this correction passed on **2026-10-26**. What-if
returned **Succeeded**, with **6 Create + 23 Ignore = 29 entries** and no
Unsupported changes: the new project, plan, site, FTP/SCM publishing policies,
and project-scoped Consumer role assignment. That is historical predeployment
evidence, not validation of the additional approved role. The project/site now
exist; parent approval/status and runtime acceptance remain separate gates.
Earlier deployment tests passed **48 chat + 22 original = 70**; Bicep compilation
and compiled stable role-name checks passed. Compilation can emit
expected `BCP081` warnings for the Web GA APIs newer than local Bicep schemas.

After independent review and the parent skill gates permit validation:

```bash
deploy/.venv/bin/python deploy/chat_deploy.py --stage validate
```

This calls actual subscription ARM **validate and what-if**, not a local syntax
check. It rejects destructive, out-of-scope, unsupported and unknown changes.
`Ignore` is allowed only at the two approved existing resource-group roots or
their descendants; it does not authorize changes to those existing resources.
Each role assignment name uses the known project ID, application resource ID and
its built-in role ID. The role module pins the principal to the exact approved
App Service identity; replacing the identity requires a separate decision.
The full template passes the actual app principal to that constrained parameter
(Bicep `any()` bridges the output's string type; ARM still enforces `allowedValues`).
The existing Consumer name/scope/role are unchanged.
It does not create resources. Operator deployment, role-write and agent-authoring
permissions must already exist. A preflight permission failure is a blocker,
not permission to assign a broader role.

### Isolated role correction — parent-run only after peer/security review

Do **not** rerun `prerequisites`, `all`, or the full `infra/chat.bicep` deployment
to add this role: they also manage project/site resources. Use the existing
resource-group-scoped role module alone, in **Incremental** mode, with the
Consumer resource condition disabled. Existing account/project declarations are
references only; no app/plan/identity/model/agent resource is in this template.
Default `includeConsumerAssignment=true` retains Consumer in the full desired
state; `false` skips its PUT, not deletes its existing assignment. **Never use
Complete mode**, which could delete existing resources.

From the project root, after the parent's independent review/validation gates:

```bash
az deployment group validate \
  --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c \
  --resource-group rg-client-sandbox-eus2-mx01 \
  --name redshift-chat-project-user \
  --mode Incremental --template-file infra/chat-role.bicep \
  --parameters principalId=ebcf9b66-cca4-46a6-a344-3f100ea7eb0d includeConsumerAssignment=false \
  --only-show-errors --output none

az deployment group what-if \
  --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c \
  --resource-group rg-client-sandbox-eus2-mx01 \
  --name redshift-chat-project-user \
  --mode Incremental --template-file infra/chat-role.bicep \
  --parameters principalId=ebcf9b66-cca4-46a6-a344-3f100ea7eb0d includeConsumerAssignment=false \
  --only-show-errors --no-pretty-print --output json
```

Inspect what-if: the only permitted Create is the exact assignment below (or
NoChange if already present); **no Modify/Delete/Unsupported**. The Consumer and
all pre-existing resources must remain untouched; stop on any unexpected change.
Only after that gate, the parent may run this isolated infrastructure command:

```bash
az deployment group create \
  --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c \
  --resource-group rg-client-sandbox-eus2-mx01 \
  --name redshift-chat-project-user \
  --mode Incremental --template-file infra/chat-role.bicep \
  --parameters principalId=ebcf9b66-cca4-46a6-a344-3f100ea7eb0d includeConsumerAssignment=false \
  --only-show-errors --query properties.outputs.cognitiveServicesUserAssignmentId.value --output tsv
```

Stable Cognitive Services User assignment resource ID (`guid(project.id, appId,
cognitiveServicesUserId)`, independent of runtime provisioning):

```text
/subscriptions/bb4b2781-6739-4fa1-994e-4ad6ce55c59c/resourceGroups/rg-client-sandbox-eus2-mx01/providers/Microsoft.CognitiveServices/accounts/foundry-sandbox-swc-mx01/projects/redshift-test-project/providers/Microsoft.Authorization/roleAssignments/1d0a3438-808c-535c-a6da-79dda6fc03c0
```

The unchanged Consumer assignment GUID is
`a2b0451e-4de4-5b0d-8dad-8567fe0633e2` at the same project scope.
No account, resource-group, subscription, group or project-identity grant is
authorized. No custom role or credential/model/API fallback is authorized.
After bounded propagation, rerun role inspection and the actual App Service
agent + allowed MCP call + continuation gate; role creation alone is not success.

### API versions verified during preparation

| Service | GA API |
|---|---|
| Microsoft.Web site, plan, configuration, publishing policies | `2026-08-01` (live provider inventory) |
| Foundry account/project/model ARM | `2026-09-01` |
| Foundry agent data plane | `v1` |
| Existing Container Apps CORS-only PATCH | `2026-07-01` |
| Role definitions/assignments | `2022-04-01` |

Live read-only preparation confirmed the exact tenant/subscription, current
Web/Foundry/ACA API availability, Node `NODE:24-lts`, and the unchanged approved
Foundry model metadata. Local Bicep compilation, actual East US 2 ARM validation
and bounded what-if passed. **Provisioning and live chat acceptance remain
parent-gated.** The earlier Brazil South ARM attempt failed as recorded above.
The current Learn Web template index can lag live provider API inventory; no
preview or deprecated fallback is used.

## Explicit deployment stages

`--apply --gates-approved` is an explicit operator attestation that independent
parent review, azure-validate and azure-deploy approvals have passed. It is not
an alternative to those gates. Without both flags mutating/billable smoke stages
fail before any operation.

Run stages separately so a failed gate stops without touching other stages:

```bash
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage prerequisites
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage agent
deploy/.venv/bin/python deploy/chat_deploy.py --stage build
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage app
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage configure
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage verify
```

`all` runs those stages in order only with both attestations; it does **not** bypass
the external review/validation gates. Prefer individual stages for first release.

- `prerequisites`: full Bicep provisioning and verification of identities, plan,
  settings/TLS, publishing policies and both exact project-only assignments.
  **Not the entry point for the current isolated role addition.**
- `agent`: use signed-in operator credentials **in memory** and GA `v1`
  `/agents/redshift-chat-agent/versions`. Page through existing versions with a
  finite bound, reuse an exact matching definition or create a new version,
  then GET/read-back its definition. A matching metadata digest alone is not
  trusted. Version/digest metadata is nonsecret.
- `app`: recheck inventory, pinned agent, source and ZIP fingerprints; configure
  only known nonsecret app settings and deploy. Existing unknown app settings are
  not overwritten wholesale. Raw app-setting CLI responses are suppressed.
- `configure`: PATCH only
  `properties.configuration.ingress.corsPolicy` on the existing MCP. Exact
  frontend origin comes from the actual ARM `defaultHostName`. Methods
  GET/POST/DELETE/OPTIONS, exact MCP transport header allowlist, exposed
  `Mcp-Session-Id`, credentials false, max-age 600. Compare the entire non-CORS
  configuration/template/identity/tags fingerprint before/after. Never change
  image, env, secrets/references, identities or MCP Host/DNS/SDK Origin guards.
  If any unexpected drift appears, stop; do not perform a broad rollback PUT.
- `verify`: perform the staged actual-runtime gate described below. Only success
  records `verified_at` and the successfully deployed source digest.

Metadata stays in ignored `deploy/chat-state.json`; ZIP/npm cache in ignored
`deploy/.chat-artifacts/`. Never store credentials, tokens, cookies, prompts,
responses, database configuration or raw errors there.

## Mandatory dataset-level actual-runtime acceptance — pending

**Consumer-only authorization historically failed with an actual-identity upstream
403; the approved project-scoped Cognitive Services User addition passed the
earlier invocation gates, not the dataset-level checks below.**
Do not substitute a developer-credential smoke, direct model call or preview
agent-scoped endpoint.

Before smoke, verify exact inventory, the pinned agent definition, nonsecret
target/build settings, and absence of credential/identity override settings.
Inspect direct **and inherited/group** role assignments: require exactly Consumer
and Cognitive Services User, both direct to the approved App Service identity at
the exact project; reject missing/duplicate roles, foreign role-definition IDs,
extra/conditional/group grants or wider scopes. Project identity must not have an unapproved
account/inherited role. If permission to enumerate effective assignments/groups
is missing, stop rather than assuming the check passed.

`verify` checks:

1. Actual MCP OPTIONS permits only the deployed frontend origin and required
   transport headers/methods, without credential permission; a hostile origin
   gets no CORS permission (or explicit 400/403).
2. Both process `/healthz` routes are reachable; the official MCP client can
   initialize, list **exactly six tools**, and perform actual `test_connection`
   without browser Origin. A fixed read-only Data API SELECT independently
   computes 2025 oil/gas/cost totals, January oil, top well gas, top state oil,
   monthly-price average and well count. MCP executes strict plans and must
   match every exact value and expected physical source, including verified
   monthly/annual substitution. Empty, incorrect, failed/unexecuted or
   unexpectedly truncated results fail. Top-N truncation is explicitly allowed.
   No static dataset totals are runtime answers.
3. BFF `/api/health` returns `healthy` and a `checkedAt`, not just process liveness.
4. A 2025 total-oil question must return the exact independent oil value, bbl,
   2025, and actual `analyze_data` evidence; metadata/numeric-looking prose fails.
   The server issues a Secure/HttpOnly/SameSite=Strict cookie.
5. A same-period gas follow-up using the same opaque cookie must return the exact
   independent gas value, Mcf, 2025, new `analyze_data` evidence and
   `continued: true`, without accepting browser response IDs.
   Transport/status, exact tool boundary, role, CORS, health and timeout gates
   remain unchanged; rate-limit or upstream failures are not retried as success.

**BFF smoke response integration contract:** `POST /api/chat` returns `reply`,
minimal `toolNames` from actual SDK MCP call items, and `continued` on a follow-up.
These contain no tool arguments/results, response IDs or credentials. BFF integration
now implements this contract, using actual SDK MCP tool names and the server-owned
continuation chain; 37 application tests passed. Runtime verification still must
observe these fields from the deployed service rather than infer live readiness
from local tests.

The BFF production credential implementation must be reviewed to confirm it is
**ManagedIdentityCredential**, with no developer/key fallback. Deployment
does not add a separate agent-authoring grant; the user-approved built-in role's
broader project permissions remain explicitly accepted. Any 403, missing tool evidence,
continuation failure, model/tool access error, stale/failed health or unexpected
grant blocks a live-ready claim. CLI/HTTP output is classified and sanitized;
never dump application logs, settings bodies, tokens, cookies or tool data to
diagnose failure. Wait for bounded provisioning/role propagation and rerun the
specific failed stage; no hidden retries of billable chat requests.

Further release evidence remains the parent/QA responsibility: browser
conversation, unsupported computation explanation, retry/clear, session
isolation/TTL/turn/concurrency/rate bounds, trusted-proxy spoof checks, output
escaping, retention disclosure and continued original MCP full acceptance.
No cost/retention/role assumption is established by mocked unit tests.

## Official references

- [Prompt agents and project Responses pattern](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent)
- [Stable 2.9.0 createVersion REST serialization](https://github.com/Azure/azure-sdk-for-js/blob/%40azure%2Fai-projects_2.9.0/sdk/ai/ai-projects/src/api/agents/operations.ts)
- [MCP tool schema](https://learn.microsoft.com/en-us/javascript/api/@azure/ai-projects/mcptool?view=azure-node-latest)
- [Scoped approval filter](https://learn.microsoft.com/en-us/javascript/api/@azure/ai-projects/mcptoolrequireapproval?view=azure-node-latest)
- [Remote MCP security guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol)
- [Foundry RBAC](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry)
- [GA project ARM schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-09-01/accounts/projects)
- [GA ACA ingress/CORS schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2026-07-01/containerapps)
- [App Service ZIP/Oryx and Entra deployment](https://learn.microsoft.com/en-us/azure/app-service/deploy-zip)
