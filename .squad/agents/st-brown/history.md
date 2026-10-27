# Project Context

- **Owner:** Requester display name not provided; do not infer.
- **Project:** Runnable Amazon Redshift metadata MCP scaffold; credentials follow.
- **Stack:** Python 3.11+, official MCP SDK, redshift-connector, stdio.
- **Created:** 2026-10-26T09:13:34-04:00

## Learnings

- User approved Detroit Lions names; stable id `st-brown` maps to St. Brown.
- Direct SQL requires endpoint network reachability and strict TLS verification.
- Initial IAM path uses the AWS provider chain and provisioned-cluster database user mapping.
- Password fallback is environment-injected at runtime from a secure store.
- Data API is an alternative, not universally better. No infrastructure work is authorized.
- Live network, IAM permissions and SQL compatibility remain unverified without credentials.
