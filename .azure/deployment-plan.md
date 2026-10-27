# AWS official Redshift MCP migration — scoped approval recorded; live ACA retained

## Explain agent and MCP failures — 2026-10-27

Status: **Deployed; specific failure explanation and supported MCP analytics verified**.
Recipe: existing AZCLI / snapshot-preserving ARM image-only release.
The user confirmed the length fix and requests that remaining generic errors be
fixed or explained. One fresh reproduction and one targeted diagnosis confirmed
Foundry HTTP 400 / tool_user_error, validation path plan.group_by, type too_long,
and the rule "List should have at most 2 items". The adapter's existing
AnalysisPlan independently enforces that limit. This explains the supplied
prompt's reproduced failure; it is not evidence that every earlier failure had
the same cause or that Redshift was disconnected.

Expose only fixed, safe failure codes/messages for this known rejection, general
MCP tool failure, tool-call budget, model-native output exhaustion, incomplete
response, failed format/grounding verification and Foundry throttling. The UI
shows reason-specific headings and safe codes; rephrase-only failures do not
offer a blind Retry. Preserve strict output/grounding checks and fail closed.
Do not add SQL, ratio/revenue/custom data-quality capabilities or extra retries.

Release scope: existing ca-redshift-chat-bs01, rg-redshift-bs01, subscription
bb4b2781-6739-4fa1-994e-4ad6ce55c59c, Brazil South. Same previously approved
target and in-memory chat-reset behavior; no new resource, RBAC role, identity,
scale, model, agent or MCP change. Retain the current prompt-849e6f254e image
for rollback. Build one immutable allowlisted Linux/AMD64 image; compare its
compiled files to the reviewed local build. Validate the actual snapshot-based
ARM template and effective what-if, permitting only image/revisionSuffix.
Re-read and compare live state under the existing operator lock before PATCH;
this is not atomic CAS. Verify unchanged configuration, identities, roles and
official MCP after rollout.

All validation checks pass — FAILURE EXPLANATIONS scope:
- [x] Local tests, typecheck and production build; peer semantic challenge addressed.
- [x] Exact immutable container matches reviewed compiled files.
- [x] Existing-context ARM validation and effective image/revision-only what-if.
- [x] Applicable policy and least-privilege existing role-scope verification.

### Section 7: Validation Proof — failure explanations

Commands completed: `npm test`, `npm run typecheck`, `npm run build`,
`deploy/.venv/bin/python .azure/chat-errors-proof/release.py inspect` and
`deploy/.venv/bin/python .azure/chat-errors-proof/release.py validate`. The latter
executes actual `az deployment group validate` / `what-if` against the fresh
snapshot template, plus exact live role and applicable-policy queries.
123 chat tests, typecheck and production build pass. New regressions cover the
observed validation rule, root/nested SDK codes, unrelated rules/statuses,
classification of incomplete/budget/failed-tool/verification responses, exact
full-prompt HTTP handling, safe logs and UI messages, no blind Retry, no leaked
rejected values, no automatic retries and no failed-response continuation.
Independent semantic challenge identified that unfinished tool statuses must not
be described as tool failures; their mapping was corrected to AGENT_INCOMPLETE
and covered by regressions. Raw errors stay private; unknown text-rule shapes
fall back to the general tool error, never a successful answer. Initial
workspace-review tooling was unavailable; the bounded inline semantic challenge
does not claim a filesystem audit. A final independent semantic review APPROVED
the corrected failure handling and bounded release, conditional on live acceptance.
The image-only ACR Linux/AMD64 release for source
`ceb4ca2929b91bea2915fe4399c54f0716b55ca629cf909c9cbd81ab2fa88967`
uses immutable digest
`sha256:3ff2aab42068c4a8209679dd287913b3df3c17bbae80f8ea36beca9c2a086101`.
Restricted no-network/read-only/cap-drop verification matched all 11 local build
files. Actual ARM validation and what-if passed with only
properties.template.containers.0.image and properties.template.revisionSuffix
as effective changes. Validation completed at 2026-10-27T21:16:42Z.
Existing environment/registry/pull identity, exact
project-scoped runtime roles and registry-scoped AcrPull remain unchanged;
applicable policy assignments were empty. Sanitized validation, image and
rollback evidence is in ignored `.azure/chat-errors-proof/`.
The preparation guard was corrected once to normalize Azure's "Brazil South"
display value; the isolated Docker checker was corrected once to retain the
local Docker endpoint while isolating temporary registry authentication. No
application change or cloud-write retry was needed for either harness issue.
One image-only PATCH deployed revision
`ca-redshift-chat-bs01--errors-ceb4ca2929`; read-only postverification confirms
one Healthy active revision with 100% traffic, the exact reviewed template and
unchanged configuration/identity/roles/official MCP. The initial verification
observed an old-template transition immediately after PATCH; one corrected
read-only verifier accepted only the exact old/new snapshots and confirmed the
new ready revision. The PATCH was not repeated.

Actual browser submission preserved all 2,947 characters of the supplied prompt.
It displayed "Too many grouping fields.", the at-most-two-fields explanation and
ANALYSIS_GROUP_LIMIT, with 19 turns remaining, no blind Retry and no unverified
assistant answer. A fresh supported 2025 oil question returned HTTP 200 in
31.245 seconds with exact 21157564.26 bbl, actual get_data_context/analyze_data
evidence and continued=false. All 123 tests/typecheck/build pass.
Explaining the rejected prompt does not execute its unsupported SQL,
ratio/revenue/completeness checks. A different failure may have a different
mapped code; unknown upstream causes remain explicitly unknown.

## Long-prompt input release — 2026-10-27

Status: **Deployed; input behavior verified; supplied-prompt processing blocked.**
The user-provided data-quality prompt exceeds the old 2,000-character composer
limit. Increase the shared input budget to 32,000 UTF-16 code units and the JSON
body budget to 256 KiB, which accommodates worst-case JSON escaping at that
character boundary. Remove HTML maxlength truncation; preserve the full draft,
show an accessible over-limit error and disable Send while oversized.
Keep matching server-side validation, request deadline, rate/concurrency limits,
no application answer-token cap and all MCP grounding/read-only rules unchanged.
Pasted SQL is context, not permission to execute arbitrary SQL or add unsupported
ratio/revenue/completeness analytics.

Scope: one immutable chat image, image/revision-only update to the existing
`ca-redshift-chat-bs01` in Brazil South and approved subscription. No new resource,
permission, scale, model, agent or MCP change. Preserve the current native-limit
image for rollback. Existing chats reset on rollout. Validate exact-prompt
delivery, exact character/byte boundaries and real browser paste/overflow states.

User approved deployment to the same web app, including in-memory chat reset.
All 111 chat tests, typecheck and production build passed. Independent Devil's
Advocate semantic review approved the boundary arithmetic, consistency, draft
preservation and retained safety/cost controls.

All validation checks pass — LONG-PROMPT INPUT scope:
- [x] Snapshot-preserving ARM validation/what-if permits only image/revision.
- [x] Immutable Linux/AMD64 image matches reviewed compiled backend/frontend.
- [x] Existing resource context, applicable policies and exact roles preserved.

### Section 7: Validation Proof — long-prompt input

At 20:52 UTC, ARM validate and what-if succeeded with exactly the chat image and
revision suffix as effective modifications. Context, policy and exact existing
role-scope checks passed; no new policy assignment or role resource is present.
All 111 chat tests, typecheck and production build passed. The full supplied
prompt fixture contains 2,947 characters and its final Y/N question reaches the
agent intact. Boundary tests cover 32,000 characters, worst-case JSON escaping,
32,001-character rejection and the separate JSON byte guard.

ACR Linux/AMD64 build `cqb` succeeded for source fingerprint
`849e6f254e37af569bb0e68b8212c6a3f80aff142d08792138a91df190e93bf0`.
Exact image:
`sha256:6c92af0f6bb01af29c8a88c99a0d0456eb6b5ff1212b88664aa3e4fd30da8579`.
Network-disabled/read-only image verification matched all 11 built files and
confirmed 32,000 input units, 262,144 request bytes and no output-token cap.
Proof and nonsecret rollback baseline: `.azure/chat-long-prompt-proof/` (ignored).
Expected revision: `ca-redshift-chat-bs01--prompt-849e6f254e`.

The guarded image-only update completed at 20:54 UTC. One active Healthy revision
serves all traffic; chat configuration/identity/environment and the MCP adapter
configuration/identity/template are unchanged. The new frontend asset and public
32,000-character configuration match the inspected image. Live roles are unchanged.

Real browser verification preserved a 3,563-character paste exactly, including its
final Y/N question, with Send enabled and no maxlength attribute. A 32,001-character
draft remained intact, set aria-invalid, displayed the accessible warning and
disabled Send. The prior draft was restored afterward.

The full 2,947-character supplied fixture was submitted to the hosted endpoint
without an input-length rejection, but received HTTP 503 / AGENT_UNAVAILABLE.
Bounded direct-agent diagnosis identified upstream HTTP 400 / tool_user_error.
This is a distinct upstream tool rejection, not remaining composer truncation;
the specific rejected argument was not established. Do not describe the supplied
prompt as end-to-end successful. Its
raw SQL, ratio, completeness and revenue checks are not added by this input fix.
No grounding check was relaxed and no automatic retry/fallback was added.
An independent supported-question smoke check returned HTTP 200 with the exact
2025 oil total and fresh get_data_context/analyze_data evidence in 26.494 seconds.

## Model-native answer limit release — 2026-10-27

Status: **Deployed and verified.**
User directive: no application token limit beyond the model's own ceiling.
Remove `max_output_tokens` from the Foundry request and remove the coupled
16,000-character completed-answer gates. Keep strict JSON/fresh MCP grounding,
incomplete-response rejection, read-only execution, tool/result limits,
230-second deadline, concurrency and scale unchanged. Longer answers may consume
more model tokens and cost more; no new Azure resource or permission is needed.

Release scope: one immutable chat image and an image/revision-only update to
`ca-redshift-chat-bs01`, retaining all live configuration and the agent3/official
MCP bindings. Preserve the current Markdown image for rollback. Existing
in-memory conversations reset at rollout. Use the reviewed snapshot-preserving
ARM validation/what-if and guarded image-only update process documented below.
Acceptance must repeat the detailed 2025 monthly/state oil, gas and operating-cost
question that previously returned 60 valid MCP rows but stopped at exactly
800 output tokens with `max_output_tokens`. Keep execution bounded to one
initial attempt plus one targeted correction/retry per failed stage.

User approved deployment to the existing Brazil South chat app, including chat
reset and higher possible token usage. All 109 chat tests, typecheck and production
build passed. An independent Devil's Advocate review approved the supplied code
semantics; the initial reviewer could not access filesystem tools. The reviewer
confirmed that retained deadlines/concurrency constrain operational exposure,
not a hard cumulative token or monetary budget.

All validation checks pass — MODEL-NATIVE ANSWER LIMIT scope:
- [x] Core AZCLI authentication, current GA API, snapshot-preserving ARM validation
  and what-if; only chat image/revision may change.
- [x] Immutable Linux/AMD64 image build and exact installed backend verification.
- [x] Azure Policy validation and unchanged least-privilege role assignments.

### Section 7: Validation Proof — model-native answer limit

All 109 chat tests, typecheck and production build passed. ACR Linux/AMD64 build
`cqa` succeeded for source fingerprint
`44c31604f947c898efe7763ee121eeb137c834b6ba67658cbe597b073deaf235`.
Immutable chat image:
`sha256:4f870df62a499741e77d68d8c87548c24455b3b653653301725d0fa669ea8ebb`.
A network-disabled, read-only run of that exact image matched all 11 built files
against the local build, confirmed both output-token fields absent, and accepted
a completed answer beyond 16,000 characters.

`az account show`, provider API readback and target context checks passed; the
latest listed GA Container Apps API remains `2026-07-01`. ARM validation and
what-if succeeded. The only effective changes are the chat container image and
revision suffix. Existing configuration, identity, agent3, official MCP binding,
probes, limits and scale are preserved. No role resources are in the template;
the exact two Foundry roles and registry-scoped AcrPull assignment were checked.
Applicable resource-group policy assignments: none.

Proof and nonsecret rollback baseline: `.azure/chat-native-limit-proof/` (ignored).
Expected revision: `ca-redshift-chat-bs01--native-44c31604f9`.
Two local verification-harness issues were corrected once each: incompatible
role-list CLI flags and relative nested what-if field paths. Neither required
an Azure resource write or another build.

The guarded image-only update completed at 20:42 UTC. One active Healthy revision
serves all traffic. Chat configuration, identities, environment, agent3 and
official MCP binding are unchanged, and the MCP adapter's configuration,
identity and template are unchanged. Public process health, exact frontend asset
and live least-privilege role-preservation checks passed.

At 20:43 UTC the same detailed question that previously exhausted the 800-token
cap returned HTTP 200 with all 60 Markdown data rows, 7,417 reply characters,
`truncated=false` and fresh `get_data_context` plus `analyze_data` evidence.
It completed in 72.755 seconds with `continued=false`. Hosted acceptance passed
without a retry; the app imposes no output-token ceiling. Model/service limits,
request deadlines and the other unchanged safeguards still apply.

## Retired custom MCP deployment removed — 2026-10-27

Status: **Deleted and resource preservation verified**,20:07 UTC.
User explicitly approved deleting only `ca-redshift-bs01` and its app-specific
Key Vault secret-reader role after verification of the live consumer bindings.
The old direct-connector deployment was still running one replica; it is now
absent and is no longer a rollback target.

Fresh readback confirmed the current chat uses agent3 and the official-backed
health URL. The actual registered Foundry agent3 MCP tool also points to
`ca-redshift-official-bs01`, not the retired service. The retained Python project
is the required policy adapter around AWS's unmodified published MCP server,
not an unused standalone direct connector; no active source directory was deleted.

Deletion guards verified the exact old app image, revision and system-assigned
principal, plus the single secret-scoped Key Vault reader assignment owned by
that principal. One app DELETE and one role-assignment DELETE were performed;
subsequent GETs confirmed both absent. The active chat and official-backed
service's templates, configuration, identity, environment and ready revisions
were read back unchanged. No shared resource, registry image, retained identity,
Key Vault or secret was deleted.

Sanitized intent/result and follow-up hosted acceptance are retained under
`.azure/legacy-mcp-retirement-proof/` (ignored). Historical rollback instructions
below that require the deleted custom deployment are no longer executable.

A fresh hosted question passed after deletion at20:09 UTC:2025 oil returned
exactly21157564.26bbl with actual current-turn `get_data_context` and
`analyze_data` tool evidence and `continued=false`. The retired app is not
required by the working chat path.

## Chat Markdown release — 2026-10-27

Status: **Deployed and verified**,2026-10-27 19:29 UTC. User approved deployment to the existing web
app, including the in-memory chat reset. The requested UI change is implemented
locally. Assistant replies support GitHub-flavored Markdown; user messages remain
literal text. Raw HTML is disabled, remote images are not loaded, and only absolute
HTTP(S) links are clickable, with no opener/referrer. Tables and code blocks scroll
within their messages. The Foundry JSON protocol and fresh MCP grounding are unchanged.

Release scope: build one immutable Linux/AMD64 image from the existing chat
Dockerfile and an allowlisted context, then update only the image and revision
suffix of `ca-redshift-chat-bs01` in `rg-redshift-bs01`, Brazil South, subscription
`bb4b2781-6739-4fa1-994e-4ad6ce55c59c`. Reuse the current ACR and managed identities.
No new resources, permissions, model/agent changes, MCP changes, or scale changes.
The existing public HTTPS POC exposure remains; this is not production hardening.

Use the existing AZCLI/ARM recipe and current `2026-07-01` Container Apps API.
Snapshot the actual live chat configuration/template/identity before validation;
do not use the historical creation definition, which contains superseded agent
and MCP settings. Validate/what-if the exact snapshot-preserving image-only
template. Execution uses a release-specific `deploy.arm` image-only PATCH and
the existing local operator lock, not `official_cutover.apply_prepared` (its
historical image allowlist is intentionally unchanged). Immediately before PATCH,
recheck the baseline under a local lock;
this is not an atomic ETag/CAS guarantee. Preserve probes, environment values,
agent3, current official MCP URL, resource limits, scale, identity and RBAC.

Rollback retains the current `--official3600` revision and immutable chat image
`sha256:7eff76f081d526ac3ae0870240b01b938edbf1c1f42647f2d3ddcdd7057a59df`.
In-memory chat chains reset on image rollout, as with previous releases.
Acceptance requires the exact new frontend assets, reachable HTTPS/health, and
one fresh grounded answer through official MCP. Keep execution bounded to one
initial attempt plus one targeted correction/retry per failed stage.

### Section 7: Validation Proof — Markdown release

Local checks: all107 chat tests passed, including assistant Markdown, user literal
text, raw-HTML/image suppression, unsafe links, semantic/scrollable tables, and
existing grounding/session protections. Typecheck and production build passed.
Every existing dependency version/integrity remains unchanged; the lockfile uses
canonical public npm tarball URLs. Goff independently APPROVED the rendering and
preservation plan, with no blockers; the executor path is clarified above.
At2026-10-27 19:22 UTC, immutable-image proof, ARM validation/what-if and static/live
role-preservation checks passed. Hosted acceptance subsequently passed.
Historical release proofs below do not validate this new image.

Release source fingerprint:
`103d6b00cc0ccb61fa46c5c1c5508a9c7eb1578f9c9ce90b68f7d15d36308b7e`.
ACR Linux/AMD64 build `cq9` Succeeded, immutable digest
`sha256:ca8503000043560fa6f15779e1fefbff82d6dcc5913446b238af4e61d9e217a3`.
Network-disabled/read-only inspection of that exact image verified Node24.22.1,
react-markdown10.1.0, remark-gfm4.0.1 and byte-for-byte hashes of all three
frontend assets against the reviewed local build.

Commands/results:
- `npm test`:107 passed; `npm run typecheck` and `npm run build`:passed.
- `az account show`, environment/registry/identity GETs:approved target unchanged.
- `az provider show`:2026-07-01 remains the latest listed GA containerApps API.
- `az deployment group validate` against
  `.azure/chat-markdown-proof/validation.json`:passed.
- `az deployment group what-if` against the same template:Succeeded. Only the
  chat image and revisionSuffix have effective changes. FQDN and ephemeral
  storage are provider NoEffect; all other resources are Ignore/NoChange.
- `az role assignment list`:same two exact project-scoped Foundry roles and one
  registry-scoped AcrPull role; the generated template contains no RBAC changes.
- `az policy assignment list` at the resource-group scope:[].

Proofs and rollback baseline are in `.azure/chat-markdown-proof/`; only this
runbook is tracked. Exact release is `release.json`, expected revision
`ca-redshift-chat-bs01--markdown-103d6b00cc`.

The single guarded image-only PATCH completed successfully. One healthy active
revision serves100% traffic; identity, configuration, environment, probes, scale,
resource limits and live RBAC are unchanged. Actual hosted HTML/CSS/JavaScript
hashes match the exact inspected image.

The real browser submitted a fresh2025 oil question requesting a Markdown table.
The deployed UI rendered semantic Product/Total/Units headers and Oil,
21,157,564.26,bbl cells, with the observed-period/source/grain caveat preserved.
Visual inspection passed. At a240px message width, the named keyboard-focusable
table region scrolled internally (238px client width,270px content), without
page overflow. No inline Markdown styles or embedded images were present.
Direct MCP health was captured healthy/connected at19:28:58 UTC, using the
existing single-flight/cache semantics rather than treating stale/checking as
failure or caching a business answer.

All validation checks pass — MARKDOWN RELEASE scope:
- [x] Core validation: authenticated context, exact image-only ARM validation and
  what-if. Existing ARM JSON is retained; Bicep compilation is not applicable.
- [x] Docker Build: immutable Linux/AMD64 image, successful locked install/build,
  exact frontend-asset verification.
- [x] Azure Policy Validation and preservation of existing managed identities,
  two project-scoped Foundry roles, registry-only AcrPull, HTTPS and scale.

## Official MCP performance improvements — 2026-10-27

Status: **Deployed and verified**,2026-10-27 18:54 UTC. User approved both proposed
improvements: bounded warm official-MCP workers and consolidation of the two
fresh context-coverage queries into one query.

Scope: modify the existing Python policy adapter in place, keeping the published
AWS server unmodified. Reuse initialized worker sessions with exclusive leases
and fresh per-operation transactions; preserve bounded concurrency, deadlines,
read-only SQL, result limits, reconciliation and unknown-settlement quarantine.
Coverage and business answers remain fresh; no result cache or direct-database
fallback. Independent correctness/lifecycle review precedes release.

