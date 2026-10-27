# Squad Decisions

## Active Decisions

### 2026-10-26T09:13:34-04:00 — Python scaffold and initial connector

**By:** User (Python selection and connector choice delegated); Gibbs (implementation).

**What:** Build `src/redshift-mcp-server/` using the official Python MCP SDK,
stdio by default and official redshift-connector for direct SQL over verified TLS.
Expose only connection probe and bounded schema/table/column metadata tools.
No credentials are needed for startup/tool discovery. Runtime configuration is
environment-only, with IAM provider-chain support and secure password fallback.

**Why:** The user requested an actual small scaffold now, credentials later, and
delegated the easiest/recommended connection approach. Direct SQL is a small
initial implementation but requires network reachability. Data API remains a
documented alternative; neither transport is universally preferable.

### 2026-10-26T09:13:34-04:00 — Approved Detroit Lions team and local state

**By:** User (roster/universe approval); Gibbs (Phase 2 persistence).

**What:** Goff lead/review, Gibbs Python/backend, St. Brown AWS, Sewell tests;
Scribe, Ralph, Rai and Fact Checker are unchanged built-ins. Eight members total.
Stable domain ids are `goff`, `gibbs`, `st-brown`, `sewell`. Detroit Lions explicitly
overrides default casting policy. Requester display name was not provided.

**Why:** Preserve approved names and roles without another roster question.
State backend is local filesystem, with existing governance preserved.
This folder is not a Git repository; no Git initialization/commit/PR is authorized.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
