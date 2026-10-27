# Redshift Analytics chat

**Current hosting target: Azure Container Apps.** See
[`deploy/CHAT-ACA.md`](../../deploy/CHAT-ACA.md) for the reviewed-target container
preparation and operator gates. App Service recovery instructions are historical;
do not use run-package/Oryx repair for this migration.

Small React/TypeScript UI and Node **24 LTS** backend-for-frontend (BFF).
The BFF serves the built UI and same-origin APIs. The browser never receives
Foundry/MCP endpoints, provider IDs or credentials. There is **no SQL/query API**.
Answers come from the registered Foundry prompt agent, not a direct model call.

For the official-MCP POC, server/Foundry response calls are bounded at230seconds,
the browser at235seconds, below ACA's240-second HTTP ingress limit. Four tools
remain the maximum; Python operations retain their50-second budget and database
statements their verified10-second setting. Health gets60seconds including MCP
setup/cleanup. Cancellation is not proof of SQL settlement: quarantine and
explicit session reset requirements are unchanged.

## Data-backed business questions

The public UI and document metadata use the generic **Redshift Analytics** brand,
without client-identifying copy. The workspace label, welcome, suggested questions
and composer ask about production totals, top wells, operating costs and monthly
prices from `oge_synthetic`. Connection health remains available separately.
The synthetic-data/public-POC, privacy, retention, reset and usage-limit notices
remain explicit. Analytics uses strict backend-interpreted versioned plans, not SQL.
No revenue/profit, gross value, ratios or arbitrary joins are supported.
The implementation is local; analytics deployment and numeric live acceptance
are pending independent implementation review.
UI regression tests cover this copy and the document title/description.

## Run and validate

Use Node 24 LTS and npm. From this directory:

```sh
npm ci
npm run build
npm test
npm run typecheck
```

The lockfile pins official public `https://registry.npmjs.org/` tarball URLs,
including Linux optional dependencies. No Microsoft feed, private registry,
authentication, or local npm configuration is required by the source/Oryx
deployment. Registry normalization preserved every package version, integrity
hash, and dependency edge. Vite remains pinned at 7.3.7; this restore repair
does not upgrade or downgrade packages.

On machines with a configured mirror, npm may rewrite public tarball hosts.
Use a mirror that serves canonical npm package paths, or select the official
registry for that command without changing global configuration:

```sh
npm_config_registry=https://registry.npmjs.org \
  npm_config_replace_registry_host=never npm ci
```

Keep TLS verification enabled. A cached restore is valid only when the cache
contains the locked package content; changing registries does not make an empty
cache usable offline. The previous Microsoft-feed lockfile combined with this
machine's `replace-registry-host=always` setting produced invalid nested feed
paths on its proxy and a `zod-to-json-schema` 404.

Runtime values are **environment variables**, never `.env` files:

| Variable | Requirement |
|---|---|
| `NODE_ENV` | `production` on App Service. Only exact `development` enables explicit `AzureCliCredential`; all other values use `ManagedIdentityCredential`. |
| `PORT` | Default `8080`; App Service may supply it. |
| `PUBLIC_ORIGIN` | Required production exact HTTPS browser origin, **no trailing slash/path**. Must match browser `Origin`. |
| `FOUNDRY_PROJECT_ENDPOINT` | Required HTTPS `https://<account>.services.ai.azure.com/api/projects/<project>`; deployer verifies the actual project endpoint. |
| `FOUNDRY_AGENT_NAME` | Default `redshift-chat-agent`. Server-owned registered agent name. |
| `FOUNDRY_AGENT_VERSION` | Optional server-owned agent version; pin the approved version for release. |
| `MCP_SERVER_URL` | Required HTTPS URL of the existing StreamableHTTP MCP `/mcp` endpoint; used **only** for health checks. Agent tools are configured separately by the deployer. |