Release target remains the existing official MCP Container App in subscription
`bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, resource group `rg-redshift-bs01`,
Brazil South. Reuse the current ACR, managed identities, federation, permissions,
Foundry agent3, chat image and endpoint. No new resources or broader permissions.
Build one immutable candidate image, validate the exact image-only update, retain
the current image/revision for rollback, and compare actual fresh hosted answers
against the recorded first-turn78.858s and follow-up36.046s baseline.

Execution bound: one initial attempt and one targeted correction/retry per failed
stage. Preserve the currently working application if acceptance fails; report
the blocker rather than continue an open-ended debugging loop.

### Section 7: Validation Proof — performance release

Implemented two exclusive task-affine warm workers, fresh named transactions
per lease, confirmed-rollback release and permanently quarantined capacity for
unknown settlement. Context coverage now uses one fresh query. No auth, IAM,
Foundry, chat or upstream package changes.

Independent review caught and rejected per-HTTP-session global teardown before
deployment. Sewell independently moved cleanup to the outer application lifespan;
Goff's follow-up APPROVED the correction after actual multi-session HTTP,
shutdown and original-hook mutation checks. Full Python suite:220 passed,
1 skipped; coordinator independently reran lifecycle/analytics:77 passed,
1 skipped, and Ruff passed.

Reviewed/restaged source fingerprint:
`bb275f86772c0d002d70642888304104290b8c24d7e6f76772d6d301f0b73e49`.
Remote ACR build `cq8` **Succeeded** at immutable digest
`sha256:677070e533b170ee271cf98a3740ebd1ba113e4a35cc1485ddae6f78f8e2a39d`.
Actual installed hashes of all nine runtime modules match the staged source.
In the exact image with networking disabled and a512MiB limit, two simultaneous
SDK1.30.0-to-official-SDK2.2.0 initialize/tools-list handshakes passed. Published
server0.1.2 and named-transaction schema verified; both stdio cleanups
acknowledged. Observed peak273670144bytes (about261MiB). This is an offline
startup/headroom proof, not a live SQL or post-query memory guarantee.

Commands/results for this release:
- `az account show`: expected subscription/tenant; `az provider show` confirms
  existing `2026-07-01` is the latest listed GA containerApps API.
- `az acr build --platform linux/amd64`: cq8 Succeeded, source fingerprint above.
- Exact-image `docker run --network none --memory512m`: both real SDK handshakes,
  installed runtime hash checks and cleanup passed.
- `az deployment group validate` against
  `.azure/official-performance-proof/validation.json`: Succeeded.
- `az deployment group what-if` for that same template: Succeeded; only official
  MCP image and revisionSuffix Modify. Ephemeral storage is provider NoEffect;
  configuration, identity, scale, DB marker and federation are preserved.
- Existing reviewed ARM JSON is retained; Bicep compilation is not applicable.
- Fresh `az policy assignment list` at the resource-group scope returned[].
- No RBAC resources are generated/changed. Registry-only AcrPull and the chat's
  exact two project-scoped Foundry roles were read back unchanged.

Exact prepared release: `.azure/official-performance-proof/release.json`,
revision `ca-redshift-official-bs01--warm-bb275f8677`. Rollback snapshot is
`before.json` in that directory. The official validation workflow completed
before the single snapshot-guarded image-only PATCH. One active healthy revision,
100% traffic, one ready replica and zero restarts were observed. Identity,
configuration, federation, DB budget, scale, resource limits and roles are
unchanged. Chat remains on `--official3600` and Foundry agent3.
Historical release proofs below do not validate this new change.

All validation checks pass — PERFORMANCE RELEASE scope:
- [x] Core validation: current authenticated context, exact image-only ARM
  template validation and what-if restricted to the existing official MCP app.
- [x] Docker Build: immutable Linux/AMD64 build, exact installed runtime hashes,
  actual SDK1/SDK2 handshakes and two-process memory headroom.
- [x] Azure Policy Validation and preservation of existing identity/RBAC,
  federation, verified DB budget, HTTPS, scale and resource settings.

### Actual hosted performance acceptance

| Fresh business request | Previous observed seconds | New observed seconds |
|---|---:|---:|
| First oil question after rollout |78.858|67.665|
| Same-session fresh gas analysis |36.046|13.171|
| Fresh oil question after session reset, warm MCP workers |69.298|22.220|

All three returned exact expected oil21157564.26bbl/gas44177025.20Mcf,
with current-turn official-MCP analysis; both new-session oil requests executed
fresh context and analysis. No business-answer or mutable-coverage cache.
These are individual observed runs, not a latency guarantee. First request
after a process restart remains slower.

The initial health-capture script waited40s and outlived the30s freshness window
after the now-faster probe completed. This returned truthfully stale, not a
failed database check. A single capture correction used5s polling and verified
fresh connected health; no business requests were rerun and no application
fallback or health semantics changed. Initial evidence is preserved separately.

Actual app-level Azure Monitor one-minute Maximum working-set samples reached
279040000bytes (about266MiB of512MiB); this is observed headroom, not a future
maximum. Hosted UI returned200. No new resources, permissions or rollback were
needed. Old image/revision and exact rollback baseline remain retained.
Evidence: `hosted-acceptance.json`, `hosted-acceptance-initial.json`,
`health-proof.json`, `live-memory-proof.json`, `live-role-proof.json`,
`deployed-proof.json` and `final-release-proof.json` under
`.azure/official-performance-proof/`.

## Official chat release — current execution, 2026-10-27

Status: **Deployed and verified — official-MCP-backed hosted chat**,
2026-10-27 18:07 UTC. Exact release preflight completed the official validation
workflow before deployment; actual hosted business acceptance now passed.
The earlier auth-only validation below is historical and scope-specific.

Candidate `--ready3600` now runs auth-only build `cq6` at immutable digest
`sha256:c21ae74027dba38dbf1e650e872a6b9de96f37426c0ee16b439fbb7d92ac4180`,
with all eight actual federation settings and verified budget marker10.
Actual one-hour STS identity/expiry and controlled near-expiry real SDK refresh
passed; no claim that an hour naturally elapsed. Nonsuperuser/schema-USAGE/
five-table SELECT/no-DML/effective statement_timeout10000 were observed through
official MCP. Own-query history showed the corrected stress statement terminal
failed after10.012833s; the specific error cause was not retained. Independent
acceptance approved this qualified setting/enforcement evidence, not a universal
SQL-settlement bound. Unknown-settlement quarantine remains unchanged.

Public HTTPS governed evidence: context36.657s, full reconciled production
analysis33.772s (oil21157564.26, gas44177025.20, cost213367864.95);
connected health30.545s, price decimal60.59583333, limit1 truncation, and
sql-field/limit501 validation failures. Evidence is retained in
`.azure/official-migration-proof/governed-{context-first,analysis-first,additional-proof}.json`.

The measured first context+analysis cannot fit the old60s BFF deadline.
Only bounded chat/Foundry230s, browser235s and health60s changed; four-tool cap,
Python50s, DB10s, grounding, reconciliation, origin/session/rate/quarantine
controls remain. ACA ingress documented240s bounds the hierarchy.
Chat build `cq7` succeeded at immutable digest
`sha256:7eff76f081d526ac3ae0870240b01b938edbf1c1f42647f2d3ddcdd7057a59df`;
103 Node tests/typecheck/production build and25 cutover tests passed.
Independent security review found no vulnerabilities; independent correctness
review conditionally APPROVED the exact timeout/image delta before application.
The guarded helper pins both exact old/release images, changes image+agent+probe
together, and retains original image/agent2/endpoint rollback. External-writer
risk remains; no atomic-CAS claim.

All validation checks pass — CURRENT CHAT RELEASE scope:
- [x] Core validation: authenticated current resource, exact prepared template,
  ARM validate/what-if modifying only chat.
- [x] Docker Build: cq7 Succeeded, tested source hash
  `d2bb72b7f190b37ef6044662a1055d9456dcb30ecf3f147c69eac4cf05fd9792`.
- [x] Azure Policy Validation and unchanged exact identity/registry pull roles.

### Section 7: Validation Proof — current chat release

Fresh `az deployment group validate` for
`.azure/official-refresh-build/chat-validation.json`: Succeeded.
Fresh group what-if: Succeeded, only `ca-redshift-chat-bs01` Modify; all other
resources Ignore/NoChange. Applicable policy assignment list returned[].
Exact two existing project roles and registry-only AcrPull were verified
unchanged. Current context tenant/subscription and healthy original revision
were checked. New exact Foundry agent version **3** was created and read back:
same model/instructions/closed tools; only server URL is the official candidate.
Version2 is preserved. Agent definition hash
`b74edd0e21028f90155db76bcf442b024aecbe15b9c3c1731b17d5906e138894`.
Evidence: `chat-validation-summary.json`, `chat-arm-validate.json`,
`chat-arm-what-if.json`, `new-agent-proof.json` under the refresh-build directory.
The exact prepared release is `.azure/official-chat-release.json`, hash
`652bd89dba19177fe9d2b93b4fd04ee3e6b4e0cd0d6aa4a497290792defe2a8b`;
helper hash `14fc85119f21f703a263c60b9e34555d00c497b3f386d557cf6632056208cdab`.
The single guarded PATCH deployed `ca-redshift-chat-bs01--official3600` with
image+agent3+official health URL together. Its initial postverify encountered
the old zero-traffic revision deprovisioning; a subsequent read-only verification
proved one active healthy new revision/replica and100% traffic. No write retry.
Original template/agent2/old MCP/image remain available for guarded rollback.
Actual post-deploy project roles were verified unchanged.
Evidence: `chat-deployed-proof.json`, `chat-live-role-verification.json`.
### Actual hosted acceptance — completed

| Public application check | Actual result |
|---|---|
| Fresh2025 oil, new session | **21157564.26 bbl**,78.858s; fresh `get_data_context` + `analyze_data`, continued=false |
| Same-session fresh2025 gas | **44177025.20 Mcf**,36.046s; fresh `analyze_data`, continued=true |
| Unsupported profit | Fixed unsupported-metric notice, no tool calls or invented result |
| Reset | Cookie rotated in memory;20turns restored |
| Supported post-reset oil | **21157564.26 bbl**,69.298s; fresh context+analysis, continued=false |
| Foreign Origin |403 `ORIGIN_REJECTED` |
| Malformed input/SQL field |400 `BAD_REQUEST` |
| Final completed health refresh |200, healthy, connected=true; checkedAt18:07:13.343Z |
| Hosted UI |200 HTML, actual React root and built script verified |

The initial post-reset **greeting** probe returned503 `AGENT_UNAVAILABLE`,
properly without a fabricated answer; its underlying provider cause is unknown.
It was not a supported business-data positive assertion. The single corrected
acceptance check used a supported2025 oil question and passed. This observation
is retained, not erased or generalized into a guarantee for arbitrary prompts.
No live application fix, relaxed grounding or retry loop was used. A separate
UI assertion was corrected for case-insensitive HTTP headers, not an app fault.

Final ARM reads confirmed chat `--official3600`/agent3/exactcq7image and official
candidate `--ready3600`/exactcq6image/eight federation settings/budget10.
One active healthy chat revision/replica; unrelated configuration/identity and
the exact two project roles are unchanged. No rollback was needed.
Actual evidence: `.azure/official-migration-proof/hosted-cutover-acceptance.json`
and `.azure/official-refresh-build/final-release-proof.json`.
No cookies, JWTs, credentials or provider identifiers were retained.

Working application:
https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io
Original image/agent2/old MCP and exact saved release baseline remain intact
for guarded rollback; no old resources or ECS trust were changed/deleted.

## Official cutover execution resumed — 2026-10-27 17:21 UTC

Status: **Validated — candidate auth-only `fed3600` revision ONLY** through the
official workflow. No DB marker or production chat cutover acceptance is implied.

User explicitly requested “switch it.” Core demonstration already passed; this
run must prove the governed endpoint and only then change paired chat bindings.
Actual operator STS account684925376801 and healthy old chat revision
`--sr9ms4f`/agent2 were refreshed; the nonsecret rollback snapshot is retained in
`.azure/official-migration-proof/chat-original-snapshot.json`.

The focused credential-refresh hypothesis is confirmed at metadata level:
actual candidate-installed botocore advisory window900s makes900s credentials
refresh-due immediately; two synthetic credential reads triggered2refreshes,
versus0for3600s. Actual IAM role `RedshiftAzureOfficialMcpRole` already permits
MaxSessionDuration3600. Live performance causality is not yet asserted.
The narrow fixed3600s auth correction and returned-expiry bounds passed38tests
and Ruff, and an independent `gpt-6.1-sol` security review APPROVED it before
cloud application. No role/trust/claim/permission relaxation, upstream fork or
application timeout change is included. Auth-only image build `cq6` is queued;
originalcq5/production images are preserved.

All validation checks pass — candidate AUTH-ONLY deployment scope:
- [x] Core validation: actual CLI/auth, reviewed candidate ARM validate/what-if,
  exact existing subscription/RG/environment/identity and rollback preservation.
- [x] Docker Build: actual auth-onlycq6 Succeeded; immutable digest
  `sha256:c21ae74027dba38dbf1e650e872a6b9de96f37426c0ee16b439fbb7d92ac4180`.
- [x] Azure Policy Validation: fresh applicable assignment listing returned[];
  Provider ARM validation succeeded. Static identity/registry assignment review:
  no new/broader Azure role, same registry-only pull UMI, same candidate system MI
  and existing dedicated Entra assignment/AWS role. Live post-deploy role and
  installed-module verification remain deployment checks, not fabricated passes.

### Section 7: Validation Proof — candidate auth-only revision

`az deployment group validate` for
`.azure/official-refresh-build/candidate-validation.json`: Succeeded.
Fresh `az deployment group what-if --no-pretty-print`: Succeeded, exactly one
Modify (`ca-redshift-official-bs01`); all other existing resources Ignore.
No Delete/Create or production changes. `az acr task show-run ... cq6`:
Succeeded, exact tag/digest retained in `image-proof.json`.
Pinned locks/upstream wheel unchanged;38auth tests and Ruff passed. Actual
default AWS STS684925376801 and healthy old chat/rollback snapshot were verified.
Evidence: `.azure/official-refresh-build/validation-summary.json`,
`arm-validate.json`, `arm-what-if.json`, `source-manifest.json`.

Remaining CUTOVER RELEASE GATES (NOT part of auth-only deployment validation):
- [ ] Runtime gates: actual candidate federation/credential refresh, database10s
  enforcement, governed context/analysis/reconciliation, fail-closed behavior.
- [ ] New exact Foundry version and reviewed paired agent/probe revision binding;
  fresh hosted business answers/health/origin/session/reset before success.

## Official MCP business-data demonstration PASSED — 2026-10-27 15:57 UTC

The user-authorized single delivery correction and conditional single business
demonstration both succeeded. This supersedes the failed diagnostic-capture
attempts below; it does not retroactively attribute those failures to AWS/MCP.

**Delivery correction:** the supported ACA exec WebSocket transport now sends
only `stty`/the tiny bootstrap first, waits for its nonce-bound
`remote_shell_ready`, then sends the readable main heredoc in256-byte stdin
chunks with receive backpressure/pacing. Main startup has a15-second deadline.
Six local transport tests passed, including anti-echo gating, no delivery before
bootstrap acknowledgement, chunk bounds, startup timeout, split-frame parsing,
and strict business-result/cleanup completion.

The one harmless startup-only probe matched the business payload's **6,580 bytes
and73 lines**, delivered in26 chunks. Main startup was confirmed and the remote
computed padding-content SHA256 matched locally; no MCP, SQL or federation calls
occurred. Overall probe time13.516s includes ARM/WSS setup.
Full transmitted Python payload SHA256:
`b38d2cd472b9855271ec0d09570273b273f68a67e109ded007e16a42679ac31c`.
Remote-computed padding-content SHA256:
`0d78782267061bdc55caa13d8f29da10cc64ca6c43b0159713cae06dca3e0771`.

**Actual native official-MCP business result**, not copied reference data:

| Year | oil_bbl_sum (bbl) | gas_mcf_sum (Mcf) |
|---|---:|---:|
| 2025 | 21157564.26 | 44177025.20 |

Observed native result: `columns=["oil_bbl_sum","gas_mcf_sum"]`,
`rows=[["21157564.26","44177025.20"]]`, `row_count=1`,
`query_id="e00c0783-b929-445c-aef6-933b7831b86d:3"`.
The SELECT used the existing daily-production identifiers and date bounds.

Provenance: existing cq5 candidate/image unchanged; unmodified published
`awslabs.redshift-mcp-server==0.1.2`, native stdio MCP protocol2025-11-25 and
its seven native tools. Actual STS caller inside the candidate was
`arn:aws:sts::684925376801:assumed-role/RedshiftAzureOfficialMcpRole/redshift-aca-runtime`.
The official `execute_query` used `enforce_read_only=true`; no operator/root
database query, direct Data API shortcut, old MCP or alternate connector was used.

Timing: initialize/tools-list6.399s, native business tool57.813s,
**91.133s end-to-end including delivery and cleanup**, within120s.
The native successful return acknowledges the upstream self-contained Batch
contract (`SET application_name → BEGIN READ ONLY → SELECT → ROLLBACK`);
the retained upstream source establishes that contract. Progress separately
observed ClientSession exit and actual stdio context closure before final proof.
All three final cleanup flags are true; this is complete proof, not a partial
result mislabeled as cleanup success. No additional named transaction calls
were imposed.

**Scope remains demonstration only.** No production/Foundry binding, source
image, persisted auth settings, public deadline or readiness/budget marker was
changed. This is not full semantic reconciliation, timeout-stress/expiry-refresh
acceptance, chat-deadline parity, or a completed production migration.

Persistent sanitized proof:
`.azure/official-migration-proof/startup-delivery-{progress,result}.json` and
`official-business-paced-{progress,result}.json`; previous failed-attempt
artifacts remain intact. No further query/retry was performed.

## Final bounded observability-corrected demo — no business proof, 2026-10-27

The user authorized one precise operator-harness observability correction and
one retry, not an application/auth/infra change. The diagnostic script now emits
stage/elapsed markers before initialization, after the actual native tool return,
and around client/stdio teardown. The transport authenticates markers with a
fresh derived run identifier, ignores echoed/unmatched markers, persists accepted
progress, and continues waiting for a distinct final proof. A native result
alone cannot claim stdio cleanup or final success. Four local mocked tests passed
(anti-echo/non-early-return, partial native result, strict final cleanup, and
deadline progress retention); all three diagnostic scripts compiled.

**Exactly one corrected retry ran: 112.974s end-to-end, inside the unchanged
120s overall budget, returning `exec_proof_deadline`.** Its last authenticated
progress was `remote_shell_ready` from the tiny remote bootstrap. No
`python_started`, runtime-identity, initialization, native-tool-return or final
completion marker from the main business harness was observed.

This narrows the observed failure boundary to **after remote shell/bootstrap
execution and before confirmation of main Python harness execution**. It does
not establish whether payload delivery, parsing/startup, or subsequent output
capture failed, and does NOT establish an AWS/MCP/SQL failure or teardown hang.
No native business rows/query_id were obtained; upstream Batch completion and
stdio close are both **unconfirmed**, not successful. Reference totals are not
presented as observed answers. The main query may not have been submitted;
this run cannot establish submission or settlement.

The authorized retry is exhausted. No additional query/exec retry, direct
Data API query, rebuild, runtime setting, readiness marker or production change
was made. Production retains its previously verified old binding; this is NOT
a completed official-MCP migration. Smallest next technical action is to
isolate the main diagnostic payload's delivery/start boundary without issuing
another business query—not another login or changing the AWS server.

Retained sanitized evidence:
`.azure/official-migration-proof/official-business-observed-progress.json` and
`official-business-observed-result.json`. The earlier unobservable
`official-business-standalone-result.json` remains intact for chronology.

## Native official-MCP business demonstration — bounded attempt, 2026-10-27

The user clarified that proving actual AWS MCP business-data execution is the
immediate goal; old-connector35s health parity is NOT this standalone demo's
acceptance criterion. This does not authorize public deadline changes, weakened
data controls, readiness markers or production cutover.

The controlled business SQL copied existing validated reference identifiers:
`SELECT SUM(oil_bbl)::varchar AS oil_bbl_sum, SUM(gas_mcf)::varchar AS gas_mcf_sum
FROM oge_synthetic.daily_production WHERE production_date BETWEEN
DATE '2025-01-01' AND DATE '2025-12-31'`.
No operator-root SQL/Data API comparison or alternate connector was used.
The harness selects the fixed new federated role's credential-process profile,
removes static AWS credential environment overrides, starts the unmodified
published official executable over standard stdio MCP and passes
`enforce_read_only=true`. No SQL or runtime auth source was patched.

Initial named-transaction harness produced no captured result; its outer capture
lasted126.670s, exceeding the requested120s. This is a harness failure and is
recorded honestly, not a successful budget check. After the user's material
simplification, a single self-contained read-only native `execute_query`
demonstration was attempted instead, avoiding our extra named BEGIN/ROLLBACK
protocol calls. The corrected supervisor imposes119s and the total observed
attempt was **117.529s**.

**Result: no native business result/proof marker was captured.**
The returned classification is `exec_proof_deadline` from the operator transport.
No actual business rows/query_id, native SQL/provider error or acknowledged
Batch/stdio cleanup was obtained. We therefore cannot state that the business
SELECT completed, that rollback/cleanup was acknowledged, or that official MCP
failed to execute it. The failure boundary remains diagnostic execution/output
capture; the specific cause is unknown. Previous successful principal/timeout
MCP results and known reference totals are NOT substituted for this missing
business-data proof.

Per the user's bound, no more query retry, direct-query shortcut, new build,
architecture change, marker or production mutation is attempted.
Next necessary correction is the bounded diagnostic stdin/result/cleanup
capture path, not another login or a change to the published MCP executable.
Retained nonsecret harnesses/results:
`.azure/official-migration-proof/official-business-demo{.py,.json}` and
`official-business-standalone{.py,-result.json}`.

## Actual federation/DB progress; live timing gate FAILED — 2026-10-27 15:21 UTC

The reported login problem is resolved: actual default-profile STS returned
account684925376801 before this execution. This is no longer an auth blocker.
No repeat approval or image rebuild occurred.

### Actual completed approved work

- Corrected the diagnostic transport using the Azure CLI's actual supported
  exec WebSocket protocol, `/bin/sh`, bounded binary stdin and explicit result
  capture. No public diagnostic endpoint/new resource was introduced.
  The intervening CLI/PTy harness stalled and was stopped; the direct supported
  WebSocket correction succeeded. No raw proxy output/token bodies were kept.
- Actual candidate MI claims verified inside candidate: tenant
  e90bd921-0e00-4e6f-b87c-713670ee27bf, v2 issuer; resource audience
  98dabd0f-b9ca-47d4-82a9-7450209d80d0; azp/client
  15d1c1b6-30bc-490a-baee-7d7c45ded6cc; oid/sub
  2a030643-be20-46a4-b375-e71fb3059a41.
  Only selected nonsecret claims were retained, never JWTs.
- Created dedicated OIDC provider
  `arn:aws:iam::684925376801:oidc-provider/login.microsoftonline.com/e90bd921-0e00-4e6f-b87c-713670ee27bf/v2.0`
  and role `arn:aws:iam::684925376801:role/RedshiftAzureOfficialMcpRole`,
  using reviewed `aws_federation.py` with actual supported aud/oaud/sub mapping.
  Applied `RedshiftOfficialFiveTableRuntime`: exact-workgroup Batch and
  GetCredentials, required ListWorkgroups, statement-owner result operations,
  explicit ExecuteStatement deny. No old ECS trust/role was changed.
- Actual candidate-local STS exchange succeeded as
  `arn:aws:sts::684925376801:assumed-role/RedshiftAzureOfficialMcpRole/redshift-aca-runtime`.
  Expiration `2026-10-27T15:24:55+00:00` was returned. Credentials stayed only in
  process memory. This proves exchange/identity, NOT expiration-triggered refresh.
- Actual returned DB username was `IAMR:RedshiftAzureOfficialMcpRole`.
  The existing root operator's administrative DB authority was verified, then
  only that new principal was created PASSWORD DISABLE/NOCREATEDB/NOCREATEUSER,
  granted schemaUSAGE and SELECT on the five approved tables, and assigned
  `statement_timeout=10000`. Catalog verified usesuper=false/usecreatedb=false.
  Actual official MCP returned that runtime username and effective timeout10000.
  No production data was changed or public/inherited/default grants modified.

### Concrete failed gate — do not cut over

First actual official standalone query did not return within55seconds.
One corrected retry used the actual named-transaction contract and retained
stage timings:

- SDK initialize: **6.891s**.
- Native BEGIN+single budget/principal SELECT: **46.193s**, successful exact
  columns/rows/row_count, runtime principal and timeout10000.
- Thus initialization+first successful result already took **53.084s**, over
  the unchanged **35s health budget**, before rollback.
- Rollback result was not received before the55.086s diagnostic deadline;
  SDK context teardown reported ExceptionGroup/BrokenResourceError. This is
  NOT proof of SQL cancellation or rollback acknowledgement.
- Bounded administrative history afterward showed the latest10 runtime SQL
  entries terminal/success, no observed active entry, millisecond SQL timings.
  That is statement-history evidence, not proof every idle transaction ended.
  No replacement runtime query was launched.
- Installed unmodified official source confirms QUERY_POLL_INTERVAL1,
  QUERY_LONG_POLL30 and QUERY_TIMEOUT3600. The public execute_query schema does
  not expose query_long_poll. Long polling is a relevant risk, but its exact
  contribution to46.193s is NOT isolated/proven; no monkeypatch or unsupported
  setting was applied.

This measured minimum path cannot satisfy current acceptance. Per the user's
bounded-execution instruction, the query stage stops after its corrected retry:
no further tuning/rebuild/debug loop, no widened budgets or relaxed integrity.
Smallest next engineering action is an independently reviewed, supported
semantics-preserving latency correction before another candidate build/proof;
there is no remaining login action. No unapproved upstream patch is applied.

**Still NOT completed:** timeout-enforcement/wait stress proof, expiry-triggered
credential refresh, full named-snapshot/reconciliation/DECIMAL/null/limits/
negative-path/business latency acceptance. The10-second marker was NEVER set;
the eight federation variables were used only inside candidate-local diagnostic
processes and are not yet persisted in the ACA template. Candidate remains
the original process-only `--jwxobc1`/cq5 image. No new Foundry version, eight
true gates, chat revision or production cutover was created.

### Working production preserved, not labelled official migration

Current production revisions/images/traffic remain exactly unchanged.
Fresh hosted old-binding answers passed: oil2025 **21157564.26** in26.133s,
then same-cookie gas **44177025.20** in10.256s, both with fresh `analyze_data`,
gas continued=true, neither truncated. Cookies stayed in memory.
After reading within the30s health-cache window, actual `/api/health`
returned **200/healthy/connected=true**, checked15:20:15.667Z.
The earlier cached503 is no longer the observed health state; no repair/restart
was applied. This verifies the retained agent2/custom-MCP app, NOT official-MCP
cutover or full new acceptance.

Evidence: `.azure/official-migration-proof/`:
`actual-mi-claims-supported-websocket.json`, `aws-federation-provision.json`,
`actual-federation-artifact.json`, `actual-sts-runtime-identity.json`,
`database-principal-applied.json`, `official-{first,named}-live-query.json`,
`official-{live-failure,batch-timing}-source.json`,
`candidate-remote-settlement.json`, `post-federation-production-preservation.json`,
`unchanged-production-business-check.json`.

## Authenticated visible-terminal discrepancy — 2026-10-27 14:50 UTC

The user supplied material proof: the app's visible terminal completed
`aws login --profile default` and printed STS account684925376801. Do NOT ask
for another blind login. One direct default-profile STS call from this agent's
Bash execution context at14:50:33Z nevertheless returned exit255 with the
expired-login classification.

Nonsecret execution metadata was compared locally without opening credentials:
only executable `/Users/jasonfarrell/.local/bin/aws`, resolving to
`/Users/jasonfarrell/.local/share/aws-cli/aws`, CLI2.37.12/Python3.14.6;
HOME `/Users/jasonfarrell`; only profile `default`; default login_session binding
is the correct account's IAM root ARN. No profile/static-credential/config-path/
login-cache-path/web-identity/container-credential environment overrides exist.
Derived config paths are `/Users/jasonfarrell/.aws/config` and
`/Users/jasonfarrell/.aws/credentials`; no contents were read from credential
stores. Evidence: `.azure/official-migration-proof/visible-terminal-renewal-check.json`.

There is a concrete usable-session discrepancy between the authenticated
visible terminal and this Bash execution context. An executable/config-path
difference is NOT proven because the visible terminal's metadata is not
available here; do not invent one. Minimum next action is to execute the
approved migration through the already-authenticated visible terminal, or
compare only its executable/HOME/config/cache-path metadata to align this
execution host. No third login, credential copy, candidate exec, source/cloud
mutation or cutover was performed in this check.

## Reported login renewal recheck — 2026-10-27 14:47:57 UTC

The user reported selecting account684925376801 during renewed CLI login.
Actual default STS verification on this execution host still fails exit255
with the expired-login/`aws login` classification. Safe profile metadata shows
only `default`, no AWS_PROFILE/AWS_DEFAULT_PROFILE override and no environment
static credentials. One explicit `--profile default` retry produced the same
expired-login result. No credential stores or token bodies were inspected.
Proof: `.azure/official-migration-proof/renewed-login-sts-check.json`.

The reported renewal is therefore not yet usable by this host's CLI; its cause
is unknown. Minimum unblock is completing `aws login --profile default` on this
same execution host (not only browser account selection), waiting for CLI
completion, and obtaining actual account684925376801 from
`aws --profile default sts get-caller-identity --region us-east-2`.
No more login retries, candidate exec, source/cloud mutations or cutover were
performed. Do not copy operator credentials into candidate or bypass STS.

## Execution resume — 2026-10-27 14:42 UTC: administrative authorization blocker

The user directed completion of the already-approved migration. Resume began
with actual administrative AWS `sts get-caller-identity`, not another build,
plan or candidate exec. It failed with CLI exit255. A bounded diagnostic
classification/recheck confirms the CLI error mentions an **expired login
session** and explicitly directs **`aws login`**; no SSO/AccessDenied wording
was detected. Provider error text/credentials were not printed or retained.
Sanitized evidence: `.azure/official-migration-proof/resume-aws-identity.json`.

**Minimum necessary user action:** renew the operator browser login with
`aws login`, selecting AWS account `684925376801`. This is operator
administrative authorization only; do not supply keys or use that identity at
runtime. After renewal, the operator must confirm actual STS caller account
before any scoped IAM/OIDC/database operation.

No candidate exec was retried in this resume. No Azure/Entra/AWS/DB mutation,
budget-marker change, agent registration, chat cutover or resource restart was
performed. Existing candidate/cq5 and Entra app/SP/sole MI assignment remain the
inputs. Claim inspection and all federation/database/acceptance stages remain
incomplete; no claim that the migration or fresh hosted business acceptance
succeeded is made. This is a concrete expired administrative-session blocker,
not the earlier incomplete-bootstrap gate or a request for repeat approval.

## Current live candidate diagnosis — 2026-10-27 14:32 UTC

Read-only inspection, no exec retry or mutation: candidate revision
`--jwxobc1` is current/ready/100%, one ready Running replica, zero restarts,
exactcq5 image. Port/probes match image startup8000; fresh healthz200.
Correct-host+Origin MCP initialize and tools/list succeeded.
Actual governed `test_connection` fails with sanitized error
**`Verified database ten-second budget is required.`**
Reviewed source identifies that gate before official-child/auth/SQL work.
Eight federation config identifiers and the budget marker are absent from live
whitelisted configuration; this remains an intentionally incomplete bootstrap,
not evidence of a crashing/wrong-port/missing-module/Host/transport failure.
Entra assignment-required SP and sole candidate app-role assignment verified
live; signed claims, STS, refresh and effective DB-budget acceptance remain
unproven. Current IAM-role read is unknown (read failed, not retried).
Finite recent console evidence shows60 healthz200 entries; system feed only
normal connection events. No later resource-write in the returned1h activity
after creation. Azure Resource Health422/AppLens unsupported do not prove an
outage. Earlier exec no-result is NOT the established runtime root cause.
Next: complete/prove scoped federation/DB prerequisites, NOT bypass the marker.
Full current facts/unknowns are documented at the top of `deploy/CHAT-ACA.md`;
sanitized JSON evidence is under `.azure/official-migration-proof/current-candidate-*`.
No validation status or acceptance gate was promoted by this diagnosis.

## Bounded candidate execution — 2026-10-27 13:47 UTC

Status: **Validated — candidate process-only bootstrap ONLY**, official workflow
checks completed. Federation, database, acceptance and production cutover are
NOT validated by this status.

### Actual bounded result — STOPPED before federation proof, 13:51 UTC

**13:53 UTC bounded production follow-up:** exactly one actual read-only call to
the unchanged production MCP `test_connection` returned `{"connected":true}`,
`isError=false`,8.147seconds. Old runtime/DB connectivity worked at that moment.
The retained prior BFF health503 has no underlying error category (the monitor
coalesces failures/timeouts); its specific cause and full Foundry/chat acceptance
remain unproven. No speculative correction, restart, code change, candidate exec
retry or extra health loop was performed.
Evidence: `.azure/official-migration-proof/production-bounded-followup.json`.
Exact two prior exec argv/results:
`.azure/official-migration-proof/candidate-exec-invocations.json`.
`deploy/CHAT-ACA.md` now contains the complete pasteable, safe in-image console
command; the user need not access a local path from inside ACA.

`azure-deploy` invoked after completion of the official validation workflow.
Actual incremental deployment `official-candidate-20261027` succeeded at
13:47:59 UTC. Candidate `ca-redshift-official-bs01--jwxobc1` is Running/Succeeded,
using the exact `cq5` digest, and HTTPS `/healthz` returned `ok`.
This is process-only health, NOT connected Redshift health.

Created candidate system MI principal `2a030643-be20-46a4-b375-e71fb3059a41`,
client `15d1c1b6-30bc-490a-baee-7d7c45ded6cc`. Assigned only that principal to
the new resource SP's `Redshift.ReadOnly` app role. Existing registry-only
AcrPull was verified again after deployment; no Azure RBAC grants were added.

**Concrete execution blocker:** supported `az containerapp exec` via bounded
PTY returned exit0 without the remote diagnostic result. Initial attempt plus
one targeted ANSI/framing correction/retry both produced no proof marker.
Retry observed456 output bytes, zero proof marker, exit0. Raw provider output
was not persisted or emitted. The transport result is NOT evidence that token
acquisition, claim mapping or STS federation succeeded or failed.
Per the user's bound, no more execution-channel/debugging retries were made.
Minimum unblock: establish a working interactive ACA command channel to
`ca-redshift-official-bs01`, then run the sanitized claim probe in
`.azure/official-migration-proof/inspect-claims.py`; return only its selected
nonsecret claim result, never the token. No repeat migration authorization or
image build is needed.

No AWS OIDC provider/runtime IAM role, database principal/grants/budget,
candidate federation environment, budget marker, Foundry agent version or chat
binding was created/changed. No eight-gate acceptance file was manufactured.
Candidate remains a single bounded0.25CPU/0.5GiB process-only deployment.
Sanitized evidence is in `.azure/official-migration-proof/`, including
`actual-mi-claims{,-retry}.json` and `bounded-execution-result.json`.

Production chat remains exactly `ca-redshift-chat-bs01--sr9ms4f` at its original
image digest and100% traffic; MCP remains `ca-redshift-bs01--0000003`, original
digest and100% traffic. No rollback is needed because no production mutation
occurred. Actual chat HTML returned200. **Fresh connected health is NOT proven:**
initial `/api/health` returned200/stale/connectednull; the follow-up returned503.
This observation must not be reported as a successful connected production
check or as completed official-MCP migration. No unrelated repair/restart or
additional debugging loop was attempted.

The user renewed execution and directed one diagnosed correction/one retry per
failed stage. Existing production remains unchanged until actual acceptance.
The successful `cq5` digest is reused; no rebuild was performed.

### Candidate bootstrap: All validation checks pass

- [x] Core Validation (CLI, auth, build, validate, what-if): authenticated exact
  subscription/tenant; generated only the reviewed candidate ARM JSON resource
  (no obsolete platform Bicep). `az deployment group validate` returned
  `Succeeded`; actual incremental what-if reports exactly one Create,
  `ca-redshift-official-bs01`, and only Ignore for existing resources.
- [x] Docker Build: existing actual successful `cq5` immutable-image evidence
  above/below is reused, not replaced with mocked/local-only evidence.
- [x] Azure Policy Validation: current MCP policy-assignment read included
  inherited management-group policies; actual candidate ARM validation/what-if
  succeeded without policy denial. This is not a compliance certification.
- [x] Role Assignment Verification: existing registry-scoped AcrPull for pull
  UMI principal `bfb1960e-711e-4061-a801-880fda281e4c` verified; no new Azure role
  requested. Candidate system MI's AWS assignment/federation remains subsequent
  runtime validation, not a bootstrap connectivity claim.

Section 7: Validation Proof is retained under
`.azure/official-migration-proof/{candidate-payload,candidate-template,validate,what-if}.json`.
Payload SHA256 `1251371a6b6a0160f2db4077ad1f014f16acd0451d6ad7dc2b4888a37789aa8e`.
The helper's sole correction targets the actual separate candidate repository
instead of the production repository; regression coverage now totals22 passing
deployment migration tests. Independent GPT6.1-sol security/correctness review
reported no security vulnerabilities in this correction/candidate payload.
Helper SHA256 `b293de33f0ce6de2b6d411243de01e704534a8f4112123fd3fba89a2fb24e342`.

Actual approved federation prerequisite mutations:
dedicated Entra resource app `98dabd0f-b9ca-47d4-82a9-7450209d80d0`
(object `ff42cc30-3af2-41fb-9e17-657ba5ebcae0`) and assignment-required service
principal `d7150b8e-191c-4895-a5fb-8bec73ed1013`, application-only
`Redshift.ReadOnly`, v2 tokens, no credentials. No MI assignment yet.
AWS STS operator account matched684925376801; root is operator only.
These are not actual candidate federation/query/refresh/budget acceptance.

## Approval record — 2026-10-27 09:04 EDT

The user explicitly selected “Approve the scoped migration and cutover after
successful verification (Recommended)”. This authorizes dedicated Entra/AWS
federation, five-table read-only permissions, one bounded candidate ACA and
conditional cutover after independent review and actual verification.
Runtime implementation is now authorized. No candidate/cloud mutation or
build occurs before concrete independent review; current production images,
agent2 and rollback configuration remain unchanged until candidate proof.
The prior execution-not-approved language below is the preserved preapproval
record, superseded only within this exact approved scope.

## Current validation execution — 2026-10-27 13:38 UTC

**Scoped remote build and offline executable handshake SUCCEEDED.**
This does not mark the migration/candidate deployment `Validated`.

Scope: user-authorized **remote ACR Docker Build validation and image-local
offline protocol proof only**, following Goff's explicit packaging-fix re-review.
Recipe: AZCLI, current `azure-validate` workflow invoked and actual plan loaded.
This is not candidate/federation/DB provisioning or production cutover validation.
No status is manually promoted to Validated. Earlier deployment evidence remains
historical, not automatically current for this migration.

### All validation checks pass

- [ ] Core Validation (CLI, auth, build, validate, what-if): current CLI/account/
  exact existing-registry read checks; no ARM resource template is deployed by
  this build-only operation, so Bicep deployment validate/what-if are not applied
  to the obsolete platform templates. Candidate-resource validation remains open.
- [x] Docker Build (if containerized): exact reviewed, allowlisted source
  snapshot to existing ACR, separate `redshift-official-candidate:src-<sha256>`;
  no overwrite of live MCP/chat repositories/tags. Actual remote install/build
  and immutable digest required; no retained old application wheel reuse.
- [x] Azure Policy Validation (build-only): current policy assignment read for existing ACR;
  no registry/config/RBAC changes. Any actual policy denial stops the operation.
- [x] Image verification: runtime nonroot image contains/imports auth module,
  installed official0.1.2 and isolated SDK versions; actual published executable
  SDK1-to-SDK2 initialize/tools-list with network disabled and dummy credentials.
  Handshake proof is not live AWS query/integrity/timing or federation proof.

### Section 7: Validation Proof — current bounded operation

13:29 UTC: Azure CLI authenticated to exact subscription/tenant. Current
azure-validate workflow progressed LoadPlan and requested the recipe checklist;
checklist above is now recorded. Current MCP/chat/IAM/DB resources are untouched.
Results/run/image/digest/protocol evidence will be recorded from actual commands,
not inferred from local mocks, source inspection or prior deployment status.

### Actual completed build and protocol evidence — 2026-10-27

- Current CLI subscription/tenant match the approved target; existing ACR is
  `Succeeded`, admin authentication disabled. Three latest runs were old
  completed builds before submission; no duplicate/pending build was reused.
  Existing-registry scoped/inherited policy assignment read returned zero
  assignments; the actual build received no policy denial. This is not a
  general Azure compliance assessment.
- Reviewed packaging fix rechecked:
  `.dockerignore` SHA256
  `26b28e8065ae0ed0fb592c699e9d6df3d77033af143b180df92fde692d0c32fb`;
  `tests/test_container.py` SHA256
  `70ec6542645955c36b96014ad4fbb29c3b3fe46382a26a8786824706b6c2b63c`.
  Focused packaging tests: **6 passed**, including actual Docker context
  filtering. No runtime/Dockerfile/lock changes were made by this operator.
- Explicit allowlisted context: **17 files, 188343 source bytes**. Fingerprint
  `eeeba9606b9cd77a0e179944f7dc8a791b4d2ea64572419f5d94150a5a6a30b0`.
  Full paths/sizes/SHA256 are retained in
  `.azure/official-build-proof/source-manifest.json`.
  Retained reproducible-input archive: 80218 bytes, SHA256
  `de38cdd0e230ac6d8b252941dba4f338a2b9f909364971579f46ed0c6dd7a117`.
  Azure CLI separately reported **77.474 KiB** for its uploaded transport
  archive; the retained archive is not claimed to be that byte-identical
  CLI-generated transport archive. No secrets, tests, old wheel, local
  environments, deployment code or unrelated application source were staged.
- Actual command: `az acr build -r acrredshiftbs01bb4b2781 --image
  redshift-official-candidate:src-<full-source-fingerprint> --platform
  linux/amd64 --timeout 600 --no-wait --no-logs
  .azure/official-build-proof/context`.
  **Run `cq5`: Succeeded**, start `2026-10-27T13:35:11.398028Z`,
  finish `2026-10-27T13:36:23.179700Z`.
  Published image:
  `acrredshiftbs01bb4b2781.azurecr.io/redshift-official-candidate@sha256:1afda7b8e545ca99d4131e07a9e3ae4aaa6868f0e0f04140258b55673d2348cb`.
  Only this new candidate tag was write/delete locked; working repositories,
  registry configuration/admin authentication and RBAC were not changed.
- Pulled that exact AMD64 digest and ran as image UID10001 with
  `--network none --read-only --cap-drop ALL --security-opt
  no-new-privileges`; no operator AWS credentials/tokens/mounts were supplied.
  Actual imported auth module:
  `/opt/adapter/lib/python3.13/site-packages/redshift_mcp_server/aws_credentials.py`.
  All **9 installed runtime module SHA256 values match staged source**,
  including auth module SHA256
  `b63bfab7718bc2dafee2737cb2814acee512fdd2ba67904db0d6fd18d6b5e754`.
- Actual **SDK1 `1.30.0` → supervisor → unmodified published official
  executable `0.1.2` / isolated SDK2 `2.2.0`** standard stdio initialize and
  tools/list passed, negotiated protocol `2025-11-25`. Exact seven expected
  tool names and named transaction parameter schema were verified.
  Container proof `13:37:58.531696Z`–`13:38:00.882797Z`; handshake/list elapsed
  **1.085 seconds**, exit0. No tool was called and AWS networking was disabled.
  This is **handshake/schema proof ONLY**, not query result normalization,
  transaction execution/snapshot behavior, DB10-second budget, refresh/
  federation readiness, end-to-end query latency or candidate acceptance.
  Operator proof script is separate from the built runtime/context and does
  not patch upstream execution. Child stderr was suppressed; zero stderr
  bytes were produced. Raw credential/provider bodies/logs were not inspected
  or persisted.
- Evidence retained under `.azure/official-build-proof/`: `run-cq5.json`,
  `protocol-proof.json`, `offline-protocol.py`, `image-source-proof.json`,
  `image-lock.json`, source manifest/archive, policy assignment read and
  sanitized live snapshots. After proof, live chat remained revision
  `ca-redshift-chat-bs01--sr9ms4f` at digest
  `sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`;
  live custom MCP remained `ca-redshift-bs01--0000003` at digest
  `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`.
  Both retain100% latest-revision traffic. No candidate ACA, Entra/AWS
  federation, IAM, database grants/budget marker or production cutover was
  created/changed.

The official `azure-validate` workflow was invoked and advanced through
`LoadPlan`/`AddValidationSteps`; applicable build-only checks above were actually
executed. It remains at `RunValidation`, not completed: candidate-resource
template validate/what-if and role/federation/effective-principal validation
are outside this bounded operation and remain open. No old template/deployment
helper was run merely to manufacture an overall pass.

**Next approved stage:** dedicated Entra/managed-identity and narrow AWS OIDC
federation setup, followed by effective-principal five-table read-only/10-second
budget verification and one bounded candidate using this digest. Actual
official-query normalization, named-transaction snapshot behavior, latency and
refresh must pass independent acceptance review before any conditional cutover.

## Runtime candidate implementation — build reviewed, NOT deployment acceptance

Local runtime work implemented the governed official-stdio execution bridge,
not a completed migration. `database.py::_cursor` is now only the existing
semantic code's compatibility facade over `OfficialCursor`; it opens no driver
connection. Every SQL/catalog/probe operation goes through official
`execute_query`; there is no Boto3 query shadow or direct driver fallback.
Existing `AnalysisPlan`, source/rollup/duplicate/orphan reconciliation and
business result envelope remain intact. Named `begin_transaction`,
`in_transaction`, `rollback_transaction` parameters preserve a single official
read-only transaction across the semantic checks/aggregate.

The downloaded, hash-verified published0.1.2 source explicitly supports this
same-snapshot transaction contract and Batch continuations. The actual seven
native names include `review_cluster` (not `get_query_plan`). Official target
resolution internally needs `redshift-serverless:ListWorkgroups`; it tolerates
denied provisioned discovery and failed best-effort tag listing. St. Brown was
given that precise IAM correction; no discovery/tag/admin expansion is implied.
The image separates `/opt/adapter` SDK1 from `/opt/official` SDK2 and uses the
fixed nonsecret credential-process profile. Auth module is St. Brown's separate
ownership, not edited by the runtime owner.

Runtime SQL literals reject backslashes/control characters, quote apostrophes,
and keep all identifiers compiler-owned. SQL limit+1 is at most501; upstream
MAX_RESULT_ROWS501 is additionally supported by the actual package, but not
the sole bound. The bridge validates shapes/counts/decimal strings and equal
text/structured envelopes; the existing business output bound remains256KiB.
A stdio supervisor bounds complete stdout frames to1MiB BEFORE SDK parsing
and reaps the child on supervisor shutdown. The bridge lifetime is50 seconds.
Unknown remote settlement quarantines the existing execution permit permanently
instead of claiming cancellation or releasing capacity on HTTP timeout.
Normal calls retain the existing two-worker/rate/semantic controls.

### Actual local evidence and blocking gates

- `src/redshift-mcp-server/.venv/bin/python -m pytest
  --basetemp="$PWD/.test-release" tests -q --disable-warnings -rs`
  from the server directory: **193 passed,1 skipped**.
  Includes actual local standard-stdio initialize/list-tools/call/close with
  the installed outer SDK, safe SQL, precision, null/empty/truncation,
  catalog scoping, actual HTTP MCP tests, host/origin, quarantine-capacity and
  packaging checks. The local SDK1 fixture is NOT claimed as SDK2 proof.
- Focused Ruff on official.py/official_stdio.py/database.py/server.py and new/
  modified bridge/database tests: **All checks passed**. Python compileall
  of the runtime package: passed.
- **Historical local blocker (dependency installation and handshake resolved by
  actual `cq5` image evidence above; offline query fixture still not run):**
  real published SDK2 executable interoperability test is explicitly
  skipped, not passed. The official0.1.2 wheel itself was downloaded and its
  SHA256 verified against public PyPI. Dependency bootstrap failed on private
  feed metadata404 and wheel-host TLS timeouts. No more local download retries,
  cloud build or candidate mutation were performed. After independent review,
  use the existing ACR builder as authorized to obtain dependencies and execute
  the real isolated SDK1↔SDK2 test before treating the candidate as usable.
- Outer dependency lock was regenerated by pip-compile without the direct
  connector. Official lock pins46 packages, with dependency constraints and
  wheel hashes validated from published PyPI JSON and existing verified
  distribution metadata/lock records; actual resolver/install/build verification
  remains REQUIRED. It is not described as an installed/tested SDK2 graph.
- DB health fails closed before auth/budget readiness; `/healthz` is lazy and
  remains process-only. Target is fixed to default-workgroup/dev/us-east-2.
  `REDSHIFT_DB_BUDGET_VERIFIED=10` is a deployment prerequisite marker, NOT
  self-proving enforcement; set only after actual effective-principal budget
  proof. Database permissions/Batch-only IAM, actual token claims/federation/
  refresh, complete source snapshot behavior and bounded latency remain live
  candidate gates. Existing chat image/agent2/MCP revision3 are untouched.
- **Update09:18 EDT:** Goff resolved the proposed mandatory-ETag blocker.
  ACA2026-07-01's documented update does not provide If-Match semantics; use
  the supported normal revision/config update with exact-target fresh snapshot,
  immediate pre-write recheck, same-operator lock, explicit revision, post-write
  verification and retained rollback baseline. This is NOT atomic compare-and-
  swap or proof against an external concurrent writer. The collaborator's
  concrete helper correction remains routed through its security snapshot
  review; missing ETag is no longer itself a mandatory cutover blocker.
  Auth/deploy artifacts and runtime changes still require coordinator-routed
  independent security/correctness review. No nested reviewer or cloud mutation
  was launched by this worker.
- **Actual upstream timing is still unproven:** existing193 passing tests
  include only a local SDK1 stdio lifecycle fixture and semantic mocks, not
  AWS Data API latency or installed SDK2 named-transaction execution. Upstream
  polling/default3600-second waits and sequential context/integrity round trips
  may exceed the unchanged four-tool/60-second chat budget. The adapter's
  50-second fail-closed deadline is a safety bound, NOT timing parity or
  successful acceptance. Candidate proof must time actual official calls,
  including begin/checks/aggregate/rollback and first-turn context, and verify
  exact native columns/rows/value types against `_rows` expectations plus
  same-snapshot semantics. No polling monkeypatch, enlarged BFF budget or
  relaxed reconciliation is authorized to manufacture a pass. If measured
  execution cannot fit, report the blocker before cutover and submit a reviewed
  semantics-preserving query consolidation rather than silently changing scope.

### Exact runtime-owned changed-file SHA256 ledger

Paths below are relative to `src/redshift-mcp-server/`; the only additional
runtime-owner artifact changed is this existing `.azure/deployment-plan.md`.
Auth/deployment collaborator files are deliberately not included in this ledger.

| File | SHA256 |
|---|---|
| Dockerfile | 858251db36fc195348c2d13b2474b0590a6b4e86c27aaa34c2cfce3f89842b77 |
| .dockerignore | 26b28e8065ae0ed0fb592c699e9d6df3d77033af143b180df92fde692d0c32fb |
| README.md | c24e771e278501e67be2711f9d24cd49ee742cdc59e58fb456352fc99f00c09a |
| pyproject.toml | 24ae3798a807941aecc5f530d338953f51dbab605f7bf202cf10cacbfe1455cc |
| requirements.lock | c27c6c54debf49d532303f064c848c1efc0c015061659fb7a3f649fae6c75662 |
| requirements-official.in | 2759b0c59c7b04b74898e7809fc6848bff28a3d674242315e466d265afbde03f |
| requirements-official.lock | b6abf1327b3b61b683f61b79012adaf2c54848b7e9ccefa42737722f0b405680 |
| aws-config | 009d4ad0598551affeed11719c0f83c0405b9820b14a558fbc3752fe54d5ba02 |
| redshift_mcp_server/official.py | 4723f3fca514260adf6e85b49c14e234107d001007d50f6fded4ead4e0986b41 |
| redshift_mcp_server/official_stdio.py | c6fa1c10cd13578765427e6ca0da6290b437a43085f15213ce4c5dc8136985bc |
| redshift_mcp_server/database.py | 0ba12257a54ac36c82984731a9e874714f835321bdd68d95342e4ef3738eb395 |
| redshift_mcp_server/server.py | 51975f46132d47ce29968f06992182c1e81af6d745038dbda5d3d21f1652a68c |
| redshift_mcp_server/analytics.py | 8e5ee0f17dd2c3aa4530ceadbcbe96c2b942a59a173410566e624f3f8703c194 |
| tests/conftest.py | 970313f154c0faaf1064f53a636e78b0f60906b64a2d2abf6ae812d27f8d48e9 |
| tests/test_analytics.py | 91250c98bef2980eb6eca3fa13fe8d38874e6b43f1f56548372adc54991c774b |
| tests/test_database.py | 9a6e54b5f39b1149238eb3a4f30cf1074a920c439382e0bd41f5e2c36322b995 |
| tests/test_hosting.py | b951e30486af44dedbf166ecfae97d59e5b85f443a10d1ec918c084e633907a5 |
| tests/test_container.py | 70ec6542645955c36b96014ad4fbb29c3b3fe46382a26a8786824706b6c2b63c |
| tests/test_environment.py | b8049b7d9fedd9912d68872f5f12a6323236b93aacea8629e45c57d2069651ee |
| tests/test_protocol.py | c835645bd06e30a5d99aa33c895f6d8ca8b875f37729b67554fdcd84077ed1cd |
| tests/test_official.py | dc27ef29e745f11be0135ff37a875b65060958bc626aedd4417a7aa24aaac708 |

Original pre-migration deployment/cleanup/history remains byte-for-byte intact:
163717 bytes, SHA256
`ac9e2d705d815ac95e2a165860882ab0d0071bfecd8f56e7f0de6943f788f68e`.

Status: architecture A selected by delegated user decision — 2026-10-26
22:15 EDT. This is the final migration PLAN, not implementation/deployment
authorization. Goff independently APPROVED A subject to the corrections now
incorporated below and confirmed that a policy adapter using the actual AWS
official server is honest official-server use. The coordinator will request ONE
scoped migration approval covering prerequisites, bounded candidate work and
conditional cutover after independent review and actual proof; no execution
before that approval. Technical gates below do not require repeat permission
when the approved scope remains unchanged.
Concrete authentication, dependency, code and release artifacts still require
independent review before execution. No runtime edits, builds, identity/role/
database grants, cloud mutation or resource retirement are authorized here.
Keep healthy chat/MCP ACA images, identities, database, vault and existing public
POC network exceptions unchanged. Do not revive retired App Service.

## Selected enterprise decision and implementation boundary

Choose **A: governed structured-plan/policy layer with ALL Redshift metadata
and query execution through `awslabs.redshift-mcp-server==0.1.2`**.
For a large electricity company new to AI, retaining deterministic metric
definitions, bounded access and traceable fresh results is preferable to giving
the model native SQL tools. Existing AWS investment remains usable while
business semantics remain understandable and portable to a future Microsoft
Fabric migration. This is an engineering risk/cost decision, NOT a claim of
regulatory compliance. Implement neither Fabric nor a generic provider framework.

Retain `AnalysisPlan` validation, metric/dimension enums, compiler-owned SQL,
date/grain reconciliation, duplicate/orphan checks, exact decimals/units,
observed-date context and null/empty/truncation rules. Replace every
`database._cursor` use with private calls to the official server; retire
`redshift_connector.connect`, custom connection/auth setup and connector
dependency from the candidate runtime. No Boto3 query shadow implementation,
direct Data API query shortcut, fallback to the old connector, or fake
official-server label. The old production image remains rollback-only.

Foundry/browser clients see the governed HTTP adapter, **not** the seven native
SQL/metadata tools. Describe it accurately as “structured analytics policy
adapter backed by the AWS official Redshift MCP server.” Retain the agent's
two public analytics tools and strict answer protocol, plus governed bounded
metadata/connection-probe tools where needed by existing consumers. The
official stdio subprocess is not separately exposed to Foundry or the internet.
Map the verified seven native tool schemas to the exact required internal
operations during implementation; unsupported or changed contracts fail closed,
not by inventing tool names/arguments or silently expanding the allowlist.

### Supplied upstream facts and concrete integration delta

Gibbs independently verified package0.1.2: Python>=3.10, MCP dependency
`>=2.1,<3` (upstream SDK lock2.2), stdio executable, seven native SQL/metadata
tools, and QueryResult `columns,rows,row_count,query_id` with DECIMAL strings.
It uses Boto3 Redshift Data API without SecretArn/database-password auth.
Preferred execution is BatchExecuteStatement with read-only BEGIN/ROLLBACK;
legacy ExecuteStatement fallback exists. Defaults include 1000 rows and
3600-second timeout with no cancellation. These are supplied research facts,
not local compatibility, federation or production tests.

1. **Keep ACA, add an internal stdio bridge, isolate dependencies.**
   Keep the outer adapter's existing MCP1 FastMCP/Streamable HTTP `/mcp` and
   port8000 contract initially. Package the pinned official executable in a
   separate virtual environment/process with its own locked MCP2 dependencies;
   never co-install incompatible MCP1/MCP2 constraints in one environment.
   The adapter uses a standard MCP stdio client lifecycle (initialize,
   negotiate, list/validate tools, call tools, close) to the child process.
   A standard MCP wire-protocol handshake MUST be tested across these SDK
   versions; separate environments do not prove wire compatibility.
   If negotiation fails, stop and submit a minimal reviewed MCP2 upgrade of
   the outer adapter, with all current HTTP/envelope regression tests, rather
   than assuming compatibility or building an ad hoc protocol translator.
   Supervise a bounded child/session lifecycle, sanitize stderr and transport
   failures, and bound result-frame ingestion. Never log credential-process
   stdout or provider bodies. Preserve nonroot/digest/lock/context controls.

2. **Replace execution, not semantics.**
   Refactor `analytics.py::_rows/_integrity/_source/_well_integrity/analyze_data/
   get_data_context` around explicit official MCP results, not DB cursors.
   All metadata/probe functions in `database.py` likewise become official-tool
   calls or are retired; remove `_cursor` rather than leaving a dormant fallback.
   `compile_query` retains only backend-owned identifiers/operations.
   Native tools have NO bind-parameter argument: do not send current `%s`
   SQL/parameter tuples unchanged and do not interpolate untrusted strings.
   Introduce one narrow typed SQL-literal encoder for validated dates, bounded
   integers and filter strings, using independently tested Redshift string/
   escape semantics. Identifiers remain compiler-owned enums; reject unsupported
   NUL/control/escape cases until safely covered. Test quotes, backslashes,
   Unicode and injection payloads. If safe serialization cannot be demonstrated,
   block that filter capability/cutover; never fall back to a driver.
   Rework cursor-dependent integrity checks and their transaction assumptions
   explicitly. Where checks and aggregates require a consistent read, prove
   the upstream batch executes them in one supported read-only transaction;
   otherwise submit an equivalent single-statement checked query and test it.
   Do not assume separate tool calls share a snapshot or that existing
   reconciliation guarantees survive automatically.

3. **Normalize official results into the unchanged business envelope.**
   Validate columns/types, row counts, nulls, query completion/ID and decimal
   strings before constructing the existing version1 result. Preserve exact
   SQL decimal aggregation, unit/source/grain/observation/null-record evidence.
   Compile SQL with `LIMIT plan.limit + 1` (at most `LIMIT 501`) to detect
   truncation and return at most500 business rows. Do not assume the native
   tool exposes a configurable501-row cap: enforce bounded, validated result
   ingestion and the business envelope independently of its1000-row default.
   Handle pagination/row_count mismatches
   explicitly, never label partial results complete. Keep complete emitted MCP
   output<=256KiB, bound internal frames/metadata too, and reject oversized
   single rows safely. Store only sanitized provenance (official package/tool
   version and query correlation) server-side; do not expose query IDs or SQL
   in browser/public payloads.

4. **Preserve enforcement despite upstream timeout/fallback gaps.**
   Prove a SUPPORTED10-second statement/workload budget on the effective
   nonsuperuser principal and fixed workgroup, including integrity queries,
   without permitting generated SQL to override it. Preserve the existing
   statement-timeout guarantee; do not invent universal polling/queue/lock
   cancellation guarantees. Document the supported limit's actual scope and
   test relevant waits. Retain a bounded overall analysis deadline; the
   upstream3600-second client wait is NOT an acceptable query bound.
   Preserve two active execution permits, no unbounded queue,120 calls/minute
   total and12 context/analytics calls/minute. On HTTP/BFF timeout or stdio
   disconnect, do NOT release execution capacity until remote completion is
   proven or an independently enforced DB deadline has actually ended the
   statement. Killing the subprocess or aborting the BFF does not cancel AWS
   SQL. Do not launch a replacement child/query behind still-running work.
   Missing completion evidence quarantines capacity/fails closed; do not
   present a cancellation guarantee the upstream server does not provide.
   Verify Batch is the successful execution path and database read-only
   enforcement/grants remain effective. Use Batch-only IAM with no
   ExecuteStatement permission, and ensure no inherited grant can enable it.
   This prevents fallback EXECUTION even if the package attempts fallback;
   no unsupported disable-fallback flag is required. Test denied Batch and
   attempted ExecuteStatement both fail closed without running fallback SQL.

5. **Keep chat stable; create a separately testable candidate.**
   Preserve current BFF allowlist, version1 envelope, `groundedReply`,
   server-owned current-turn evidence, four-call/60-second budgets, sessions,
   cookies, origin, UI and public API. Add only necessary provenance/fixture/
   bridge compatibility tests; no parser weakening or chart implementation.
   Preserve adapter `test_connection -> connected:true`, but execute its
   harmless probe through the official MCP path; keep `/healthz` process-only.
   Build a parallel candidate endpoint after explicit authorization, retaining
   old MCP ACA unchanged. Register a NEW exact Foundry agent version bound
   to candidate HTTP adapter; keep agent2 intact. Pin candidate BFF/probe URL
   and new agent version together. No change to public BFF contracts is needed
   merely because internal native tool names differ.

## Credential design — approval required; federation NOT tested

Use the AWS-documented Microsoft Entra ID -> AWS STS pattern:
https://aws.amazon.com/blogs/security/how-to-access-aws-resources-from-microsoft-entra-id-tenants-using-aws-security-token-service/

The adapter workload's ACA system MI obtains a short-lived Entra access token
for a purpose-specific resource application. A tightly scoped
`credential_process` helper exchanges that token with AWS STS
AssumeRoleWithWebIdentity and emits temporary AWS credentials only to Boto3's
standard credential-provider pipe, including a valid `Expiration` so Botocore
can refresh the expiring credentials by invoking the helper again.
Configure the official child with an
explicit profile/region/config path; deny unintended environment/shared-profile/
container-credential fallbacks. Use Botocore's refresh lifecycle rather than
assuming a short-lived helper retains state. Any deliberate shared cache must
be genuinely process-memory-only with synchronized refresh, never persistent
helper state or token files. Redact failures and fail closed.
Static AWS keys, copied operator credentials and DB-password/SecretArn auth
are excluded. The Entra app is a resource/audience, not a client-secret app.

Before creating AWS trust, prove the actual ACA-issued token's issuer,
audience and stable subject plus client identity claims (`azp`/`appid` as
applicable), token version and expiration. Verify which claims AWS exposes
as supported trust-condition keys and how audience/authorized-party mapping
works; do NOT assume arbitrary JWT claims can be IAM condition keys.
Bind the exact tenant/provider, resource audience and intended MI subject,
with any additional supported client restriction, rather than broad tenant
trust. Never retain raw tokens. Prove successful refresh over a real credential
expiry and denied wrong MI/audience/tenant before declaring federation working.

Use a NEW purpose-specific AWS runtime role/OIDC trust. The current TaskRole
trusts ECS tasks only; preserve it unchanged. Do not “repair” it by adding
broad Entra trust or use renewed AWS administrator/root CLI as runtime auth.
The existing chat MI remains solely a Foundry client; candidate adapter MI
receives only its approved federation assignment. Registry pull UMI unchanged.

### ONE minimum authorization request — prerequisites through conditional cutover

Ask the user ONCE to approve the following scoped migration, including
prerequisites, bounded candidate proof, and conditional production cutover/
rollback only after the technical gates pass. This approval has NOT yet been
given. Resolve concrete
object IDs, role ARNs, workgroup ARN, database and table/principal names in
reviewed artifacts BEFORE applying them:

- **Entra:** create one purpose-specific resource application/service principal
  with an application app role and assignment-required service principal; assign
  only the candidate adapter's MI service principal to that app role.
  Configure only the token audience/version necessary for the documented
  exchange. No application secrets, tenant-wide API consent, subscription
  Owner/Contributor or assignment to arbitrary managed identities.
- **AWS:** create/reuse one exact verified Entra OIDC provider and create one
  new role restricted to the verified MI/audience/tenant. Allow STS web-identity
  assumption only through that trust. Add only required Data API
  BatchExecuteStatement, DescribeStatement and GetStatementResult operations
  plus the target workgroup credential operation and strictly necessary
  selected metadata discovery. Scope execution/GetCredentials to the actual
  Redshift Serverless workgroup/database where IAM supports it. For operations
  that require Resource `*`, document that limitation; apply supported
  statement-owner conditions to describe/result access (for example
  `redshift-data:statement-owner-iam-userid` bound to the calling IAM identity)
  and prove session-owner behavior. Use Batch-only execution with no effective
  ExecuteStatement permission, even if the upstream package attempts it. No
  Secrets Manager, arbitrary role assumption, broad Redshift admin or copied
  ECS role trust. Exact action/resource/condition support requires review,
  not assumed JSON. Existing role lacks Batch permission and is not sufficient.
- **Database:** verify the ACTUAL IAM-mapped nonsuperuser database principal,
  not the operator's principal. Grant only schema `USAGE` and `SELECT` on
  `oge_synthetic.daily_production`, `monthly_production`, `annual_production`,
  `monthly_prices`, `wells`, with only required database connect/session
  privileges. No superuser, DML, DDL, schema CREATE, blanket future-table grants
  or broad inherited/public write privileges. Configure and prove the enforced
  SUPPORTED10-second statement/workload budget on the fixed workgroup and
  read-only principal without SQL override. Resolve effective role inheritance
  and document actual timeout/queue/lock scope without promising universal
  cancellation; if supported mechanisms cannot preserve the existing controls,
  cutover remains blocked.
- **Azure candidate only:** permit implementing/building reviewed source and
  deploying one bounded candidate adapter ACA in the existing Brazil South
  environment/registry, with a separate system MI, existing pull UMI, approved
  HTTPS test ingress and no new public native-SQL endpoint. Permit the new
  agent version and bounded official-path read-only tests. Candidate replica/
  logging/build and Data API/Foundry test costs are incremental; no pricing
  estimate is invented. Minimize to one bounded replica and retire candidate
  only after separately authorized outcome/cleanup.

**Conditional cutover/rollback is included in the SAME requested approval.**
It becomes executable only after independent concrete-artifact review and
actual candidate proof satisfy the technical gates below; no mandatory second
permission request is needed for unchanged approved scope. Include the
narrowly reviewed existing-chat ACA revision/config updater and
matching rollback executor, immutable candidate image/agent-version/probe
binding, a brief planned session reset and bounded acceptance window. Keep
current chat image, agent2, MCP image/endpoint, identities and vault available.
There is currently no approved existing-chat update/rollback executor;
`chat_aca.py create` and legacy App Service stages must not be replayed.

The requested scope excludes deletion of old resources or vault secrets,
changes to current ECS trust, unrelated role changes, broad roles, long-lived
keys, Fabric implementation and a longer database timeout. A material scope
change or unresolved technical blocker must return to the coordinator, not be
silently treated as covered by this approval.

## Release evidence, latency and rollback gates

Before conditional cutover: independently review concrete code/auth/IAM/DB/release artifacts;
run focused existing semantic, HTTP, parser, health, deployment and origin/
session tests plus stdio cross-SDK/injection/pagination/refresh/adversarial tests.
Prove actual official-server invocation on every metadata/query route and
absence of driver/Boto3-query fallback. Verify refused write/out-of-scope
queries, missing Batch failure, malformed/oversize results, credential expiry,
timeout/lock behavior, and capacity holds after disconnect.

Run bounded measured end-to-end cold/warm first-turn and same-session follow-up
tests on candidate, including all integrity checks. Record tool-count/latency
and Data API/Foundry calls without raw payloads. Require completion within
existing BFF60-second/four-tool-call budget and real DB10-second statement
limits; no arbitrary load test or timeout increase to make acceptance green.
If integrity round trips exceed budget, optimize checked SQL within the
governed semantics and re-review, rather than skipping checks or permitting
unbounded work. Health must retain its35-second/single-flight semantics.

At approved cutover verify HTTPS assets/process/fresh DB health, then2025 oil
**21,157,564.26 bbl**, followed in SAME cookie/session by gas
**44,177,025.20 Mcf** with fresh official-backed analysis, continued true and
correct units/period/decimal values. Test null/empty/truncated/error behavior,
origin spoof rejection, secure reset and nonleakage. Visual analytics preference
remains recorded; no chart work is part of this migration.

Rollback is the matched current chat digest + agent2 + old MCP/probe URL/config,
not a switch to an internal fallback connector. Restore by reviewed revision
operation, disclose/reset affected in-memory sessions, and recheck health and
the oil/same-session gas pair. Preserve both known-good image digests recorded
below. Only a separate post-success approval may retire the old custom MCP
workload/obsolete connector artifacts or its unneeded permissions; preserve
database, vault, pull identity, chat MI and unrelated workloads throughout.

---

## Earlier investigation — retained audit trail

The initial investigation and alternative comparison below are historical.
Selection A and the gates above supersede “no architecture selected” and
“await research” wording below; they do not grant execution permission.

## Migration investigation gates

- Audit local agent instructions, tool allowlists, BFF grounding/result parsing,
  health contracts, tests, and deployment/image pins before proposing cutover.
- Await separately verified upstream AWS server authentication, tool schemas,
  result envelopes, transport, and hosting facts; do not assume compatibility
  with Azure managed identity or the current structured-plan tools.
- Explicit decision required if upstream SQL tools conflict with the prior
  user-required structured-plan-only interface. Preserve SQL safety and fresh,
  same-session data grounding; do not silently remove these guarantees.
- Compare a thin structured-plan/policy adapter using the official connector
  with a native upstream-tool agent path; no architecture selected yet.
- Preserve sessions, units, result evidence, and the recorded preference for
  visual analytics. No chart implementation is authorized by this audit.
- Cutover requires independent review, approved auth/transport design, new
  versioned agent/tool bindings, contract tests, immutable images, and explicit
  deployment approval. Retain the current agent/image configuration for rollback.
- Numeric acceptance remains oil **21,157,564.26 bbl**, followed in the same
  session by freshly queried gas **44,177,025.20 Mcf**; include origin/cookie,
  health, tool-error, and fresh-result grounding checks.

## Local integration audit — evidence and change map

Read-only source audit completed; only this existing plan was edited. Upstream
AWS contract research is deliberately separate. Tool names below describe the
CURRENT custom implementation, not verified AWS official tools. Live facts below
are the supplied verified baseline, not a new cloud check during this audit.
This investigation and its alternatives remain pending coordinator/independent
review; no final architecture or Azure-to-AWS trust decision has been made.

### Exact current coupling that a name swap would break

1. **Custom connection and server boundary.**
   `src/redshift-mcp-server/redshift_mcp_server/server.py` registers exactly six
   tools: `get_data_context()`, `analyze_data(plan)`, `test_connection()`,
   `list_schemas(limit)`, `list_tables(schema, limit)`, and
   `describe_table(schema, table, limit)`. `mcp` is FastMCP Streamable HTTP at
   `/mcp`, port 8000; `healthz` is process-only. `_transport_security` validates
   exact Host/Origin allowlists. `_run` enforces two workers/no admission queue,
   120 total calls/minute and 12 analytics/context calls/minute, and holds worker
   permits until execution actually settles after cancellation.
   `database.py::_cursor` directly calls `redshift_connector.connect` with
   hostname-verified TLS, a 10-second statement timeout, `BEGIN READ ONLY`,
   rollback/close on every call, and sanitized failures. Metadata functions use
   bound parameters and bounded fetches. Replacing only server branding or
   retaining this DB execution path would NOT satisfy the requested official
   connector migration. These connection/metadata implementations must be
   replaced by official-server calls or retired after approved cutover.

2. **Domain semantics, not merely a connector.**
   `analytics.py::AnalysisPlan`, `Measure`, `Filter`, `Ordering`, `compile_query`,
   `_source`, `_well_integrity`, `analyze_data`, and `get_data_context` implement
   a closed strict version-1 semantic layer over `oge_synthetic`.
   Plans forbid extra fields/SQL/expressions/unknown identifiers: production
   sums; monthly price avg/min/max; well counts; up to three measures, two
   dimensions, four filters, 500 result rows and 3661 inclusive days.
   Daily production is authoritative; monthly/yearly rollups require per-well,
   per-period reconciliation, valid grain, and nonnull matching measures.
   Well joins reject duplicates/orphans. Prices use DECIMAL(38,8), full months,
   no well joins. No revenue/profit/ratios or price-production joins.
   Results include `version,status,executed,executed_at,items,truncated,units,
   source,source_grain,joined_sources,plan,notes`; aggregate values are decimal
   strings with null counts, source-record counts and observation bounds.
   `_response_bytes` bounds the complete duplicated MCP envelope to 256 KiB;
   byte/row truncation is explicit. Empty is not zero; null is unknown.
   This logic is directly coupled to `database._cursor` and cursor-style SQL;
   it cannot transparently survive a different execution/result protocol.

3. **Registered Foundry agent must be versioned and rebound.**
   `deploy/chat_deploy.py::TOOLS`, `MCP_TOOLS`, `MCP_URL`, `agent_definition`,
   `agent_matches`, and `agent` bind the server label `redshift`, current `/mcp`
   URL, exact two-tool allowlist, and scoped no-approval tools.
   Instructions REQUIRE structured `analyze_data` on every factual turn,
   `get_data_context` for unknown observed dates/semantics, no raw SQL, and final
   JSON `{kind:"answer",reply}` or exact server-owned clarification/unsupported
   reason enums. They also require units/source/grain/period/null/truncation
   caveats, distrust tool/data instructions and cap calls at four.
   `agent()` compares actual definitions and creates/reuses an exact version;
   do not mutate/delete current version 2. A new approved definition/version
   must bind the verified native tools or adapter tools and required auth.
   Registration currently lives inside the obsolete App Service deployment
   helper and calls `inventory()`; do not run its stage unchanged. Extract/reuse
   only reviewed pure definition/comparison logic in ACA-compatible operations.

4. **BFF response evidence/parser is custom-contract-specific.**
   `src/redshift-chat/server/providers.ts::ALLOWED_TOOLS`, `createAgent`,
   `agentPayload`, and `createResponseCaller` use the GA project Responses client
   with `agent_reference`, stored server-owned `previous_response_id`, no retry,
   completed status, no approval requests, and at most four `mcp_call` records.
   Unknown/failed/incomplete calls fail closed. Only current-response
   `analyze_data` passes as answer evidence; context alone never does.
   `grounding.ts::parseToolOutput` accepts single business JSON, one-text-block
   MCP CallToolResult with matching optional structuredContent, or the observed
   two-document Foundry encoding whose sole `structuredResponse` equals the
   first object. It rejects errors, mismatches and output above 256 KiB.
   `validateAnalysis` hardcodes the custom plan/result schema, five sources,
   units, grain, decimal strings, counts, nulls and limits. Native AWS result
   columns/rows, pagination, asynchronous status or other envelopes CANNOT be
   assumed compatible; verified fixtures and an explicit normalizer/evidence
   validator are required. Never loosen this to arbitrary JSON or use old
   response evidence as proof of a new query.
   `groundedReply` requires current analysis evidence for `{kind:"answer"}`,
   supplies non-data templates and overrides empty/caveats truncated/null data.
   Existing limitation: it checks evidence shape/presence, not numerical
   equality between every prose number and row; `executed_at` is parse-validated,
   not an independent freshness clock. Preserve current-response execution
   gating and independently test exact numeric answers; do not overclaim a
   cryptographic or complete semantic grounding guarantee.

5. **Health is a separate MCP client/auth surface.**
   `providers.ts::createProbe` independently initializes an unauthenticated
   StreamableHTTPClientTransport, calls ONLY `test_connection` with `{}`, checks
   `connected:true`, and terminates/closes the MCP session. Updating the
   agent URL alone leaves this probe on the old connector.
   `server/config.ts::Config/readConfig` separately reads HTTPS
   `MCP_SERVER_URL`; this value is for the BFF probe, not the registered agent's
   remote binding. Verify native transport/probe/auth or an adapter equivalent.
   `health.ts::HealthMonitor` must retain the 35-second deadline, 30-second
   cache, stale/checking/unavailable states, single-flight through cleanup, and
   no false connected fallback. Keep `/healthz` process-only so a downstream
   failure cannot trigger chat restarts. A list-tools/HTTP200-only replacement
   must not claim actual database connectivity.

### Public API and user experience invariants to retain

- `server/app.ts::createApp` continues accepting POST `/api/chat` ONLY
  `{message}`; response is `{reply,turnsRemaining,truncated,expiresAt,toolNames,
  continued}`. `toolNames` comes from actual calls, never model claims; no
  provider IDs, SQL, raw rows, endpoints or credentials reach the browser.
  `/api/session/reset` accepts `{}`; `/api/config` contains public limits only;
  `/api/health` remains `{status,connected,checkedAt}`.
- `server/state.ts::Sessions`, `RateLimiter`, `contracts.ts::LIMITS` and the
  app's session/cancellation locks remain: opaque Secure/HttpOnly/
  SameSite=Strict `__Host-` cookie, exact-origin CSRF, no trust in forwarding
  headers, server-only continuation, 20 attempts, 30-minute TTL, two concurrent
  chats, five API requests/minute/socket, timeout quarantine and explicit reset.
  Four tool calls / 60 seconds / 800 output tokens may conflict with a native
  multi-step discovery/execute/poll/results protocol; verify actual call counts
  before deciding any explicit bounded budget change.
- Existing one-replica/single-active-revision deployment is required by
  in-memory session/rate state. New revision/restart can invalidate sessions;
  do not promise seamless chain continuity across agent-contract cutover.
  Preserve same-session follow-ups within each accepted deployment and disclose
  any planned reset at cutover/rollback.
- Plain-text safe/accessible chat rendering and units remain unchanged.
  Visualization remains a recorded preference, not permission to add a chart
  schema/UI or relax result provenance. Current API is text, not a chart API.

### Local authentication assumptions — not an AWS trust solution

- `providers.ts::createAgent` uses the chat's system ManagedIdentityCredential
  in production (AzureCliCredential only in development) for Foundry. The
  supplied chat principal is `92f43c89-a02c-4636-b7c5-775067c221d5` with exactly
  its two project roles. That identity/authorization does NOT establish AWS
  access and must not be conflated with the registry pull UMI.
- Current `agent_definition` has no MCP auth/connection binding; `createProbe`
  supplies no auth headers. Any protected official endpoint requires explicit
  support/design for BOTH Foundry-to-MCP and health-probe-to-MCP calls.
- `redshift_mcp_server/config.py::Settings.from_env` supports default password
  auth and an optional provisioned-cluster IAM mode using the AWS provider
  chain (`AWS_REGION`, `REDSHIFT_CLUSTER_IDENTIFIER`, `auto_create=False`).
  This optional path is not a verified Azure workload federation setup.
  `deploy/deploy.py::settings` explicitly restricts the approved deployment to
  password mode/TCP5439. `app_document` injects only a system-MI Key Vault
  reference via `REDSHIFT_PASSWORD` secretRef, not a literal password.
  The AWS Data API reference query in `chat_deploy.py::analytics_reference`
  uses an operator CLI/workgroup; it is acceptance evidence, NOT proof of
  runtime IAM, official-server auth, or transferable Azure-to-AWS trust.
- Await the independently verified AWS auth/transport/tool facts and parent
  auth decision. Do not copy developer AWS credentials, create keys, assume
  Managed Identity is accepted by AWS, grant roles, or remove existing vault/
  database/network exceptions while investigating.

### Architecture decision to escalate, not silently implement

**A — Thin structured-plan/policy wrapper over the official server.**
Keep the closed plan and result contract if still required by the user; move
domain validation, backend-owned query compilation, integrity checks, decimal/
unit/null/truncation normalization into a policy adapter whose ONLY Redshift
execution/metadata dependency is the AWS official MCP server. Remove use of
our `redshift_connector`/`database._cursor` execution path after cutover.
This retains custom analytics business logic, not a custom DB connector.
It is technically conditional on upstream capabilities: parameter binding or
equivalently safe serialization, bounded/paginated results, cancellation,
read-only enforcement and integrity-query execution semantics must be checked.
The current multi-query cursor/transaction model is not portable by assertion.
Benefits: fewer BFF/agent contract changes and stronger deterministic scope.
Costs: maintained policy code, possible extra service/hops and upstream calls,
latency/compute/IAM/operational work. Existing BFF limits also need profiling.

**B — Native official tools directly in the Foundry agent.**
Retire custom server/analytics execution only after verified replacement;
rewrite agent instructions/allowlist, BFF result evidence/normalization and
health bindings for actual upstream tools and transport. Semantic safety,
read-only database authorization, bounded queries/results, source/grain/units,
null/empty/truncation and no-double-counting still need enforceable controls.
Prompt instructions alone are not equivalent to the current closed validator.
Fewer policy-layer hops may reduce maintenance, but native discovery/polling
can add tool/token/API cost and budget pressure; no cost winner is asserted.

**Blocking user/coordinator decision:** if verified official tools expose raw
SQL, may the agent generate it under new enforced controls, or must the prior
explicit structured-plan/no-arbitrary-SQL requirement remain through A?
Using an official DB connector and retaining an application semantic policy
are compatible; claiming direct native tools while secretly continuing our
custom DB connector is not. Neither path is selected by this audit.

### Tests, packaging and deployment wiring requiring coordinated changes

- `src/redshift-chat/tests/provider.test.ts`, `tests/fixtures/foundry.ts`:
  actual native/adapter tool fixtures, current-response evidence, observed GA
  encoding, failed/unknown/approval/incomplete tools, malformed payloads,
  size/decimal/units/source/null/empty/truncation and fresh continuation.
  Preserve strict old-parser cases where that encoding still applies.
- `tests/health.test.ts`: replace ONLY verified native probe/tool/auth/transport
  expectations, preserving deadlines/cleanup/cache and truthful DB health.
  `tests/app.test.ts`: same-cookie fresh oil/gas, chain isolation, response
  fields, no raw payload leaks, origin/reset/limits/cancellation unchanged.
  `tests/ui.test.tsx`: retain plain-text/accessibility/health behavior and revise
  plan-safety copy assertions only after an approved contract decision.
- `src/redshift-mcp-server/tests/test_analytics.py`, `test_database.py`,
  `test_protocol.py`, `test_config.py`, `test_hosting.py`, `test_container.py`:
  retain semantic/safety coverage if A; replace connector mocks with official
  client boundary tests, real verified protocol fixtures and bounded
  cancellation/pagination/error cases. If B, retire obsolete tests only with
  equivalent enforced replacement coverage, not to make a renamed server pass.
- `deploy/chat_deploy.py::mcp_acceptance`, `analytics_items`, `agent_answer`,
  `acceptance_plan` hardcode six listed tools/two agent tools and the custom
  result envelope; adapt these pure assertions to verified replacements.
  `analytics_reference`/`exact_number` can remain independent acceptance
  concepts. `verify()` targets deleted App Service; DO NOT execute it.
  `deploy/test_chat_deploy.py` contains corresponding tool/definition/version/
  precision/freshness/source/origin tests; migrate relevant tests, not the
  legacy app provisioning workflow.
- `deploy/chat_aca.py::definition` currently pins agent version `"2"` and old
  MCP URL independently; `image_reference`, `source_files`, `source_hash`,
  `build` enforce repository/digest, explicit context and source approval.
  `create` deliberately refuses existing-app overwrite: there is no approved
  chat revision-update/rollback executor yet. A narrowly reviewed existing-ACA
  revision/config switch is prerequisite, NOT replaying create or App Service.
  Update `deploy/test_chat_aca.py` for version/endpoint and exact update/
  rollback invariants without recreating identities or broad grants.
- `deploy/deploy.py::RUNTIME_FILES/source_manifest/build/app_document`,
  `configured_release_app`, release verification and `test_deploy.py` embed
  custom Python sources, port8000, `/healthz`, repository, password secretRef,
  host/origin/config assumptions. Its image-only release validation preserves
  the old contract and cannot be presumed an official-host migration executor.
  Re-scope only after the actual official hosting/auth contract is established.
- `src/redshift-mcp-server/{Dockerfile,.dockerignore,pyproject.toml,
  requirements.lock,requirements-build.lock}` package the custom entrypoint/
  connector and hash-pinned dependencies; a native server or adapter requires
  reviewed provenance, pinned official package/image and matching lock/context/
  nonroot/startup changes, not a renamed custom wheel.
  `src/redshift-chat/{Dockerfile,.dockerignore,package.json,package-lock.json}`
  remain unless adapter/SDK changes require dependencies; rebuild only when
  approved source changes require it. Keep immutable digest/source gates.
- Future operator documentation updates belong in `deploy/CHAT-ACA.md`,
  the CURRENT top of `deploy/CHAT-README.md`, and the custom server README as
  applicable. Preserve all retired App Service failure/cleanup history.
  Historical proof and image evidence are not rewritten as new migration proof.

### Minimal gated cutover and rollback sequence (not authorized execution)

1. Finish separate upstream verification: exact AWS publisher/package/version,
   tools/schema/results, transport/hosting, auth and target Redshift support.
   Resolve A versus B explicitly, including the previous structured-plan
   requirement and who enforces SQL/read-only scope.
2. Review exact Azure-to-AWS and MCP-client authentication boundaries, least
   privilege, result safety, latency/cost and network compatibility. Obtain
   independent architecture/security review and deployment approval separately;
   no permission grant or cleanup follows merely from this investigation.
3. Implement approved client/adapter + agent definition/new version + BFF
   allowlist/normalizer/probe together, preserving public/session contracts.
   Add verified fixtures and focused tests before a release. Prepare reviewed
   ACA update and rollback operations; do not use legacy App Service stages.
4. Build approved immutable artifacts, retain current rollback references, and
   validate the official path without switching the working chat. Confirm actual
   official execution provenance, tool schema, error behavior, read-only scope,
   deadlines, precision and observed-data semantics; no success from mock data.
5. Approved cutover atomically coordinates chat image, agent version, agent MCP
   binding and probe endpoint/auth; old chains may require explicit reset.
   Keep the old connector/agent/image intact during the acceptance window.
6. Require HTTPS UI/assets, process health, fresh actual connected health,
   2025 oil **21,157,564.26 bbl** (first turn, continued false), then same-cookie
   gas **44,177,025.20 Mcf** (continued true, fresh current-turn official-path
   query evidence, not recalled oil/context). Verify units/period/exact decimals,
   no-rows/null/top-N caveats, failure/approval/malformed-result rejection,
   origin spoof/reset/cookie controls and no provider/SQL/secret leakage.
   Direct native results need replacement source/semantic checks, not just
   these two happy-path numbers. User visual preference remains recorded.
7. On failed acceptance, restore the matched prior chat digest + agent version2
   + old agent MCP binding and BFF probe URL/config as ONE rollback set, verify
   fresh health and oil/same-session gas again, and disclose session resets.
   Only a separately approved post-success cleanup may retire custom runtime
   execution. Never revive App Service or delete retained vault/DB/identities.

Rollback baseline supplied for this investigation:
chat `ca-redshift-chat-bs01--sr9ms4f`,
`sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`;
custom MCP `ca-redshift-bs01--0000003`,
`sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`;
Foundry `redshift-chat-agent` version2; MCP/probe URL
`https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp`.
Retain runtime principal/project roles, registry pull UMI, environment/registry/
vault, database and approved POC network exceptions. No live verification,
cloud change, install, Docker build, runtime edit, or extra note artifact was
performed for this local audit. Documentation-only change needs no runtime tests.

---

# CURRENT: User-directed chat migration to Azure Container Apps — 2026-10-26

Status: ACA deployed and verified; obsolete App Service and dedicated B1 plan retired

### Approved cleanup completed — 2026-10-27 02:00:10 UTC

User-selected retirement and Goff's exact-scope approval were executed, not
left as a proposal. Deleted only App Service
`app-redshift-chat-bs01-bb4b2781`, then its confirmed-empty dedicated B1 plan
`asp-redshift-chat-bs01`. Before deleting the app, removed exactly its old
principal `ebcf9b66-cca4-46a6-a344-3f100ea7eb0d`'s two project-scoped assignments:
`1d0a3438-808c-535c-a6da-79dda6fc03c0` (Cognitive Services User) and
`a2b0451e-4de4-5b0d-8dad-8567fe0633e2` (Foundry Agent Consumer).
These were the explicitly approved permissions outside this resource group.

Direct ARM GETs now return **ResourceNotFound** for both retired resources.
Immediately before plan deletion, direct ARM plan/site and subscription-wide
site reads plus cross-resource-group Resource Graph found zero references.
Both old assignment IDs are absent; new runtime project assignments are unchanged.

Exactly six resources remain in `rg-redshift-bs01`, all Brazil South:
`ca-redshift-chat-bs01`, `ca-redshift-bs01`, `cae-redshift-bs01`,
`acrredshiftbs01bb4b2781`, `kv-redshift-bs01`, `umi-redshift-imagepull-mx01`.
Retained resource inventory/tags, chat/MCP revisions and image digests, identities
and pull UMI are unchanged; the vault-only `SecurityControl=Ignore` exception
is preserved. No other Foundry/database/IAM, images, policies or resources changed.

Postcleanup HTML, chat `/healthz`, fresh connected `/api/health`, and MCP
`/healthz` all HTTP200. Actual connected check timestamp:
`2026-10-27T02:00:06.253Z`. Chat remains one active Healthy/RunningAtMaxScale
revision `ca-redshift-chat-bs01--sr9ms4f`, one replica.
No restart, package build or repeat business query was needed.
Sanitized before/operation/after proof:
`deploy/.chat-artifacts/obsolete-appservice-cleanup-proof.json`
(`completed_verified`; all 12 verification checks passed).

### Current verified result — 2026-10-27 01:53 UTC

- HTTPS UI: https://ca-redshift-chat-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io
- One active Healthy/RunningAtMaxScale revision `ca-redshift-chat-bs01--sr9ms4f`,
  one replica, image digest
  `sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`.
- React HTML and both built assets HTTP200; fresh `/api/health` connected true.
  Coordinator independently observed loaded UI + Redshift connected at21:51EDT.
- Actual managed-identity oil answer **21,157,564.26 bbl** with
  `get_data_context` + `analyze_data`, continued false,19 turns remaining.
  Same-cookie gas answer **44,177,025.20 Mcf**, fresh `analyze_data`,
  continued true,18 turns remaining. Verification finished01:51:47UTC.
- Live wrong-origin request with spoofed proxy headers rejected403; correct
  same-origin reset200 and cookie rotated; Secure/HttpOnly/SameSite=Strict verified.
- Runtime system principal `92f43c89-a02c-4636-b7c5-775067c221d5`: exactly the
  two accepted project-only roles, no broad grants. Pull UMI unchanged.
- Actual tags null, no secrets, exact nonsecret runtime values/probes/scale and
  HTTPS-only ingress verified. MCP revision3/image/CORS unchanged.
- Initial downstream503/AGENT_UNAVAILABLE was recorded during warm-up.
  Bounded read-only in-container diagnostics confirmed MCP/Foundry egress,
  system-MI token acquisition and exact SDK calls succeeded; final full HTTP
  acceptance passed without configuration/image/restart changes.
- Persistent sanitized proof: `.azure/chat-aca-deployment.json`,
  `.azure/chat-aca-acceptance.json`, `deploy/.chat-aca-image.json`.
  Build context removed; no background helper remains.
- Cleanup completed in the separately approved retirement above; old App
  Service/dedicated plan were NOT dependencies of the new ACA or acceptance.
  Legacy `chat_deploy.py verify` still targets
  old App Service and is superseded; only its pure safe HTTP/numeric assertions
  were reused in new-ACA acceptance, without inventory or old-resource checks.

Independent concrete implementation/security review APPROVED by Goff.
Reviewed image-source SHA256:
`5a7894538f4887aaf430c3cd4b16957e7f68e35dac5f34d5ca5442192fbbcc76`;
`chat_aca.py` SHA256 `f8b5e385eea74dcd1899d4c152505505fb46d02d20f09975eb89c0069cfa5696`;
shared `deploy.py` SHA256 `582fdf26e37ae10e4f82d5bff4e6270370f7fb8dd08081be2cd06fb5d2e689a6`.
The user explicitly authorizes validation and deployment of this new chat ACA.
No new-resource policy exception, App Service repair or MCP/agent change authorized.

### Current ACA — All validation checks pass

- [x] Core validation: authenticated subscription, reviewed helper/source hashes,
  exact existing resources, ARM validate/what-if of generated chat-only resource
  (Bicep compilation N/A: reviewed imperative ARM recipe, not Bicep).
- [x] Docker validation: allowlisted lockfile/context and real remote ACR
  Linux/AMD64 image build; no local Docker installation/build.
- [x] Azure Policy validation: applicable current assignments/definitions,
  no copied `SecurityControl=Ignore` exception.
- [x] Role assignment verification: separate system runtime MI, existing pull
  UMI, exact two Foundry roles at the accepted project scope only.
- [x] Proof recorded with actual outcomes; official validation workflow complete
  before creating the chat workload.

### Section 7: Validation Proof — Current ACA, 2026-10-27 UTC

Executed commands: `chat_aca.py plan`, `chat_aca.py check`, SHA256 checks,
`python -m unittest discover -s deploy -p test_chat_aca.py`,
`az account show`, Azure Policy MCP assignment list and selected actual policy
definition reads, `az deployment group validate` (exact generated chat-only
template), `az deployment group what-if`, `az role assignment list` (existing
registry scope), reviewed `chat_aca.py build --approved-source-sha256 ... --execute`,
and `az acr task list-runs` (actual run/platform/output digest confirmation).

- Authenticated subscription/tenant match approved context; reviewed source and
  helper hashes remain exact. Existing environment/registry/UMI check passed.
- Generated `.azure/chat-aca.validation.json` directly from reviewed helper,
  containing only the new chat resource. Real ARM validation succeeded before
  and after binding the actual built digest. Actual what-if succeeded: Create1
  (chat), Modify0, Delete0; all existing resources Ignore. Bicep compilation and
  the Bicep-specific core shell helper are N/A for imperative ARM JSON; actual
  ARM validate/what-if and authenticated CLI checks were executed instead.
- Azure Policy MCP found inherited management-group baseline/audit/deny/deploy
  policies plus subscription assignments. Examined creation-deny (classic-only)
  and governance-deny initiative; actual ARM policy evaluation passed. No
  `SecurityControl=Ignore`, exception or new resource tags applied.
- Real remote ACR build `cq4` Succeeded, Linux/AMD64, start
  `2026-10-27T01:41:35.470550+00:00`, finish
  `2026-10-27T01:42:54.408347+00:00`.
- Immutable image:
  `acrredshiftbs01bb4b2781.azurecr.io/redshift-chat@sha256:1cdf2a6a97fad3a9bbef6514ef0eec875b8fbf82663ac65d5bb11184fb072593`.
  Source/run/tag/digest proof saved in `deploy/.chat-aca-image.json`.
- Static runtime-MI/project-role verification approved by independent reviewer
  and checked in focused tests; existing pull UMI retains registry-scoped AcrPull.
- Build verification: real remote image build plus local Node24 102 tests,
  typecheck and React/TS build passed; 7 helper tests passed again.
- Official validation workflow completed through UpdateStatus; azure-deploy invoked.

### ACA pre-deploy checklist

- Subscription/region/existing RG/environment explicitly confirmed by user;
  actual authenticated context and existing resources rechecked.
- Imperative ARM/Azure CLI recipe: AZD init/provision/environment variables,
  AZD service tags, Terraform and SQL/EF migrations are N/A; do not generate or
  mutate extra resources to satisfy unrelated recipe paths.
- Existing pull UMI principal `bfb1960e-711e-4061-a801-880fda281e4c` has actual
  registry-scoped AcrPull, already used successfully by unchanged MCP. No new
  pull role or propagation wait required. Runtime identity remains separate.
- Actual current environment consumption0.25/500 cores; requested additional0.25.
- Source/helper hashes exact; actual successful image digest bound to generated
  payload and ARM validation. No exception tags; new chat creation only.

The user explicitly replaced App Service recovery with Container Apps. This
section supersedes ALL recovery instructions below; historical proof is retained.

- Approved subscription `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, RG
  `rg-redshift-bs01`, Brazil South; new chat app `ca-redshift-chat-bs01`.
