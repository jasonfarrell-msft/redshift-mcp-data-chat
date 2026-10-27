# Redshift structured analytics MCP server

A small Python server using the **official Python MCP SDK** (`mcp`) and AWS's
**`redshift-connector`**. Default transport: **Streamable HTTP**, listening only at
**http://127.0.0.1:8000/mcp**. No arbitrary SQL tool or database
connection at import/startup.

The package lives at `src/redshift-mcp-server/redshift_mcp_server/` relative
to the workspace root; there is no second, project-local `src` directory.

## Structured analytics (implemented locally, not deployed)

`get_data_context()` returns live observed production/price dates and a bounded
semantic catalog. `analyze_data(plan)` accepts a strict Pydantic version-1 plan:
unknown fields, arbitrary identifiers, SQL, expressions and client-defined joins
are rejected. The schema is hard-fixed to `oge_synthetic`.

```json
{"plan":{"version":"1","dataset":"production","start_date":"2025-01-01","end_date":"2025-12-31","measures":[{"field":"oil_bbl","aggregation":"sum"}],"group_by":["state"],"order_by":{"measure_index":0,"direction":"desc"},"limit":5}}
```

Datasets and semantics:

- `production`: `sum` of `oil_bbl` (bbl), `gas_mcf` (Mcf) and/or
  `operating_cost_usd` (USD). Inclusive dates required, at most 3661 days.
  Optional `group_by` (up to two of `well_id/state/basin/operator`), `time_bucket`
  (`none/day/month/year`), up to four `filters` with `field`, `operator` (`eq/in`)
  and `values` (1–20 strings), and `order_by` with `measure_index`/`direction`.
  Values are query parameters, never SQL. There is no raw-row query endpoint.
- Daily production is authoritative; duplicate/null native well-day keys fail
  closed before querying metrics. A full-month `month/year` trend can use
  `monthly_production`; a full-year `year` trend can use `annual_production`.
  Each request first verifies unique rollup grain and exact **per-well/period**
  equality of all three metrics with daily records, with no null metrics.
  Failed checks fall back to daily rather than combining sources.
  This verifies equivalence, not complete calendar coverage. Whole-dataset
  total equality alone never enables substitution.
- Well dimensions require unique/non-null well IDs and no unmatched production
  IDs in the selected range. Duplicate/orphan checks fail closed; no fan-out.
- `prices`: `avg/min/max` of `oil_usd_per_bbl` (USD/bbl) or `gas_usd_per_mcf`
  (USD/Mcf), full-month ranges and `none/month/year` buckets, without dimensions
  or well filters. Verify unique, nonnull, month-aligned price dates. Averages
  use `DECIMAL(38,8)` to avoid the original price scale truncating to cents.
  All-null averages remain null; no zero-denominator calculation is exposed.
- `wells`: `{"field":"wells","aggregation":"count"}`, optional dimensions and
  filters, no dates; unique/non-null well IDs are required.
- Revenue, profit, gross value, ratios, expressions and production/price joins
  are deliberately unsupported. No production answer is hardcoded.

Results contain `version`, `status` (`ok/empty/truncated`), `executed`,
`executed_at`, `items`, `truncated`, `units`, physical `source`/`source_grain`,
`joined_sources`, normalized `plan` and explanatory notes. Exact decimal results
are strings (for example `"oil_bbl_sum":"123.45"`); SQL, credentials and provider
IDs are not returned. Each aggregate includes source-record count, actual first/
last observations, and per-measure `*_null_records`. Null is not zero; missing
periods are omitted, not zero-filled. Counts/observation bounds refer to the
selected source grain, not necessarily daily records. Date bounds are not proof
of gap-free data. Empty input is distinct from an all-null aggregate.

At most 500 result rows and **256 KiB including both FastMCP text/structured
copies and framing allowance**. Row/byte truncation is explicit, including
intentional top-N results. Per process, all direct MCP calls share two worker
permits (no queue) and 120 admitted calls/minute; analytics/context additionally
share 12/minute. Cancellation retains permits until worker completion. Existing
verified TLS, 10-second **per-statement** timeout, READ ONLY and unconditional
rollback remain. These are bounded operations, not a distributed spending cap:
LIMIT is not a scan cap, and a rollup check still scans bounded daily data.
The existing single-replica POC remains public; reset/restart/multiple replicas
reset or multiply process-local protections. The disclosed superuser identity
was explicitly retained by the user for this synthetic POC only.

