# Chat migration to Azure Container Apps

## Official-backed chat cutover deployed and verified — 2026-10-27

The current release is `ca-redshift-chat-bs01--official3600`, exact Foundry
agent version **3**, with both the agent MCP tool and BFF health probe bound to
`https://ca-redshift-official-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp`.
Public chat:
https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io

- Chat build `cq7`: immutable
  `sha256:7eff76f081d526ac3ae0870240b01b938edbf1c1f42647f2d3ddcdd7057a59df`.
- Official candidate `--ready3600`, build `cq6`:
  `sha256:c21ae74027dba38dbf1e650e872a6b9de96f37426c0ee16b439fbb7d92ac4180`.
  Published AWS server0.1.2 remains unmodified; no direct-query shadow path.
- Secretless STS duration is3600s, avoiding immediate advisory refresh for
  900s credentials. Actual identity/expiry and controlled near-expiry live
  refresh were proven. No operator credentials were copied into the runtime.
- Actual public governed context and reconciled analysis passed before release:
  2025 oil21157564.26, gas44177025.20, cost213367864.95; price DECIMAL, null,
  truncation, invalid-plan and connected-health evidence retained.
- Bounded chat/Foundry230s < browser235s < ACA ingress240s. Health60s.
  Four-tool cap, Python50s, effective DB10000ms, read-only permissions, closed
  plans, reconciliation, grounding, origin/rate/session/quarantine unchanged.
- 103 Node tests/typecheck/build,25 cutover tests, independent security and
  correctness reviews, fresh exact-template ARM validation/what-if and live
  role checks passed. Only the chat template changed.

Exactly one guarded PATCH changed image+agent version+probe URL together.
Its first postverify observed the old zero-traffic revision deprovisioning;
subsequent read-only verification confirmed one active healthy new revision.
No PATCH retry occurred. This is snapshot/local-lock guarded, not atomic CAS.

**Actual hosted business/session/negative acceptance passed.**
Fresh2025 oil: **21,157,564.26 bbl** in78.858s, with fresh context+analysis.
Same-session gas: **44,177,025.20 Mcf** in36.046s, with fresh analysis and
continued=true. Both reported daily source/grain and zero nulls.
Unsupported profit produced fixed non-answer text without tools.
Cookie reset restored20turns; a supported post-reset oil request ran fresh
context+analysis, returned the same exact total in69.298s and continued=false.
Foreign Origin403 and malformed input400 passed. Final health refresh was
healthy/connected=true at18:07:13.343Z; UI and final exact ARM bindings passed.
No rollback was needed.

Qualification: an initial post-reset greeting returned fail-closed503
`AGENT_UNAVAILABLE`; its underlying provider cause is unknown. That unsuitable
business-data positive probe was replaced once with the supported oil request,
not an application change or weakened check. The original observation remains
in the proof. Arbitrary conversational prompts are not a supported analytics
guarantee. One UI capture assertion also required case-insensitive HTTP header
lookup; actual HTML/root/built script were verified, not repaired.

Latest proof:
`.azure/official-migration-proof/hosted-cutover-acceptance.json`.
Release/build/validation/final live-state proof: `.azure/official-refresh-build/`,
especially `final-release-proof.json`.

Rollback retains `.azure/official-chat-release.json` (original template and
paired binding), original agent2, old MCP, and original chat image
`sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`.
Use `official_cutover.py prepare-rollback` with the reviewed original release
hash and a fresh explicit suffix, then its guarded `apply` with the resulting
artifact hash and current evidence gates. It restores image+agent2+old probe
together; never invoke legacy App Service stages or delete old resources.
Normal release replaces in-memory sessions; each acceptance cookie stays only
in memory. Historical progress sections below are preserved, not current state.

## Official native-MCP business demonstration succeeded — 2026-10-27

The one authorized transport correction now waits for authenticated remote
bootstrap acknowledgement before sending the readable heredoc in paced256-byte
stdin chunks. Six tests passed. A harmless size-matched6,580-byte/73-line probe
confirmed startup within the15-second deadline and matched the candidate-
computed padding fingerprint, without MCP/SQL/federation calls.

The subsequent **single native official-MCP demonstration succeeded** using the
candidate's actual federated `RedshiftAzureOfficialMcpRole` identity and the
unchanged published `awslabs.redshift-mcp-server==0.1.2` executable:

| 2025 actual native result | Value |
|---|---:|
| Oil | 21157564.26 bbl |
| Gas | 44177025.20 Mcf |

Native query ID: `e00c0783-b929-445c-aef6-933b7831b86d:3`; one row, both
decimal strings. Native `execute_query` took57.813s; total **91.133s**, within
the120-second diagnostic budget. `enforce_read_only=true` used the official
self-contained read-only Batch. Successful upstream Batch completion, client
session exit and stdio closure were all observed before the final success proof.
No root/direct-DataAPI query or old custom MCP supplied these answers.