- Reuse existing environment `cae-redshift-bs01`, registry and image-pull UMI.
- Non-root Linux Node24 React+BFF image; remote ACR Linux/AMD64 build after review.
- External HTTPS, exact same-origin checks, min=max 1, 0.25 CPU/0.5 GiB.
- Separate system-assigned runtime identity; only the two accepted project roles.
- No cloud mutation, image build or deployment until independent review.
- App Service and healthy MCP/agent/database/vault/network remain unchanged.
- Preparation gates: narrow container artifacts, focused tests and instructions,
  independent review, then operator azure-validate and azure-deploy.

Artifacts: `src/redshift-chat/{Dockerfile,.dockerignore}`,
`deploy/{chat_aca.py,test_chat_aca.py,CHAT-ACA.md}`; directly related origin
regression in `tests/app.test.ts` and hosting-neutral proxy-policy comment.
Exact runtime config, roles/scopes, commands, base-image provenance, health/session
acceptance and cost limitations are in `deploy/CHAT-ACA.md`.
Read-only Azure discovery confirmed environment
`/subscriptions/bb4b2781-6739-4fa1-994e-4ad6ce55c59c/resourceGroups/rg-redshift-bs01/providers/Microsoft.App/managedEnvironments/cae-redshift-bs01`
and domain `happygrass-e982f5d6.brazilsouth.azurecontainerapps.io`.
Coordinator quota evidence: environment count2/50; existing consumption
cores0.25/500 ->0.5/500 after chat; no new environment or quota request.
Local Node24 verification:102 tests, typecheck and Vite/TS build passed;
7 focused ACA helper tests passed at preparation checkpoint; subsequent remote
build/deployment/acceptance proof is recorded above.
Actual helper read-only prerequisite check passed with the existing Python venv.
Review image-source SHA256 (22 allowlisted files):
`5a7894538f4887aaf430c3cd4b16957e7f68e35dac5f34d5ca5442192fbbcc76`.
Independent review, official azure-validate, azure-deploy and real live
acceptance are now complete; historical statuses below are superseded.

