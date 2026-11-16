# Engineering Roadmap

Status legend: `COMPLETED` · `IN PROGRESS` · `BLOCKED` · `NEXT` · `NOT STARTED`

| Epic | Name | Status | Notes |
|---|---|---|---|
| 01 | Engineering Foundation | COMPLETED | [#1](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/1) |
| 02 | Odoo Digital Enterprise | IN PROGRESS | [#2](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/2) — full pipeline prototyped end-to-end (see below); scale-up to full §7 volumes still pending |
| 03 | Planning & Performance Model | IN PROGRESS | [#3](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/3) — BUDGET version (BU x month) + Actual vs Budget variance done; quarterly FORECAST reforecasts still pending |
| 04 | Enterprise Analytics Engine | IN PROGRESS | [#4](https://github.com/inspiringviz-spec/benacta-ai-decision-system/issues/4) — P&L, concentration, project profitability done + tested; AR/AP aging and DSO unblocked on 2026-11-16 (ADR-0004) |
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

**Payments without journal entries — resolved (2026-11-16, [ADR-0004](adr/0004-payment-settlement-signal.md)):** not a platform bug. The bank journal has no outstanding account, so Odoo 18+ registers payments without an accounting entry and `amount_residual` never moves; `cannot marshal None` was XML-RPC choking on `action_post`'s `None` return. The ERP Adapter now derives `effective_residual` from `matched_payment_ids`, and AR/AP aging, working capital and DSO run on it (`tests/test_working_capital.py`).

**Payments rebalanced (2026-11-16):** the Odoo instance also carries 116 customer invoices (origin `BD/SO/*`, 24 untagged
customers, created 2026-09-17 by a generator outside this repo) with no payments. `data/generators/payments_rebalance.py`
now settles every unpaid document according to the segment payment behaviour (business-domain.md), on the dataset clock
(2026-08-09): 19 payments registered (incl. the three multi-million pilot invoices that sat in the 91+ bucket and 2
partials), 74 documents left open because not yet due. Idempotent (per-document seeded RNG, matched documents skipped);
plan in `data/ground-truth/payments_rebalance_2026-08-09.json`. Result: AR EUR 525.8k (0-60 days only), AP 0, DSO 61 days.
Open points: the BD batch assumes a clock near 2026-09-17 while the repo's is 2026-08-09 (decide one); no overdue AR
remains (storyline 4 *customer distress* has nothing to show, Crest Systems' invoices were paid in the pilot); AP is fully
settled, so AP aging is empty.

## Next

- Decide full-scale volume for Epic 02 (§7 targets: 500/150/300/200 + 50k/30k/100k transactions) — pragmatic scaling recommended, see conversation history.
- Move the Odoo API key from local `.env` to a GitHub Actions repository secret before any CI touches it.
- Epic 04 (Analytics Engine) can now be scaffolded against real data shapes.
