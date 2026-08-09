# Engineering Roadmap

Status legend: `COMPLETED` · `IN PROGRESS` · `BLOCKED` · `NEXT` · `NOT STARTED`

| Epic | Name | Status | Notes |
|---|---|---|---|
| 01 | Engineering Foundation | COMPLETED | [#1](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/1) |
| 02 | Odoo Digital Enterprise | IN PROGRESS | [#2](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/2) — Odoo Online (Enterprise) live at `benacta.odoo.com`, API connectivity verified (ADR-0002) |
| 03 | Planning & Performance Model | NOT STARTED | [#3](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/3) |
| 04 | Enterprise Analytics Engine | NOT STARTED | [#4](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/4) |
| 05 | MCP Capability Layer | NOT STARTED | [#5](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/5) |
| 06 | Enterprise Knowledge / RAG | NOT STARTED | [#6](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/6) |
| 07 | Finance Intelligence | NOT STARTED | [#7](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/7) |
| 08 | Operations Intelligence | NOT STARTED | [#8](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/8) |
| 09 | Commercial Intelligence | NOT STARTED | [#9](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/9) |
| 10 | Decision Engine | NOT STARTED | [#10](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/10) |
| 11 | Executive Cockpit | NOT STARTED | [#11](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/11) |
| 12 | Scenario Simulation | NOT STARTED | [#12](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/12) |
| 13 | Decision Memory | NOT STARTED | [#13](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/13) |
| 14 | Evaluation & Trust | NOT STARTED | [#14](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/14) |
| 15 | Security & Governance | NOT STARTED | [#15](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/15) |

## Blocked items

None currently.

## Next

- Build the ERP Adapter (`/integrations/odoo`) and data generators (`/data/generators`) against the live Odoo instance (Epic 02).
- Move the Odoo API key from local `.env` to a GitHub Actions repository secret before any CI touches it.
