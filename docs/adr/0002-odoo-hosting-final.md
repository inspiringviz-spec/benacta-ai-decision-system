# ADR-0002: ERP hosting — Odoo Online (Enterprise) via External API, not Odoo.sh

## Status

Accepted. Supersedes the ERP hosting decision in [ADR-0001](./0001-cloud-first-infrastructure.md).

## Context

ADR-0001 originally chose Odoo.sh for its GitHub-linked custom code deployment. In practice, walking through Odoo.sh's actual signup flow surfaced two things:

1. Odoo.sh has no standalone free trial — it requires an active paid subscription with "Odoo.sh Cloud Platform" as the hosting type (~€112.60/month for 1 user), materially more than the Standard Cloud Hosting tier (~€44.88/month, Enterprise, all apps, Studio, Multi-Company, External API).
2. Re-examining the platform's actual technical requirements (§6 of the master prompt: "Integrate through supported APIs") showed that nothing in this project's architecture needs Odoo-side custom Python module deployment. All business logic (analytics engine, MCP tools, agents, decision engine) lives in `/platform`, outside Odoo. The only things the ERP Adapter needs from Odoo are:
   - Read/write access via the External API (XML-RPC), used for the data generators (Epic 02) and for the MCP tools that read financial/operational data (Epic 04, 05).
   - Optional no-code custom fields/views via Odoo Studio, if the data model needs fields beyond Odoo's standard schema — included in the Custom plan regardless of hosting type.

## Decision

Use **Odoo Online (Enterprise, Custom plan, Standard Cloud Hosting)** at `benacta.odoo.com`, authenticated via an API key scoped to **RPC** (not the MCP-labeled scope, which is for exposing Odoo directly as a tool provider to external agents — the opposite of §10's requirement that agents never get unrestricted/direct data access).

Do not provision Odoo.sh unless a genuine need for server-side custom Odoo modules emerges later.

## Consequences

- ~€68/month cheaper than Odoo.sh, with no loss of capability the platform actually needs.
- No GitHub-linked deployment pipeline for Odoo-side code — not needed, since no custom Odoo modules are planned.
- Any future need for custom fields/views is handled via Odoo Studio (no engineering work) before reaching for custom code.
- Connectivity verified via `integrations/odoo/test_connection.py` against `benacta.odoo.com` (Odoo 19.4 Enterprise, `saas~19.4+e`).
- Credentials (API key) are kept in a local `.env` (gitignored, never committed) for development. Before any CI/CD automation touches Odoo, the key must move to GitHub Actions repository secrets — never committed to this public repository.
- If a genuine need for server-side custom Odoo logic emerges later, the ERP Adapter abstraction (§35 of the master prompt) means migrating to Odoo.sh at that point would not require changes anywhere else in the platform.