## Historical deployment plan and proof (superseded, retained)

# Redshift MCP synthetic POC deployment plan

## CURRENT — approved complete run-from-package recovery

Status: Ready for Validation

User-directed deployment21:17:22EDT; Goff approved supported local ZIP package
mode on the SAME App Service. Build/stage a complete Linux/Node24 package from
frozen reviewed source and lockfile, including production node_modules and
reviewed dist. Only WEBSITE_RUN_FROM_PACKAGE=1 and
SCM_DO_BUILD_DURING_DEPLOYMENT=false may change; deployment-induced recycle
authorized, no standalone restart/new infrastructure/permissions. No Oryx
seed restoration or broken-leaf rebind. Official focused validation, exact
implementation/artifact review, azure-deploy, single bounded supported ZIP
deployment and actual package/health/MI oil+same-cookie gas acceptance required.
Official focused validation and exact implementation/artifact review are now
required; no cloud mutation before completion. Previous candidates/failures retained below.

### Current All validation checks pass

- [ ] Core validation: current authenticated context, frozen source, existing
  app/runtime/scoped roles, only two planned setting changes, local cache off,
  no overlapping deployment, policy baseline preservation. Infrastructure
  bootstrap/Bicep/ARM what-if N/A: no resource deployment or topology changes.
- [ ] Docker build: target app is not a container deployment; Docker is used
  solely as an existing Linux-amd64 Node24 artifact builder/test runner.
  Complete-package lockfile build/prune/native/import/read-only startup checks
  required; MCP image build is N/A and MCPv3 must remain exact.
- [ ] Azure Policy validation: current assignments and reviewed unchanged
  definitions, current existing-resource scoped permissions; no grants.
- [ ] Exact package/controller/helper implementation and artifact reviewed by
  one independent GPT6.1-sol reviewer; focused helper regression tests.
- [ ] Record real source ZIP AND distinct complete runtime ZIP/manifest hashes,
  no source/runtime fingerprint conflation; old file-rebind guards N/A.

## Dependency recovery execution candidate — BLOCKED / NOT Validated

**Checkpoint requested21:09:52EDT: investigation stopped; no mutation.**
No authentic matched production dependency archive/manifest pair has been
retrieved or staged. SHA256s are **NOT AVAILABLE**, not invented. Confirmed
actual startup needs `/home/site/wwwroot/oryx-manifest.toml`; its compressed
dependency file must be named by that authentic manifest. The proposed normal
pair is `node_modules.tar.gz` plus `oryx-manifest.toml`, but an actual retained
manifest has NOT established its compressed filename yet. Both proposed
shared-root seed paths returned ENOENT in the preceding diagnosis.

Only exact successful deployment41631de7-c24a-4669-9c26-756fdb4753ea and frozen-
source build9c404952-a780-43c9-ae24-3ec7a597b52f were targeted for provenance.
The read-only log parser encountered an optional null details_url and stopped;
no claim that all retained artifacts were searched or no copy exists. No
broader traversal, new diagnostic loop, remote write or package installation.

### Concrete build/delivery candidate for Goff — not authorized execution

If a matched pair is unavailable, the supported build alternative is an
**authentic Oryx Node24 build from the exact frozen source ZIP/lockfile**, not
a fabricated manifest or an isolated one-package install. On an existing,
compatible isolated Linux Oryx builder, after validating tool/version
availability and source pins, use this candidate command (not run):

```bash
TMPDIR="$PWD/deploy/.chat-artifacts/dependency-recovery/scratch" \
oryx build "$PWD/deploy/.chat-artifacts/dependency-recovery/source" \
  --output "$PWD/deploy/.chat-artifacts/dependency-recovery/output" \
  --intermediate-dir "$PWD/deploy/.chat-artifacts/dependency-recovery/intermediate" \
  --platform nodejs --platform-version 24.22.1 \
  -p compress_node_modules=tar-gz \
  --log-file "$PWD/deploy/.chat-artifacts/dependency-recovery/build.log"
```

`source` must be safely extracted from the already-reviewed ZIP
`redshift-chat-2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c.zip`
(SHA256 `cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429`);
verify all20 entries/unchanged lockfile first. Builder availability, exact
installed Oryx options and Node24 compatibility are **not yet validated**.
No install/new builder resource is authorized by this planning assignment.
Oryx may restore dependencies in its isolated build; no local/on-app install
has been performed. Stage the generated pair, record actual SHA256/size/build
provenance and manifest-selected filename, verify tar paths/links/no secret
files and locked2.9.0/transitives/importability before delivery eligibility.

If generated manifest really names `node_modules.tar.gz`, the exact supported
delivery commands proposed for independent review are:

```bash
az webapp deploy --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c \
  --resource-group rg-redshift-bs01 --name app-redshift-chat-bs01-bb4b2781 \
  --type static --src-path deploy/.chat-artifacts/dependency-recovery/output/node_modules.tar.gz \
  --target-path /home/site/wwwroot/node_modules.tar.gz \
  --clean false --restart false --track-status false --async false --timeout 120000
az webapp deploy --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c \
  --resource-group rg-redshift-bs01 --name app-redshift-chat-bs01-bb4b2781 \
  --type static --src-path deploy/.chat-artifacts/dependency-recovery/output/oryx-manifest.toml \
  --target-path /home/site/wwwroot/oryx-manifest.toml \
  --clean false --restart false --track-status false --async false --timeout 120000
```

Do NOT run either while artifact hashes/provenance remain unavailable. After
concrete Goff approval and focused official validation, invoke azure-deploy
before any delivery. Archive terminal success and actual target hash must
precede manifest delivery; each gets its own operation proof. App settings,
roles, agent2/MCPv3, source/backend/UI bytes and node_modules link untouched.
Readonly eligibility must establish exact leaf/parent identities, no active
deployment, preservation pins, and absent or safely backed-up destination
bytes; ENOENT metadata alone is not sufficient with this known filesystem
anomaly. No broad cleanup or old executor.

`--restart false` suppresses a requested postdeployment restart; it is **not**
a guarantee that an already-crashing platform will not automatically recycle/
retry startup. Manifest publication can affect its next cold start; the
generated Oryx script replaces ephemeral `/node_modules`. Goff must review
this implicit activation and non-atomic two-file-pair risk. No second explicit
restart is authorized. Observe readiness for at most10minutes after terminal
delivery; if activation does not occur, stop rather than restart.

First acceptance is dependency import/listen/healthz/fresh connected health,
not HTML recovery. The independently broken client HTML leaf may remain;
keep its repair and cosmetic/numerical release gates separate. Fail once on
delivery ambiguity, changed target, missing imports or continued503; no
automatic retry/revert. Retain any prior readable bytes before replacement;
reversion itself requires reviewed authorization, never blind deletion.

**Current executable restoration is BLOCKED:** no authentic pair/hashes,
unvalidated existing Linux builder, and unresolved shared-root ENOENT fault.
Do not repeat the already-failed full ZIP mechanism. If no approved safe pair
delivery is available, the precise alternative is Azure App Service support
restoring dependency-seed visibility/worker cold-start state and investigating
the exact wwwroot ENOENT boundary, correlation
`5ffe6c98-f754-43cb-b5ba-ae1c807e9f4d`. No extra resource, grant, setting or
second restart is implied. This is a fixed review checkpoint, not an open-ended
investigation or a claim of Ready for Validation.

## PRIORITY: chat outage startup diagnosis — complete, awaiting recovery review

**2026-10-27T01:05:43Z — outage unresolved; NOT Validated.** One bounded,
read-only ARM/SCM investigation (no SSH) established a concrete application
startup failure, not merely an unknown worker outage:
**`ERR_MODULE_NOT_FOUND: Cannot find package '@azure/ai-projects' imported from
/home/site/wwwroot/dist/server/providers.js`.** Actual startup repeatedly runs
Oryx → `npm start` → `node dist/server/index.js` → Node24 failure/exit1.
Oryx explicitly reports the build manifest missing before each failure.
Latest extracted occurrence:01:02:28.599Z.

Exact shared-root metadata: `node_modules` is a symlink to `/node_modules`;
its `@azure/ai-projects` package, `node_modules.tar.gz` and
`oryx-manifest.toml` return ENOENT2 through SCM. This is SCM's namespace, not
proof about the worker's ephemeral `/node_modules`; the actual worker log
independently proves package resolution fails. Remote package.json still pins
2.9.0; actual compiled index/providers are readable and match reviewed hashes.
Static ESM imports run before index.ts's try/catch/listen. `/healthz` does not
read client HTML, so the existing index.html fault alone cannot explain this
startup failure. Physical deletion versus SMB invisibility remains unproven.

ARM site Running/Normal, one instance; ResourceHealth Available reported
01:01:33.344Z (latest advertised GA API2026-07-01). ARM processes returned429,
SCM process API503: neither retried. Restart activity is Succeeded00:48:11.844Z,
correlation **5ffe6c98-f754-43cb-b5ba-ae1c807e9f4d**. This proves control-plane
acceptance, not healthy application startup. Before snapshot01:01:20 timed out;
after01:02:25 HTML/health routes503; final01:05:34 requests timed out. No
healthy claim, extra restart, upload, install, settings or resource mutation.

**Recovery candidate, NOT approved/executed:** restore a matched, lockfile-pinned
Node24 production dependency archive AND authentic generated Oryx manifest,
using reviewed supported static artifact delivery to only
`/home/site/wwwroot/node_modules.tar.gz` then `/home/site/wwwroot/oryx-manifest.toml`,
clean=false/restart=false. Archive alone is insufficient: Oryx extraction is
manifest-gated. Preserve application/UI/backend bytes and settings; do not
change the node_modules link or install one package ad hoc. Exact builder,
archive safety, installed Oryx compatibility, leaf visibility, backup/abort
rules, hard pins and command/gates need Goff review and focused official
validation/deploy workflow before any write. Observe only existing platform
startup attempts afterward; no second explicit restart authorized. Full
dependency import/health, preservation and eventual numerical/session gates
remain mandatory. If supported leaf delivery cannot safely address the shared
filesystem fault, escalate the precise seed-path/SMB and startup evidence to
Azure support with the correlation above rather than retrying blindly.

