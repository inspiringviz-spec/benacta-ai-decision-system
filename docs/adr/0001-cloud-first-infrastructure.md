# ADR-0001: Cloud-first infrastructure, repository scope, and ERP hosting

## Status

Accepted. **The ERP hosting decision in this ADR (Odoo.sh) was superseded by [ADR-0002](./0002-odoo-hosting-final.md).**

## Context

The development machine is a restricted VM without Docker or reliable local infrastructure. The product mandate requires the local machine to need only Git, VS Code, Claude Code, and a browser (§21 of the master prompt).

Additionally, this repository was created inside a parent directory (`my_ai_projects`) that is itself an uninitialized Git working tree containing many unrelated client project folders. Initializing Git at the parent level would have entangled this project with unrelated client work.

An ERP system of record (Odoo 19) is required as the primary data backend (§6).

## Decision

1. **Repository scope**: `git init` was run directly inside `AI-native Enterprise Decision System/`, isolating this project from the parent directory. The parent's untracked state was left untouched.
2. **ERP hosting**: Odoo.sh was chosen over Odoo Online (SaaS) or a self-managed VM install. Odoo.sh is GitHub-linked, supports deploying custom addon code (required for the Decision System's ERP adapter and any Odoo-side customization), and requires no local installation — consistent with the cloud-first constraint. Odoo Online was rejected because it does not support custom code deployment. A self-managed VM was rejected as unnecessary operational overhead compared to a managed option that already fits the constraint.
3. **Repository visibility**: public, per explicit user choice.

## Consequences

- Epic 02 (Odoo Digital Enterprise) is blocked on the user creating an Odoo.sh account and linking it to this GitHub repository — this cannot be done by Claude (no interactive browser/signup capability).
- The Decision Engine and Analytics Layer must depend on an ERP Adapter interface (§6, §35), not directly on Odoo's schema, so that Odoo.sh's specific constraints don't leak into the rest of the platform.
- Being a public repository, no secrets, credentials, or customer-identifying data may ever be committed. `.env*` files are gitignored; real credentials belong in GitHub Actions secrets / Odoo.sh environment config, never in the repo.