Production starts with **`npm start`**, which executes
**`node dist/server/index.js`**. It needs only production npm dependencies and
compiled artifacts; no TypeScript runtime or dev dependency is used at startup.
Startup fails closed if required configuration is absent/invalid.

For local development, set placeholders to actual approved resources in your
shell (not a file), authenticate separately with your own authorized Azure CLI
login, then use two terminals:

```sh
export NODE_ENV=development
export PUBLIC_ORIGIN=http://127.0.0.1:5173
export FOUNDRY_PROJECT_ENDPOINT=https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT
export FOUNDRY_AGENT_NAME=redshift-chat-agent
export MCP_SERVER_URL=https://YOUR-MCP-HOST/mcp
npm run dev
# Second terminal, same directory:
npm run dev:client
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the BFF on port 8080.
The development cookie is not Secure, **only** for local loopback HTTP.
Production uses a different `__Host-` cookie with Secure always enabled.
Local CLI success does **not** establish production managed-identity access.

## Deployment handoff (deployer only)

No resource, role, agent, model, CORS or other infrastructure changes are made
by this app. Target: Linux App Service B1, one instance, Node 24 LTS,
`app-redshift-chat-bs01-bb4b2781`, plan `asp-redshift-chat-bs01`, Brazil South.

### Selected deployment: full-source ZIP and Linux Oryx build

The parent deployer selected **full-source**, not the alternative precompiled
recipe below. Validate locally or in CI first. Package only this allowlist,
with **contents at zip root**, not an extra `redshift-chat/` directory:

```sh
npm ci
npm run build
npm test
npm run typecheck
zip -q -r redshift-chat-source.zip client server vite.config.ts tsconfig.json tsconfig.server.json package.json package-lock.json
```

Do not include `dist`, `node_modules`, tests, environment files, runtime downloads
or any other workspace files. The archive must be new: `zip` updates an existing
archive and can otherwise retain stale entries. Inspect its entries before upload.

Configure App Service/Oryx for this **source** archive:

- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- `NPM_CONFIG_PRODUCTION=false` so TypeScript/Vite dev dependencies exist at build time
- default Oryx npm install/build path running `npm run build`; unset any
  `CUSTOM_BUILD_COMMAND` from the precompiled strategy
- `POST_BUILD_COMMAND=npm prune --omit=dev --production=true --ignore-scripts`
- Node runtime `NODE|24-lts` (verify current runtime availability)
- startup command `npm start`
- the production runtime variables above, including the exact deployed public URL
- no `WEBSITE_RUN_FROM_PACKAGE` combination that disables the required remote build

Oryx must compile the client/server and then prune development dependencies.
The resulting runtime needs `dist/client`, `dist/server`, `package.json`,
`package-lock.json` and Linux production dependencies. Verify build/prune success
in Oryx logs and check `/healthz` and built `/` after deployment. Local macOS
dependencies must never be shipped as Linux runtime dependencies.

### Alternative only: precompiled ZIP

This is **not the parent-selected deployment strategy**. A separate precompiled
archive can contain only `dist`, `package.json`, and `package-lock.json` at root,
after a local/CI `npm run build`. It needs Linux production dependency installation:

- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- `CUSTOM_BUILD_COMMAND=npm ci --omit=dev --ignore-scripts`
- unset the source strategy's `POST_BUILD_COMMAND` and `NPM_CONFIG_PRODUCTION`
  overrides; retain the same Node runtime, startup and production app settings

`CUSTOM_BUILD_COMMAND` replaces Oryx's default build/install path, avoiding its
automatic `npm run build` against a zip intentionally containing no source/dev
tools. Deploying this archive with remote build disabled and no Linux dependencies
will not work. Never mix source and precompiled settings. See
[official Oryx configuration](https://github.com/microsoft/Oryx/blob/main/doc/configuration.md).

## Foundry request and release gate

Verified against official quickstart and installed SDK/type definitions:
`@azure/ai-projects` **2.9.0**, `@azure/identity` **4.14.0**. The project client
uses GA **`v1`**; its OpenAI client uses the GA project `/openai/v1` base URL.
`AgentReference.version` is supported.

```ts
const openai = project.getOpenAIClient({
  maxRetries: 0, timeout: 230_000, logLevel: 'off',
});
await openai.responses.create(
  {
    input: message,
    previous_response_id: serverOwnedPreviousId, // omitted on the first turn
    max_output_tokens: 800,
    max_tool_calls: 4,
    stream: false,
    store: true,
  },
  {
    body: {
      agent_reference: {
        name: configuredName, type: 'agent_reference',
        // version: configuredVersion, when pinned
      },
    },
    signal: dispatchAbortSignal,
    timeout: 230_000,
    maxRetries: 0,
  },
);
```

The SDK's API-version enum is type-only exported, so the source uses the exact
verified literal `'v1' as KnownApiVersions`, not an invented API version.
There is **no** `azureConfig.agentName`, `allowPreview`, request `model`, key,
DefaultAzureCredential, broad-role retry, SQL fallback, or hidden provider retry.
Production explicitly selects system `ManagedIdentityCredential`.
Token acquisition receives the dispatch cancellation signal; managed-identity
HTTP operations have a 10-second deadline and SDK retries disabled. SDK HTTP
logging is disabled; app logs contain only fixed event/error codes.

The registered prompt agent is created/configured **by the deployer**, using
existing `gpt-5.4-mini` deployment (model version `2026-03-17`), with exactly:
`get_data_context`, `analyze_data`.
Its MCP `allowed_tools` must be those two names only and `require_approval:
"never"` must apply only to that allowlist. No other tools or direct database
path are permitted. `test_connection` remains BFF-health-only; legacy metadata
tools remain available to existing MCP clients but not to the agent.
The agent must execute `analyze_data` on each data answer/follow-up.
Context establishes observed date coverage, never an assumption of current data.
The BFF independently enforces this boundary, not just the instructions.

### Fail-closed answer protocol

Every registered-agent final output must be exactly one JSON object (no markdown):

```json
{"kind":"answer","reply":"<concise natural-language explanation of this response's executed result>"}
{"kind":"clarification","reason":"missing_period"}
{"kind":"clarification","reason":"ambiguous_request"}
{"kind":"unsupported","reason":"unsupported_metric"}
{"kind":"unsupported","reason":"unsupported_scope"}
```

These are alternative objects, not one multi-object response. `answer` requires
at least one successful **current response** `analyze_data` MCP call with a
validated executed-result envelope. An empty call list, context-only calls,
metadata, prose assertions or `previous_response_id` cannot satisfy it. The same
check runs again on every follow-up. The completed Responses object is required;
an optional MCP call status, when present, must also be `completed` (the installed
OpenAI SDK documents that field as optional). Any failed/malformed call rejects
the whole response, including a non-data response; there is no fallback.

Non-data responses accept **only** `kind` and one enumerated `reason`, never
model-authored reply text, labels, numbers or extra fields. The BFF renders fixed
questions/refusals. Thus tagging an invented total as clarification cannot expose
it. Classification does not rely on a numeral regex. `answer` accepts only
`kind` and `reply`; plain prose, unknown tags/reasons, malformed/oversized JSON
and incomplete model output return the existing sanitized error without advancing
the successful continuation chain.

This is server-enforced JSON parsing of final text, **not a claim of Foundry
constrained decoding**. No new response-format API field, preview API, model
fallback, credentials or SDK dependency was introduced. Instructions request the
protocol; the BFF, not model compliance, determines whether output is usable.
The original final-protocol rollout required the matching pinned agent definition.
The serialization-only fix below does not change that registered v2 definition.

The installed official MCP `CallToolResultSchema` validates wrapped tool output.
FastMCP's single JSON text block and `structuredContent`, when both are present,
must agree; `isError` and invalid/inconsistent wrappers fail closed. Direct
business JSON is also accepted for Foundry serialization. The local compatibility
fix additionally recognizes the observed GA encoding:
`JSON.stringify(payload) + "\n" + JSON.stringify({structuredResponse: payload})`.
It accepts exactly two object documents separated only by JSON whitespace; the
second must have only `structuredResponse`, an object deeply equal to the first
(object key order may differ; array order and types may not). A quote/escape-aware
boundary scan supports multiline JSON without splitting on LF. Nested MCP or
`structuredResponse` wrappers, mismatches, extra keys/documents, malformed JSON,
nonobjects and surrounding prose fail closed. The original **256 KiB total UTF-8
input bound**, including both documents and whitespace, remains in force.
This normalization does not itself establish analysis evidence. Analysis validation
requires the version, execution flag/timestamp, supported source/dataset/grain,
plan/measure/unit shape, bounded rows, counts, decimal strings, observation fields
and consistent status/truncation. Exact decimals are not converted to floating
point. This is result validation; the backend remains the authoritative strict
plan validator/compiler. No backend execution code changed for this revision.

Empty analyses render an honest **server-owned** no-observations notice instead
of model prose. Partial/truncated or null-bearing analyses prepend mandatory
server-owned caveats to their grounded explanation, preserving legitimate top-N
and available-observation answers without implying complete coverage or zero.
Truncated data sets `truncated: true`;
malformed/incomplete model output is an error, not a successful partial answer.
These notices do not invent zeros or claim complete totals. A normal complete
result permits the model's explanation, not a mathematical proof that every
word matches its evidence; exact numerical release acceptance remains mandatory.

`max_tool_calls` is typed/documented as the maximum total built-in tool calls
per response, across tools. MCP is a hosted tool in the Responses tool union.
The BFF sends **4** and rejects returned MCP calls outside the allowlist, errors,
approval requests, or more than four calls. That response validation is defense
in depth, **not** a substitute for platform-side pre-execution enforcement.
The actual Foundry remote-MCP enforcement semantics still require the staged
deployment check. Stop release for revised approval if the service cannot enforce
this bound; do not silently remove it.

**Not yet live-verified:** new-project-scoped **Foundry Agent Consumer** sufficiency
for this exact GA project Responses + `agent_reference` + `previous_response_id`
path, actual tool execution, continuation, output/tool bounds and retention.
The deployer must validate from the **actual App Service managed identity**,
without an inherited broad grant masking the result, and capture sanitized
evidence. A 401/403 returns `AGENT_FORBIDDEN` with an actionable fixed message,
never a successful answer or alternate credential/model call. Do not publish a
ready claim if this gate fails. Independent architecture/security review is also
required before release; no additional agent was launched in this implementation
because the task explicitly prohibited other agents/sessions.

Reference:
[official TypeScript agent quickstart](https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code?tabs=typescript#chat-with-an-agent).
No resources are created by application startup or test execution.

## APIs and protections

| Route | Behavior |
|---|---|
| `GET /healthz` | Process liveness only; no database/model call and no financial work. |
| `GET /api/health` | Official MCP SDK StreamableHTTP `test_connection` only, **no LLM**. `healthy/checking/stale/unavailable`, `connected`, `checkedAt`. Unavailable returns 503. |
| `GET /api/config` | Only public input/turn/rate/TTL limits. No URLs, IDs or secrets. |
| `POST /api/chat` | Exact JSON `{ "message": "..." }`; no additional fields. Returns `{reply, toolNames, continued, turnsRemaining, truncated, expiresAt}`. |
| `POST /api/session/reset` | Exact JSON `{}`. New server-owned chain/cookie; no deletion of remote Responses. Rejects an in-flight session. |

Minimal deployment evidence is `reply`, `toolNames`, and `continued`.
`toolNames` contains only names from actual provider output items of type
`mcp_call`, preserving call order and duplicates. It is empty when no MCP calls
occurred; advertised tools, prompt/reply mentions and health probes are not
evidence of agent tool execution. No arguments, tool results, call IDs, provider
response IDs or server labels are returned as evidence. Only the validated
`answer.reply` is returned as escaped plain text and must explain executed results,
units, observed dates, source/grain, and null/empty/truncated limitations.
`continued` is true only when the BFF supplied the session's server-owned
`previous_response_id` on this dispatch; first turns and turns after reset return
false. It does not independently prove the provider used prior context.
Live release verification compares exact oil and gas values in the actual agent
answer against independent read-only Redshift Data API aggregates and requires a
new analysis on a second cookie-bound turn. Tool names or numeric-looking prose
alone are not numerical acceptance; local mocks are not a live readiness claim.

State-changing APIs require exact `Origin === PUBLIC_ORIGIN`, JSON content type,
and no content encoding. Cross-site Fetch Metadata is rejected. API responses
are no-store; there is no cross-origin browser allowlist. CSP restricts scripts
and connections to same origin and forbids embedding. Text is escaped by React,
not interpreted as HTML/Markdown, including tool-backed model output.

Cookie: cryptographically random 256-bit opaque ID, HttpOnly, Secure,
SameSite=Strict, Path=/, no Domain, absolute 30-minute TTL. Server holds prior
response ID, attempts and busy flag; the browser holds only ephemeral display
history. No localStorage, transcript database, browser provider ID, or persistent
site history. Unknown/expired cookies return `SESSION_EXPIRED`; they never silently
start a new chain. Reset is explicit recovery and does not delete Foundry data.

- 20 user **attempts**, reserved synchronously before provider dispatch; errors
  and explicit retries consume turns. Turn 21 makes no provider request.
- One in-flight dispatch per session; two across the instance. A deadline sends
  cancellation and returns a fixed timeout. Its slot stays occupied until actual
  underlying work/cleanup settles; a late result cannot advance the chain.
  An uncertain timed-out chain requires New chat, not silent continuation.
- 2,000 UTF-16 input code units, 800 output tokens (including model reasoning),
  four tool calls, 230-second chat deadline, no automatic retries. Empty output
  fails safely; incomplete output-budget responses now fail closed rather than
  returning unparseable partial JSON. Final protocol text above 16,000 characters
  is rejected, never silently sliced into an apparently successful answer.
- Maximum 1,000 session entries / 10,000 rate entries; expired inactive entries
  are evicted, capacity rejects new entries rather than resetting protections.
- Five requests/minute per verified **socket IP**, shared by **all** `/api/*`
  routes including health/config/reset. `Retry-After: 60` on rate limit.
  **All forwarded-IP headers are deliberately ignored.** No trusted proxy range
  has been independently established for this deployment. App Service proxy peers
  may therefore share this small limit across multiple users. This is fail-closed
  and spoof resistant, but can be restrictive. Do not switch to the first
  `X-Forwarded-For` value to loosen it. A validated deployment-specific proxy
  trust design and tests are needed to improve client attribution.
- Health has a **60-second overall deadline**, one underlying probe, 30-second
  cache, MCP session termination and transport cleanup. Expired results are
  explicitly stale; a hanging cancelled probe cannot start an overlapping one.
  UI marks a displayed success stale at 30 seconds and offers manual refresh;
  it does not poll or spend tokens for health.
- 16 KiB JSON body limit, 10-second body/headers deadlines, fixed sanitized API
  error codes; prompts, cookies, tokens, provider bodies and answers are not logged.

These are public-POC abuse controls, **not authentication, durable quotas or a
financial cap**. Restart resets state. New cookies/IPs can bypass conversation
budgets. GlobalStandard inference and remote MCP data may cross regions.
Foundry Responses are explicitly stored for continuation; verify actual retention
policy and disclose it before release. New chat/expiry does not delete them.

## Validation evidence and limitations

### GA tool-result serialization fix — local only, pending review

Sewell's narrow consumer fix passes **100 chat tests**, typecheck and production
build using the retained Node **24.22.1** runtime. Synthetic fixtures prove the
direct business JSON, official MCP envelope and observed two-document encoding
normalize to the same object and produce identical analysis-validation results.
Mocked installed-SDK and HTTP tests accept fresh context plus analysis on first
turn and continuation, but reject context-only continuations and malformed,
conflicting or over-budget copies. Final-answer and non-data guards are unchanged.

**Not reviewed, not Ready for Validation, not deployed, not live-verified.**
The hosted app remains BLOCKED; operator diagnosis is not App Service
managed-identity proof. Goff must review before the parent validates/freezes a new
chat-only ZIP and authorizes deployment. Preserve MCP image v3 and registered
agent v2 unchanged; this fix needs no instruction, SDK, identity or budget change.
Require actual hosted exact oil and fresh same-cookie gas acceptance afterwards.

Historical independent consumer-grounding revision (St. Brown): local Node 24 provider/HTTP
regressions cover missing calls, context-only fake totals, follow-ups without new
execution, malformed/failed result envelopes, all five source/grain families,
successful grounded answers, fixed clarification/refusal templates and attempts
to smuggle facts through non-data tags. Goff subsequently approved that revision;
the new serialization fix still awaits its own review. Mocked tests do **not**
approve a release.

Earlier integration validation used official **Node 24.22.1**: `npm run build`, `npm run typecheck` and
the mocked test suite: **37 tests passed, 0 failed**. The exact runtime used for
this integration follow-up is
`/Users/jasonfarrell/Projects/NextEra_RedShiftMcpPoc/src/redshift-chat/.runtime/node-v24.22.1-darwin-arm64/bin/node`.
It was downloaded from the official Node distribution and SHA-256 verified;
its `bin` directory was prepended to `PATH` for all three commands, rather than
using the default Node 26. The ignored `.runtime/` is local validation tooling
only and is excluded from the deployment allowlist.

The public-registry lockfile also passed a clean `npm ci` against the deployment
cache using this machine's configured mirror, and a separate official-registry
offline `npm ci` using the populated local cache. Both installed 239 packages.
The rebuilt app again passed all 37 tests and typechecking. Linux-targeted
`npm ci --dry-run --os=linux --cpu=x64` checked lockfile platform selection only;
it is not an actual Linux installation or proof of a successful remote Oryx build.
The parent's `deploy/chat_deploy.py --stage build` also completed with the
existing default registry settings and deployment cache; no environment override
or deployment-script change was needed.

Earlier **alternative precompiled-strategy** validation, not validation of the
parent-selected source/Oryx deployment, also passed
`npm ci --omit=dev --ignore-scripts --offline` (172 production
packages) and a production `npm start` smoke check for `/healthz`, built React
HTML/JS, public config and CSRF rejection, with no real provider or MCP calls.
Tests cover server-owned chain continuation/isolation,
actual-call-only tool-name evidence, first/reset/continued dispatch flags and
absence of private tool/provider fields in the HTTP evidence,
secure cookies, expiry/reset, turn 21, attempted overrides, concurrency races,
timeout quarantine/cancellation, safe 403/empty/tool failures, origin/JSON/body
controls, IP spoof resistance and bounded stores, health timeout/cache/single-flight
and actual official MCP transport cleanup, official Foundry SDK request
serialization/cancellation/no-retry, React escaping/health/error/composer markup,
keyboard/IME behavior, safe client errors and restricted static serving.

Tests mock the provider and run MCP against local fixtures; they incur no model
cost, call no real database and do not establish cloud readiness. No interactive
browser E2E, accessibility audit, live managed-identity authorization or deployment
was performed here. Production dependency advisory lookup was attempted but the
public feed returned HTTP 429, so dependency security status is **not certified**.