## Setup (macOS/Linux)

Python 3.11+ is required (verified locally on Python 3.13).
From the workspace root:

```sh
cd src/redshift-mcp-server
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
cp .env.example .env
# Edit .env locally with your connection information before starting the server.
.venv/bin/redshift-mcp-server
```

The last command starts the HTTP server and prints its MCP endpoint URL. Keep it
running while clients connect; a persistent running server is expected, **not a
hang**. Stop with Ctrl-C. `/mcp` is an MCP protocol endpoint, not an ordinary
browser page or interactive SQL shell. Equivalent entry point:
`.venv/bin/python -m redshift_mcp_server`. With the virtual environment active,
use `redshift-mcp-server` or `python -m redshift_mcp_server`.

If you use `uv`, the equivalent environment setup is `uv sync --extra dev`,
and the command is `uv run redshift-mcp-server`. To inspect the running server,
launch `npx @modelcontextprotocol/inspector` separately, select **Streamable HTTP**,
and connect to `http://127.0.0.1:8000/mcp` (requires Node.js/npm for the Inspector
UI). The protocol tests below do not require Inspector or Node.

## MCP client URL

Start the server first, then register its URL in a client supporting Streamable
HTTP. For clients using the `mcpServers` format:

```json
{
  "mcpServers": {
    "redshift": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

Client-specific configuration keys may differ; select **Streamable HTTP**, not
legacy SSE or a subprocess/stdio transport. The client does not launch this
server. If port 8000 is occupied, use `redshift-mcp-server --port 8001` (or
`python -m redshift_mcp_server --port 8001`) and update the client's URL.
The bind address defaults to `127.0.0.1`. Explicit container hosting uses
`--host 0.0.0.0`; these are the only two supported bind addresses.

There are deliberately **no secrets in client JSON**. Configure the **server
process** using its local `.env` file (below), or use a trusted launch wrapper/
secret manager to inject environment variables before starting it. Environment
variables in a separate shell or HTTP client's process are not forwarded to an
already-running server.
This project never creates a real `.env` or an AWS credentials file.
The AWS SDK may use existing credential sources through its normal provider chain.

## Configuration

### Where to put connection information

From `src/redshift-mcp-server/` (the folder containing `pyproject.toml`), copy
`.env.example` to **`src/redshift-mcp-server/.env`** relative to the workspace
root, then edit that local file with your endpoint, database, user, and chosen
authentication settings. The template contains placeholders only; fill them in.
The real `.env` is ignored by source control: never commit or share it.
Restrict its permissions, for example with `chmod 600 .env`, and prefer a secure
runtime secret manager for shared/deployed environments.

Both `redshift-mcp-server` and `python -m redshift_mcp_server` load `.env`
**once at startup from the current working directory**. Launch from this project
folder; there is no automatic search in parent folders or your home directory.
Alternatively, use `redshift-mcp-server --env-file /path/to/local.config` (also
supported by the module entry point). An explicitly requested missing file is
an error. A missing default `.env` is fine; unreadable or malformed files fail
with a sanitized message, without printing file contents or credentials.

**Already-exported environment variables take precedence**, even if empty.
Values from `.env` are loaded into the server process's environment, not into
your shell or client. There is **no hot reload**: after editing `.env`, stop the
server and start a fresh process. Environment-variable interpolation is disabled,
so `$` and `${...}` in passwords stay literal. Quote passwords containing spaces
or `#`, for example with single quotes around the whole value. If the value
contains a single quote, use double quotes around it (or dotenv's supported
quote escaping); do not `source .env` in a shell, whose expansion rules differ.

Connection settings are validated **on each tool call**, not on import/startup. Without them,
the client can still initialize and list all four tools. Calling a tool returns
an actionable missing-setting error naming variables, never their values.