Evidence: `deploy/.chat-artifacts/outage-startup-diagnosis-proof.json`,
`outage-startup-dependency-layout-proof.json`, `outage-startup-final-evidence.json`.
No raw logs/provider bodies/authentication saved. Detailed review candidate
and limitations are in St. Brown's existing repair inbox. Historical failed
deployments, prior restart proof, null verified markers and blocked validation
remain unchanged. Cosmetic release is subordinate to outage recovery.

## User-approved single restart — recovery NOT established, 2026-10-27T00:57:19Z

**Operational result: BLOCKED; NOT Validated; final release incomplete.**
The user explicitly selected “Restart the chat App Service and continue repair”
after disclosure of brief UI interruption and reset of in-memory conversations/
rate state. The coordinator supplied Goff's independent approval for this exact
bounded restart; no historical file-repair review is represented as restart
approval. Exactly one supported `az webapp restart` explicitly targeted
subscription `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, `rg-redshift-bs01`,
`app-redshift-chat-bs01-bb4b2781`, at **00:48:10.195Z**; CLI accepted
**00:48:12.025Z**. This acceptance is not proof of process replacement.

Pre-restart public HTML/process routes were200; initial DB health was stale,
not fresh. After the call, fresh connected public health briefly passed at
00:49:03, checkedAt00:48:50.676Z. Subsequent public transport failures are
retained. Final **00:57:19Z** observations returned **HTTP503** for `/`,
`/index.html`, `/healthz`, `/api/health`, and both known JS/CSS asset paths.
Read-only observation finished within the fixed ten-minute maximum
(deadline00:58:10.195Z); no additional restart or deployment is pending.

Actual BFF identity was still the pre-call PID/start identity at00:49:44.
Later fresh SSH attempts were unreachable, so **worker process replacement is
unproven**, not a proven missing or replaced process. SCM's namespace/parent
identities changed, but its final absolute AND dirfd `O_NOFOLLOW` HTML opens
still returned **ENOENT2**; parents were real directories with exact strict
realpaths. Four-read worker/SCM convergence therefore FAILED. The underlying
physical SMB/storage or startup cause remains unproven.

Actual post-call preservation checks passed: configuration/scoped permissions,
all20 source/eight compiled files, agent2/MCPv3, deployment records and local
state unchanged. Earlier failed deployments remain FAILED, verified markers
null, approved executor/worker/tests untouched, and backup absent. No upload,
file repair, settings/grants/network/resource changes, rollback, marker
reconciliation or numerical/session acceptance occurred. Official validation
still stops at RecordProof/ResolveErrors; **do not mark Validated**.

Proof: `deploy/.chat-artifacts/appservice-restart-final-proof.json`, with the
exclusive `appservice-restart-20261027-operation.json`, before/after preservation,
after1/after3 actual observations, retained failed after2 checkpoint, bounded
readiness and final-public proofs. Fingerprints are retained as private digests.
Next safe avenue: platform-assisted exact-leaf storage/worker-startup diagnosis
using this evidence and safe structural error allowlists; no second restart,
guard weakening, automatic retry or deployment. Static delivery requires a
separately recovered worker, actual four-read convergence and focused official
validation before its own terminal/asset/acceptance gates.

## Current repair revision — focused validation BLOCKED, no apply

**Current status: BLOCKED / NOT Validated — 2026-10-27T00:34Z.**
The exact approved revision was operated read-only, not altered. Its real worker
probe FAILED before any mutation: `FileNotFoundError`, errno2, replace-attempted/
completed bothfalse. Independent fixed read-only syscall classification
established the precise current failing operation:
**worker `openat(client_fd, 'index.html', O_RDONLY|O_NOFOLLOW)` returns ENOENT2**,
although its relative stat reports regular623/inode5418 and its absolute read
still returns the OLD public hash. Parent relative opens succeed. SCM also
remains unopenable. This mandatory guard failure cannot be waived to deploy.

**No invented drift:** worker namespace remains `mnt:[4026532645]`, dev72,
parents5361/5369/5417, target5418. Actual BFF remains PID1928 with exact
`node`, `dist/server/index.js` argv; newly sampled start ticks **1811687**
are a current observation, not a historical pin. Exclusive backup is absent.
The previously recorded worker absolute reads did not establish the now-tested
dirfd-relative open contract. Do not describe this as proven PID/mount drift.

No apply gate or operation journal was created; no azure-deploy/apply/upload,
restart/retry/revert/cleanup, remote write or marker reconciliation occurred.
No new-bundle numerical/session acceptance was run. Existing source/ZIP/
state/null markers/agent2/MCPv3 remain unchanged. The transient preflight
`/api/health`503 was retained; subsequent fresh health was healthy/connected,
checkedAt **00:30:14.224Z**, with exact OLD public HTML and expected assets.
Final read-only public preservation also passed at00:36Z with fresh
healthy/connected checkedAt **2026-10-27T00:36:32.572Z**; proof
`path-repair-final-public-preservation-proof.json`. This does not resolve
the mandatory relative-open failure or authorize a new mutation.

### Section 7: Validation Proof — approved R1–R3 actual focused attempt

- Official workflow invoked without completion argument, then followed printed
  LoadPlan/AddValidationSteps/RunValidation/BuildVerification/
  StaticRoleVerification actions. Actual failure recorded before any
  Validated/apply claim. RecordProof is completed only after this real evidence;
  unresolved failure must stop at ResolveErrors, **not UpdateStatus**.
- Exact controller/worker/tests hashes equal Goff's approved
  `b85e6dc5364866ff28244750e88c4b1b4b8590db98dc5c4c72b3e91b0ddb60b1` /
  `5a9bfd6ca8a27b2b1774c8e50d76c4c29523d2404024cd48621b5c21319a2207` /
  `d93f573952c179ff8ac0d677bb2585b812470d5b6330c75a517f9b6a1c839217`.
  No authoring/modification of these files.
- `deploy/.venv/bin/python -B deploy/chat_deploy.py --stage check`: PASS.
  Audited existing preflight executed unchanged with only its operational proof
  write destinations routed to `path-repair-{preflight,policy-roles}-proof.json`:
  current context/configuration, actual agent2/MCPv3, exact app/registry/
  single-secret scopes and all11 policy fingerprints PASS. No grants/settings.
- Approved controller's read-only `frozen`/`live` checks PASS: exact frozen
  source/ZIP/all20 remote source/eight compiled files, disabled SCM+FTP basic
  publishing, no incomplete deployment, old static failure still terminal.
  State canonical SHA remains
  `8e298ec3462259d58eebca1f174cfe58dce1e8b0ac10117152c3de69e8ecf1db`.
- Read-only approved `--probe` through existing Entra worker transport: **FAIL**
  above; safe result retained. Separate read-only syscall/proc classification
  positively identifies worker relative leaf open ENOENT2, unchanged process/
  namespace/parents, fresh actual start ticks, exact argv and backup absence.
  No apply was attempted to investigate this failure.
- Initial use of CLI Python for mixed helper preflight found its missing
  `azure.identity` visibility; project Python lacked `azure.cli`. Both existing
  interpreters are Python3.13.17. Read-only preflight then used existing CLI
  packages via process-only PYTHONPATH with project Python; no installation,
  restore, credential/configuration/app-setting or approved-artifact change.
  This tooling observation is not the application/path root cause.
- BuildVerification rechecked the frozen20-entry ZIP/source, reviewed eight
  compiled hashes and generated623-byte HTML/JS/CSS. Prior unchanged
  **101chat/68helpers/typecheck/build** proof and exact reviewed **47 guard
  tests plus Goff3 adversarial methods** retained; no unrelated suite/build/
  restore. Docker/MCP build/ARM bootstrap what-if N/A.
- Static role code review confirms project Consumer/User and registry-scoped
  pull assignments; existing single-secret role preserved by current exact-role
  check. No infrastructure or role-code edits.

Current attempt proof:
`deploy/.chat-artifacts/path-repair-approved-current-preflight-proof.json`,
`path-repair-current-worker-drift-proof.json` (its actual data records NO drift),
`path-repair-current-syscall-boundary-proof.json`,
`path-repair-focused-build-proof.json`,
`path-repair-preflight-health-observation.json`,
and `path-repair-{preflight,policy-roles}-proof.json`.
Earlier failed health/tooling observations remain separately retained.
Approval below stays historical approval, not successful validation.

### All validation checks pass — approved R1–R3 focused repair and conditional static delivery

- [ ] Core Validation (CLI, auth, build, validate, what-if): actual unchanged
  source/ZIP/agent/backend/executor pins, current target/configuration/scoped
  roles/policy, no overlapping deployment, fresh read-only worker process
  start/argv/parents/old target/exclusive backup absence and SCM discrepancy.
  Prior unchanged101chat/68helpers/build proof retained; Docker/ARM/infra
  build/what-if N/A to this existing single-file operation.
- [x] Docker Build (if containerized): N/A; verified unchanged MCPv3 digest/revision.
- [x] Azure Policy Validation: current exact definition/scope/enforcement
  fingerprints, no resource/location/exemption changes.
- [x] Build Verification: exact frozen ZIP/all20/source and reviewed generated
  HTML/JS/CSS/eight compiled hashes; exact approved47guard/Goff3adversarial
  proof; no source build/restores.
- [x] Static Role Verification: unchanged project Consumer/User, registry-only
  pull, single-secret vault roles; no template/role changes.
- [ ] Record Proof / Resolve Errors / UpdateStatus: real focused proof first,
  official workflow completed before new Validated/apply-gate assertion.

**Ready for Validation / APPROVED WITH GATES / NOT Validated — 2026-10-27T00:21:52Z.**
Goff approved ONLY Sewell's independently revised repair and the unchanged
conditional one-file static delivery, with mandatory gates recorded in
`.squad/decisions/inbox/goff-appservice-path-repair-review.md`.
The original v1 rejection/hashes remain there as historical evidence.
Sewell independently revised only the ignored local controller/worker/guard
tests for R1 object identity, R2 exact argv/fresh process start identity, and
R3 read-only inspection after ambiguous apply. St. Brown did not participate;
the independent revision cycle is now approved, not live-validated.

Exact revised hashes, fix map, limitations and local evidence:
`.squad/decisions/inbox/sewell-appservice-path-repair-revision.md`.
Goff independently recomputed all three exact revised hashes and ran
**47 focused tests plus3 independent adversarial test methods**, including
four identical-byte substitutions, actual process-stat/argv guard drift,
and ambiguous apply through the actual offline-mocked transport wrapper.
Actual default and
explicit dry-runs under a rejecting audit hook observed zero network,
subprocess, mutation, write-open or credential-read attempts.
The focused official validation proof and apply journal remain absent.
No remote probe/apply, upload, restart, source/ZIP/agent/MCP/state changes or
new verification claim occurred. Prior evidence/status sections below are
historical and do not validate the revised executor.

Next: focused official azure-validate and azure-deploy gates for the exact
approved hashes; only actual worker/SCM absolute AND dirfd O_NOFOLLOW OLD-byte
read convergence, repeated cold SCM reads after TTL within an evidenced
at-most10second observation window, and unchanged public/health/preservation permit
the already-reviewed conditional one-file NEW-HTML delivery. No delivery was
executed. Individual executor request timeouts/success labels do not establish
that external timing gate. Its own terminal success, target/public assets,
all20 sources/all8 compiled files and preservation must precede narrow truthful
composite reconciliation and the unchanged full app-MI oil/fresh same-cookie
gas/session verifier. No extra customer approval is needed for unchanged scope.
All failed deployment records and null verification markers remain.

## Historical exact-path diagnosis — before revised repair approval

**Historical status at diagnosis: BLOCKED; read-only diagnosis complete.**
The revised repair is now approved with gates above, but remains NOT Validated
and cannot execute before those gates. User's 23:34:19Z diagnosis/repair
request explicitly requires peer review before filesystem writes/restarts.
Prior static-mechanism validation below is historical; its operation FAILED.
No further upload, remote write, restart, source/backend/configuration/
resource/grant/network/credential change or state reconciliation occurred.

Actual evidence through **2026-10-26T23:51:57Z**:

- The exact three parents `/home/site/wwwroot`, `/dist`, `/dist/client`
  positively are real directories in **both** views: lstat/strict realpath
  checked; no dangling-parent symlink. Actual worker HTML is a regular
  623-byte file whose read hash matches the OLD public HTML. SCM cold lstat,
  readlink, strict realpath and actual open return ENOENT2.
- Proven separate CIFS mounts: SCM namespace `mnt:[4026532811]`, dev74,
  mount1809; worker `mnt:[4026532645]`, dev72, mount2164. Same captured
  mount-source identity digest, both rw, SMB3.1.1/cache=strict/actimeo=1.
  Actual BFF PID1928 (`MainThread`), approved `node dist/server/index.js`,
  cwd `/home/site/wwwroot`, worker namespace. Approved compiled module
  resolves actual root `/home/site/wwwroot/dist/client/`; per-request open.
- Precise paired SCM probe: initial lstat ENOENT; enumeration hydrates regular
  623-byte metadata and immediate absolute/dirfd lstat can succeed; **actual
  dirfd O_RDONLY|O_NOFOLLOW open STILL returns ENOENT2**. Thus a listing or
  warm stat is not proof the destination is openable. Exact ASCII filename
  confirmed. Force-sync statx still fails in SCM but succeeds in worker.
- This establishes the cross-mount pathname/open fault boundary, **not the
  underlying SMB/cache/server physical cause**. No EACCES/EROFS observed;
  mode/rw metadata is not a successful write test. Exact receiver temporary
  leaves absent; forbidden ephemeral staging paths were not operated on.
- Public `/`, `/index.html`, `/healthz` HTTP200; HTML remains OLD hash
  `8b2ff9fbc51c2f0dc987260333d6ce3919eb5ba502d84db379692c9c5b277cd1`.
  Fresh DB **healthy, connected=true**, checkedAt **23:50:08.220Z**.
  Current static failure remains terminal3/complete/inactive. No incomplete/
  running deployment observed; an old complete successful `active=true`
  Kudu artifact record is not a running deployment.
- Source `2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c`
  and ZIP `cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429`
  freshly exact; operational state unchanged, verified fields null.
  Agent2/MCPv3 untouched. No new-bundle oil/gas acceptance claimed.
- Parent ResourceHealth Available at23:36:03Z; AppLens401 is a diagnostic-tool
  limitation, not app-identity failure. No enabling grants/configuration.

Peer-review proposal and exact paths/commands/backup/reversion/stop gates:
`.squad/decisions/inbox/st-brown-appservice-path-repair.md`.
Recommend one worker-side atomic rebind of the exact HTML **using the existing
OLD working bytes**, with exclusive resolved backup
`/home/site/wwwroot/dist/.html-path-repair-20261026/index.html.before`.
No parent replacement, chmod/chown, cleanup, restart or new-copy upload by
the repair executor.
Its success requires restored **actual SCM AND worker open/read** with unchanged
public bytes; otherwise stop for exact-leaf platform SMB query/open comparison,
not speculative retries. **Goff's current review should cover BOTH repair
and conditional delivery** of the unchanged reviewed new HTML after actual
path convergence; the user already authorized retry/repair, so no additional
user-approval roundtrip is required. Focused official validation/deploy, own
terminal proof and unchanged
full managed-identity numerical/session acceptance before verification markers.
Sanitized evidence: `deploy/.chat-artifacts/path-repair-*-proof.json`.

### Exact executor prepared LOCALLY ONLY — 2026-10-27T00:08:53Z

Still **awaiting Goff review / not Validated / no remote mutation**.
Ignored `deploy/.chat-artifacts/path-repair-executor.py` SHA-256
`7f02edc5ee7dd6d959d8361496a7256e21f11d55d6e835ad551ffb29623daace`;
fixed worker payload `path-repair-worker.py` SHA-256
`33c2b8e9727a0436d62e0338f74076360cb5daeb97e71d76367cffca9a7d03f9`.
Exact implementation/test hashes, future official proof schema and review-only
apply command are in St. Brown's scoped repair inbox above.

- Default/explicit dry-run is genuinely local-only. Actual dry-runs passed
  immutable source/ZIP/all20/local reviewed eight compiled/generated assets/
  unchanged state/null-marker checks; payload compile/pin passed.
- **29 in-memory/mocked guard tests passed**. No real mutator or network call
  in tests. Actual default dry-run under rejecting CPython audit hook observed
  **zero** attempted network/subprocess/mutation/write-open/credential reads.
- Explicit real apply requires all three approval/gate flags and fresh new
  scope/hash-bound official validation proof; that proof **does not exist**.
  No apply operation journal exists; no real apply was executed.
- Executor implements old-byte-only exclusive backup/stage, O_NOFOLLOW/
  fstat/dirfd/realpath/fresh-identity/size/SHA guards, file fsync, exactly one
  replace, actual absolute+dirfd worker/SCM opens, two cold SCM reads and public/
  connected-health preservation. No upload/retry/restart/revert/cleanup or
  marker writes. Real CIFS repair success is not claimed by local tests.

Proof: `deploy/.chat-artifacts/path-repair-local-review-proof.json`,
`path-repair-local-dryrun-proof.json`, `path-repair-audited-default-proof.json`,
`path-repair-local-tests.log`. No unrelated suites or dependencies rerun/
restored. No production code, MCP README, app-state or cloud changes.

## Approved one-file static recovery — focused mechanism revalidation

**Status: Validated; approved static recovery terminal FAILED — release BLOCKED.**
Same frozen source/ZIP/623-byte HTML; Goff
approved the exact Entra-only static upload and strictly bounded composite
reconciliation at **2026-10-26T23:15:36Z**. Binding constraints and review are
preserved below. No restart, rebuild, new artifact, source/backend/configuration/
resource/grant/network/credential changes. Prior failed ZIP records stay FAILED.

### All validation checks pass — approved static mechanism

- [x] 1. Core Validation (CLI, auth, build, validate, what-if): fresh existing
  context/inventory/settings/roles/agent/MCP, idleness and disabled basic auth;
  exact local frozen source/ZIP/HTML plus 20 remote sources/eight compiled files.
  Prior unchanged 101/68 suite/typecheck/build proof retained; no rebuild/restore.
  ARM/bootstrap what-if N/A (no infra changes).
- [x] 2. Docker Build (if containerized): N/A one static file; MCP digest/
  revision/protected configuration unchanged.
- [x] 3. Azure Policy Validation: current policy fingerprint preservation;
  no new resources, locations, exemptions or configuration.
- [x] Build Verification: verify existing reviewed generated HTML/JS/CSS and
  eight compiled files, source-addressed ZIP bytes/scan; no build is authorized.
- [x] Static Role Verification: unchanged project Consumer/User, ACR pull and
  single-secret vault scopes, and Entra-only existing CLI static mechanism.
- [x] Record Proof / Resolve Errors / Update Status: actual focused proof first;
  official workflow completion before azure-deploy/static mutation.

### Section 7: Validation Proof — focused approved static mechanism

Actual checks completed **2026-10-26T23:21:52Z** before static upload. Followed
official LoadPlan/AddValidationSteps/RunValidation/BuildVerification/
StaticRoleVerification actions; no new Validated claim until final status action.

- Fresh `deploy/.venv/bin/python -B deploy/chat_deploy.py --stage check`: passed
  current subscription/tenant, supported GA APIs, Node 24, existing resources/model.
  Existing `ui-copy-preflight.py`, with proof filenames only redirected in memory
  to `static-recovery-*`, passed inventory/settings, agent 2, MCP v3, exact app/
  ACR/single-secret roles, CORS/protected config and **11** current policy
  definition/scope/enforcement fingerprints. Fresh policy MCP retrieval succeeded.
- New operation-specific ignored hard-pinned `static-recovery-evidence.py before`
  passed: frozen source
  `2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c`;
  ZIP `cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429`;
  **20/20** reopened ZIP entries and actual remote source bytes; **8/8**
  compiled server bytes; existing reviewed HTML **623 bytes** / SHA-256
  `ef3adcb74301dda22edf7d066480676da0697a2d8f3c1c4ae9ae74c6f1377e20`.
  New public JS hash
  `0c8f0fc0c74040c17f0d24e7f093e50e609097bb5a838c85eaeb76f1c53c2d20`;
  unchanged CSS hash
  `a4e5952744af999a5ca69665755f1347ace925c84d93327eddf2d585ee8bc6b5`.
- Disabled SCM/FTP basic publishing rechecked; current helper uses Entra, no
  publishing credential fallback. No incomplete tracked deployment; latest is
  the old terminal failed recovery. Prior state snapshot/hash and deployment
  IDs retained separately; source/agent/configuration/roles unchanged.
- BuildVerification explicitly rechecked reviewed generated HTML and all eight
  compiled hashes against the snapshot and prior source validation. Unchanged
  **101 chat / 68 helper tests, typecheck/build** proof retained from 22:52;
  no rerun claimed. Rebuild, package restore, Docker and bootstrap ARM/what-if
  **N/A** to the approved single-static-file mechanism and are not authorized.
- Static review: unchanged project-only Consumer/User, registry-only AcrPull,
  single-secret Secrets User. No template/role edits. Goff's exact static-copy
  mechanism approval and zero-restart/zero-cleanup conditions read in full.

Proof: `deploy/.chat-artifacts/static-recovery-{preflight,policy-roles,before}-proof.json`;
prior allowlisted state at `static-recovery-prior-state.json`. Existing frozen
ZIP/source/build/test history and both failed ZIP proofs retained. This is
focused mechanism validation, **not static deployment or hosted acceptance**.

### Actual bounded static recovery — terminal failure, 2026-10-26T23:26Z

Official focused azure-validate completed **2026-10-26T23:22:31Z**, then invoked
azure-deploy before the sole approved mutation. Rechecked actual current context,
unchanged state/pins, disabled SCM basic publishing and deployment idleness.
Executed the EXACT independently approved one-file command through existing
`chat_deploy.cli`: static HTML only, exact target, clean=false, restart=false,
track-status=false, async=false, timeout=120000. No settings/provision/agent/MCP/
image/grant/resource/credential/network/build/restore/restart stage.

- New static operation **e0607d31-6943-4878-9f17-be9f401fcf1c** was independently
  correlated as the sole new deployment ID after the captured prior ID set,
  within this isolated operation's start-time window. CLI returned failure.
  Queried that exact ID to terminal: **status 3, complete=true, active=false**;
  start **2026-10-26T23:23:26.0021144Z**, end
  **2026-10-26T23:23:28.224922Z**.
- Exact sanitized cause:
  `rsync: [receiver] open "/home/site/wwwroot/dist/client/index.html" failed:
  No such file or directory (2)`; rsync **exit 23**.
  No actual Oryx/npm compilation, restore or pruning occurred. This independent
  static-copy failure narrows the blocker to opening the destination HTML,
  not compilation/dependencies. Deeper filesystem/mount/path-resolution cause
  remains unproven; no filesystem hack, unlink, chmod, parent replacement,
  extra attempt, cleanup, rollback or restart was authorized/performed.
- Actual postfailure inspection completed **2026-10-26T23:26:21.046814Z**:
  **20/20 remote sources** and **8/8 compiled server files** still exactly match
  reviewed frozen bytes. Direct target HTML remains **Kudu HTTP 404**.
  Public `/`, `/index.html` and `/healthz` are **HTTP 200**. Both public HTML
  routes still have OLD hash
  `8b2ff9fbc51c2f0dc987260333d6ce3919eb5ba502d84db379692c9c5b277cd1`
  and reference the old JS containing **Redshift Explorer**. Public new JS and
  unchanged CSS remain HTTP 200/exact reviewed hashes but are not enough to
  claim release. No-store/target alignment success is not claimed.
- First read-only postfailure collection saw `/api/health` **HTTP 503**; retained
  as an actual observation, no raw body or causal inference. Later collection
  observed stale then **healthy, connected=true**, fresh checkedAt
  **2026-10-26T23:25:40.775Z**. This health recovery does not repair delivery.
- Fresh postfailure inventory, app project-only Consumer/User, settings,
  TLS/disabled SCM+FTP basic publishing, registered agent **2**, MCP **v3**
  protected configuration/revision/CORS passed. Preupload ACR/single-secret
  exact roles passed; no role writes. Agent and MCP hashes remain as below.
- Entire allowlisted state still equals its captured pre-static snapshot.
  **NO marker reconciliation was performed**, and both verified fields remain
  **null**. No full new-bundle oil/gas verifier was run: own static terminal
  success, exact direct target and public alignment gates FAILED. Old successful
  decoder acceptance and both FAILED ZIP records retain their historical status.

Separate operation proof: `deploy/.chat-artifacts/static-recovery-upload-proof.json`.
Actual live/state proof: `static-recovery-terminal-live-proof.json`.
Prior state retained: `static-recovery-prior-state.json`. New source/ZIP remain
frozen at `2a6ff854…` / `cd4ce8db…`; no successful static/composite provenance or
new acceptance marker is fabricated. This approved bounded recovery is finished
with a verified **terminal failure**, not “initiated” or still pending.

## Final neutral assistant speaker label — source-only copy release

**Status: Validated; deployment BLOCKED — terminal recovery failure, not live-verified.**
Independent St. Brown review APPROVE:
`.squad/decisions/inbox/st-brown-ui-copy-release.md`. Only the assistant label in
`client/components.tsx` differs among all 20 runtime entries from the last
successful decoder ZIP; the rendered regression test asserts the new speaker
span and absence of old branding. Every other runtime byte is unchanged.
Reviewed source: `2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c`.
Existing resources/regions/roles and accepted synthetic public/admin POC risks
remain user-confirmed. No configuration/provisioning/agent/MCP changes.
New bundle runtime acceptance is blocked by terminal Oryx output-copy failure;
the responsive public app still serves the previous bundle and old speaker label.
Prior verified proof below is retained; it does not verify this new copy release.

### All validation checks pass — final UI copy

- [x] 1. Core Validation (CLI, auth, build, validate, what-if): current existing
  preflight/inventory, 101 chat tests, Node 24 typecheck/build, 68 helper tests.
  Bootstrap ARM validation/what-if N/A: no infrastructure change.
- [x] 2. Docker Build (if containerized): N/A chat-only source ZIP; verify
  existing MCP v3 digest/revision/protected configuration unchanged.
- [x] 3. Azure Policy Validation: fresh applicable assignment/definition
  comparison against previous reviewed baseline; no policy changes.
- [x] Build Verification: old packager rejects new source; freeze correctly
  pinned new helper/ZIP, reopen every entry and scan selected files.
- [x] Static Role Verification: unchanged project Consumer/User, ACR pull,
  single-secret vault scopes; no role writes.
- [x] Record Proof / Update Status: actual new artifact evidence before
  Validated; separate mandatory real hosted acceptance after deployment.

### Section 7: Validation Proof — final UI copy

Actual proof recorded **2026-10-26T22:52:31.598462Z**, before cloud mutation.
Official azure-validate LoadPlan → AddValidationSteps → RunValidation →
BuildVerification → StaticRoleVerification actions completed in order.

- `deploy/.venv/bin/python -B deploy/chat_deploy.py --stage check`: passed.
  Fresh existing inventory/settings/live exact scopes and agent GET passed;
  unchanged project Consumer/User, ACR pull and single-secret vault roles.
- New ignored `ui-copy-package-reviewed.py`: hard-pins independently reviewed
  source and agent 2, proves only component label differs against previous ZIP,
  preserves previous ZIP/state, uses existing audited manifest/save_state APIs.
  Old decoder packager correctly rejected the new source before writes.
- Retained Node **24.22.1**, project-local TMPDIR and existing dependencies:
  **101 chat tests passed**, typecheck/build passed; printed BuildVerification
  action additionally reran build successfully (same tests, not extra cases).
  Existing `cd deploy && .venv/bin/python -B -m unittest -q test_chat_deploy`:
  **68 passed**. No restore/npm ci/unchanged MCP test run.
- New source SHA-256:
  `2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c`.
  New immutable ZIP SHA-256:
  `cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429`.
  ZIP: `deploy/.chat-artifacts/redshift-chat-2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c.zip`;
  **20 entries / 49,113 bytes**. Every reopened entry equals manifest bytes;
  audited allowlist/selected-file credential scan passed. No secret files read.
- Fresh policy MCP retrieval plus latest GA **2026-07-01** applicable/inherited
  assignment reads: **11** definitions/scopes/enforcement match prior reviewed
  baseline. Existing public synthetic-POC exceptions/MFA protections retained.
  This is source-only policy preservation, not a broad compliance assertion.
- Docker/MCP build and ARM/bootstrap validation/what-if **N/A**: unchanged
  infrastructure. MCP **v3** digest
  `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`,
  revision `ca-redshift-bs01--0000003`, protected hash
  `a87f7b2964a457d3a37de5631c60513acbe2330512b80117ce6affec435e7b94`
  and CORS unchanged. Agent **2** definition
  `8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20`.
- Static review reconfirmed `infra/chat-role.bicep` project-only Consumer/User,
  `infra/resources.bicep` ACR pull at registry, helper Secrets User at one secret.
  No templates/roles/configuration/network/credentials/resources were edited.

Proof: `deploy/.chat-artifacts/ui-copy-{preflight,policy-roles,validation}-proof.json`
and `ui-copy-package-validation.log`. Previous successful ZIP/agent pin/state
retained at `deploy/.chat-artifacts/ui-copy-rollback-20261026/`.
No runtime acceptance claimed for the new bundle at validation time.

### Terminal deployment/recovery outcome — final UI copy

Official azure-validate completed `UpdateStatus` **2026-10-26T22:52:57Z**.
Invoked azure-deploy before mutation, followed its existing AZCLI deployment/
recovery/verification guidance, and reconfirmed the approved subscription/tenant,
existing RGs and regions. New AZD environment/provision/bootstrap/migrations/
role/image/configuration stages were N/A. Only the unchanged helper's
`--apply --gates-approved --stage app` was executed.

- Initial deployment `54908fdf-90d9-4908-9ff9-9433daf6e38d` reached terminal
  Kudu **status 3, complete=true, active=false**, ending
  **2026-10-26T22:55:45.405378Z**. Oryx npm/build completed, but final output copy
  failed: rsync receiver rename to `dist/client/index.html`, **ENOENT (2)**,
  rsync **exit 23**. Existing dependency install also reported 1 moderate and
  3 high audit findings; not independently assessed or changed in this copy scope.
- One bounded recovery reused the identical frozen ZIP; no source/config/guard/
  grant change. Recovery `9c404952-a780-43c9-ae24-3ec7a597b52f` was inspected and
  waited to terminal state, **not merely handed off while pending**:
  **status 3, complete=true, active=false**, ending
  **2026-10-26T22:59:33.6210633Z**. Same exact terminal failure:
  rsync receiver rename of the generated HTML into `dist/client/index.html`
  failed with **ENOENT (2)**; rsync **exit 23**. No overlapping or further
  deployment, restart, permission change, rollback or unchecked retry.
- At resume **2026-10-26T22:58:13Z**, public `/` and `/healthz` were HTTP **200**.
  Final artifact inspection **23:00:05Z**: all **20** Kudu source entries match
  the reviewed new ZIP, but public HTML still references old
  `/assets/index-Cp4GJAH3.js` (HTTP 200, SHA-256
  `05b1e932e300b9920993b008d0e6d83a4e055ddadf436cb4a6a0539f19787cd0`).
  It still contains **Redshift Explorer**; it is **not** the reviewed new
  `/assets/index-BB76jn9J.js`. CSS remains exact/unchanged.
  Public HTML SHA-256:
  `8b2ff9fbc51c2f0dc987260333d6ce3919eb5ba502d84db379692c9c5b277cd1`.
  Kudu `dist/client/index.html` GET returned **404** after failure. Therefore
  source-copy presence is not accepted as successful deployment/served alignment.
- Final health inspection **2026-10-26T23:02:01.739675Z**: actual public database
  health **healthy, connected=true**, fresh checkedAt
  **2026-10-26T23:01:47.081Z**. Earlier stale responses are retained in proof.
  Fresh postfailure inventory/agent/settings/exact scopes and all 11 policy
  definitions passed; agent **2**, MCP **v3** image/revision/protected hash/CORS
  remain unchanged.
- New-bundle full oil/fresh same-cookie gas verification **not run**: terminal
  deployment failure and old served assets leave the existing deployed-source
  guard closed. No gate was bypassed, no new acceptance claimed.
  State retains new frozen source/ZIP, previous successfully deployed
  `77005490…` / `1e094ff7…` fingerprints, and **both verification fields null**.
  Historical prior oil/gas acceptance below remains historical.

Sanitized terminal evidence:
`deploy/.chat-artifacts/ui-copy-recovery-terminal-proof.json`,
`ui-copy-deployment-failed-proof.json`,
`ui-copy-postfailure-{preflight,policy-roles}-proof.json`.
No raw Kudu/provider logs, tokens or cookies retained. A separately authorized
reviewed recovery for the Oryx destination-copy failure is required; this release
is **BLOCKED**, not pending, deployed-successful or complete.

### User-directed retry readiness — 2026-10-26T23:04:39.769Z authorization

User said “lets try again”; scope is only these same approved copy bytes.
Reread this plan and actual Section 7 proof, official `UpdateStatus` record,
reopened all 20 frozen ZIP entries and reconfirmed source/ZIP/agent 2 pins plus
live unchanged inventory/settings/agent/MCP. Prior official source validation
remains valid; no drift or new dependency/infra/MCP tests were introduced.

**No third blind ZIP deployment was started.** Current latest deployment remains
the terminal failed recovery above, no incomplete tracked deployment, worker
Running/Normal. Exact read-only diagnostics distinguish a misleading directory
listing from a recovered path: `dist/client` exists (directory, mode 777), and
the new JS exists/readable, but direct Kudu VFS HTML GET is **404** and a fixed
read-only `stat` of `dist/client/index.html` returns **exit 1 / ENOENT**, not
permission denied. Two previous Oryx builds succeeded and failed only at receiver
rename of generated HTML, **ENOENT (2), rsync 23**. The parent-directory/output
failure has not been demonstrated cleared; deeper filesystem/deletion cause is
unproven. Do not infer a storage corruption cause or perform cleanup/chmod/delete.

At **2026-10-26T23:09:31Z**, public `/` is HTTP 200 with the old HTML hash
`8b2ff9fbc51c2f0dc987260333d6ce3919eb5ba502d84db379692c9c5b277cd1`.
The NEW JS URL already returns HTTP 200 and exact reviewed bytes:
`/assets/index-BB76jn9J.js`, SHA-256
`0c8f0fc0c74040c17f0d24e7f093e50e609097bb5a838c85eaeb76f1c53c2d20`.
CSS is unchanged/exact. Thus only the served HTML pointer must be delivered;
the new JS does not need another upload/build. Process `/healthz` is HTTP 200.
Current health observations and timestamps are in the new readiness proof,
not inferred from the previous successful numerical run.

#### Minimal supported alternative — PROPOSED, NOT EXECUTED; independent approval required

Microsoft documents individual static-file deployment through `az webapp deploy
--type static --target-path`; installed CLI help confirms explicit target,
clean=false and restart=false. References:
https://learn.microsoft.com/en-us/azure/app-service/deploy-zip#deploy-individual-files
and https://learn.microsoft.com/en-us/cli/azure/webapp#az-webapp-deploy.

1. Reconfirm unchanged frozen pins, idle terminal deployment, exact current
   public new JS/CSS and all 20 frozen remote source bytes. Retain all old proof.
2. Deploy ONLY existing reviewed `src/redshift-chat/dist/client/index.html`
   (**623 bytes**, SHA-256
   `ef3adcb74301dda22edf7d066480676da0697a2d8f3c1c4ae9ae74c6f1377e20`)
   through the supported static-file mechanism to the existing absolute target
   `/home/site/wwwroot/dist/client/index.html`; no new ZIP or source file:
   `az webapp deploy --resource-group rg-redshift-bs01 --name
   app-redshift-chat-bs01-bb4b2781 --src-path
   src/redshift-chat/dist/client/index.html --type static --target-path
   /home/site/wwwroot/dist/client/index.html --clean false --restart false
   --track-status false --async false --timeout 120000`.
   Use the existing subscription-pinned sanitized CLI wrapper; no raw output.
   No application setting/credentials/auth/agent/resources/network change.
3. Wait terminal supported deployment success, then require exact public HTML,
   referenced JS/CSS and complete frozen source/unchanged compiled server bytes.
   Existing global build settings stay untouched; if this mechanism unexpectedly
   invokes Oryx/build/configuration work, fails, or changes any additional file,
   stop without cleanup, automatic rollback or another attempt.
4. **No fingerprint override.** Independently approve truthful deployment-state
   evidence reconciliation BEFORE any `save_state` update: the original ZIP's
   entire source manifest must match actual remote bytes, complete client build
   must match actual served bytes, compiled backend must remain exact, and the
   supported static delivery must be terminal successful. Do not pretend either
   failed ZIP deployment succeeded or replace helper guards. If this evidence
   model is not approved, no deployed fingerprint or success marker may change.
5. Only after approved actual deployment-evidence gates, run the unchanged full
   verifier with fresh independent Data API references, serialized rolling-window
   waits, actual app-MI exact 2025 oil/fresh same-cookie gas, strict protocol/
   session/roles/source/health checks. Only it can persist verified fields.

Risks: existing target-path/filesystem fault may also reject static deployment;
no guarantee of repair. A failed in-place HTML write could transiently affect
the root page. No restart is proposed, but any unexpected runtime interruption
must stop the operation. Static publication does not itself prove full ZIP
deployment or numerical behavior. No dependencies are restored; no BFF, source,
agent, MCP, CSS, JS, configuration or grants are edited. This mechanism change
awaits independent reviewer approval; current copy release remains **BLOCKED**.

New proof: `ui-copy-user-retry-{structural,filesystem,readiness}-proof.json`
under `deploy/.chat-artifacts/`. These are read-only diagnostics, not a third
deployment or hosted acceptance proof.
Final read-only inspection **2026-10-26T23:11:35.407633Z** reconfirmed all **20**
actual remote source files and compiled grounding exact (SHA-256
`ab9e826093080efc470e1a8890701839f9d1b899d00247481a9686deb07712fc`).
Actual fresh DB health **healthy, connected=true**, checkedAt
**2026-10-26T23:11:07.603Z**. Both verification fields remain null.

#### Independent mechanism approval — Goff, 2026-10-26T23:15:36Z

**APPROVE one static HTML recovery, with the following binding constraints.**
The proposed historical subsection above remains a record of what was proposed;
this approval does not mean executed, newly Validated, deployed or live-verified.
Release remains **BLOCKED** until the actual gates below pass.
Review: `.squad/decisions/inbox/goff-static-html-recovery-review.md`.

1. Complete focused mechanism revalidation through the existing official
   validation/deployment workflow before upload. Preserve the frozen source
   validation and record this mechanism delta; do not manufacture a workflow
   status or skip printed actions. No source/artifact rebuild or config change
   is necessary or authorized. Recheck idle deployment, disabled SCM basic
   authentication, exact source/ZIP/HTML pins, 20 remote sources, eight compiled
   server JS files, new public JS/CSS and unchanged settings/roles/agent/MCP.
2. The sole authorized cloud mutation is:

   ```sh
   az webapp deploy --resource-group rg-redshift-bs01 \
     --name app-redshift-chat-bs01-bb4b2781 \
     --src-path src/redshift-chat/dist/client/index.html \
     --type static --target-path /home/site/wwwroot/dist/client/index.html \
     --clean false --restart false --track-status false --async false \
     --timeout 120000
   ```

   Execute only through existing `chat_deploy.cli`, which adds the approved
   subscription, suppresses raw output and captures JSON; give its outer call
   adequate bounded time for the 120-second operation. Local HTML must still be
   exactly 623 bytes/hash `ef3adcb74301dda22edf7d066480676da0697a2d8f3c1c4ae9ae74c6f1377e20`.
   No extraction/cleaning, publishing credentials, fallback, settings/grants/
   resource edits or extra application file upload. Linux Kudu OneDeploy's
   incremental copy is distinct from Oryx; generic copy-stage "build" wording
   alone is not compilation. Actual Oryx/npm/restore/prune work is out of scope.
3. **No restart is approved or required by BFF HTML caching.** ARM startup is
   `npm start`; actual reviewed compiled index/app match remote. HTML is statted
   and streamed per request from module-relative `dist/client`, not cached at
   startup. Independent read-only diagnostics still show target ENOENT with an
   existing parent and misleading listing; no dangling symlink is established.
   The cloud filesystem may still reject a write or present inconsistent views.
   If post-upload public bytes do not change, stop: do not infer that restart
   fixes it. A separate runtime-path/restart review must consider resetting
   in-memory conversations/continuation/rate limits and interrupting chats.
4. Require the **new static operation's own terminal successful deployment
   record**, not CLI exit alone or `/latest` without ID correlation. Retain both
   failed ZIP records unchanged. Capture sanitized separate composite-recovery
   proof; no raw provider bodies/logs/tokens. Recheck exact direct target bytes,
   both public `/` and `/index.html`, referenced JS/CSS, all 20 remote source
   files and all eight compiled server JS files against frozen reviewed bytes.
   Public HTML must be `no-store`. Require process health and unchanged protected
   configuration, agent 2/MCP v3 and exact roles. Stop on failure, unexpected file
   change, drift, timeout, overlapping deployment or runtime interruption;
   no automatic cleanup/retry/rollback/restart.
5. **Precisely bounded marker reconciliation is approved only after step 4.**
   Preserve prior state plus separate recovery provenance. A hard-pinned
   recovery evidence collector may check these new operation-specific gates;
   leave the failed-ZIP-only `ui-copy-artifact-check.py` assertions untouched.
   Re-read state/pins immediately before writing, abort on concurrent change,
   then use existing `chat_deploy.save_state` with ONLY:
   `deployed_source_sha256=<frozen source>`,
   `deployed_zip_sha256=<frozen ZIP>`, `verified_at=None`,
   `verified_source_sha256=None`. No new allowlist keys, fake old deployment
   success, `verify()` monkeypatch, source override or guard skip.
   The deployed fingerprints mean the exact complete artifact is now
   materialized through evidenced composite recovery, not that either old ZIP
   command succeeded. No marker may be written just to unlock the verifier.
6. Run the unchanged normal FULL verifier only after that truthful marker gate:
   fresh independent Data API references, exact app-MI oil, fresh same-cookie
   gas continuation, current health/protocol/session/roles/source and serialized
   rolling-window waits. Only the normal verifier may persist verified fields.
   Record actual acceptance or actual failure, not historical numerical proof.

Independent observation at **23:15:36Z**: 20/20 remote source files and **8/8**
compiled server JS files equal local reviewed build; public `/` and `/index.html`
still serve old HTML; new JS/CSS exact; `/healthz` HTTP 200. No deployment, state
marker, new validation status, restart or cloud configuration was changed by
this review. Health freshness must be measured again during actual acceptance.

## Data-backed answers through structured analysis plans — approved implementation

**Status: Validated, deployed and live-verified.** The CHAT-ONLY GA decoder
correction completed the official azure-validate workflow, then azure-deploy's
existing App Service application stage. Full actual hosted numerical acceptance
passed **2026-10-26T22:43:40.817798Z**, with fresh independent Data API references,
current-response `analyze_data`, strict JSON decoding/plaintext rendering and
same-cookie fresh gas continuation. MCP **v3** and registered agent **v2** remain
unchanged. Earlier HTTP 503 failures below are historical, not current acceptance.
Current proof: `.squad/decisions/inbox/st-brown-decoder-correction-release.md`.
Historical v3 execution: `.squad/decisions/inbox/st-brown-analytics-v3-deployment.md`.

### GA result-serialization compatibility fix — 2026-10-26T22:16:27Z

#### All validation checks pass — CHAT-ONLY decoder correction

- [x] 1. Core Validation (CLI, auth, build, validate, what-if): existing-resource
  read-only preflight/inventory and source checks; complete current chat tests,
  typecheck/build and deployment-helper tests using installed dependencies.
  ARM/bootstrap validation/what-if is N/A: no infrastructure, image or agent
  definition change is proposed or authorized.
- [x] 2. Docker Build (if containerized): N/A for this chat-only source ZIP;
  confirm existing MCP v3 immutable digest and revision remain unchanged.
- [x] 3. Azure Policy Validation: retrieve current applicable assignments and
  review for the unchanged approved resources/public synthetic-POC scope.
- [x] Build Verification: retain old ZIP/state; freeze a new reviewed-source
  addressed ZIP, reopen all manifest entries and verify bytes/selected-file
  credential scan, keeping the registered agent v2 pin unchanged.
- [x] Static Role Verification: inspect unchanged project-only Consumer/User,
  ACR pull and single-secret vault scopes; no grant changes.
- [x] Record Proof / Resolve Errors / Update Status: complete the official
  workflow before marking this new correction Validated. Hosted acceptance
  was blocked at validation time until the new deployed runtime passed all gates.

#### Section 7: Validation Proof — CHAT-ONLY decoder correction

Checks completed **2026-10-26T22:25:25.055798Z**, before any runtime mutation.
Independent review authority: Goff's **2026-10-26T22:19:42Z** approval of Sewell's
decoder correction. No new production code, agent definition or MCP changes.

- Official workflow: LoadPlan → AddValidationSteps → RunValidation →
  BuildVerification → StaticRoleVerification; RecordProof/status steps follow.
- `deploy/.venv/bin/python deploy/chat_deploy.py --stage check`: passed current
  subscription/tenant, supported GA APIs, Node 24 and existing account/model/MCP.
  Existing `inventory()`, `verify_app_settings()` and agent GET confirm original
  resources/identities/TLS/basic-publishing, exact project-only Consumer/User,
  registered agent **2** and unchanged definition
  `8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20`.
- Retained Node **24.22.1** PATH and project-local TMPDIR: `npm test` **100 passed**,
  `npm run typecheck` and `npm run build` **passed**. Existing
  `cd deploy && .venv/bin/python -B -m unittest -q test_chat_deploy`: **68 passed**.
  No npm restore/dependency change or unchanged MCP suite was run.
- `deploy/.venv/bin/python -B deploy/.chat-artifacts/decoder-package-reviewed.py`
  repeated the same 100 chat tests/typecheck/build using installed dependencies,
  not additional distinct tests. The OLD source-pinned packager was retained,
  not bypassed. NEW packager hard-pins the current approved hash and agent 2.
- New source SHA-256:
  `77005490f46fe33177ebec38dd45585d01343f8e05f125b799b19303eecaff25`.
  Only `server/grounding.ts` differs among the 20 packaged files compared with
  the prior frozen ZIP. The changed shared test fixture is correctly excluded.
- New ZIP SHA-256:
  `1e094ff7c8cfca6fdfce66c3c96013923ebd8bc62d9b7ea9a846ad1b637ec985`.
  Path: `deploy/.chat-artifacts/redshift-chat-77005490f46fe33177ebec38dd45585d01343f8e05f125b799b19303eecaff25.zip`;
  **20 entries / 49,113 bytes**. Reopened every entry, exact manifest/bytes match,
  selected-file credential scan passed and sample numeric references are absent
  from packaged runtime source. This is not a universal secret-format guarantee.
- Prior ZIP/source/state are retained in
  `deploy/.chat-artifacts/decoder-rollback-20261026/`; old ZIP hash remains
  `99496c928e6b49f45f26afb0be57e0787f35589da17435715d3b6294a858a66f`.
  Only existing allowlisted source/ZIP/null verification fields were updated.
- Docker proof **N/A**: CHAT-ONLY source correction. Existing MCP revision
  `ca-redshift-bs01--0000003`, digest
  `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`,
  protected configuration hash
  `a87f7b2964a457d3a37de5631c60513acbe2330512b80117ce6affec435e7b94`,
  min/max 1/1 and 0.25 CPU / 0.5 GiB remain unchanged. No Docker/ACR build.
- Policy MCP retrieval succeeded; direct `atScope()` read with discovered latest
  GA **2026-07-01** returned **11** applicable/inherited assignments, no pagination.
  All allowlisted definition fingerprints equal the prior reviewed baseline.
  Accepted public synthetic-POC exceptions/MFA/write protections remain intact.
  Two operator URL/scope errors and an unsupported definition API 404 were
  resolved with correct query construction/allowlisted policy GETs/latest GA;
  final checks all passed, no runtime or policy change.
- Static RBAC review: `infra/chat-role.bicep` project-only Consumer/User;
  `infra/resources.bicep` AcrPull at ACR; deployment helper single-secret vault
  scope. Fresh read-only live exact-scope MCP and app role checks passed.
  Bootstrap ARM/what-if **N/A** for approved unchanged resources/image/agent.

Sanitized proof: `deploy/.chat-artifacts/decoder-preflight-proof.json`,
`decoder-policy-roles-proof.json`, `decoder-validation-proof.json`; test/package
logs alongside them. Historical validation/runtime 503 proof is preserved.
This section is artifact validation, **not hosted acceptance**.

**Status: Validated, deployed and live-verified — CHAT-ONLY compatibility fix.** Goff independently
approved Sewell's decoder fix at **2026-10-26T22:19:42Z**. Official validation
checks and proof above passed before deployment. Actual hosted acceptance passed
**2026-10-26T22:43:40.817798Z**; the unchanged full verifier persisted matching
source/verification fields only after all original gates passed. This subsection
supersedes the diagnosis's
proposed-fix status below, not historical v3 validation/release proof.

#### CHAT-ONLY deployment and actual hosted acceptance

- Official azure-validate completed `UpdateStatus` at
  **2026-10-26T22:26:03.139066Z**. Then invoked azure-deploy and read its predeploy
  checklist, AZCLI recipe/error/verification and live-role instructions.
  Current approved subscription/tenant/RG and existing East US 2 App Service,
  Sweden Central Foundry project and Brazil South MCP were reconfirmed.
  New AZD environment/provisioning/location/resource/role/migration steps were
  N/A for this approved existing-resource source-only release.
- Executed only
  `deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage app`.
  **Exit 0**; Entra-authenticated Kudu active successful build completed
  **2026-10-26T22:29:15.8525189Z**. No retry/redeploy/configure/agent/image stage.
  Existing nonsecret target/build settings and disabled publishing basic auth
  remained exact. Runtime resources, grants, identity and network stayed unchanged.
- Actual Kudu VFS reads matched all **20** frozen source files. Downloaded public
  HTML and referenced JS/CSS matched reviewed build bytes; compiled
  `dist/server/grounding.js` SHA-256
  `ab9e826093080efc470e1a8890701839f9d1b899d00247481a9686deb07712fc`
  matched the reviewed local build. Client-neutral business UX remains unchanged.
- Full existing verifier was executed via its unchanged
  `chat_deploy.main(["--apply","--gates-approved","--stage","verify"])`,
  using ignored `decoder-verify-observed.py` to retain only sanitized public
  fields/reference observations and serialize heavy probes. No acceptance
  function, runtime code or guard was replaced. A 65-second rolling-window wait
  separates the direct numerical MCP probes from hosted chat.
- First full attempt failed at no-Origin MCP acceptance with suppressed details.
  A second full attempt reached an HTTP 503; its precise phase was not captured,
  so it is **not claimed to be a decoder or continuation failure**. After an
  isolated health/oil diagnosis (alive process, initially stale health; actual
  hosted oil HTTP 200 with `get_data_context,analyze_data`), the final complete
  bounded attempt passed all gates. No overlapping retries, automatic provider
  fallback, production edit, grant change or rollback was used.
- Fresh independent Data API query completed **2026-10-26T22:41:10.000099Z**.
  Remote MCP numerical/source acceptance passed all five physical sources,
  including 2025 oil **21,157,564.26 bbl**, gas **44,177,025.20 Mcf**, cost
  **213,367,864.95 USD**, monthly/annual aggregates, top well/state, price average
  and 1,000 wells. These values are not runtime source constants.
- Actual hosted first turn completed **2026-10-26T22:43:29.125453Z**, HTTP 200,
  **17,861 ms**: exact **21,157,564.26 bbl**, 2025-01-01 through 2025-12-31,
  `get_data_context,analyze_data`, `continued=false`, `truncated=false`, 19 turns.
  Same-cookie follow-up completed **2026-10-26T22:43:39.747097Z**, HTTP 200,
  **10,621 ms**: exact **44,177,025.20 Mcf** for that same period, fresh
  `analyze_data`, `continued=true`, `truncated=false`, 18 turns.
- Process alive and actual database health `healthy,connected=true`, fresh
  `checkedAt=2026-10-26T22:41:53.918Z`; original no-Origin transport, safe CORS and
  hostile-origin rejection passed. Secure/HttpOnly/SameSite=Strict cookies,
  current-response execution, source/grain/period/units, strict final protocol
  and plaintext public rendering passed through the real App Service MI.
- Post-release exact MCP protected hash/revision/image, identities, CORS,
  min/max/resources and live project Consumer/User plus ACR/single-secret roles
  remained unchanged. The unchanged verifier wrote
  `verified_at=2026-10-26T22:43:40.817798Z` and verified source
  `77005490f46fe33177ebec38dd45585d01343f8e05f125b799b19303eecaff25`.
  Final preservation inspection passed **2026-10-26T22:43:47.626352Z**.

Proof: `deploy/.chat-artifacts/decoder-hosted-artifact-proof.json`,
`decoder-hosted-acceptance-proof.json`, `decoder-isolated-hosted-diagnosis.json`,
and owned release inbox. Only validated matching source/ZIP/deployed/verified
allowlisted state fields changed. Historical proof/rollback artifacts remain.
Interactive browser UX acceptance is not claimed by these HTTP/bundle gates.

- Only the chat tool-output adapter changed: preserve single business JSON and
  official MCP envelopes; additionally accept the observed business JSON + LF +
  `{structuredResponse: payload}` representation as exactly two object roots.
  The second has that sole own key and an object deeply equal to the first.
  Object key order may vary; array order/types must agree. Quote/escape-aware
  boundary detection handles multiline JSON, allowing only JSON whitespace
  between roots and around the pair. Each root is independently JSON-parsed;
  a third document, trailing prose, malformed/nonobject data, nested envelopes,
  extra/unrecognized wrapper keys or mismatching copies fail closed.
- Original 256 KiB **total original UTF-8 input** limit remains. Existing
  completed-call, context, source/grain/plan/result, current-response execution,
  final single-JSON and fixed nondata-template guards are unchanged. Context
  never grounds an answer, including continuation; no fallback/retry was added.
- Node **24.22.1** using retained runtime: `npm test` **100 passed**;
  `npm run typecheck` and `npm run build` **passed**. Existing
  `cd deploy && .venv/bin/python -m unittest -q test_chat_deploy`: **68 passed**.
  Tests prove synthetic direct/single-envelope/observed-pair payload equality and
  identical analysis validation; mocked installed SDK and HTTP first/follow-up
  calls require fresh analysis and preserve public fields. Build refreshed local
  generated output only. No dependency restore, MCP tests/code/image, agent
  definition, identity, resource, grant or configuration change.
- Goff's independent review found no blocking defect: **85 targeted provider/HTTP
  tests**, typecheck, **68 deployment-helper tests**, and **206 independent
  source/compiled adversarial checks** passed. No build, packaging, cloud call or
  implementation edit was performed by the reviewer.
- Original local-fix next step (now completed above): revalidate and freeze a new immutable **chat-only ZIP**, then obtain
  deployment approval. Preserve MCP **v3** and registered agent **v2** without re-registering.
  Actual app-MI exact oil plus fresh same-cookie gas acceptance against independent
  fresh references remains mandatory after release. Operator diagnosis and local
  synthetic SDK/HTTP tests are not managed-identity or hosted numerical proof.

Exact files, commands, regression coverage and limitations:
`.squad/decisions/inbox/sewell-foundry-result-serialization-fix.md`.
Independent compatibility-fix approval and test evidence (appended dated section):
`.squad/decisions/inbox/goff-consumer-grounding-revision-review.md`.

### Narrow runtime diagnosis — 2026-10-26T22:11:42Z

**Exact registered-service/BFF serialization mismatch identified; still BLOCKED.**
Actual GA registered-agent v2 calls using explicit operator AzureCliCredential
return successful MCP outputs as two JSON documents separated by LF:
`JSON.stringify(payload) + "\n" + JSON.stringify({structuredResponse: payload})`.
Both representations deeply agree. The deployed consumer's whole-string
`JSON.parse` at `server/grounding.ts:25`, called by `providers.ts:97`, rejects
the second document; the unchanged provider replay produces `AGENT_UNAVAILABLE`.
Actual decoded analysis and final JSON pass existing validators; direct MCP
single-wrapper outputs also pass. Live v2 instructions/fingerprint match frozen.

Operator inference is **not app-MI proof**. A fresh actual hosted question at
22:11:09Z still returns 503 / `AGENT_UNAVAILABLE` after 19.278 seconds, with only
that fixed failure event and no current 401/403 event in inspected logs.
Proposed strict two-document/equality normalization requires independent review,
source fix, revalidation, new immutable artifact and approved release, followed
by actual hosted oil plus fresh same-cookie gas acceptance. No fix, source/
agent/resource change, grant or rollback was made during diagnosis; Verified
markers stay null. Full structural evidence, limitations and regression scope:
`.squad/decisions/inbox/st-brown-agent-unavailable-diagnosis.md`.

### Analytics v3 execution — 2026-10-26T21:59:36Z

- Existing-resource image/source/agent-only release; no provisioning, grants,
  credentials, networks, regions, resources, CORS or scaling changed.
- Sole healthy running MCP revision `ca-redshift-bs01--0000003`, reviewed
  `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e`.
  Full `deploy.py --apply --stage verify --image-tag v3` passed, including
  fresh independent Data API comparisons across all five physical sources.
- Actual 2025 totals: oil **21,157,564.26 bbl**, gas **44,177,025.20 Mcf**,
  operating cost **213,367,864.95 USD**. Monthly/yearly, dimension/top-N,
  prices and wells comparisons passed. These are direct MCP results, **not**
  successful hosted-agent answers.
- New registered agent **version 2** has reviewed definition
  `8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20`.
  App settings pin version 2; ZIP
  `99496c928e6b49f45f26afb0be57e0787f35589da17435715d3b6294a858a66f`
  is deployed. Kudu reports active successful completion
  `2026-10-26T21:37:53.8306061Z`; all 20 actual remote source files and
  downloaded HTML/JS/CSS match the reviewed source/build byte-for-byte.
- Read-only preservation hash remains
  `b18835eca7051980441ccf484ef478eb18d01c0b7113d174aa067d0331828d61`.
  Post-release exact existing project Consumer/User, ACR AcrPull and
  single-secret Key Vault Secrets User checks passed.
- Process health and actual database health recovered after startup.
  Full chat verification reached `/api/chat`, then failed HTTP 503.
  A separate literal 2025 oil question also failed HTTP 503 /
  `AGENT_UNAVAILABLE` after 17.2 seconds. Secure cookie attributes passed;
  **no numerical hosted answer or same-cookie gas continuation passed**.
  The public classifier does not identify which provider/grounding field
  failed; no raw provider output was exposed or unsupported cause invented.
- `deploy/chat-state.json` retains deployed fingerprints/version but
  `verified_at` and `verified_source_sha256` are null. Prior rollback artifacts
  remain intact. No automatic rollback, guard relaxation, code edit/rebuild,
  credential fallback, delegation or Git operation was performed.
  Stop for a narrowly reviewed provider/serialization/grounding diagnosis before
  another immutable release; do not equate local tests with runtime success.

### All validation checks pass — analytics release v3

- [x] 1. Core Validation (CLI, auth, build, validate, what-if): run the existing
  release-specific read-only helpers, complete MCP/chat/deployment tests and
  chat typecheck/build with installed dependencies. Resource-template ARM
  validation/what-if is not applicable: this release changes image, source ZIP
  and pinned agent only; no infrastructure template, role or resource change.
  Do not execute historical bootstrap templates to validate an image update.
- [x] 2. Docker Build (if containerized): inspect the fixed MCP manifest and
  Dockerfile; freeze reviewed source hash; build immutable `v3` on existing
  ACR Linux/AMD64 builder, preserving `v2`/`v1` and all rollback metadata.
- [x] 3. Azure Policy Validation: retrieve subscription policy assignments,
  review against unchanged regions/resources and approved public synthetic POC.
- [x] Build Verification: preserve old chat state/ZIP/agent pin; validate new
  source-addressed ZIP contents/hash and new agent-definition fingerprint.
- [x] Static Role Verification: confirm existing App Service project-only
  Consumer/User and MCP image-pull/vault-secret roles; no new grants.
- [x] Record Proof / Resolve Errors / Update Status: complete the official
  azure-validate workflow and append timestamped Section 7 proof before Validated.

### Section 7: Validation Proof — analytics v3, 2026-10-26T21:09:26Z

**Artifact validation passed; runtime release NOT performed.** St. Brown used
the official azure-validate workflow, following each printed action. Independent
review is Goff's approved consumer revision and earlier approved backend boundary,
not self-approval. Historical proof below remains unchanged.

Commands executed from the workspace root with existing environments:

```sh
src/redshift-mcp-server/.venv/bin/python -m pytest -q src/redshift-mcp-server/tests
src/redshift-mcp-server/.venv/bin/python -m ruff check src/redshift-mcp-server
deploy/.venv/bin/python -m unittest discover -s deploy -p 'test_*.py' -q
export PATH="$PWD/src/redshift-chat/.runtime/node-v24.22.1-darwin-arm64/bin:$PATH"
# In src/redshift-chat:
npm test
npm run typecheck
npm run build
# From workspace root:
deploy/.venv/bin/python deploy/deploy.py --check --stage update --image-tag v3
deploy/.venv/bin/python deploy/chat_deploy.py --stage check
deploy/.venv/bin/python deploy/deploy.py --apply --stage build --image-tag v3 --approved-source-sha256 c6fe241b6cb170841d403799af07456d09ed790b75cf0b8503dc994a8ee0ca1e
deploy/.venv/bin/python deploy/.chat-artifacts/analytics-package-reviewed.py
```

- MCP **148 passed**; Ruff **passed**; deployment helpers **107 passed**;
  Node **24.22.1** chat **59 passed**, typecheck and production build **passed**.
  Packaging repeated the same 59 chat tests/typecheck/build, not additional tests.
  Deployment unit-test printed stage/update messages are mocks, not Azure actions.
  No `npm ci`, dependency installation or local Docker retry was performed.
- Read-only helpers confirmed the exact approved tenant/subscription and GA API
  availability, existing unchanged model, and Node runtime. Additional existing
  `inventory()`/configured-app reads confirmed App Service East US 2, Foundry
  project Sweden Central, MCP Brazil South, original identities, existing
  project-scoped roles, HTTPS/TLS/basic-publishing protections and unchanged
  MCP min/max 1/1, 0.25 CPU / 0.5 GiB. ARM also reports existing 1 GiB ephemeral
  storage; an initial overly strict local dictionary equality rejected this
  additional field. Named CPU/memory/scaling checks passed and the exact app
  fingerprint stayed unchanged. No runtime code fix or resource edit was needed.
- The AZCLI recipe is adapted to this approved **existing-resource artifact-only**
  release: bootstrap `infra/main.bicep` validation/what-if is **not applicable**.
  No infrastructure template, region, SKU, role, identity, network, secret
  reference or CORS change is proposed. Running old resource-creation templates
  is neither necessary nor authorized. Release-specific read-only helpers replace
  bootstrap validation; actual ACR Linux/AMD64 build replaces local Docker build.
- Azure Policy tool returned 15 assignments including unrelated lab scopes;
  direct read-only ARM `atScope()` returned all **11 applicable/inherited**
  assignments without pagination. Their definitions were retrieved/fingerprinted.
  The creation-deny rule targets classic resources, not these existing targets;
  MFA/write protections remain intact. No policy/resource configuration is changed
  by source packaging or the successful existing-registry artifact build.
  This is scoped release validation, **not** a claim that all historical
  infrastructure passes a fresh organizational compliance audit. Existing public
  synthetic-POC/admin exceptions remain accepted; no exemption was added.
- **Static Role Assignment Verification: Verified.** `infra/chat-role.bicep`
  pins the original app principal, with Foundry Agent Consumer and Cognitive
  Services User at the exact project only. The latter's broader permissions were
  explicitly accepted previously. `infra/resources.bicep` / `deploy.py` retain
  UMI AcrPull at ACR and MCP system-identity Key Vault Secrets User at the single
  password-secret scope. No new role, grant or credential path is required.
  No role-write/provision/configure/bootstrap function was called.
- Fixed MCP manifest includes `analytics.py`; Dockerfile retains hash-pinned
  Python, hash-verified dependencies and nonroot user. Chat manifest automatically
  includes `server/grounding.ts`. New agent allows **only** `get_data_context` and
  `analyze_data`; strict final JSON alternatives match the reviewed consumer.
  UI/index title and business questions are client-neutral. Chat package manifests,
  lockfile and checked build configuration are byte-identical to the deployed
  rollback ZIP. No dependency/auth/infrastructure delta was added by this gate.

Immutable artifacts and fingerprints:

| Evidence | Exact value |
| --- | --- |
| MCP reviewed source SHA-256 | `c6fe241b6cb170841d403799af07456d09ed790b75cf0b8503dc994a8ee0ca1e` |
| Existing app approval SHA-256 | `73c72ae7337b2184a9b54edfe204747fb982d1baa15245d39c42135d78296e90` |
| ACR run / platform / result | `cq3` / `linux/amd64` / `Succeeded` |
| New immutable `v3` digest | `sha256:5bb2d6eb90493805caff0beee3b7d9a11a5f0e19e47d5f208303cc6136d8ec9e` |
| Chat source SHA-256 | `900997e9fa54ba68ceb88ee43159211c5d733ebd0bc9f606fc3d4bfefa806a22` |
| Chat ZIP SHA-256 | `99496c928e6b49f45f26afb0be57e0787f35589da17435715d3b6294a858a66f` |
| Desired agent-definition SHA-256 | `8d49d49bbf79072a5fbd3a9a7869bb81b91f4289bcc04a6b47f43e7e9de17d20` |

The new ZIP is
`deploy/.chat-artifacts/redshift-chat-900997e9fa54ba68ceb88ee43159211c5d733ebd0bc9f606fc3d4bfefa806a22.zip`
(20 files, 48,734 bytes). Every entry was reopened and compared byte-for-byte
with the audited manifest; no unlisted files were packaged and the selected-file
credential scan passed (not proof against every possible secret format).
The ignored packaging script uses the same `source_manifest`, immutable ZIP
entry verification/write logic, `package_path`, and allowed `save_state` fields
as `chat_deploy.build()`, replacing its unconditional `npm ci` with existing-
dependency tests/typecheck/build. It rejects any source-hash change and safely
reuses the exact ZIP after the agent stage without overwriting the new agent pin.

Rollback preserved **before build state changes** in
`deploy/.chat-artifacts/analytics-v3-rollback-20261026/`: old MCP/chat state
snapshots, source-file hashes, prior artifact fingerprints, read-only inventory,
policy-definition fingerprints and actual ACR proof. Original
`deploy/.chat-artifacts/redshift-chat.zip` remains unchanged, SHA-256
`42dd319cf26e83ef407f0c9f24262316729a9d9ccab2eac325e1706257420696`,
source `7802547e4aa2a5ef0f3365435916dadae707c4a11d22cf6376643497310dfe7f`.
The previous registered agent is still **version 1**, definition SHA-256
`dc1f844509d3489b4d084ff993ae1c4b719631f35b694e21d173e12252940099`;
its actual read-only live definition matched that rollback state. Both prior
ACR `v1`/`v2` digests and build history were rechecked, not overwritten.

**Stop boundary:** live MCP remains `v2`,
`sha256:474fa8cb2fd7d9a3b35c2c918911f3c4c2d7474fe576455d3b1b4bb87ee5fa13`,
revision `ca-redshift-bs01--0000002`; exact app approval hash remained stable
after the ACR build. No Container App update, agent registration, App Service
settings/source deployment, inference, database query, auth/grant or network
change was performed. No dotenv/secret read, Git operation or delegation.
No raw logs, tokens, cookies, query results or secret-bearing app snapshot was
stored. New analytics numerical/runtime/GA serialization acceptance remains
pending **after** coordinated release; local tests/generated SQL do not prove it.

After this workflow completes and the parent invokes **azure-deploy**, use only:

```sh
deploy/.venv/bin/python deploy/deploy.py --apply --stage update --image-tag v3 --approved-source-sha256 c6fe241b6cb170841d403799af07456d09ed790b75cf0b8503dc994a8ee0ca1e --approved-app-sha256 73c72ae7337b2184a9b54edfe204747fb982d1baa15245d39c42135d78296e90
deploy/.venv/bin/python deploy/deploy.py --apply --stage verify --image-tag v3
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage agent
export PATH="$PWD/src/redshift-chat/.runtime/node-v24.22.1-darwin-arm64/bin:$PATH"
deploy/.venv/bin/python deploy/.chat-artifacts/analytics-package-reviewed.py
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage app
deploy/.venv/bin/python deploy/chat_deploy.py --apply --gates-approved --stage verify
```

The v3 image is already built; do not rebuild/retag or edit frozen MCP sources/
README. Any approval/source/ZIP/agent drift blocks release. No `all`,
`prerequisites`, `configure` or new resource what-if is required. Parent must
establish actual GA MCP serialization, strict JSON completion, independent exact
oil/gas totals/units/periods and same-cookie fresh analysis after release.

Implementation and deployment approved by the user on 2026-10-26;
implementation locally tested; analytics NOT deployed.
Goff rejected the original consumer grounding artifact (empty/context-only calls
allowed invented totals), then independently **APPROVED St. Brown's narrow
fail-closed protocol revision** on 2026-10-26. See
`.squad/decisions/inbox/goff-consumer-grounding-revision-review.md`.
This is implementation approval, **not deployment validation**: authorized Azure
validation, actual deployment, GA-service MCP/protocol serialization, exact MCP/
agent numerical acceptance and same-cookie fresh-analysis continuation remain
pending release gates. Historical evidence below is unchanged. On 2026-10-26 the user
corrected the metadata-explorer interpretation. The application must answer
natural-language questions using actual data in `oge_synthetic`, not merely
list Redshift schemas, tables or columns.

User clarification: "We need to ensure that was is passed to the MCP is some
kind of plan that the backend can interpret into a query of sorts that Redshift
will understand."

The agent-to-MCP contract must therefore be a structured analysis plan rather
than raw SQL. Backend-owned validation and compilation must restrict access to
the approved schema and tables, parameterize values, enforce read-only execution
and bounded cost/results, and return actual results for the agent's grounded
natural-language answer. No SQL console or arbitrary SQL input is authorized.
Metadata tools may support internal planning but must not define the user-facing
experience. The client-neutral UI requirement remains.

The user approved the reviewed strict-plan validator/compiler, grounded registered
Foundry agent and business-question React experience on existing infrastructure.
Goff and Fact Checker reviewed the design with source/grain, admission, grounding
and numerical acceptance conditions. Independent implementation/security review
must still pass before release. Existing infrastructure, credentials, permissions
and the deployed metadata correction remain unchanged during local implementation.

Confirmed catalog: five approved tables (`annual_production`,
`daily_production`, `monthly_production`, `monthly_prices`, `wells`) and their
27 columns. Goff proposed a versioned, strict JSON analysis-plan contract with
closed metric/aggregation/grouping/filter operators and backend-owned source
selection; Fact Checker independently approved the direction with launch
conditions for verified grain/join semantics, MCP-level resource controls,
numeric-result grounding, and restricted credentials or explicit synthetic-POC
risk acceptance. A daily-production-only first slice was proposed, not approved;
do not silently narrow the user's whole-schema target to that slice.

Implementation must replace the explorer UX and metadata-only agent instructions,
add a safe plan validator/compiler/executor, and validate actual numerical answers
against independent aggregates. Schema names, SQL fragments, arbitrary functions
and user-defined join predicates must not be accepted as executable plan input.
Read-only transactions alone are not sufficient authorization while the current
database login is a superuser. Public analytics launch requires resolving that
credential boundary explicitly; the user's synthetic-POC admin risk acceptance
below resolves that launch decision for this POC only. Deployment is authorized
but deliberately deferred until independent code review and validation.

### Confirmed POC identity decision and live dataset evidence

The user explicitly selected "Keep the current admin identity for this
synthetic-data POC" after disclosure that it is a superuser and that application
validation failure would have broader consequences than with a dedicated
schema-restricted read-only identity. Retain the existing Key Vault-backed
credentials without reading dotenv contents or changing grants. This is a
synthetic-POC risk acceptance, not approval for production or nonsynthetic data.
The compiler, read-only transaction and service-side controls remain mandatory.

Read-only AWS Data API profiling verified:

- Daily production: 2,162,475 records, 2016-01-01 through 2025-12-31.
- Monthly production: 71,020 records, 2016-01 through 2025-12.
- Annual production: 6,377 records, 2016 through 2025.
- All three production sources have identical whole-dataset sums:
  oil 222089936.27 bbl; gas 465370680.34 Mcf;
  operating cost 1605311212.23 USD.
- Wells: 1,000 rows and 1,000 distinct well IDs. Daily production has zero
  orphan well IDs. Monthly prices: 120 rows and 120 distinct price months.

These checks do not prove per-well/per-period reconciliation, uniqueness of
production grain, null semantics or completeness. Verify those conditions
before enabling source substitution, joins or derived metrics that rely on
them. Do not use LIMIT as a scan-cost bound.

### Approved implementation and release scope

1. Replace metadata exploration with natural-language answers from actual
   `oge_synthetic` records. Support the five-table schema through bounded,
   backend-owned production, well and price semantics rather than a silently
   daily-only slice.
2. Add a strict versioned structured-plan contract, validator, parameterized SQL
   compiler and result/provenance envelope. Backend-owned sources and registered
   joins only; no arbitrary SQL, schema names, expressions or join predicates.
   Return exact decimals, units, periods, null/empty/truncated distinctions and
   unsupported-request errors without inventing revenue/profit definitions.
3. Enforce time, output and admission limits at the MCP boundary, including
   direct callers. Verify source/grain and join integrity; avoid double counting.
   Keep existing chat limits, health checks, client neutrality and privacy UX.
4. Update the registered Foundry agent instructions/tool allowlist and pinned
   version, application provider and React chat UX. Require tool-grounded
   numerical answers, not database metadata explanations.
5. Independently review correctness, security and cost; compare MCP results and
   hosted agent numerical answers against independently calculated aggregates.
6. After Azure validation passes, release a new immutable MCP image and reviewed
   App Service bundle to the existing targets. Preserve identities, Key Vault,
   grants, ingress, CORS, regions, resource sizing and rollback artifacts. No new
   resources or permissions are requested.

### Local implementation and evidence — 2026-10-26

Consumer-grounding revision: `server/providers.ts` now accepts only strict final
JSON (`answer` with `reply`, or `clarification`/`unsupported` with a closed reason).
New related `server/grounding.ts` validates actual current-response MCP execution
results and renders non-data text from fixed server templates, never arbitrary
model clarification prose. Data answers require fresh validated `analyze_data`
on every turn. Missing/context-only/history evidence, failed/malformed tools and
incomplete model output fail closed; empty results use an honest fixed notice,
while partial/null results carry mandatory server-owned caveats.
Registered-agent instructions and deployment acceptance/tests are aligned.
No response-format API support or constrained decoding is assumed. Backend
`analytics.py`/`server.py`, credentials, permissions and deployed artifacts remain
unchanged. Goff must independently re-review this revision before Azure validation,
immutable runtime release and actual managed-identity oil/gas exact-answer and
same-cookie continuation gates. No live numerical claims follow from local mocks.
Revision evidence: Node 24.22.1 chat tests **59 passed**, typecheck and production
build passed; credential-free chat deployment-helper tests **68 passed**.
Detailed independent handoff: `.squad/decisions/inbox/st-brown-consumer-grounding-revision.md`.

Changed runtime: new `redshift_mcp_server/analytics.py` and MCP `server.py`;
chat `server/providers.ts`, `client/App.tsx`, `client/index.html`;
deployment `deploy.py` and `chat_deploy.py`. Related MCP/chat/deployment tests,
READMEs, this plan and Gibbs's own decision inbox were updated. No credentials,
grants, infrastructure resources, networks, deployment state or deployed runtime
were changed. No commits or PRs were created.

Public tool contract (not SQL):

```json
{"plan":{"version":"1","dataset":"production","start_date":"2025-01-01","end_date":"2025-12-31","measures":[{"field":"oil_bbl","aggregation":"sum"}],"group_by":["state"],"order_by":{"measure_index":0,"direction":"desc"},"limit":5}}
```

Result shape (illustrative value, not a production answer):

```json
{"version":"1","status":"ok","executed":true,"executed_at":"<execution timestamp>","items":[{"state":"<observed state>","oil_bbl_sum":"123.45","oil_bbl_sum_null_records":0,"source_records":2,"first_observation":"<observed date>","last_observation":"<observed date>"}],"truncated":false,"units":{"oil_bbl_sum":"bbl"},"source":"oge_synthetic.daily_production","source_grain":"day","joined_sources":["oge_synthetic.wells"],"plan":{"version":"1"},"notes":["<coverage/null/precision caveats>"]}
```

The real `plan` echoes all validated normalized plan fields. Exact decimals are
strings. Empty input, all-null aggregates and row/byte truncation are distinct.
Maximum 500 rows/256 KiB includes both FastMCP representations and framing.
Date windows are at most 3661 inclusive days. Production grain is checked for
duplicate/null well-day keys; well joins require unique/non-null dimension keys
and no orphans. Monthly/yearly substitution requires per-well/period exact
reconciliation of all three metrics, unique rollups and no null metrics, otherwise
daily is used. Prices are separate unique monthly observations, never joined to
production. Averages use Redshift DECIMAL(38,8); no ratios/revenue/profit/gross
value or arbitrary expressions are implemented.

MCP admits at most two workers with no additional waiting queue, 120 calls/minute
globally and 12 analytics/context calls/minute per process. Cancellation holds
the worker permit until actual completion. Verified TLS, 10-second per-statement
timeout, read-only transactions and rollback are preserved. These are not hard
cost caps; full rollup reconciliation and date-context profiling scan native
facts, and process-local limits reset/multiply on restart/additional replicas.
The existing single-replica POC is unchanged.

Local validation:

- MCP Python suite: **148 passed**; Ruff check passed.
- React/BFF: **48 passed**, TypeScript check and production Vite/server build passed.
- Deployment helper suites: **105 passed**, credential-free mocked checks;
  audited offline runtime source-manifest check passed.
- No dependency manifests changed; no dependency restore was needed.

Additional authorized live **read-only** Data API evidence for 2025:

- Oil **21157564.26 bbl**, gas **44177025.20 Mcf**, operating cost
  **213367864.95 USD**; January oil **1929647.87 bbl**.
- Highest gas well **SYN-00593**, **264818.46 Mcf**.
- Highest oil state **NM**, **4635530.30 bbl**.
- Average monthly oil price **60.59583333 USD/bbl** at DECIMAL(38,8);
  **1000 wells**.
- Native compiled queries for daily totals, monthly January trend, annual trend,
  state grouping, prices and wells exactly matched independent reference SELECTs.
  The generated integrity checks verified unique/non-null well-day and well keys,
  price month alignment/uniqueness and 2025 per-well monthly/annual reconciliation.

These checks exercised generated SQL via the independent Data API test harness,
**not** the runtime connector or a deployed analytics MCP/Foundry agent.
Runtime uses only the direct TLS connector. Full numerical release acceptance
still awaits the new deployment and must observe MCP execution plus actual
App Service managed-identity oil/gas answers and same-cookie continuation.

Release handoff: complete independent implementation/security review, then Azure
validation. Use `deploy.py --check --stage update --image-tag v3`, review the
reported source/app hashes, and apply only `build/update/verify` with the approved
hashes. **Do not use MCP configure/all/bootstrap stages.** Then use chat
`agent/build/app/verify` with `--apply --gates-approved` on cloud stages, no
resource/grant/CORS provisioning. New chat ZIPs are source-addressed and do not
overwrite the prior ZIP; retain the previous chat state/version for paired
ZIP/agent rollback. Exact commands are in `deploy/README.md` and
`deploy/CHAT-README.md`. Independent review is pending, not silently waived.

## Redshift metadata-discovery correction — deploy requested

**Status: Deployed and verified.** Independent review, tests, live native-query
checks, configured-app guards and ACR Linux/AMD64 artifact validation passed.
On 2026-10-26 the user
requested deployment of all changes after diagnosis of the ownership-filtered
`information_schema.schemata` query. Replace the affected metadata discovery
with Redshift-native catalogs, preserving exact tool contracts, bounded
parameterized read-only operations and current-database isolation. Verify
schema, table and column discovery for the existing dataset rather than
accepting connection/tool invocation alone.

Use existing Azure CLI/ACR/Container Apps deployment targets in subscription
`bb4b2781-6739-4fa1-994e-4ad6ce55c59c`, `rg-redshift-bs01`, Brazil South.
Build a new immutable MCP image tag, preserve the prior image for rollback,
and update only the existing Container App image. Preserve environment values,
Key Vault references, identities, grants, ingress, CORS and resource placement.
Deploy any reviewed chat-side acceptance changes to the existing East US 2
App Service only if its runtime source changes. The client-neutral UI remains.
No new services, permissions, credentials, SQL tools, database mutations or
network changes are authorized or needed. Independent review and Azure validation
must pass before deployment; live acceptance must find `oge_synthetic`, its
known tables, and column metadata through the MCP and agent.

The correction now uses `SVV_ALL_SCHEMAS`, `SVV_ALL_TABLES`, and
`SVV_ALL_COLUMNS`, always scoped to `current_database()`. Public result keys,
parameterization, limits and read-only transactions are preserved. Deployment
acceptance now requires both actual schemas, all five known local tables,
valid wells columns, actual agent tool evidence and same-session table answers.
The reviewed image-only release helper supports a new `v2` tag, prevents
overwriting existing tags, checks source/app fingerprints, preserves the entire
configuration/identity and records the previous image/revision for rollback.

### All validation checks pass — metadata correction

- [x] 1. Core Validation: independent Goff review APPROVE; 105 MCP, 63 chat
  deployment and 39 release-helper tests passed. Read-only Azure context and
  configured-app release guards passed. No infrastructure template, parameter,
  role, secret, network or resource placement changes; ARM provisioning
  validation/what-if are not applicable to this image-only revision update.
- [x] 2. Docker Build: ACR Linux/AMD64 build `cq2` succeeded for reviewed source,
  tag `v2`, digest
  `sha256:474fa8cb2fd7d9a3b35c2c918911f3c4c2d7474fe576455d3b1b4bb87ee5fa13`.
  Local Docker dependency downloads failed TLS negotiation; used the existing
  ACR builder for artifact validation instead. No certificate/security bypass,
  dependency/source change, or Container App update during build validation.
- [x] 3. Azure Policy Validation: existing approved Container App image update
  only; no policy exceptions or configuration changes. Current Azure provider
  checks passed.

### Section 7: Validation Proof — metadata correction, 2026-10-26

- Independent Goff review: APPROVE for native catalog correctness, contracts,
  database isolation, SQL parameterization, dataset acceptance and image-only
  release preservation. Reviewer confirmed all 207 targeted tests pass.
- Exact corrected native SQL, extracted from the reviewed application, ran
  successfully against Redshift through metadata-only Data API diagnostics:
  schemas `oge_iceberg`, `oge_synthetic`, `public`; all five expected local
  tables; five `wells` columns. Runtime-admin MCP acceptance follows deployment.
- `deploy/deploy.py --check --stage update --image-tag v2`: PASS.
  Reviewed runtime source SHA-256:
  `f4601f5bac9d1470c2595c1c4a7b592fa8b7aca484f554820dd1ccd291a0f9b3`.
  Approved current-app SHA-256:
  `956238afc1c25333ef7782bd977157afbb2d81bb4ff606be3740e1f812702d6c`.
  Existing revision is `ca-redshift-bs01--0000001`; previous digest remains
  `sha256:1f7c40921f16cafb9d08df09fe98034098cf797cf43d006426993716c84a5a80`.
- Serialize publishers and app writers for this release. The helper uses ARM
  ETags when present; a live fingerprint and pre/post drift guards remain
  mandatory when the service does not return ETags.
- Remote Docker artifact validation:
  `deploy/deploy.py --apply --stage build --image-tag v2
  --approved-source-sha256 f4601f5bac9d1470c2595c1c4a7b592fa8b7aca484f554820dd1ccd291a0f9b3`:
  PASS. Live ACR run `cq2` is `Succeeded`, platform Linux/AMD64; registry digest,
  recorded source SHA-256 and v2 tag match. The original v1 image is retained.
- Image-only release completed as `ca-redshift-bs01--0000002`, healthy and
  running, pinned to the v2 digest above. Full pre/post configuration and identity
  fingerprints match after excluding only the intended image/revision change.
  Initial asynchronous ARM readback tripped the fail-closed drift guard;
  read-only inspection confirmed the preserved fingerprint, and the same release
  resumed without another image/configuration mutation. Rollback image and
  previous revision are retained in ignored `deploy/state.json`.
- Actual deployed MCP, using its existing `admin` runtime credentials:
  `test_connection` true; `list_schemas` returns `oge_iceberg`, `oge_synthetic`,
  `public`; `list_tables(oge_synthetic)` returns all five expected tables;
  `describe_table(oge_synthetic, wells)` returns `well_id`, `state`, `basin`,
  `operator`, `start_month`, with no truncation or tool errors.
- `deploy/deploy.py --apply --stage verify --image-tag v2`: PASS.
  `deploy/chat_deploy.py --apply --gates-approved --stage verify` with Node 24:
  PASS, including actual agent schema names, all five table names, observed MCP
  tool calls, secure session cookies and same-session continuation. Initial
  post-switch transport checks failed; subsequent direct checks and complete
  sequential verification passed without permission/configuration changes.
- Existing client-neutral frontend runtime and registered agent definition were
  unchanged, so no unnecessary App Service redeployment or agent version was
  created. Improved deployment-only acceptance is persisted locally, and the
  successful application verification timestamp is in ignored chat metadata.

## Client-neutral UI update — application-only release

**Status: Deployed and verified.** Azure validation workflow and application-only
checks passed; reviewed source ZIP deployed successfully on 2026-10-26.
User requested client-neutral, Redshift-data-focused UI
wording and deployment on 2026-10-26. Gibbs updated headings, workspace text,
suggested questions, composer guidance and HTML metadata without changing
backend behavior, agent tools, infrastructure, credentials or roles.
Public synthetic-data, privacy, retention and metadata-only disclosures remain.
Goff independently approved the update with no blocking findings.
Local Node 24 validation: 47 application tests, typecheck and production build
passed; reviewer independently confirmed all 9 UI tests pass.

Deployment recipe: existing Azure CLI/Entra-authenticated App Service source ZIP,
using only `deploy/chat_deploy.py` application packaging/deploy/verify stages.
Target remains `app-redshift-chat-bs01-bb4b2781` in `rg-redshift-bs01`,
East US 2, subscription `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`.
No provisioning, region, role, model, MCP or CORS changes. Verify the hosted HTML
and referenced JavaScript contain the updated neutral copy, and rerun the full
live health/agent/continuation acceptance gates after deployment.

### All validation checks pass

- [x] 1. Core Validation (CLI, auth, build, validate, what-if): Node 24 tests,
  typecheck and build passed; active subscription matches the approved target.
  Recheck existing deployment inventory before packaging/deployment.
  Infrastructure compilation, ARM validation and what-if are not applicable to
  this source-only update: no infrastructure template or parameter changed.
- [x] 2. Docker Build (if containerized): not applicable; existing App Service
  uses a source ZIP and Linux Oryx, not a new image.
- [x] 3. Azure Policy Validation: no resource configuration or policy changes;
  previously approved existing App Service target and deployment settings remain.

### Section 7: Validation Proof — UI-only release, 2026-10-26

- `npm test`, `npm run typecheck`, `npm run build` with Node 24: PASS,
  47 application tests and production client/server build.
- Independent Goff review: APPROVE; 9 targeted UI tests rerun successfully.
- `az account show --query '{name:name,id:id}'`: approved existing subscription
  `TSJasonFarrell-Sub`, `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`.
- `deploy/.venv/bin/python deploy/chat_deploy.py --stage check` with Node 24:
  PASS, read-only context, GA APIs, Node 24 and existing account/model/MCP checks.
- Source packaging reused `source_manifest()` credential scanning and allowlist,
  verified stable source SHA-256, and recorded ZIP/source fingerprints through
  `save_state()`. Existing dependencies were not reinstalled; lockfile unchanged.
- Static role review: no infrastructure, role, backend or authentication files
  changed. Preserve the previously reviewed two project-scoped runtime roles.
- ARM validation/what-if, Docker and new policy evaluation: not applicable to this
  application-only source update; no provisioning or configuration change planned.
- `deploy/chat_deploy.py --apply --gates-approved --stage app`: PASS;
  Entra-authenticated Kudu deployment completed with basic publishing disabled.
- Hosted HTML returned HTTP 200; its referenced JavaScript exactly matches the
  reviewed local production bundle and contains the new dataset-focused copy
  with no client-name matches. Browser snapshot confirmed the rendered headings,
  suggestions, composer and retained disclosures.
- `deploy/chat_deploy.py --apply --gates-approved --stage verify`: PASS on retry;
  process health, actual Redshift health, CORS, pinned agent/MCP execution,
  conversation continuation, exact project roles and deployed fingerprints passed.
  The initial post-deploy check returned HTTP 503; the subsequent full check
  succeeded without further configuration changes. Successful verification
  metadata is persisted in ignored `deploy/chat-state.json`.

## React chat and Foundry extension — deployed, live API acceptance passed

**Status: Deployed; all scripted live acceptance gates passed on 2026-10-26.**
Site: https://app-redshift-chat-bs01-bb4b2781.azurewebsites.net.
After independent peer/security review and assignment-only validation, deployed
JasonFarrell's approved **Cognitive Services User at project scope**, retaining
Foundry Agent Consumer. The actual App Service managed identity now returns a
natural-language schema answer with observed `list_schemas` tool execution;
a second turn with the same secure session cookie confirms `continued: true`.
Real Redshift health reports `healthy` and `connected: true`.

The complete `--stage verify` retry passed process health, current Redshift
health, exact-origin CORS, original no-Origin MCP acceptance, pinned registered
agent, exact project-scoped roles, deployed source fingerprints and conversation
continuation. The verifier persisted `verified_at` and `verified_source_sha256`
in ignored deployment metadata. An earlier retry failed the separate no-Origin
MCP probe; the subsequent complete retry passed without provisioning changes.
Interactive browser UX acceptance remains outstanding.

Earlier predeployment evidence below followed user approval of the original
plan and the explicit region choice **“Deploy the chat App Service in East US 2
(Recommended)”**. Independent Rai security review reported no vulnerabilities in
the new application/deployment support. Local application integration passed
**37 tests**, including actual API `reply`, actual MCP `toolNames` and server-owned
continuation-chain handling. Earlier deployment tests passed **70 total**, including
rejection of wrong-region site/plan inventory and unsafe what-if changes. Local Bicep
compilation and compiled East US 2 parameter-wiring checks passed; expected
`BCP081` warnings remain for live-provider GA Web APIs newer than local schemas.
The verified MCP deployment and its evidence below are preserved unchanged.

Current local correction validation: **56 chat + 22 original = 78 deployment
unit tests** and full/role-only Bicep compilation pass. Compiled inventory confirms
the isolated mode contains only the additional role assignment; the original MCP
plan below is byte-identical. Only existing Web schema `BCP081` warnings remain.
These local checks preceded the successful cloud role and live acceptance gates
recorded above.

### Earlier extension validation proof — before the role correction

- [x] Earlier validation checks passed: core CLI/authentication, Bicep compilation,
  live subscription ARM validation and what-if for `infra/chat.bicep` with
  `infra/chat.parameters.json`.
- [x] Docker build: not applicable; Node 24 source ZIP deploys through Linux Oryx.
  Clean dependency restore, typecheck, 37 application tests and production build pass.
- [x] Azure Policy validation: actual resource-provider preflight passes for the
  approved East US 2/Sweden resources; no policy exception is added.
- [x] Revised static role/security review: retain project-scoped Agent Consumer
  and add explicitly approved project-scoped Cognitive Services User for the
  exact App Service identity. Earlier Consumer-only review does not approve this
  correction. The separate review approved it; exact runtime sufficiency has now
  passed the mandatory live gate.
- [x] Earlier independent security review: Rai found no vulnerabilities in application,
  infrastructure, or earlier region/role-name/what-if corrections. This does not
  cover the current Cognitive Services User addition.

Commands actually completed on 2026-10-26:

- `validate-deployment.sh --scope sub --location brazilsouth --subscription
  bb4b2781-6739-4fa1-994e-4ad6ce55c59c --template infra/chat.bicep
  --parameters infra/chat.parameters.json`: overall PASS, no Modify/Delete.
- `deploy/.venv/bin/python deploy/chat_deploy.py --stage validate`: PASS,
  bounded inventory **6 Create, 23 Ignore, 0 Unsupported**. Existing resources are
  unchanged. Role assignment uses a known-resource-ID-derived name so what-if can
  resolve its resource ID before the new principal exists.
- `deploy/.venv/bin/python deploy/chat_deploy.py --stage build` with Node 24 PATH:
  PASS. Allowlisted source ZIP excludes dotenv, dependencies and team state.
  Lockfile tarballs use official npm URLs with unchanged versions/integrities.
- Deployment unittest suite: 70 passed. Application build/typecheck/tests: passed.

These are predeployment checks; actual managed-identity agent authorization,
conversation continuation, health, browser UX and CORS still require live acceptance.

### Extension resources and architecture

Subscription: **TSJasonFarrell-Sub / `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`**.
The user selected **public POC with request and conversation limits** and explicitly
accepted Sweden for the new Foundry project.

| Resource | Proposed change |
|---|---|
| App Service plan | `asp-redshift-chat-bs01`, Linux **B1**, one instance, **East US 2 (`eastus2`)**, existing `rg-redshift-bs01` whose metadata remains Brazil South |
| Web app | `app-redshift-chat-bs01-bb4b2781`, **East US 2**, React static UI plus **Node 24 LTS** backend-for-frontend (BFF), same origin, system-assigned managed identity |
| Foundry project | New `redshift-test-project` child of existing AIServices account `foundry-sandbox-swc-mx01`, **Sweden Central**, existing `rg-client-sandbox-eus2-mx01` |
| Prompt agent | `redshift-chat-agent`, registered in the new project, remote MCP in its harness |
| Model | Reuse existing **`gpt-5.4-mini`**, model version **`2026-03-17`**, `GlobalStandard`, capacity **950**, observed `Succeeded`; no deployment or capacity increase |
| Existing MCP | Remains **Brazil South**; no image/configuration/identity change except the later exact-origin CORS-only update |

Actual ARM validation in Brazil South failed with
`InternalSubscriptionIsOverQuotaForSku`: Linux B1 limit **0**, usage **0**, required
**1**. A minimum quota-1 request failed with `QuotaNotAvailableForResource`, request
`ec9d9495-e3da-4602-ae9e-4610d235992b`. Azure quota CLI verified East US 2 Linux B1
limit **11**, usage **0**. The approved alternative changes only the new plan/site
region; it does not rename their historical `bs01` names, relocate the resource
group, or change existing MCP/Foundry placement. Bicep `appLocation` is constrained
to `eastus2`, and runtime inventory requires **both** plan and site in that region.
Subscription deployment-record location remains `brazilsouth` to avoid existing
deployment name/location conflicts. Project, site and process are now provisioned;
that is not proof of successful chat acceptance.

Earlier research observed no child named `redshift-test-project`; it now exists.
Names, capacity, policies and supported runtime must be rechecked before any further
approved provisioning.
Model metadata advertises GA `agentsV2` and Responses support; this is not proof of
end-to-end agent authorization or MCP execution. This model satisfies GPT 5.3+
policy; no model router or unapproved model fallback. **GlobalStandard inference
is not guaranteed Sweden-only**: prompts and MCP metadata can cross regions.

Flow: **browser → same-origin BFF → Foundry registered prompt agent → existing
remote MCP → Redshift → agent's natural-language answer → browser**.
Use `@azure/ai-projects` **2.9.0**, `@azure/identity` **4.14.0** (Node >=22),
GA project API **`v1`**, and project ARM API **`2026-09-01`**; revalidate GA
versions/schema before provisioning. Follow the official TypeScript pattern
`getOpenAIClient().responses.create(..., {body: {agent_reference: ...}})` [E2].
Use the server-owned `previous_response_id` for continuation, not browser-supplied
response IDs; verify this exact combination in the staged gate.
Do not use the agent-scoped endpoint helper requiring `allowPreview: true`.

No new Foundry account, resource group, custom agent container, storage account,
transcript database, model deployment, VNet or private endpoint is proposed.
Do not alter the existing MCP image, database credentials, AWS rules or identities.

### Tool scope and user experience

- Agent MCP URL:
  `https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp`.
  Configure remote MCP `allowed_tools` as exactly **`test_connection`,
  `list_schemas`, `list_tables`, `describe_table`**; `require_approval: "never"`
  applies only to these four bounded read-only tools [E3]. No wildcard tools.
- These tools answer **connection and metadata questions**, not business-row
  aggregates such as revenue totals. Instruct the agent to explain this limitation
  rather than fabricate results. No arbitrary SQL/query tool, direct-query API,
  code interpreter, browser MCP/model access or alternative database path.
  The fixed internal `SELECT 1` connection check is not a user-query capability.
- Render actual user/assistant conversation and tool-backed natural-language
  answers, with loading, sanitized error, explicit retry and clear-chat controls.
  Render escaped text or sanitized Markdown, never unsanitized HTML. Show a
  synthetic-data/public-POC notice and metadata-only scope.

### Identity, security and staged authorization gate

Use App Service **system managed identity**, with tokens and SDK calls only in the
BFF. No keys/secrets in browser, code, config files or logs; no new credential is
needed for the existing anonymous MCP. Keep existing MCP Key Vault/TLS controls.
Use HTTPS-only, current supported TLS, same-origin BFF APIs and exact-Origin CSRF
checks for browser state-changing requests; reject foreign/missing browser Origin.
Do not log chat text, cookies, tokens or raw downstream errors.

**Authorization is an explicit unresolved pre-live gate, not a proven design.**
The actual managed-identity 403 establishes that **Foundry Agent Consumer**
(`eed3b665-ab3a-47b6-8f48-c9382fb1dad6`) alone is insufficient for this deployed
GA project Responses path. Retain that existing assignment; do not delete it.
After live built-in-role permission review and disclosure of broader project
data/connection-secret access, JasonFarrell explicitly selected **“Yes, use
Cognitive Services User at project scope”**. Add that built-in role
(`a97b65f3-24c7-4388-baec-2e87135dc908`) **only** for App Service managed identity
`ebcf9b66-cca4-46a6-a344-3f100ea7eb0d` at:

`/subscriptions/bb4b2781-6739-4fa1-994e-4ad6ce55c59c/resourceGroups/rg-client-sandbox-eus2-mx01/providers/Microsoft.CognitiveServices/accounts/foundry-sandbox-swc-mx01/projects/redshift-test-project`

This is explicit acceptance of this built-in role's broader permissions within
that project, not permission to grant it at account/RG/subscription scope or to
create a custom role. No project-identity grant, credential fallback, model,
agent-definition, identity or site change is approved by this correction.

After approval, execute only this bounded sequence:

1. Obtain independent peer/security review of this exact role correction, then
   inspect the assignment-only incremental what-if in `deploy/CHAT-README.md`.
   Do not rerun full `prerequisites`, app deployment or agent provisioning.
2. Create **only the additional project-scoped Cognitive Services User assignment**
   using `infra/chat-role.bicep` with `includeConsumerAssignment=false`.
   The existing Consumer remains untouched in incremental mode. Inspect effective
   direct/inherited/group assignments: require exactly the two approved roles,
   both direct to this identity at this project; reject extra, conditional,
   group or wider-scope grants. Keep chat unready.
3. From the **actual App Service managed identity**, after bounded propagation
   retries, invoke the GA project Responses path against the registered agent,
   observe a real allowed MCP call and natural-language reply, then a follow-up
   using the stored prior-response ID. Capture sanitized identity, endpoint,
   role/scope, response/tool evidence; do not substitute developer credentials.
4. **Stop and do not release/claim healthy ready chat** if any authorization,
   model access, tool execution or continuation test fails. No preview endpoint,
   API-key, model-only, unapproved-role or direct-SQL fallback. Existing MCP stays live.

Do **not** provision the previously suggested speculative custom role.
Foundry User is not approved for this runtime.
Microsoft's baseline guidance also recommends **account-scoped Foundry User for
the project managed identity** [E1]; its necessity for this exact workload remains
unproven, so that grant is **not included**, including implicit portal defaults.
Any further role, custom role, account-scope project-identity permission or other scope
expansion requires failure evidence, a revised least-privilege proposal, independent
review and **new approval** before applying it.

### Public POC limits and retention

Enforce limits **on the server before any new Foundry API request**:

- Random opaque **HttpOnly, Secure, SameSite=Strict** session cookie; server maps it
  to prior-response ID, turn count and **30-minute absolute TTL**. Browser cannot
  select another session's response IDs or override agent/model/tool settings.
- Maximum **20 user turns per chain**, not 20 displayed messages. Reserve each
  attempt atomically before dispatch; serialize requests within a session.
  Reject turn 21 without an API call; retries consume a turn and cannot silently
  replay a billable request. Clear chat creates a new chain, not a financial cap.
- Input **2,000 characters**, output **800 tokens per response**, maximum **4 tool
  calls per response**, at most **2 concurrent chat requests** across the instance.
  Verify SDK/platform tool-call limit semantics against remote MCP during
  implementation; if it cannot enforce this bound, stop for revised approval.
- **5 requests/minute/IP** on public BFF dynamic routes, including health/session
  creation and clear operations. Validate IP syntax and the trusted App Service
  proxy chain; never trust arbitrary client `X-Forwarded-For`. Test spoof rejection.
- In-memory session/IP stores: TTL eviction, maximum **1,000 sessions / 10,000 IP
  entries**, reject new entries when full rather than discarding active protections.
  No persistent chat transcript database. One instance only; scaling needs review.

Restart resets server maps and rate limits; expired/restarted sessions require a
new chain. Browser history is ephemeral. Clear/expiry removes local state **but
does not delete remote Foundry Responses**; disclose provider-side retention and
verify applicable retention settings before release. Limits reset and users can
change IP/cookies; these are POC abuse controls, **not durable quotas or a spend cap**.
Bound request deadlines and SDK retries; timeouts must not start hidden extra chains.

### Independent Redshift health and narrowly scoped CORS

The BFF health route calls **only MCP `test_connection`**, without AI, using a
bounded MCP session closed in `finally`. Use a single-flight check, a **35-second
overall deadline** accommodating roughly 30 seconds for handshake plus the
existing connection/statement timeouts (10 seconds each), and **30-second cache**.
Report `checkedAt` and `checking`, `stale` or `unavailable` explicitly; never label
an expired success as current. Process `/healthz` alone is not database proof.

No browser-direct MCP is required; browser/BFF remain same-origin. If applying the
requested frontend CORS allowlist, change **only ACA ingress `corsPolicy`** using
GA `Microsoft.App/containerApps@2026-07-01` [E4]: exact deployed frontend HTTPS
origin, methods **GET, POST, DELETE, OPTIONS**, `allowCredentials: false`, allowed
headers **Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version, Last-Event-ID**,
exposed header **Mcp-Session-Id**. No wildcard origins.
SDK `allowed_origins` is **not CORS**; preserve its Origin and MCP Host guards.
Do not add the frontend as an allowed Host or unnecessarily modify SDK origins:
Foundry/BFF calls have no browser Origin. Test real OPTIONS response headers,
hostile-Origin rejection and continued successful agent/BFF no-Origin calls.
CORS is not authentication and cannot prevent direct abuse of the existing public MCP.

### Incremental cost and release acceptance

The approved ceiling remains **$14.60/month at 730 hours** for Linux B1, based on
the earlier Brazil South **$0.020/hour** estimate. East US 2 is the user-approved
quota-available alternative; recheck its public retail rate before provisioning
and stop for approval if that ceiling would increase. Add model input/output tokens, applicable agent/tool
usage, transfer and existing Azure/AWS charges. Reusing capacity 950 does not mean
free inference or new reserved capacity. Recheck pricing; no budget or hard spend
cap is provisioned. The earlier MCP baseline below remains separate and unchanged.

Before enabling chat, require independent architecture/security/code review and:

- React/BFF build and targeted tests for escaping, CSRF, cookie/session isolation,
  TTL/clear/restart, concurrent turn reservation, turn-21 rejection before SDK use,
  input/output/tool bounds, rate-limit IP spoofing, storage limits and sanitized errors.
- Health tests for timeout, single-flight/cache expiry, `checkedAt`, database-down
  reporting and MCP session cleanup; separate process-health semantics.
- Exact deployed inventory/roles and the **actual-identity staged authorization
  gate above**, then browser multi-turn conversation with observed allowed MCP
  use, actual assistant answer, retry/clear and live Redshift health.
- Metadata question succeeds; business aggregate question explains unsupported
  scope. No SQL endpoint/tool or credentials in bundle, logs or network payloads.
  OPTIONS/hostile-origin/Host tests pass and existing MCP acceptance still passes.
- Record sanitized URLs, agent/model versions and live evidence. Only then mark
  **this extension** ready/deployed; never reuse old MCP evidence as chat proof.

**Approval recorded:** the user approved this public POC scope, cross-region/model
routing disclosure, incremental costs, resettable controls/remote-retention caveat,
and **conditional project-scoped Agent Consumer smoke-test stage**, then approved
East US 2 for the new App Service plan/site. Following the actual-identity 403 and
live permission disclosure, the user separately approved **Cognitive Services User
at project scope only** as recorded above. Approval does not prove authorization
sufficiency or authorize any other broader role/scope. Exact frontend CORS origin
must come from the actual deployed ARM `defaultHostName`; never synthesize it.
Any failed gate pauses release for decision.

**Next gate:** independent peer/security review, followed by parent-run
assignment-only validation/what-if and, only after those gates, the isolated
assignment command in `deploy/CHAT-README.md`. Stable additional assignment GUID:
`1d0a3438-808c-535c-a6da-79dda6fc03c0`.
No cloud command was run for this correction. Local compilation and mocked tests
are not live authorization evidence. Actual-identity agent + allowed MCP +
continuation, CORS/browser and original-MCP regression acceptance remain release
gates. Only successful actual-runtime verification may write `verified_at`.

**Official extension references**

- [E1 — Foundry RBAC and project-scoped Agent Consumer](https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry)
- [E2 — Prompt-agent quickstart and TypeScript project Responses pattern](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent)
- [E3 — Remote MCP tools and approval configuration](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol)
- [E4 — ACA GA 2026-07-01 ingress/CORS schema](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2026-07-01/containerapps)

> **Status: Deployed — cloud image build and full external postdeployment verification passed on 2026-10-26.** The user selected "Approve and deploy".
> All five regional resources and their resource group are in Brazil South.
> Independent implementation and security reviews approved the POC scope and tooling corrections.
> Historical prerequisite-only preflight limitations remain documented below.
> Revised 2026-10-26 to honor: “do not use a vnet … its a poc with synthetic data”.

## Execution evidence and current boundary

The resource group `rg-redshift-bs01` and all five regional resources are deployed
in Brazil South (`brazilsouth`): `acrredshiftbs01bb4b2781`,
`umi-redshift-imagepull-mx01`, `kv-redshift-bs01`, `cae-redshift-bs01`, and
`ca-redshift-bs01`. Full live verification passed with exact inventory and role
checks. ACR is Basic with admin and anonymous pull disabled. The environment has
no VNet, managed infrastructure RG or log workspace.

- MCP: https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/mcp
- Health: https://ca-redshift-bs01.happygrass-e982f5d6.brazilsouth.azurecontainerapps.io/healthz
- ACR Linux/AMD64 build: **`cq1`**, tag `redshift-mcp-server:v1`, succeeded before app creation.
- Deployed immutable digest: **`sha256:1f7c40921f16cafb9d08df09fe98034098cf797cf43d006426993716c84a5a80`**.
- Sole active revision: **`ca-redshift-bs01--0000001`**, Healthy,
  `RunningAtMaxScale`, one replica, 0.25 vCPU / 0.5 GiB, min/max 1/1.
  `RunningAtMaxScale` is expected at the intentional maximum of one; no restart was needed.
- Password transferred directly through the SDK in memory; the app uses a
  system-identity Key Vault reference and environment `secretRef`, not a literal secret.
  The system identity has secret-scoped `Key Vault Secrets User`; the image-pull
  UMI has registry-scoped `AcrPull`. Exact-role verification found no extra roles.
  Temporary upload authority was cleaned up (`owned_officer: null`).
- All supported nonsecret connection values were independently compared in memory
  with the actual local settings and matched; no secret was printed.
- Approved AWS public IPv4 TCP5439 rule: **`sgr-041636c02c8e1089b`**;
  original rules were preserved.

The complete command
`deploy/.venv/bin/python deploy/deploy.py --apply --stage verify` succeeded,
reporting the verified URL, revision and digest. It covered infrastructure,
roles, probes, secret references, image, scaling, HTTPS 200, hostile host/origin
rejection, AWS rule, and an external official MCP client performing initialize,
`tools/list`, `test_connection` (`connected: true`, `SELECT 1`) and bounded
`list_schemas(limit=1)`. The first MCP attempt encountered a transient
`ExceptionGroup`; an isolated sanitized retry passed, followed by the entire
verification command passing. The first attempt is not recorded as a pass.

Prerequisite verification initially stopped because Key Vault reported `publicNetworkAccess: Disabled`,
despite creation and an explicit update requesting `Enabled`. The vault activity log
confirms an inherited management-group policy modified the request:
`MCAPSGovDeployPolicies`, definition `KeyVault_PublicNetwork_Modify`,
display name "SFI-NS2.2.1 Secure PaaS Resources - Key Vaults (excluding NSP configured resources)".
The policy performed `AddOrReplace` on `Microsoft.KeyVault/vaults/publicNetworkAccess`.

The user then explicitly directed: **“Use the tag SecurityControl: Ignore to override this”**.
The coordinator confirmed that the policy definition supports this exact tag exclusion,
merged `SecurityControl: Ignore` onto **only `kv-redshift-bs01`**, and successfully
enabled public access. This resolved the inherited-policy blocker without modifying
policy or tagging the resource group or unrelated resources. The imperative vault
creation payload now preserves this exact choice for future creation; existing
vaults remain untouched, and verification requires the exact tag plus public access.
The earlier Bicep preflight predates the tag choice; review/revalidate it before
future use, not as an alternative apply path over these resources.

Next, the coordinator observed the environment returned `Succeeded`, location
`Brazil South`, `infrastructureResourceGroup: null`, `vnetConfiguration: null`,
and `appLogsConfiguration: {destination: null, logAnalyticsConfiguration: null}`.
Its `workloadProfiles` contained exactly
`[{name: 'Consumption', workloadProfileType: 'Consumption', enableFips: false}]`,
with no min/max capacity fields. The verifier previously insisted on empty profiles
and stopped on this representation. The surgical correction accepts absent/null/empty
legacy profiles or exactly one built-in `Consumption` name/type with absent/null/zero
`minimumCount` and `maximumCount`; dedicated, multiple, unexpected and nonzero-capacity
profiles still fail. Region, no-subnet/internal-network, no-infrastructure-RG,
no-log-destination and resource-inventory guards are unchanged; there is no general
fallback or topology expansion. Creation still requests `--enable-workload-profiles false`.

The vault-tag/Consumption correction passed **17 synthetic deployment tests**.
The Azure CLI compatibility correction excluded the unsupported subscription
argument only from `az ad` calls (**18 tests**); the healthy
`RunningAtMaxScale` guard correction brought the deployment suite to **22 tests**.
Independent Goff security reviews found no actionable vulnerabilities in these
infrastructure/authentication changes; Goff's Devils Advocate review approved
the state predicate. Live staged execution, the new-environment quota gate,
cloud build and full workload acceptance subsequently completed. No unresolved
deployment blocker remains. Local Docker's historical PyPI TLS failure was not
reclassified as success; the approved cloud build supplied the image-validation gate.

## 1. Scope and resources

Deploy the existing metadata-only Python MCP server as an **anonymous public HTTPS** POC.
No custom VNet, subnet, NAT, private endpoint, private DNS, NSG or gateway.
The sole network-policy exclusion is the user-directed vault-only tag described above.
Retain TLS, managed identities, least-privilege RBAC and Key Vault references; synthetic data does not justify leaking passwords.
All deployment resources belong to **`rg-redshift-bs01`**, **Brazil South (`brazilsouth`)**.
Subscription: **`TSJasonFarrell-Sub` / `bb4b2781-6739-4fa1-994e-4ad6ce55c59c`**.
Tenant: `e90bd921-0e00-4e6f-b87c-713670ee27bf`.

| Resource | Name and configuration |
|---|---|
| Resource group | `rg-redshift-bs01`, Brazil South |
| Container Registry | `acrredshiftbs01bb4b2781`, **Basic**, public endpoint, admin/anonymous access disabled, permissions mode **`rbac`**, not ABAC |
| Image-pull identity | `umi-redshift-imagepull-mx01`, user-assigned; registry-scoped `AcrPull` only |
| Key Vault | **`kv-redshift-bs01`**, Standard, Entra RBAC, public endpoint, soft delete/purge protection; vault-only `SecurityControl: Ignore` |
| Container Apps environment | `cae-redshift-bs01`, **Consumption-only**, default Azure network, external; no infrastructure subnet |
| Container App | `ca-redshift-bs01`, system identity plus image-pull UMI; 0.25 vCPU / 0.5 GiB, min/max **1/1**, single revision |
| App image | `acrredshiftbs01bb4b2781.azurecr.io/redshift-mcp-server@sha256:1f7c40921f16cafb9d08df09fe98034098cf797cf43d006426993716c84a5a80`; build `cq1`, tag `v1` |
| Persistent roles | Registry-scoped `AcrPull`; secret-scoped `Key Vault Secrets User` for app system identity |

**Single-RG feasibility:** Microsoft documents a separate managed infrastructure RG **when deploying into your own network** [1].
Select supported Consumption-only (documented as legacy, not removed), explicitly `--enable-workload-profiles false`, with no subnet [2].
Azure's internal platform network is unavoidable service infrastructure, **not a customer VNet resource to provision**.
This default-network design does not require a customer-visible `MC_`/`ME_` infrastructure RG or separately billed PIP/LB.
Do not select dedicated workload profiles or add `infrastructureResourceGroup`.
The API may represent the approved Consumption-only capacity as a singleton built-in
Consumption profile; this is not permission to add dedicated capacity or a managed RG.
After creation verify the strict profile guard, absent subnet/managed RG and subscription
resource delta; stop on any other platform discrepancy rather than silently adding a second RG.
No Log Analytics/App Insights resources: explicitly select no log destination; use sanitized console/system streaming and built-in metrics.

## 2. Reused verified readiness evidence

Earlier read-only research on 2026-10-26 established the following; checks do not reserve names or guarantee capacity.

| Check | Actual result and revised implication |
|---|---|
| Subscription/providers | Enabled; App, ContainerRegistry, KeyVault, ManagedIdentity and Authorization registered; Brazil South supported |
| Names | RG absent; `kv-redshift-bs01` and `acrredshiftbs01bb4b2781` available; no deleted-vault collision; repeat before execution |
| Environment quota | Brazil `ManagedEnvironmentCount` **1/50**; proposed **2/50** |
| Consumption CPU | Existing Brazil environment **0.5/500** cores; **not** evidence of the new environment's allocation |
| Resource counts | RGs **14 → 15** (limit 980); ACR Brazil/subscription **1/2 → 2/3**; KV **0/1 → 1/2**; UMI **0/3 → 1/4** |
| App/RBAC counts | Brazil apps **2 → 3**; subscription role assignments **98 → 100**, temporary upload peak 101 |
| Unsupported quota routes | ACR/KV/identity count quotas not exposed by attempted quota APIs; actual counts are not invented limits |
| Authorization/policy | Provisioning plus Authorization write allowances observed; unrelated deny only; four policies listed, actual effects require validation/what-if |

After approved environment creation, before app deployment, query **its own** `az containerapp env list-usages`.
Require **0.5 available Consumption vCPU** for a 0.25-core replica plus replacement overlap; max 1 does not eliminate revision surge.
No new network-resource quota is needed. Recheck permissions, names and policy effects before mutation.
Previously verified latest GA APIs: App environment/app **2026-07-01**, ACR **2025-11-01**, KV **2026-05-15**,
UMI **2024-11-30**, role assignments **2022-04-01**, RG **2023-07-01**.
Validate current schema before generating staged Bicep/AZCLI; no unverified preview dependency.

## 3. Application, image and identity preparation — after approval

- Keep local binding default loopback; deployment explicitly overrides host **`0.0.0.0`**, port **8000**. Preserve Streamable HTTP **`/mcp`**.
- Configure the SDK's exact allowed hosts and HTTPS origins from the actual ACA hostname/environment domain and explicit local test settings.
  Keep DNS-rebinding protection enabled; do not use unrestricted wildcards. Account for platform probe Host headers in tests.
- Add **`/healthz`** for startup/liveness/readiness: process/HTTP health only, **no database or Key Vault calls**.
  Start lazily without a password/DB connection so the real image can bootstrap identity; health alone never proves DB acceptance.
- External ingress targets 8000, `allowInsecure=false`; platform HTTPS termination, no app authentication as already approved.
  Redshift uses TLS with certificate/hostname verification, bounded timeouts and sanitized errors; no arbitrary-SQL public tool.
- Use nonroot Python **3.13 slim**, selecting the latest supported 3.13 stable patch and verified digest at generation time.
  Pin explicit patch/distro/digest, not floating `latest`; target **`linux/amd64`**. Keep runtime dependencies locked.
- `.dockerignore` must exclude **all `.env*`**, `.venv`, caches, `.git`, `.aws`, `.azure`, `.squad`, logs, credentials and private keys.
  Upload only allowlisted runtime files/locked dependencies/Dockerfile; no `COPY . .`, secret ARG/ENV or credential-bearing helper.
- Local Docker validation was blocked by PyPI CDN TLS. Use **`az acr build`** (ACR Tasks), no local Docker daemon needed; tag **`redshift-mcp-server:v1`**.
  Basic public ACR needs no firewall bootstrap/window. Validate build-context contents first; record successful Linux/AMD64 build and digest.
  Tasks execution succeeded as run `cq1`; the exact Linux/AMD64 image passed this gate before app creation.
- Assign UMI **`AcrPull`** (`7f951dda-4ed3-4680-a7ca-43fe172d538d`) at this registry only.
  Enable ACR ARM-audience authentication; pass the UMI **resource ID** as registry identity and attach it to the app.
  Microsoft explicitly supports creating the app directly with its private image using a preauthorized UMI [3]; no dummy image/service needed.
- Assign system identity **`Key Vault Secrets User`** (`4633458b-17de-408a-b874-0445c86b69e6`) at
  `<vault-resource-id>/secrets/redshift-password` (unversioned scope) where supported; never grant app Owner/Contributor or vault-wide write.
  Do not set global `AZURE_CLIENT_ID` to the image-pull identity.

## 4. Secure transfer and staged execution

1. Parent challenges correctness/security/cost; obtain explicit plan approval. Then implement tests/runtime/container/README and staged Bicep plus orchestration.
   Prerequisite `azure-validate` and validation/what-if completed before approved execution;
   the later vault tag choice and profile-verifier correction require parent review.
2. Create exact RG, Basic ACR, UMI and public RBAC vault; build sanitized source in ACR; authorize UMI image pulls.
   Create Consumption-only environment without a subnet/log workspace and verify its quota and single-RG inventory.
3. Upload current validated local Redshift password through the application's **`load_environment()` API** into
   `SecretClient.set_secret("redshift-password", password)` using signed-in Entra authentication, **in memory only**.
   Never view/read raw `.env` with tools, dump settings, serialize credentials, use password CLI arguments/substitutions,
   enable HTTP-body/debug logging, or write a password file. No credentials enter source, image or ordinary configuration.
4. If needed, temporarily grant uploader `Key Vault Secrets Officer` at this new vault to create the secret.
   SDK read-back/in-memory equality may emit only success/version metadata; remove temporary role in `finally`, also on failure.
   Preserve the existing local configuration. Public vault data access still requires Entra RBAC; it is not anonymous.
5. Create app **using our real image and real entrypoint**, both identities, nonsecret settings, lazy startup and `/healthz`; no password reference yet.
   Get its system principal and actual ingress FQDN; update exact SDK host/origin configuration.
6. Assign secret-scoped read role, wait/retry bounded RBAC propagation, then add ACA secret **reference**:
   `keyVaultUrl: https://kv-redshift-bs01.vault.azure.net/secrets/redshift-password`, `identity: system`.
   Map existing password environment setting using **`secretRef`**, never a literal password [4]. Restart/create revision as required.
