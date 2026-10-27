# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Python / backend | Gibbs | MCP tools, packaging, validation, connector lifecycle |
| AWS integration | St. Brown | IAM, Redshift connectivity, TLS and network prerequisites |
| Code review | Goff | Review implementation and design; enforce scope and handoffs |
| Testing | Sewell | Protocol, credential-free startup, query parameterization, cleanup |
| Scope & priorities | Goff | Trade-offs, architecture, acceptance and sequencing |
| Session logging | Scribe | Automatic — never needs routing |
| Work queue | Ralph | Backlog status, pending handoffs, completed-work checks |
| RAI review | Rai | Content safety, bias checks, credential detection, ethical review |
| Verification | Fact Checker | Verify SDK/API claims, distinguish local evidence from live AWS claims |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, assign `squad:{member}` label | Lead |
| `squad:{name}` | Pick up issue and complete the work | Named member |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, the **Lead** triages it — analyzing content, assigning the right `squad:{member}` label, and commenting with triage notes.
2. When a `squad:{member}` label is applied, that member picks up the issue in their next session.
3. Members can reassign by removing their label and adding another member's label.
4. The `squad` label is the "inbox" — untriaged issues waiting for Lead review.

## Rules

### Local project constraints

- Use the approved stable ids: `goff`, `gibbs`, `st-brown`, `sewell`, `scribe`, `ralph`, `rai`, `fact-checker`.
- Rai's existing template-seeded directory is `agents/Rai/`; preserve it on case-insensitive filesystems.
- State backend is local; filesystem writes are valid. No Git operations in this non-Git folder.
- Current small scaffold is implemented by Gibbs directly; do not spawn additional agents or sessions for it. Goff and Sewell may independently review after handoff.
- Never read live `.env` files or write secrets into source, client JSON, or team state.
- User approval and scoped assignments override the generic concurrency defaults below.

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn the tester to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. The Lead handles all `squad` (base label) triage.
