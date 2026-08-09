# Engineering Roadmap

Status legend: `COMPLETED` · `IN PROGRESS` · `BLOCKED` · `NEXT` · `NOT STARTED`

| Epic | Name | Status | Notes |
|---|---|---|---|
| 01 | Engineering Foundation | COMPLETED | [#1](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/1) |
| 02 | Odoo Digital Enterprise | IN PROGRESS | [#2](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/2) — full pipeline prototyped end-to-end (see below); scale-up to full §7 volumes still pending |
| 03 | Planning & Performance Model | NOT STARTED | [#3](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/3) |
| 04 | Enterprise Analytics Engine | IN PROGRESS | [#4](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/4) — P&L, concentration, project profitability done + tested; AR/AP aging blocked on an Odoo platform bug (see below) |
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

## Epic 02 prototype — status (2026-08-09)

End-to-end pipeline validated against the live `benacta.odoo.com` instance at prototype scale:

| Entity | Count | Notes |
|---|---|---|
| Customers | 25 | 5 segments per `docs/domain/business-domain.md` |
| Suppliers | 15 | 5 categories; "Certified Components" deliberately concentrated on 2 sources |
| Products | 20 | 6 families, priced to hit each family's target margin |
| Employees | 8 | PM/Lead Engineer, hr.employee only — no extra paid seats |
| Projects | 15 | Incl. Project Atlas & Orion matching master prompt §15/§16/§18 exactly; 8 more cover the remaining causal storylines; 5 healthy baseline |
| Sales orders → invoices → credit notes → payments | 30 → 25 → 4 → 22 | |
| Purchase orders → vendor bills → credit notes → payments | 20 → 17 → 3 → 15 | Raw-material suppliers carry a ~18% price escalation over the 36-month window (steel inflation storyline) |
| Posted journal entries | 52 documents / 193 lines | |

**Known platform issue (not our code):** `account.payment.register` creates the payment record but never creates/posts its journal entry (`move_id` stays `False`), and calling `action_post` on `account.payment` directly fails server-side (`TypeError: cannot marshal None`) on every payment tested. The error trace routes through `saas_trial/controllers/main.py`, suggesting the database may still be on trial infrastructure despite the paid subscription. Net effect: every invoice currently shows as fully outstanding in Odoo regardless of intended payment status, so AR/AP aging and DSO are not yet reliable — P&L, concentration, and project profitability are unaffected (they don't depend on payment/reconciliation state). Next: retest after some time (possible trial-to-paid infra migration delay), or raise with Odoo support.

## Next

- Decide full-scale volume for Epic 02 (§7 targets: 500/150/300/200 + 50k/30k/100k transactions) — pragmatic scaling recommended, see conversation history.
- Move the Odoo API key from local `.env` to a GitHub Actions repository secret before any CI touches it.
- Epic 04 (Analytics Engine) can now be scaffolded against real data shapes.