| Environment variable | Requirement/default |
|---|---|
| `REDSHIFT_HOST` | Required endpoint DNS name (not a URL) |
| `REDSHIFT_PORT` | `5439`; integer 1–65535 |
| `REDSHIFT_DATABASE` | Required database name |
| `REDSHIFT_USER` | Required database user |
| `REDSHIFT_AUTH_MODE` | `password` by default; or `iam` |
| `REDSHIFT_PASSWORD` | Required in password mode; local ignored `.env` or secure runtime injection |
| `REDSHIFT_CONNECT_TIMEOUT` | `10` seconds; integer 1–60 |
| `AWS_REGION` | Required in IAM mode |
| `REDSHIFT_CLUSTER_IDENTIFIER` | Required in IAM mode (provisioned cluster) |

**Preferred when available: IAM temporary database credentials.** Set
`REDSHIFT_AUTH_MODE=iam` with region and provisioned-cluster identifier. The
connector uses the standard AWS credential provider chain (for example a workload
role, existing authenticated AWS profile, or runtime-provided temporary AWS
credentials); this project never accepts literal AWS keys in code or client JSON.
IAM identity permissions and database user mapping must already be configured;
automatic database-user creation is disabled. This initial IAM path targets
provisioned Redshift, not Redshift Serverless IAM. Password mode can also connect
to an accessible Serverless SQL endpoint.

**Password fallback:** supply database credentials through the ignored local
`.env` file or secure runtime environment injection. Do not paste passwords into
command-line arguments, shell history, committed source/configuration, README
examples, MCP client JSON, or Squad state.
Do not grant a superuser: use a dedicated least-privilege database identity
limited to intended metadata visibility. Database grants are the authorization
boundary; metadata names/default expressions can themselves be sensitive.

## Tools

| Tool | Arguments | Result |
|---|---|---|
| `test_connection` | None | `{"connected": true}` after `SELECT 1` |
| `list_schemas` | `limit=100` | Visible schemas except `pg_catalog`/`information_schema` |
| `list_tables` | `schema`, `limit=100` | Visible table/view names and types |
| `describe_table` | `schema`, `table`, `limit=100` | Column names/types/order/nullability/defaults |

