# KPI Catalog & Planning Model

Extends master prompt §8 (Planning & Performance) and §13 (agent responsibilities). This is the concrete metric/dimension catalog that Epic 03 (Planning Model) and Epic 04 (Analytics Engine) implement, and what the CFO/COO/CRO agents investigate against.

## Planning calendar & versions

Mirrors a real corporate FP&A calendar, so "Current Forecast vs Previous Forecast" (§8) is a meaningful comparison, not just two flat numbers:

| Version | Cadence | Notes |
|---|---|---|
| BUDGET | Set once, start of fiscal year | The baseline everything is measured against |
| FORECAST (Q1, Q2, Q3, Q4 reforecasts) | Quarterly | Each reforecast supersedes the previous — enables "Current Forecast vs Previous Forecast" |
| ACTUAL | Continuous | From Odoo transactions |
| SCENARIO | Ad hoc | Tied to Decision Engine simulations (Epic 12), never persisted as "official" |

## Dimensions (§8)

Time · Company (single company for now, multi-company-capable per Odoo config) · **Business Unit** (one per product family — see below) · Project · Customer · Product · Supplier · **Cost Center** · Account (chart of accounts).

## Cost centers

Engineering · Procurement · Fabrication/Manufacturing · Installation & Commissioning (field) · Sales & Marketing · Quality · Maintenance/Service · G&A.

Business Units map 1:1 to the 6 product families in `business-domain.md`, so revenue/margin can be sliced either by BU or by cost center.

## CFO Agent — KPI catalog

| Metric | Definition | Feeds |
|---|---|---|
| Revenue | By segment, BU, product family, region | P&L, Executive Pulse |
| Gross Margin / % | Revenue − COGS | P&L |
| Contribution Margin | Gross Margin − directly attributable variable costs | Project profitability |
| EBITDA / EBITDA Margin | Operating result before D&A | Executive Pulse |
| Backlog / Book-to-bill | Signed-not-yet-recognized revenue / bookings vs billings | Forward visibility |
| DSO, DPO, Cash Conversion Cycle | Standard working-capital metrics | Cash forecasting |
| AR aging | 0-30 / 31-60 / 61-90 / 90+ buckets, by customer segment | Storyline 4 (customer distress) |
| Customer concentration | % revenue from top 10 customers | Credit/commercial risk |
| Cost variance | Budget vs Actual, by cost center and by project phase | Variance investigation |
| Change-order recovery rate | % of scope-creep cost recovered via change orders | Storyline 3 |
| FX exposure | Unhedged position by currency pair | Storyline 8 |

## COO Agent — KPI catalog

| Metric | Definition | Feeds |
|---|---|---|
| Schedule variance | Days ahead/behind baseline, by project and by phase | Project Performance Agent |
| Cost variance by phase | Engineering / Procurement / Fabrication / Installation, budget vs actual | Margin bridge |
| Engineering hours utilization | Budgeted vs actual hours per project (§7 "engineering hours") | Storyline 3, 5 |
| Fabrication capacity utilization | % of plant capacity used, by period | Storyline 5 (capacity chain) |
| On-time delivery rate | Supplier→Benacta and Benacta→customer | Storyline 2 |
| Supplier quality/defect rate | Defects per shipment, by supplier | Supplier risk |
| Inventory turns / obsolete % / stockouts | Standard inventory health metrics | Working capital, Epic 04 |
| Warranty claim rate | Claims and rework cost as % of project revenue | Storyline 6 |
| Field service response time | Hours from request to technician dispatch | Service quality |

## CRO / Commercial Agent — KPI catalog

| Metric | Definition | Feeds |
|---|---|---|
| Pipeline value & win rate | By segment, by BU | Sales forecast |
| Quote-to-order conversion | % of quotes that convert | Commercial efficiency |
| Customer profitability | Margin by customer, not just revenue | Cross-sell/pricing decisions |
| Sales cycle length | Days from first contact to signed contract, by segment | Segment comparison (§domain: F&B vs energy vs mid-market differ a lot here) |
| Customer churn/retention | By segment | Storyline 4, 6 |

## Executive Pulse (§15) — composition

Each headline KPI on the cockpit's home screen decomposes into the metrics above, so a click-through always lands on real evidence rather than a dead end:

- **Revenue** → segment/BU/product breakdown
- **EBITDA** → gross margin − opex by cost center, bridged period-over-period
- **Cash** → DSO/DPO/CCC + AR aging + upcoming milestone billings
- **Margin** → contribution margin by project, cost variance by phase
- **Working Capital** → AR + Inventory − AP, trended
- **Backlog** → book-to-bill, by segment
- **Operational Performance** → schedule variance, capacity utilization, on-time delivery
- **Forecast** → current vs previous quarterly reforecast, by BU

## Why this matters for the agents

Every one of the 10 causal storylines in `business-domain.md` now has a specific, named metric path an agent can walk: e.g., storyline 5 (capacity constraint) shows up first as **Fabrication capacity utilization** climbing, which an investigation traces to **schedule variance** on affected projects, which shows up in **EBITDA** via **cost variance by phase** (overtime premium) — a real evidence chain, not a hand-wave.
