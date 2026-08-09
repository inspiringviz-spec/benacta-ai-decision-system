# BENACTA AI Decision System

An AI-native Enterprise Decision Intelligence platform: it observes the enterprise, detects what matters, investigates why it is happening, quantifies impact, simulates alternatives, supports human judgment, records decisions, and measures outcomes.

Full product mandate: [`BENACTA_AI_DECISION_SYSTEM_MASTER_PROMPT.md`](./BENACTA_AI_DECISION_SYSTEM_MASTER_PROMPT.md).

## Status

See [`docs/roadmap.md`](./docs/roadmap.md) for the current engineering status across all epics.

## Repository structure

```text
/apps
    /api            Backend API service
    /cockpit        Executive Decision Cockpit (frontend)

/platform
    /agents         CFO / COO / CRO / specialist agents
    /mcp            MCP business capability layer
    /rag            Enterprise knowledge / retrieval
    /analytics      Deterministic analytics engine
    /decision-engine
    /scenario-engine

/integrations
    /odoo           Odoo ERP adapter

/data
    /generators     Synthetic enterprise data generators
    /ground-truth   Evaluation ground-truth (kept separate from generated data)

/knowledge
    /policies
    /procedures

/evals              Agent and system evaluation suites
/tests

/docs
    /architecture
    /domain
    /adr            Architecture Decision Records
```

## Business environment

A fictional industrial enterprise, **Benacta Manufacturing Group**, backed by Odoo 19 as the system of record. See the master prompt (§5–§7) for the full business domain and data model.

## Engineering approach

Built through an agentic software engineering workflow — GitHub issues/epics as the backlog, PRs, reviews, ADRs. See `docs/adr/` for architectural decisions and `docs/roadmap.md` for epic-by-epic status.
