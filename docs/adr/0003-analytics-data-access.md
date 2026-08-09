# ADR-0003: Analytics Engine data access — direct Odoo API, not ELT/dbt, for now

## Status

Accepted.

## Context

Building Epic 04 (Analytics Engine) raised the question of data access pattern: query Odoo directly via the External API for every calculation (what Epic 02's generators already do), or build a proper ELT pipeline (Odoo API → land in a warehouse → dbt transforms) for better query performance at scale.

Two constraints shape this decision now:

1. The development machine is a VM with real **storage constraints** — running a local/managed warehouse adds footprint we don't need yet.
2. Current data volume is prototype-scale (dozens to low hundreds of records per entity, ADR referenced in `docs/roadmap.md`), not the full §7 target volumes (500/150/300/200 + 50k/30k/100k transactions). Direct API queries are fast enough at this scale.

The user's stated longer-term intent is to move the platform to proper cloud infrastructure (managed data warehouse, containers/Kubernetes) once the concept is validated — this decision is explicitly scoped as "for now," not a permanent architectural stance.

## Decision

Epic 04's Analytics Engine queries Odoo directly via the same External API client pattern as Epic 02 (`data/generators/odoo_client.py` → to be generalized into `platform/analytics`'s own client), computing metrics in Python at request time. No warehouse, no dbt, no ELT pipeline for now.

## Consequences

- Lowest possible infrastructure footprint — fits the VM's storage constraints, nothing new to run or maintain.
- Query performance is acceptable at prototype scale; it will degrade at full §7 transaction volumes (XML-RPC round-trips don't parallelize/aggregate like SQL does).
- **Revisit this ADR** when either (a) data volume is scaled up meaningfully, or (b) the platform moves to a cloud deployment — at that point, introduce an ELT pipeline (Odoo API → Postgres warehouse, the same instance planned for Epic 06's RAG store — → dbt models) without needing to rewrite agent or MCP-layer logic, since they depend on the Analytics Engine's interface, not on how it fetches data (mirrors the ERP Adapter abstraction principle from ADR-0002).