Metadata results are structured `{"items": [...], "truncated": false}` objects.
Limits are integers 1–500. Names are exact case-sensitive catalog values, up to
127 UTF-8 bytes, with nonempty content and no NUL. Quoted/unusual names are safe:
they are **query parameters**, never interpolated SQL identifiers.
Discovery uses Redshift's native
[`SVV_ALL_SCHEMAS`](https://docs.aws.amazon.com/redshift/latest/dg/r_SVV_ALL_SCHEMAS.html),
[`SVV_ALL_TABLES`](https://docs.aws.amazon.com/redshift/latest/dg/r_SVV_ALL_TABLES.html),
and [`SVV_ALL_COLUMNS`](https://docs.aws.amazon.com/redshift/latest/dg/r_SVV_ALL_COLUMNS.html),
including visible local and external metadata, always filtered to
`database_name = current_database()`. This avoids the owner-only
`information_schema.schemata` filter observed with a different schema owner.
Existing grants still determine visibility; no permission expansion is required.
Public result keys are unchanged: native `schema_name` is returned as
`table_schema` for tables/columns, and native `TABLE` is normalized to
`BASE TABLE`; `VIEW` and other native types are preserved.
Empty results mean no matching **visible** metadata, not necessarily that an
object does not exist. Cross-database discovery is intentionally excluded.
If truncated, narrow the schema/table or increase the limit; cursor pagination
is intentionally out of scope.

## Connection and safety behavior

- Each call opens its own connection lazily; no pool or generated credential files.
  The connector/AWS SDK may cache temporary IAM credentials in process memory.
- Synchronous connector work runs in `asyncio.to_thread`, not the MCP event loop.
- TLS is mandatory with `ssl=True`, `sslmode="verify-full"` (CA and hostname
  verification). There is no insecure bypass setting.
- A bounded connect timeout and a 10-second SQL statement timeout are applied;
  transactions are read-only and always rolled back, cursors/connections closed.
- Database and cleanup failures return sanitized messages; raw connector exception
  strings are neither returned nor logged. Cleanup attempts all steps, and cleanup
  failures are surfaced (an earlier operation failure takes precedence).
- No row-data querying, arbitrary SQL, writes, or remote auth layer.
- The HTTP listener defaults to `127.0.0.1`. The SDK's localhost DNS rebinding
  protection remains enabled: non-local Host and Origin headers are rejected locally.
  This is not authentication; trusted local processes can call the tools.
  The explicitly approved anonymous, synthetic-data Container Apps POC below
  uses platform HTTPS termination and an exact Host/Origin allowlist.
  Authentication/authorization are **not implemented here**; a production
  network service needs them and a separate security review.
  This is **not a hardened multi-user production service**.
- A cancelled tool cannot forcibly stop a connector thread; connector/socket and
  statement timeouts bound normal waits, not every possible IAM/network failure.

The explicit read-only transaction uses Redshift's documented
[`BEGIN READ ONLY`](https://docs.aws.amazon.com/redshift/latest/dg/r_BEGIN.html).

### Why direct SQL rather than the Redshift Data API?

The official connector is a small DB-API-shaped starting point with ordinary
parameterized metadata queries and TLS. **The endpoint must be reachable** from
the MCP process: VPC routing/VPN, DNS, security groups, firewall rules, and database
permissions still matter. Avoid public cluster exposure in normal deployments;
the synthetic-data POC below explicitly accepts public access as an exception.

The **Redshift Data API** is a good alternative when an HTTPS AWS API and IAM fit
your environment better, especially when direct database networking is awkward.
It has its own IAM/auth configuration, supported deployment requirements, and
asynchronous statement polling/result handling; it is not universally easier or
better. It is not implemented here.

## Local verification versus live verification

```sh
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pip check
```

Tests use connector fakes and real MCP Streamable HTTP clients against loopback
servers on ephemeral ports, including console and module subprocess launches. They
verify credential-free startup/tool discovery, isolated synthetic `.env` loading,
environment precedence, literal password characters, sanitized file errors, missing settings, schemas,
validation, TLS flags, IAM options, parameter binding, result bounds, offloading,
sanitization, rollback, cleanup, and HTTP Host/Origin rejection. Test servers are
stopped after use. They do **not** verify live AWS IAM permissions,
endpoint reachability, certificate chains, or actual Redshift SQL behavior.
Once runtime credentials and network access are ready, call `test_connection`
from an MCP client, then metadata tools against an approved schema.

## Container / Azure Container Apps hosting

This is an **anonymous public HTTPS synthetic-data POC**, not a production
deployment pattern. No bearer token or Entra authentication layer is added.
Anyone reaching the approved endpoint can invoke the four bounded tools; database
permissions still determine metadata visibility. Host/Origin validation is
DNS-rebinding defense, **not caller authentication or CORS**.

Build context: **`src/redshift-mcp-server/`**, not the workspace root.
The image command is:

```sh
redshift-mcp-server --host 0.0.0.0 --port 8000
```

Local console and module entry points still default to loopback. The same
`--host`, `--port`, and `--env-file` options work with
`python -m redshift_mcp_server`.

| Hosting interface | Contract |
|---|---|
| `REDSHIFT_MCP_ALLOWED_HOSTS` | Comma-separated **exact bare DNS names**, e.g. `poc.example.com,alternate.example.com`; no URL, wildcard, port, path, or IP |
| Host headers | Each configured name and its exact `:443` form; no arbitrary port or suffix matching |
| Origin headers | Exact `https://<name>` and `https://<name>:443`; absent Origin allowed by the official SDK |
| Loopback | Existing localhost, `127.0.0.1`, and IPv6-loopback Host/HTTP Origin checks remain enabled in both modes |
| Local bind | Remote allowlist is ignored with `--host 127.0.0.1`; local protection is never expanded |
| MCP | Official Streamable HTTP at `/mcp`, externally `https://<actual-ingress-fqdn>/mcp` |
| Process health | Unauthenticated `GET /healthz` → HTTP 200 `ok`; no settings, database, AWS, or Key Vault calls |

Set the allowlist to the actual ACA **application ingress FQDN** in runtime
environment configuration. The platform's
[`CONTAINER_APP_HOSTNAME`](https://learn.microsoft.com/en-us/azure/container-apps/environment-variables#built-in-environment-variables)
is documented as **revision-specific**, so the server deliberately does not
assume that it equals the stable application URL. Add revision or custom-domain
names explicitly only if clients will use them. No entire environment domain
or `*.azurecontainerapps.io` wildcard is allowed.

Without the allowlist the public-bind image starts for identity/bootstrap and
health probes, but public MCP requests fail closed (loopback remains usable).
After learning the ingress FQDN, set `REDSHIFT_MCP_ALLOWED_HOSTS` and deploy a
new revision. Invalid nonempty allowlists fail startup with a sanitized error.
An allowlist in a local configuration file is loaded once with the same explicit
current-directory dotenv behavior; injected runtime environment takes precedence.

Configure ACA ingress with external HTTPS, `allowInsecure=false`, and target port
**8000**. The container serves internal HTTP behind platform TLS termination.
Use HTTP startup/liveness/readiness probes on **`/healthz`, port 8000**.
Health intentionally accepts platform/replica-IP Host headers, without widening
the SDK's separate `/mcp` checks. A healthy process proves **nothing about
Redshift or Key Vault secret resolution**. Verify the actual `test_connection`
and bounded metadata calls separately after credentials/networking are ready.
Secrets must be runtime **Key Vault-backed ACA secret references**, never build
arguments, literal image environment values, client configuration, or files.
Startup remains lazy and credential-free.

### Image and dependency reproducibility

The Dockerfile pins official **Python 3.13.17 slim-trixie**, verified against
Docker Hub and the official Registry V2 API on **2026-10-26**, including
`PYTHON_VERSION=3.13.17` in its Linux/AMD64 image configuration:

- Multi-platform index: `sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962`
- Linux/AMD64 manifest: `sha256:d879ed88565a7a3c614b980b369d4a5025a9d057b71f93d09fc6d0b2ca823a18`

Build for **`linux/amd64`** (cloud ACR Tasks can build without a local Docker
daemon). The immutable index pin selects that platform's manifest when the build
target is supplied. Runtime UID/GID is **10001:10001**; only the final wheel,
hash-locked runtime dependencies, and base image are installed in the final stage.
Wheel-building tools have a separate lock and remain in the build stage.
No `COPY . .` is used. `.dockerignore` is deny-by-default with a small runtime
allowlist, and explicitly excludes `.env*` (including `.env.example`), local
environments, caches, logs, credentials, tests, and deployment artifacts.
Never upload a workspace-root or unfiltered ACR build context.

`requirements.lock` locks only the project runtime dependency graph (including
the declared MCP CLI extra); `requirements-build.lock` locks the isolated
Hatchling wheel-building graph. Both include hashes for pip's `--require-hashes`.
To deliberately update the locks, use Python 3.13 with `pip-tools` installed:

```sh
python -m piptools compile pyproject.toml --generate-hashes --allow-unsafe --strip-extras \
  --no-emit-index-url --no-emit-trusted-host --output-file requirements.lock
printf 'hatchling>=1.27\n' | python -m piptools compile - --generate-hashes --allow-unsafe \
  --strip-extras --no-emit-index-url --no-emit-trusted-host \
  --output-file requirements-build.lock
```

Verify Linux/AMD64 wheel resolution and rerun tests after an update. Unit/protocol
tests use only synthetic configuration and bounded helper servers. Static file
and package validation is not a container execution claim: the local Docker
daemon was unavailable; a successful cloud image build/run remains a deployment
acceptance gate.

`--allow-unsafe` is pip-tools terminology for retaining packages such as
`setuptools`: Redshift's connector declares it as a runtime dependency, so it
must also be explicitly pinned and hashed. Do not omit it from the runtime lock.
# Official AWS MCP migration candidate — not deployed

The governed HTTP service now executes its existing structured analytics and
metadata operations through the published **AWS
`awslabs.redshift-mcp-server==0.1.2`** stdio server. It is an application policy
adapter, not an AWS-published HTTP server. No direct driver or Boto3-query
fallback exists. Production version3 is retained separately for rollback.

The official Python wheel SHA256, verified against public PyPI release metadata:
`03a3fff27161cf0bd3e75765eb9c8ef5f1cfe920811015dcb2c543d712826b40`.
Publisher repository: https://github.com/awslabs/mcp/tree/main/src/redshift-mcp-server.
The image isolates outer MCP1 `/opt/adapter` and upstream MCP2 `/opt/official`.
The fixed, nonsecret `aws-config` uses the auth owner's short-lived
`credential_process`; no tokens/keys are stored in that file.

Required target is `default-workgroup` / `dev` / `us-east-2`.
`REDSHIFT_DB_BUDGET_VERIFIED=10` must be set ONLY after live review proves the
effective nonsuperuser principal's supported ten-second database budget.
Without that proof/federation, process health starts normally but DB health
fails closed. See the approved scope and auth environment ABI in
`.azure/deployment-plan.md` and `redshift_mcp_server/aws_credentials.py`.

The bridge uses the official `execute_query` tool's named read-only transaction
parameters for one snapshot across existing integrity checks and aggregates,
then rolls back. The official package implements these with Data API batches.
Two lazily started isolated stdio workers (the same cap as HTTP execution)
retain their initialized SDK sessions, event loops and dedicated threads across
operations. One task owns each worker's anyio/SDK contexts for its entire life;
workers are exclusively leased, never shared by concurrent operations. Every
lease starts a new uniquely named read-only transaction and returns the worker
to the idle FIFO only after a validated successful rollback. No database
transaction/snapshot or business result is cached between leases.

`get_data_context` executes one compiler-owned live query: two independent
MIN/MAX/COUNT aggregates cross-joined into one row. This avoids a second MCP
query without joining fact rows or changing the public production/price
coverage objects; empty tables still yield null bounds and integer zero counts.
All analysis integrity, well/join and rollup reconciliation checks are unchanged.
IAM must permit only the approved target and Batch execution and deny legacy
ExecuteStatement. Only compiler-authored SQL is accepted internally; dates/
integers/strings are typed and quote-escaped, backslash/control literals rejected.
No native SQL tool is exposed by this HTTP adapter.

SQL/result limits remain501 sentinel rows /500 business rows and256KiB emitted
MCP envelopes; child stdout frames are bounded to1MiB before SDK parsing.
The absolute bridge deadline is50 seconds, including worker lease/startup,
transaction calls and rollback. HTTP admission and worker leasing reject
saturation without adding a waiting queue. A timeout/error without proven
settlement permanently quarantines both that worker slot and the operation's
execution permit; aborting
HTTP/stdio does NOT cancel remote SQL. Operators must prove remote settlement
before any recovery restart. This is intentionally fail-closed, not HA.
Quarantined workers are stopped but never replaced to replenish capacity.
Initialization failures before any BEGIN may be rebuilt only after local
session/process cleanup completes. Runtime configuration changes require a
restart rather than reusing workers under a different environment; forked
processes discard inherited pool state. The outer ASGI application lifespan runs
the SDK session manager once and stops workers only after that manager exits;
deleting an individual HTTP MCP session never stops the shared warm pool.
Stdio application exit also stops workers. These paths and a fallback process
exit hook stop workers once and join their threads under one shared eight-second
budget; SDK stdio teardown closes input and escalates process-group termination.
Shutdown does not restore capacity in a running service. Actual live latency
savings have not yet been measured.

Local protocol validation uses the real pinned SDK2 executable and actual MCP
initialize/list-tools/call-tool against SDK1, with ONLY AWS execution replaced
by offline fixtures. Missing upstream dependencies block this proof/cutover;
do not call mocks a successful interoperability test.

The original connector documentation below is retained as historical context;
password/driver instructions no longer describe the candidate execution path.

---