This proves official MCP business-data execution, **not production cutover or
public health/chat latency acceptance**. Production, source image, persisted
auth configuration, public deadlines and readiness markers remain unchanged.
Latest sanitized evidence:
`.azure/official-migration-proof/startup-delivery-{progress,result}.json` and
`official-business-paced-{progress,result}.json`. Prior failed evidence below
is historical and preserved, not the current demonstration outcome.

## Latest single corrected demo — stopped at diagnostic bootstrap

Only the operator diagnostic artifacts were instrumented with authenticated,
incrementally retained progress and a separate strict final completion proof.
Four mocked capture tests passed. The one authorized corrected retry completed
in **112.974s** of the unchanged120s budget with `exec_proof_deadline`.
Last authenticated stage: **`remote_shell_ready`**. The main Python harness's
first marker was not observed, so neither native query submission nor business
results, upstream Batch completion, or stdio cleanup can be claimed.

The observed boundary is remote bootstrap → main diagnostic Python execution/
capture, not a proven AWS/MCP/SQL or teardown fault. No further retry was made.
The smallest next technical action is isolating delivery/start of that payload,
without another business query. Production, published image, auth/infra source,
public deadlines and readiness markers were unchanged. This is not a completed
official-MCP migration. Sanitized latest evidence is in
`.azure/official-migration-proof/official-business-observed-{progress,result}.json`;
older result files remain unchanged.

## Bounded native MCP business demo — not yet proven

User priority is actual official-MCP business execution, not old35s health
parity. With the user-approved120s demonstration budget, the named harness
returned no captured proof and overshot to126.670s (not a budget pass).
After the user's simplification, one supported self-contained read-only
`execute_query` attempt selected2025 SUM(oil_bbl)/SUM(gas_mcf) from the known
daily-production table, without our extra named transaction protocol calls.
The hard-supervised run ended at117.529s with operator transport
`exec_proof_deadline`: no native result, query_id, SQL error or cleanup
acknowledgement was captured. This is NOT a successful business demonstration
or proof of an AWS MCP/server/SQL failure.

No root/direct-DataAPI business shortcut, official-server patch, credential
file, public deadline change, readiness marker or production cutover occurred.
No further retry was made. The next correction must address the bounded
diagnostic execution/result-capture path; authentication is not the blocker.
See retained `.azure/official-migration-proof/official-business-standalone-result.json`
and the precise current record at the top of `.azure/deployment-plan.md`.

## Live federation progress and timing blocker — 2026-10-27 15:21 UTC

Operator login is now actually valid. Candidate-local safe claim inspection
and STS federation succeeded through the supported exec WebSocket transport.
Created only the dedicated tenant-v2 OIDC provider and
`RedshiftAzureOfficialMcpRole` with the reviewed narrow Batch-only policy.
Actual runtime identity:
`arn:aws:sts::684925376801:assumed-role/RedshiftAzureOfficialMcpRole/redshift-aca-runtime`.
Actual derived DB principal `IAMR:RedshiftAzureOfficialMcpRole` is newly created,
nonsuperuser/NOCREATEDB/password-disabled, with USAGE and five-table SELECT.
Effective `statement_timeout=10000` was returned by the real official server.
No credentials/JWTs were stored. Expiration was observed; automatic expiry
refresh and timeout stress/enforcement acceptance remain unproven.

**Migration NOT complete: actual latency gate failed.** First standalone call
timed out55s. One corrected named-transaction retry initialized in6.891s and
returned BEGIN+one budget SELECT in46.193s, already53.084s before rollback.
Rollback acknowledgement was not received by55.086s. This exceeds the unchanged
35s health requirement. Statement history afterward showed recent terminal SQL,
but is not a cancellation/transaction-close guarantee.
Unmodified upstream has1s polling/30s long polling; no public tool tuning was
found. Exact network-delay cause is not established, so no monkeypatch,
unsupported setting, relaxed budget or repeated rebuild is attempted.

Next action is one independently reviewed supported latency correction, then
fresh proof—not another login or approval. No budget marker/federation template
settings/new agent/chat cutover were enabled; candidate stays process-only.
New provider/role/DB user are retained for the approved migration; old ECS
trust, production images, agent2, identities and traffic are unchanged.

**Existing hosted application freshly works (old binding, NOT official):**
oil21157564.26 then same-session gas44177025.20 with fresh `analyze_data`,
26.133s/10.256s; connected health200/healthy/true at15:20:15.667Z.
No restart/repair was needed. See `.azure/deployment-plan.md` for the precise
resource ledger and `.azure/official-migration-proof/` for retained real evidence.

## Execution resume blocker — 2026-10-27 14:42 UTC

Actual administrative `aws sts get-caller-identity` now fails, exit255:
sanitized classification confirms expired login session and CLI's `aws login`
instruction. No provider bodies/credentials were retained.
**User action:** run `aws login` and select account `684925376801`; the operator
must then verify STS caller account before applying the approved scoped IAM/DB
changes. No keys are needed. This is not a request for migration reapproval.
Proof: `.azure/official-migration-proof/resume-aws-identity.json`.
No candidate exec retry, source/image change, resource mutation, restart or
cutover occurred during this resume. Official migration remains incomplete.

