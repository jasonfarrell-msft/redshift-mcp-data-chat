# Project Context

- **Owner:** Requester display name not provided; do not infer.
- **Project:** Runnable Amazon Redshift metadata MCP scaffold; credentials follow.
- **Stack:** Python 3.11+, official MCP SDK, redshift-connector, stdio.
- **Created:** 2026-10-26T09:13:34-04:00

## Learnings

- User chose Python and delegated easiest/recommended initial connection approach.
- Direct TLS connector selected for the small metadata scaffold; Data API remains an alternative.
- Startup/tool listing must work without credentials. Configure only on tool calls.
- Installed connector fetches rows as sequences (probe must accept list rows).
- Explicit `sslmode="verify-full"` is required; never rely on connector defaults.
- Tested locally on Python 3.13; no live Redshift connectivity established.
- Workspace is a non-Git folder; state backend is local; no commits.

### Verification handoff

- Final local suite: 45 tests pass, lint/style checks pass, dependency check passes.
- Wheel builds successfully; both console/module entry points pass real MCP stdio checks.
- Verified official Redshift documentation supports `BEGIN READ ONLY`; use autocommit
  only for session setup/explicit BEGIN, then disable it for metadata work.
- Preserved template-seeded built-in policies and existing union merge attributes.
- Team state validation confirms eight linked members and consistent casting state.
- No live database validation or independent review is claimed.