7. Apply the explicitly approved TCP5439 AWS rule below, then real DB and external MCP acceptance. Stop on authorization failures.
   Remove only temporary permissions/POC-owned AWS additions on failed rollback; never remove pre-existing rules or destroy resources without approval.

## 5. User-approved public Redshift access

Existing read-only checks confirmed public/AVAILABLE `default-workgroup`, database `dev`, port **5439**:
`default-workgroup.684925376801.us-east-2.redshift-serverless.amazonaws.com`.
Preserve validated username/settings. AWS role-based DB authentication/ECS-only role remains deferred; current password is locally validated.

The user explicitly directed that the Redshift firewall be wide open for this
synthetic-data POC after being offered specific-IP rules and a quota increase.
Add only **TCP5439 from `0.0.0.0/0`** to **`sg-c2bac6ae`** in `us-east-2`.
This is not authorization for all ports, IPv6, different security groups, or
unrelated changes. Preserve existing rules and record the new rule ID.
The rule is idempotent: reuse an equivalent existing rule rather than duplicate it.
The current default AWS CLI principal is account root; this is a known operational
risk, not a request to create credentials or expand IAM permissions.
No static Azure egress, NAT, quota increase, or outbound-IP reconciliation is needed.
Retain Redshift TLS and password authentication. Public SQL access and anonymous
public metadata MCP access are explicit POC risk acceptances, not production guidance.
Verify the rule and the actual Azure-to-Redshift connection after deployment.