## Current candidate diagnosis — 2026-10-27 14:29–14:32 UTC, read-only

**Corrected failure boundary:** the earlier exec no-result is a diagnostic-tool
limitation, NOT an established root cause of candidate runtime failure.
Fresh live inspection finds the candidate process healthy but intentionally
not database-ready: it is still the incomplete process-only bootstrap.

- ProvisioningSucceeded/Running, latest=latest-ready
  `ca-redshift-official-bs01--jwxobc1`, single active revision/100% traffic.
  One Running replica, container ready/started=true, **restartCount0**; no exit
  code/reason reported for this running container. Exact successful `cq5` digest.
- HTTPS ingress8000 matches retained image CMD `0.0.0.0:8000` and all three
  `/healthz`:8000 probes. Fresh `/healthz` returned200/`ok`.
- Correct-host/correct-Origin MCP initialize and tools/list succeeded, protocol
  `2025-11-25`; the six expected adapter tools were returned.
- Exactly one governed readiness call, `test_connection`, returned
  `isError=true`: **`Verified database ten-second budget is required.`**
  Initialization/list/call/close took4.503seconds. The retained reviewed
  `child_environment` source raises this error BEFORE launching the official
  child or token/STS/SQL work. This is the observed failure, not a DB query,
  crash, wrong port, denied Host, or MCP transport failure.
- Live whitelisted configuration contains only target workgroup/database/
  region and exact allowed Host. The eight federation identifiers and
  `REDSHIFT_DB_BUDGET_VERIFIED` are absent. Optional executable override is
  absent normally; the image's pinned default is used.
- Fresh Graph reads confirm the dedicated Entra SP is assignment-required
  and only the candidate MI has `Redshift.ReadOnly`. Actual token claims,
  STS trust/exchange/refresh and effective DB budget are NOT proven.
  Current IAM-role read failed with no retained specific category; its
  current existence is unknown, not inferred from that failure.
- Finite console read returned60 healthz200 lines and no classified exception;
  finite system read returned only two normal event-stream connection events.
  This is limited recent evidence, not proof there were never older errors.
  Latest resource-write activity is successful creation13:47:57Z; later
  returned events are only successful getAuthToken actions from old exec
  attempts, NOT Entra token/STS acceptance.
- Azure Resource Health returned422 (unknown), and AppLens does not support
  this resource type. They do not establish an Azure platform outage.

**Smallest next action:** complete/prove the already-approved scoped
federation and effective10-second DB-budget prerequisites, then configure the
candidate from that evidence. Do not merely set the budget marker to bypass
the gate. No rebuild/restart, new architecture, portal handoff, exec retry,
cutover or cloud mutation was performed in this diagnostic pass.
Evidence: `.azure/official-migration-proof/current-candidate-{state,events,readiness,federation-prerequisites,diagnosis}.json`.

## Bounded existing-production follow-up — 2026-10-27 13:53 UTC

Retained503 evidence contains only HTTP503 after200/stale/connectednull; the
health monitor collapses timeout, false tool result and exceptions into the
same cached unavailable state. There is no retained provider error category
that supports a specific production correction.

Exactly ONE fresh read-only probe called existing production MCP
`test_connection` at13:53:47 UTC. Actual SDK HTTP initialize/tool call/close
succeeded in8.147seconds: `isError=false`, `{"connected": true}`.
The old runtime and database connection therefore worked at that instant.
This does not prove the old BFF's complete Foundry/chat flow or identify the
cause of its earlier503. No production correction, restart, reset, code change,
candidate exec retry or additional health probe was justified/performed.
Proof: `.azure/official-migration-proof/production-bounded-followup.json`.

### Exact prior candidate exec attempts and safe console unblock

Both attempts used the SAME CLI argv (the difference was local result parsing):

```text
az containerapp exec --resource-group rg-redshift-bs01 --name ca-redshift-official-bs01 --container redshift-official --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c --command "/opt/adapter/bin/python -c <in-memory sanitized claim-inspection script>" --only-show-errors
```

The remote script placeholder above is solely for readability. Full exact argv,
shell rendering and remote script are retained, without tokens or credentials,
in `.azure/official-migration-proof/candidate-exec-invocations.json`.
Attempt1: local classification `candidate_exec_no_result`, CLI exit0,
90-second upper bound. Attempt2: same classification, CLI exit0,456 output bytes,
no `OFFICIAL_PROOF_JSON=` marker,90-second upper bound. Neither attempt proves
that the upper bound was reached; exit0 is the CLI exit, NOT remote-query
acceptance. No provider error code was captured; raw provider output was not
retained, so no remote error text or auth denial can truthfully be supplied.

**Minimum actionable operator step:** open Azure Portal → Container Apps →
`ca-redshift-official-bs01` → Console, choose container `redshift-official`
and `/bin/sh`. Paste this command directly INSIDE that console. It uses only
nonsecret identifiers and the module already installed in the cq5 image; it
does not reference a local-workspace file:

```sh
env \
  REDSHIFT_AWS_ROLE_ARN=arn:aws:iam::684925376801:role/RedshiftAzureOfficialMcpRole \
  AWS_REGION=us-east-2 \
  REDSHIFT_AZURE_TENANT_ID=e90bd921-0e00-4e6f-b87c-713670ee27bf \
  REDSHIFT_AZURE_RESOURCE_APP_ID=98dabd0f-b9ca-47d4-82a9-7450209d80d0 \
  REDSHIFT_AZURE_MI_CLIENT_ID=15d1c1b6-30bc-490a-baee-7d7c45ded6cc \
  REDSHIFT_AZURE_MI_PRINCIPAL_ID=2a030643-be20-46a4-b375-e71fb3059a41 \
  REDSHIFT_AWS_OIDC_ISSUER=https://login.microsoftonline.com/e90bd921-0e00-4e6f-b87c-713670ee27bf/v2.0 \
  REDSHIFT_AWS_OIDC_AUDIENCE=98dabd0f-b9ca-47d4-82a9-7450209d80d0 \
  REDSHIFT_AWS_OIDC_SUBJECT=bootstrap-inspection \
  /opt/adapter/bin/python -m redshift_mcp_server.aws_credentials --inspect-claims
```

Return ONLY this module's selected-claims JSON or its sanitized failure
classification. Never print environment contents, identity endpoint headers,
the JWT, STS credentials or provider debug logs. `--inspect-claims` deliberately
permits discovering the real subject; it does not exchange STS credentials or
prove the JWT signature/AWS trust. Those remain later acceptance gates.

## Official candidate execution update — 2026-10-27 13:51 UTC

Candidate bootstrap is now actually deployed from successful `cq5` digest
`sha256:1afda7b8e545ca99d4131e07a9e3ae4aaa6868f0e0f04140258b55673d2348cb`
in the separate `redshift-official-candidate` repository. Candidate revision
`ca-redshift-official-bs01--jwxobc1` is Running; HTTPS process `/healthz` passed.
System principal `2a030643-be20-46a4-b375-e71fb3059a41`/client
`15d1c1b6-30bc-490a-baee-7d7c45ded6cc` is the only assigned member of the new
Entra resource SP's application role. Resource app
`98dabd0f-b9ca-47d4-82a9-7450209d80d0`; SP
`d7150b8e-191c-4895-a5fb-8bec73ed1013`, assignment-required.

**Migration NOT completed.** ACA exec diagnostic channel returned exit0
without a proof result on initial attempt and one framing-correction retry.
Execution stopped at that stage per user request; token/STS/DB/refresh and
cutover remain unverified. Minimum unblock is a working candidate interactive
exec channel and sanitized claim probe:
`.azure/official-migration-proof/inspect-claims.py`. Never emit the JWT.
No AWS/IAM/DB mutations, new agent or production binding changes occurred.
Candidate-only validate/what-if and deployment evidence are retained in
`.azure/official-migration-proof/`; detailed scope/result is at the top of
`.azure/deployment-plan.md`.

Production revision/images/traffic remain unchanged. Actual HTML200 observed;
connected health was stale/null then503, so current connectivity is not claimed.
The historical completed deployment below is not current migration acceptance.

## AWS official candidate migration — implementation artifacts, NOT deployed

The separately user-approved scope retains this working chat, agent2 and the
old MCP unchanged until actual candidate proof and independent security/
correctness review plus current Azure validation/deployment gates. New
`aws_federation.py` CLI is read-only/artifact-only. `official_cutover.py apply`
is a gated executor; it has NOT been executed.
No App Service stage is reused. Do not execute legacy `chat_deploy.py` stages.

```sh
deploy/.venv/bin/python deploy/aws_federation.py policy
deploy/.venv/bin/python deploy/aws_federation.py preflight
deploy/.venv/bin/python deploy/official_cutover.py agent-plan
deploy/.venv/bin/python deploy/official_cutover.py candidate-plan --image "$REVIEWED_ADAPTER_DIGEST"
deploy/.venv/bin/python deploy/official_cutover.py chat-preflight \
  --agent-version "$ACTUAL_NEW_VERSION" --revision-suffix official-20261027-a
deploy/.venv/bin/python -m unittest discover -s deploy -p test_official_migration.py -q
src/redshift-mcp-server/.venv/bin/python -m pytest -q src/redshift-mcp-server/tests/test_aws_credentials.py
```

Candidate: **only** `ca-redshift-official-bs01`, existing environment/registry/
pull UMI, separate system MI, single-active/min=max1, 0.25 vCPU/0.5 GiB and
HTTPS port8000 process-only `/healthz`. Bootstrap deliberately lacks federation
and `REDSHIFT_DB_BUDGET_VERIFIED`; health must not start the official child.
No role/secret changes are part of bootstrap. Candidate creation/build and the
subsequent MI configuration executor remain later reviewed deployment work.

