# Business Domain — Benacta Manufacturing Group

Reference model for all synthetic data generation (Epic 02) and for the scenarios agents will investigate (Epics 07-10). Extends master prompt §5-§7.

## Positioning

Benacta Manufacturing Group is an **industrial EPC-style contractor**: it engineers, manufactures, installs, and maintains custom process equipment for B2B industrial clients. Operating model: **Engineering → Procurement → Fabrication → Installation & Commissioning → Maintenance/Service** — project-based, not catalog/retail.

Not construction/BTP (buildings, roads, civil works) — this is industrial process equipment for factories and production sites.

## Product families (6)

| Family | Description | Margin profile |
|---|---|---|
| Process Vessels & Tanks | Pressure vessels, mixing tanks, storage tanks | Medium, engineering-heavy |
| Material Handling Systems | Conveyors, automated sorting/palletizing | Medium |
| Automated Production Lines | Robotics-integrated assembly/packaging lines | High value, high complexity, highest overrun risk |
| Industrial Thermal Systems | Heat exchangers, industrial HVAC, cooling systems | Medium-high |
| Control & Automation Systems | PLC/SCADA integration, sensors, retrofits | High margin, lower capital intensity |
| Spare Parts & Maintenance Kits | Recurring, lower complexity | Highest margin, steady volume, low risk |

## Customer segments

| Segment | Profile | Payment behavior | Risk |
|---|---|---|---|
| Large multinational F&B manufacturers | Long sales cycles, strict specs, high volume | Good, on-time, 60-day terms | Low, but demanding on quality/schedule |
| Pharma / life sciences | Smaller volume, highest compliance bar, sticky relationships | Very good | Low financial risk, high schedule/quality risk |
| Energy & utilities | Large contract values, multi-year, milestone-billed | Slow, bureaucratic, 90-day terms | Cash-timing risk, not credit risk |
| Mid-market industrial manufacturers | Higher volume of smaller projects, price-sensitive | Variable, some late payers | Highest credit/AR risk |
| High-growth newer accounts | Fast-growing, attractive future pipeline, thin history | Unproven | Highest uncertainty — the "accept conditionally" cases |

~500 customers distributed roughly: 15% large F&B, 10% pharma, 10% energy/utilities, 50% mid-market industrial, 15% newer/high-growth.

## Supplier categories

| Category | Exposure |
|---|---|
| Raw materials (steel, specialty alloys) | Commodity price volatility — feeds the supplier inflation chain |
| Electronic / automation components | Lead-time and geopolitical exposure |
| Subcontracted fabrication & installation labor | Regional capacity constraints |
| Logistics / freight | Expedited-shipping cost spikes |
| Specialized certified components (pressure-rated, compliance parts) | Few qualified suppliers — concentration risk |

~150 suppliers, with intentional concentration on 2-3 single-source certified-component suppliers (needed for the concentration-risk scenario).

## Causal storylines (10)

Beyond the 3 named in master prompt §7, for narrative richness. Ground-truth metadata for all of these is stored separately under `/data/ground-truth`, never labeled in the data agents see.

1. **Steel/alloy inflation** (§7 baseline) — supplier price increase → fixed-price project costs rise → margin erosion → EBITDA impact.
2. **Single-source component disruption** — a certified-component supplier has a delivery disruption → project schedule slips → penalty clauses trigger → revenue recognition and cash both move.
3. **Change-order recovery** (mirrors the §16/§18 Atlas example) — a pharma client's scope creep drives engineering-hour overruns; a change order can recover part of the margin loss if negotiated.
4. **Customer financial distress** — a mid-market customer's payment behavior deteriorates → AR aging worsens → working capital deteriorates → a credit decision is needed (hold shipment vs. extend terms).
5. **Capacity constraint from growth** (§7 baseline) — strong bookings in a new region outstrip engineering/fabrication capacity → a trade-off between overtime cost, subcontracting, or delaying other projects.
6. **Warranty / commissioning failure** — a delivered production line fails commissioning tests → rework costs → customer relationship and future-pipeline risk.
7. **Front-loaded cash requirement** — a large multi-year energy contract has favorable long-term margin but heavy upfront spend before milestone billing catches up → near-term cash forecast risk.
8. **FX exposure** — an international contract priced in EUR sources key components in USD → margin volatility independent of operational performance.
9. **Strategic low-margin acceptance** — competitive pressure creates a decision to accept a thinner-margin project to enter a strategic new account (the §18 "should we accept this?" pattern).
10. **Product-line mix shift** — a legacy product family (e.g. older thermal systems) declines while Control & Automation grows — a portfolio-level margin trajectory story, not a single-project one.

## Organization

Departments: Sales, Engineering, Procurement, Fabrication/Operations, Installation & Commissioning, Finance & Controlling, Project Management Office. Every project carries a named Project Manager who contributes qualitative commentary (§7) — this is what feeds RAG-retrievable "PM commentary" documents in Epic 06.

## Geography

HQ + fabrication in one home region; sales and installation footprint across 3-4 regions to support the FX and logistics storylines (§7, storyline 8 above).