## 6. Acceptance and cost

Do not mark Deployed until image pull with UMI, system-identity Key Vault reference resolution, healthy revision and HTTPS `/healthz` pass.
From an external official MCP client, initialize anonymously at `https://<actual-fqdn>/mcp`, run `tools/list` and a bounded metadata call.
Verify live **`SELECT 1`** through an internal controlled connection test (not a new arbitrary-SQL public tool).
Check host/origin rejection, no password leakage, expected roles, no admin ACR credentials, preserved AWS rules and single-RG Brazil inventory.
Publish URL, image digest/revision and sanitized test evidence. A successful local test or health probe is not Azure-to-AWS proof.

Retail Prices API read live **2026-10-26**, USD Brazil South Consumption list rates; **730 hours/month**, no assumed free grant:

| Item | Verified rate | Approximate monthly amount |
|---|---|---:|
| ACR Basic Registry Unit | **$0.1666/day** | **$5.07** |
| ACA 0.25 CPU / 0.5 GiB, min 1 | Active CPU $0.000024/sec; idle CPU $0.000003/sec; memory $0.000003/GiB-sec | **$5.91 idle–$19.71 active** |
| KV Standard operations | $0.03/10,000 | Pennies at POC volume |
| ACR Tasks | Paid meter $0.0001/vCPU-sec (also a zero-rate tier exists) | About $0.12 for 2-vCPU/10-min build |