Auth ABI: `REDSHIFT_AWS_ROLE_ARN`, `AWS_REGION`,
`REDSHIFT_AZURE_RESOURCE_APP_ID`, `REDSHIFT_AZURE_TENANT_ID`,
`REDSHIFT_AZURE_MI_CLIENT_ID`, `REDSHIFT_AZURE_MI_PRINCIPAL_ID`,
`REDSHIFT_AWS_OIDC_ISSUER`, `REDSHIFT_AWS_OIDC_AUDIENCE`,
`REDSHIFT_AWS_OIDC_SUBJECT`. All are nonsecret exact identifiers. The sole
runtime role is `arn:aws:iam::684925376801:role/RedshiftAzureOfficialMcpRole`,
region `us-east-2`; never the operator/root or existing ECS role.
`/opt/adapter/bin/python -m redshift_mcp_server.aws_credentials` is the
credential-process command. Standard output contains temporary AWS credentials
and Expiration only and MUST remain Boto3's private pipe. No token/key files,
cross-process cache, CLI credential fallback or database password exists.
`--inspect-claims` is a separate bootstrap diagnostic inside candidate ACA:
returns selected nonsecret claims, not the JWT; subject mismatch is permitted
ONLY in this mode. Tenant/audience/client/object/app-role/time validation still
applies. Local JWT comparisons are not signature verification; STS must verify
signature and exact role trust before credentials are issued.

Entra resource app/SP uses application-only `Redshift.ReadOnly`, assignment
required, only candidate system MI assigned. v2 trust maps AWS `:aud` to real
`azp` and `:oaud` to original resource audience, plus exact `:sub`/tenant issuer.
Do not assume `sub == oid`, or use arbitrary `:appid`/`:azp` condition keys.
v1 is supported only with its explicitly verified issuer/audience/appid. AWS
OIDC provider audience changes by version. The artifact generator does not
create a provider, app, SP, assignment or role. Its `identifierUris` payload
is a **post-create** app patch after Entra returns actual appId, not a way to
choose appId during creation.

Required runtime IAM: fixed-workgroup BatchExecuteStatement and
GetCredentials; ListWorkgroups Resource `*` is necessary because official
0.1.2 resolves even a fixed target by discovery; DescribeStatement/
GetStatementResult Resource `*` with statement-owner condition. Explicit deny
ExecuteStatement blocks legacy execution. No provisioned DescribeClusters,
tag permissions, Secrets Manager or broad Redshift grants. Resource/action
support and `${aws:userid}` session ownership still need independent review
and actual IAM proof; this is a proposed policy, not validated federation.

Remaining hard gates: actual candidate claims; app/SP write permission
(directory read does not prove it); nonsuperuser IAM-mapped DB principal,
exact five SELECT tables/schema USAGE and effective public/inherited/default
grants; supported non-overridable ten-second DB budget and wait scope;
real STS-expiry refresh and wrong-MI/audience/tenant failures; successful
Batch-only official execution/protocol/numerical proof; new agent version
definition hash bound only to candidate governed endpoint. No production
write/DDL permission probes without separate review.

`new_agent_definition()` reuses only the existing pure business definition
and replaces its one MCP URL, preserving model, protocol, instructions and two
public tool names. Register a **new** version through the existing GA Foundry
data-plane contract after gates; never overwrite version2. No agent registration
executor is enabled by these artifact CLIs.

Cutover artifact updates only `FOUNDRY_AGENT_VERSION`, `MCP_SERVER_URL` and an
explicit unique `revisionSuffix` in ONE existing-chat template PATCH. Image,
identity, roles, origin, scale, probes and every unrelated template field stay
exact. The tool hashes all other mutable resource/configuration fields, requires
the current active-ready revision, exactly one healthy active revision with100%
traffic and one ready running replica, and locks `deploy/.official-chat-cutover.lock`
for its own cooperating processes. It re-reads immediately before the single
supported ACA Update PATCH. It does NOT send an unsupported If-Match header,
change revision mode, redirect traffic or retry writes.

**Concurrency honesty:** ACA2026-07-01 Update documents no If-Match contract.
The former ETag prerequisite was self-introduced and is removed following
Goff's independent approval. Snapshot comparison plus the local lock is NOT
atomic compare-and-swap and cannot exclude an external portal/CLI writer
between recheck and update. Use a coordinated maintenance window. Any observed
drift, ambiguous active revision, failed provisioning or timeout stops without
overwrite/retry. Do not interpret snapshot checks as an external-writer lock.

The original release artifact is the explicit immutable rollback baseline;
artifact files are created exclusively, never overwritten. `prepare_rollback`
restores all original template fields/bindings except its necessary NEW unique
rollback revision suffix. It refuses unrelated config/identity drift.
`apply` requires the reviewed artifact hash, reviewed helper source hash and
all eight current evidence gates (the exact keys are listed in the function).
Gate booleans are operator attestations, not substitutes for retained review/
Azure/candidate evidence. The executor waits at most300seconds and verifies
the exact new revision/template/bindings, preserved configuration/identity,
100% single-active traffic and one ready running replica. A repeated invocation
of the same artifact verifies an already completed revision without another
PATCH; it never replaces the original rollback baseline.

The explicit `.azure/official-chat-gates.json` schema is:

