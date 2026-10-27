# Squad Team

> NextEra_RedShiftMcpPoc

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Goff | Lead / reviewer | [goff](agents/goff/charter.md) | Active |
| Gibbs | Python / backend | [gibbs](agents/gibbs/charter.md) | Active |
| St. Brown | AWS integration | [st-brown](agents/st-brown/charter.md) | Active |
| Sewell | Tests / quality | [sewell](agents/sewell/charter.md) | Active |
| Scribe | Memory / decisions / logs | [scribe](agents/scribe/charter.md) | Active |
| Ralph | Work queue / monitor | [ralph](agents/ralph/charter.md) | Active |
| Rai | Responsible AI / privacy | [rai](agents/Rai/charter.md) | Active |
| Fact Checker | Verification / devil's advocate | [fact-checker](agents/fact-checker/charter.md) | Active |

## Project Context

- **Project:** NextEra_RedShiftMcpPoc
- **Created:** 2026-10-26
- **Requester display name:** Not provided; do not infer it from local paths.
- **Stack:** Python 3.11+, official Python MCP SDK, AWS redshift-connector.
- **Goal:** A runnable stdio Redshift metadata MCP scaffold under `src/redshift-mcp-server/`; credentials follow later.
- **Naming:** User-approved Detroit Lions universe overrides the default casting allowlist. Domain ids are `goff`, `gibbs`, `st-brown`, `sewell`; built-in names remain unchanged.
- **State backend:** Local filesystem at `.squad/`. This workspace is a folder, not a Git repository. No Git initialization or automatic commits.
- **Scope:** Direct TLS SQL first, IAM when available, environment-injected password fallback. No arbitrary SQL tool or production deployment.