**Baseline approximately $11–$25/month**, plus builds, requests ($0.40/million before grants), storage overages, outbound transfer/taxes and AWS Redshift charges.
No NAT, private-link, customer PIP/LB, private DNS or dedicated-environment fee is planned. Free grants may reduce ACA charges but may be shared/consumed already.
Planning allowance **$30/month Azure plus variable transfer/AWS**, not an enforced cap or guaranteed quote [6].
Min 1 favors an immediately healthy POC; min 0 is a later explicit cost/cold-start tradeoff, not assumed.

## 7. Sources and remaining approval gates

### Prerequisite preflight and actual execution gates completed

- [x] Core validation: Azure CLI/authentication, Bicep build, subscription-scope
  ARM validation and what-if of the real prerequisite resources.
- [x] Bootstrap build-context gate: deny-by-default context, hash-locked Linux
  dependencies, application wheel, 102 application tests and 12 deployment tests.
- [x] Azure Policy validation: inspect applicable assignments and effects for
  the selected subscription, region, SKUs, identities and public POC endpoints.
- [x] Static role verification: registry-scoped AcrPull for the UMI and
  secret-scoped Key Vault Secrets User for the system identity.
- [x] Record prerequisite validation proof and complete azure-validate before azure-deploy.
- [x] Review corrected vault-tag, Consumption, Azure CLI and healthy-revision guards.
- [x] Complete live prerequisite verification and new-environment quota gate.
- [x] Complete exact production Linux/AMD64 cloud image build before app creation.
- [x] Deploy digest-pinned app, configure managed-identity secret reference, clean temporary authority and apply approved AWS rule.
- [x] Pass full external MCP/Redshift and infrastructure verification; publish URLs, revision and digest.

### Section 7: Validation Proof

Historical ARM preflight scope: **non-workload prerequisites only**, before ACR
cloud image build. Actual cloud build and postdeployment verification subsequently
completed; they do not expand that preflight into a full-template validation.
Evidence collected during this deployment session on 2026-10-26.

| Check | Command or tool | Result |
|---|---|---|
| Source/context | `deploy/.venv/bin/python deploy/deploy.py --check` | Pass; no dotenv loaded or uploaded |
| Deployment tests | `deploy/.venv/bin/python -m unittest discover -s deploy -p test_deploy.py -q` | 17 passed after vault-tag/profile correction; 18 after narrow `az ad` compatibility correction; 22 after healthy `RunningAtMaxScale` guard correction |
| Application tests | Application `.venv/bin/python -m pytest -q` | 102 passed |
| Lint/format/dependencies | Application Ruff check/format and `pip check` | Pass |
| ARM core preflight | `validate-deployment.sh --scope sub --location brazilsouth --subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c --template infra/redshift-bs01.bicep --parameters infra/main.parameters.json` | CLI, auth, compile, provider validation and what-if passed; 7 Create, 0 Modify, 0 Delete |
| Application wheel | `pip wheel --no-deps --no-build-isolation` | Pass |
| Policy | Assignment/definition inspection, provider preflight, then execution activity log | Preflight missed inherited vault network modification; resolved during execution by exact user-approved vault-only tag exclusion, then public access enabled |
| Static roles | Independent code/security review | UMI registry-scoped AcrPull; app system identity secret-scoped Secrets User |
| Local Docker | Exact production Dockerfile, Linux/AMD64 build attempted | Historically blocked by PyPI CDN TLS connectivity, not passed; approved cloud alternative completed before app creation |
| Cloud image | ACR Tasks exact Linux/AMD64 production build | Run `cq1` succeeded; deployed immutable digest recorded above |
| Live workload | `deploy/.venv/bin/python deploy/deploy.py --apply --stage verify` | Full infrastructure and external MCP/Redshift verification passed; first transient MCP failure, isolated retry and subsequent complete pass distinguished above |
| Reviews | Independent integration/security reviews, prerequisite-template review and later Goff reviews | Approved within explicit public synthetic-POC scope; no actionable infrastructure/auth vulnerabilities; healthy-state predicate approved |

Historical preflight validated by: `azure-validate` workflow; prerequisite-only
scope. Workload/image validation and live postdeployment tests are now complete.

### Staged validation boundary

The first deployment gate covers **non-workload prerequisites only**: resource
group, registry, identities/roles, vault, and Container Apps environment.
ARM validation and what-if passed with seven Creates, zero Modifies/Deletes.
Local Docker dependency downloads fail because the host cannot establish TLS
to the official PyPI file CDN; certificate verification has not been weakened.
After validated prerequisite creation, use the already-approved ACR Tasks
Linux/AMD64 build as the **mandatory image-validation gate before app creation**.
Do not mark the workload healthy or complete until that exact production image
builds and external MCP/Redshift acceptance passes. A local build was attempted,
not passed; cloud run `cq1` and subsequent full external acceptance now satisfy
those gates. No nonexistent full-template workload preflight is claimed.

1. [Custom networks / managed resources](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks#managed-resources): separate RG condition is deployment into **your own network**.
2. [Environment types](https://learn.microsoft.com/en-us/azure/container-apps/environment#types), [networking/default network/outbound IP changes](https://learn.microsoft.com/en-us/azure/container-apps/networking), [CLI environment creation](https://learn.microsoft.com/en-us/cli/azure/containerapp/env#az-containerapp-env-create).
3. [Managed-identity ACR pulls, including direct private-image bootstrap](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull).
4. [Key Vault secret references](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets#reference-secret-from-key-vault).
5. [Container Apps GET GA 2026-07-01 / outboundIpAddresses](https://learn.microsoft.com/en-us/rest/api/resource-manager/containerapps/container-apps/get?view=rest-resource-manager-containerapps-2026-07-01).
6. [Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), [ACA billing](https://learn.microsoft.com/en-us/azure/container-apps/billing), [ACA quotas](https://learn.microsoft.com/en-us/azure/container-apps/quotas).
7. [AWS security-group quotas and rule counting](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html#vpc-limits-security-groups).

**Remaining deployment gates: none.** Reviewed tooling corrections, live prerequisite
and quota checks, mandatory cloud image build, app/configure stages and full external
MCP/Redshift acceptance completed. Public unauthenticated MCP, no VNet, vault-only
policy exclusion and TCP5439 from any IPv4 address are user-directed synthetic-POC
risk acceptances, not production recommendations.
Prepared artifacts: application hosting/probe changes, digest-pinned Dockerfile,
hash-locked dependencies, deny-by-default build context, and `deploy/` staged
automation with a dedicated tooling environment. Approved deployment mutations and
verification are complete; `deploy/state.json` retains nonsecret resumable metadata.
**Image/workload cloud-validated, deployed and externally verified.**