```json
{
  "independent_security_review": true,
  "independent_correctness_review": true,
  "azure_validate_current": true,
  "azure_deploy_current": true,
  "actual_candidate_proof": true,
  "new_agent_candidate_binding": true,
  "sts_expiry_refresh": true,
  "db_budget_10s": true
}
```

Do not create/mark this evidence file true before the underlying checks pass.

**Intended operator commands, only AFTER new helper review and all actual gates:**

```sh
# Capture live original baseline and explicit revision; no cloud writes.
deploy/.venv/bin/python deploy/official_cutover.py prepare-cutover \
  --agent-version "$ACTUAL_NEW_VERSION" --revision-suffix official-20261027-a \
  --output .azure/official-chat-cutover.json

# Independent review records printed canonical artifact hash and helper file SHA.
# .azure/official-chat-gates.json contains the eight evidence-backed true gates.
deploy/.venv/bin/python deploy/official_cutover.py apply \
  --artifact .azure/official-chat-cutover.json \
  --reviewed-artifact-sha256 "$REVIEWED_CUTOVER_ARTIFACT_SHA256" \
  --reviewed-helper-sha256 "$REVIEWED_HELPER_SHA256" \
  --gates-file .azure/official-chat-gates.json --execute

# If live numerical/session acceptance fails AFTER revision is healthy, prepare
# explicit rollback; stop instead if provisioning/config state is ambiguous.
deploy/.venv/bin/python deploy/official_cutover.py prepare-rollback \
  --artifact .azure/official-chat-cutover.json \
  --reviewed-artifact-sha256 "$REVIEWED_CUTOVER_ARTIFACT_SHA256" \
  --revision-suffix rollback-20261027-a --output .azure/official-chat-rollback.json
deploy/.venv/bin/python deploy/official_cutover.py apply \
  --artifact .azure/official-chat-rollback.json \
  --reviewed-artifact-sha256 "$REVIEWED_ROLLBACK_ARTIFACT_SHA256" \
  --reviewed-helper-sha256 "$REVIEWED_HELPER_SHA256" \
  --gates-file .azure/official-chat-gates.json --execute
```

Revision readiness is not business acceptance: separately verify same-session
fresh oil21,157,564.26/gas44,177,025.20 and existing origin/reset/contracts.
Preserve old images/resources; session reset during revision change is expected.

AWS diagnostic preflight matched account684925376801 (root operator,
diagnostics only); Entra filtered app read succeeded with zero matching
resource apps. Directory create/assignment permissions remain **unproven**.

**Deployed and verified; obsolete App Service retired — 2026-10-27 02:00 UTC.**
Independent implementation/
security review and official azure-validate completed; azure-deploy created the
new chat ACA. The commands below document the completed migration, not an
instruction to rebuild/recreate the existing app.

- URL: https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io
- Revision: `ca-redshift-chat-bs01--sr9ms4f`; one active healthy running replica.
- ACR run `cq4`, Linux/AMD64, successful immutable image:
  `acrredshiftbs01bb4b2781.azurecr.io/redshift-chat@sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`.
- Runtime principal: `92f43c89-a02c-4636-b7c5-775067c221d5`, exactly the two
  project-only roles below; pull UMI unchanged.
- Actual HTTPS HTML/assets and fresh connected health passed. Real MI oil answer
  **21,157,564.26 bbl**, then same-cookie gas **44,177,025.20 Mcf**, continued true
  with fresh `analyze_data`; secure cookie/reset rotation and wrong-origin403
  despite spoofed proxy headers passed. Coordinator also independently observed
  loaded UI and connected status in browser.
- Initial transient downstream503 cleared after bounded in-container
  egress/MI/exact-SDK diagnosis, with no image/config/restart change.
- Sanitized proof: `.azure/chat-aca-{deployment,acceptance}.json` and
  `deploy/.chat-aca-image.json`. No secrets/tokens/cookies/raw logs retained.

The App Service helper/run-package experiments are superseded, not deployment
inputs. Do not execute them. The separately user-approved, independently
reviewed cleanup deleted the obsolete App Service, its dedicated B1 plan and
exactly two old identity project assignments. They were not dependencies of
this ACA or its successful acceptance. See completed cleanup evidence below.

## Exact target and identity

