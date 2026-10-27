# Project Context

- **Owner:** Requester display name not provided; do not infer.
- **Project:** Runnable Amazon Redshift metadata MCP scaffold; credentials follow.
- **Stack:** Python 3.11+, official MCP SDK, redshift-connector, pytest, stdio.
- **Created:** 2026-10-26T09:13:34-04:00

## Learnings

- User approved Detroit Lions names; stable id is `sewell`.
- Offline tests must cover real MCP discovery, missing settings, parameters and lifecycle failures.
- Do not read live `.env` files. Remove inherited AWS/Redshift test environment first.
- Gibbs implements the initial tests; Sewell's independent review is still pending.
- Local fake-connector verification is not a live database integration test.