Subscription `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, RG `rg-redshift-bs01`,
Brazil South. Create only `ca-redshift-chat-bs01` in existing
`cae-redshift-bs01`. Reuse registry `acrredshiftbs01bb4b2781` and registry-scoped
AcrPull UMI `umi-redshift-imagepull-mx01`; do not grant any additional pull role.
The UMI authenticates image pulling only. Node's existing
`ManagedIdentityCredential` without a client ID selects the app's separate
system-assigned identity for Foundry (ACA's supported identity endpoint; no
App-Service-only endpoint implementation). Never set `AZURE_CLIENT_ID` to the UMI.

Grant exactly these roles to the **new system principal**, both at:

`/subscriptions/bb4b2781-6739-4fa1-994e-4ad6ce55c59c/resourceGroups/rg-client-sandbox-eus2-mx01/providers/Microsoft.CognitiveServices/accounts/foundry-sandbox-swc-mx01/projects/redshift-test-project`

- Foundry Agent Consumer: `eed3b665-ab3a-47b6-8f48-c9382fb1dad6`
- Cognitive Services User: `a97b65f3-24c7-4388-baec-2e87135dc908`

No account/subscription role grants, new registry/vault/environment/model/agent,
secrets, dotenv reads, or changes to MCP/database/network are needed.
The registered agent remains `redshift-chat-agent`, version `2`.

## Operator migration commands (completed; do not blindly replay)

Run from the workspace root with the existing deployment Python environment.
`plan` is local; `check` performs only safe selected-resource reads.

```sh
deploy/.venv/bin/python deploy/chat_aca.py plan
deploy/.venv/bin/python deploy/chat_aca.py check
deploy/.venv/bin/python -m unittest discover -s deploy -p test_chat_aca.py -q
```

After independent artifact/security review and azure-validate, the operator uses
azure-deploy to run these exact stages from the workspace root. Set
`REVIEWED_SOURCE_SHA256` to the reviewed `plan` fingerprint; do not silently
recompute an approval from changed files.

```sh
deploy/.venv/bin/python deploy/chat_aca.py build \
  --approved-source-sha256 "$REVIEWED_SOURCE_SHA256" --execute
```

This performs **remote ACR Linux/AMD64** compilation, not a local Docker build.
It stages only explicit package/build files and immediate `server/*.ts` /
`client/*.{ts,tsx,css,html}` source; no node_modules, .runtime, .env, tests,
logs, .squad, unrelated source or ZIPs are uploaded. `.dockerignore` is also
deny-by-default. Symlinks fail closed. Node `24.22.1-bookworm-slim` is pinned to
manifest digest
`sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205`
(resolved read-only from Docker Hub). Build and production dependency stages use
the unchanged lockfile via `npm ci`; production image excludes dev dependencies,
build tooling and Oryx. Runtime is non-root and serves both dist trees on 8080.
The source-hash tag is never overwritten. Build evidence is
`deploy/.chat-aca-image.json`: source SHA256, run ID, platform, tag, image digest.
The actual build/image digest is recorded above and in the evidence file.

Set `REVIEWED_IMAGE` to the exact `acrredshiftbs01bb4b2781.azurecr.io/redshift-chat@sha256:...`
from this evidence, after reviewing remote build success/provenance.

```sh
deploy/.venv/bin/python deploy/chat_aca.py create \
  --image "$REVIEWED_IMAGE" \
  --approved-source-sha256 "$REVIEWED_SOURCE_SHA256" --execute
```

Creation refuses to overwrite an existing chat app, verifies registry evidence,
uses HTTPS-only ingress, single-active-revision mode, min=max 1 and 0.25 CPU /
0.5 GiB. If creation succeeds but role grants fail, do **not** recreate or restart:
after resolving the exact project-scoped permission issue, bounded role retry is:

```sh
deploy/.venv/bin/python deploy/chat_aca.py roles --image "$REVIEWED_IMAGE" --execute
```

No automated cleanup/deletion or generalized resource updater is provided.
The helper reuses existing sanitized CLI/ARM and idempotent exact-scope role
helpers; it never invokes MCP/App Service deployment stages.

## Health, session and acceptance gates

Expected exact public origin:
`https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io`.
The generated `PUBLIC_ORIGIN` is that exact string (no trailing slash).
Creation verifies actual Azure FQDN before grants. Browser calls remain
same-origin; wrong/old/http origins are rejected even with spoofed proxy headers.
Secure `__Host-` cookies and strict CSRF checks are unchanged. Forwarding headers
are ignored; rate limits conservatively aggregate by verified socket, which can
group ACA proxy clients together. Do not weaken this to trust arbitrary headers.

Startup/readiness/liveness check process-only `/healthz` (2-second timeout,
10-second intervals, startup 30 failures, readiness/liveness 3). Readiness means
the BFF process is ready, **not** that Foundry/Redshift are ready. Verify separately
`/api/health`: actual MCP `test_connection`, 35-second deadline, single-flight,
30-second cache. Do not make a downstream outage restart the BFF.

After Azure provisioning/RBAC propagation, inspect only selected nonsecret
metadata: expected image digest, provisioning success, one active healthy running
revision, min=max1, actual FQDN and system-principal roles. Then:

1. HTTPS `/` serves React and `/healthz` returns 200. No Oryx/dependency failure.
2. `/api/health` reports a fresh real connected result; no fallback healthy state.
3. In a real browser at the ACA origin, ask 2025 total oil production:
   grounded answer must be **21,157,564.26 bbl** with actual `analyze_data`.
4. In the **same cookie/session**, ask “And total gas for the same period?”:
   grounded **44,177,025.20 mcf**, fresh `analyze_data`, continued true, no stale
   oil evidence. Preserve the GA two-document parser and strict no-analysis reject.
5. Verify wrong-origin rejection, reset starts a new chain, IDs/endpoints/tokens
   never appear in UI or logs, and keyboard/plain-text rendering works.
6. Confirm MCP remains `ca-redshift-bs01--0000003`, its reviewed digest unchanged,
   with all prior allowed hosts/origins intact. No MCP CORS update is needed:
   browser calls only the BFF; its MCP SDK probe sends no Origin; Foundry's
   registered MCP connection is unchanged. Backend Host/Origin checks remain on.

One replica/single active revision is required because sessions/rate state live
in process memory. Deploy/restart/crash can invalidate all sessions; short
revision handoff overlap can also occur. Accepted synthetic-POC limitation, not
durable sessions or HA. Public unauthenticated POC network acceptance is retained;
production requires separate access-control/private-network design.

## Capacity and costs

Coordinator's read-only quota evidence: Brazil South ManagedEnvironmentCount
2/50; environment consumption cores 0.25/500. Reusing the environment adds zero
environments; one 0.25-vCPU replica makes 0.5/500. No quota increase required.
New cost is one always-on Consumption replica (0.25 vCPU/0.5 GiB), request/log
usage and ACR build/storage; Sweden Central Foundry calls keep existing
token/model costs and cross-region latency/possible transfer costs. min=1
prevents scale-to-zero savings. The separately authorized retirement deleted
the old B1 plan, removing that ongoing compute resource; the retained ACA,
registry, vault and Foundry usage still incur their applicable costs.
No unverified monetary savings estimate is claimed.

## API references and local evidence

- [Container Apps current GA schema: 2026-07-01](https://learn.microsoft.com/azure/templates/microsoft.app/2026-07-01/containerapps)
- [Managed identities](https://learn.microsoft.com/azure/container-apps/managed-identity)
- [ACR remote builds](https://learn.microsoft.com/cli/azure/acr#az-acr-build)
- [Health probes](https://learn.microsoft.com/azure/container-apps/health-probes)
- [Consumption billing](https://learn.microsoft.com/azure/container-apps/billing)

Provider read-only discovery confirmed `2026-07-01` as latest non-preview
Container Apps API. Shared ACR API `2025-11-01`, identity API `2024-11-30`,
role assignment API `2022-04-01` are retained; no Foundry resource mutation.
Local Node24 suite: **102 tests passed**, typecheck and Vite/TS build passed.
ACA helper: **7 tests passed**. Real remote image build, ARM validation/
what-if, official validation workflow, live role/config verification and
full HTTP numerical/session acceptance also passed; local tests alone were
not used to claim deployment validation.

Review candidate image-source SHA256:
`5a7894538f4887aaf430c3cd4b16957e7f68e35dac5f34d5ca5442192fbbcc76`
(22 allowlisted build inputs). The actual read-only `check` stage passed using
the existing deployment virtualenv; no dependency installation was needed.

## Completed approved cleanup — 2026-10-27 02:00:10 UTC

Deleted `app-redshift-chat-bs01-bb4b2781` and then its dedicated
`asp-redshift-chat-bs01` B1 plan. Immediately before plan deletion, direct ARM
plan/site and subscription-wide site reads plus cross-resource-group Resource
Graph confirmed zero references; no deployment slots existed. Postcleanup
direct ARM GETs independently returned **ResourceNotFound** for both resources.

Removed only these exact assignments for old principal
`ebcf9b66-cca4-46a6-a344-3f100ea7eb0d` at the Foundry project scope documented above:

- `1d0a3438-808c-535c-a6da-79dda6fc03c0`: Cognitive Services User.
- `a2b0451e-4de4-5b0d-8dad-8567fe0633e2`: Foundry Agent Consumer.

Both IDs are now absent; the new runtime's two project assignments are unchanged.
Exactly six resources remain in `rg-redshift-bs01`, all Brazil South:
`ca-redshift-chat-bs01`, `ca-redshift-bs01`, `cae-redshift-bs01`,
`acrredshiftbs01bb4b2781`, `kv-redshift-bs01`, `umi-redshift-imagepull-mx01`.
Retained metadata/tags, identities, image digests and revisions are unchanged;
the vault-only `SecurityControl=Ignore` exception remains. No other external
resources, permissions, policies, images or database dependencies were changed.

Postcleanup HTML, chat `/healthz`, fresh connected `/api/health` and MCP
`/healthz` returned HTTP200. Connected `checkedAt`:
`2026-10-27T02:00:06.253Z`; one active healthy chat revision/replica confirmed.
No app restart, package build or repeat business queries were needed.
Sanitized exact before/operation/after proof:
`deploy/.chat-artifacts/obsolete-appservice-cleanup-proof.json`
(`completed_verified`; all 12 verification checks passed).

### Retained dependency boundaries

Keep the new ACA, existing ACA environment/registry/pull UMI, healthy MCP app,
Key Vault/database dependencies, and Foundry account/project/registered agent
version2/model. Do not delete the new system principal's project role grants.
Old App Service/dedicated plan and its separate old runtime identity are not
used by the new app. No new acceptance helper requires the old app to exist.
The legacy App-Service-specific `chat_deploy.py verify` should no longer run;
the completed ACA checks reused only pure request/numeric validators from it.
Existing MCP CORS still includes the old origin but is not a runtime dependency
for server-to-server ACA traffic; no MCP change is needed for old-app cleanup.
