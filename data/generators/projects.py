"""Pilot project generator (Epic 02).

15 projects: 2 flagship (Atlas, Orion — mirroring the master prompt's own
§15/§16/§18 example numbers exactly, so later CFO-agent/Decision-Engine
testing has a ready-made golden case), 8 covering the remaining causal
storylines, and 5 healthy baseline projects (control group — not every
project should be a problem).
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from common import GROUND_TRUTH_DIR, write_ground_truth
from odoo_client import OdooClient

TODAY = date(2026, 8, 9)


def load(name: str) -> list[dict]:
    return json.loads((GROUND_TRUTH_DIR / name).read_text())


def by_segment(customers: list[dict], segment: str) -> list[dict]:
    return [c for c in customers if c["segment"] == segment]


def describe(spec: dict) -> str:
    lines = [
        f"Contract value: EUR {spec['contract_value']:,}",
        f"Planned margin: {spec['planned_margin_pct']}%",
        f"Budget: EUR {spec['budget']:,} | Forecast cost: EUR {spec['forecast_cost']:,} | Actual cost to date: EUR {spec['actual_cost']:,}",
        f"Engineering hours: planned {spec['eng_hours_planned']}h / actual {spec['eng_hours_actual']}h",
        f"Milestones: {spec['milestones']}",
        f"Project Manager: {spec['pm']}",
        "",
        f"PM commentary: {spec['commentary']}",
    ]
    return "\n".join(lines)


def build_specs(customers: list[dict], employees: list[dict], rng: random.Random) -> list[dict]:
    energy = by_segment(customers, "Energy & Utilities")
    pharma = by_segment(customers, "Pharma / Life Sciences")
    midmarket = by_segment(customers, "Mid-market Industrial")
    fnb = by_segment(customers, "Large F&B")
    highgrowth = by_segment(customers, "High-growth New Account")
    pm = lambda: rng.choice(employees)["name"]

    specs = [
        {
            "name": "Project Atlas — Automated Production Line",
            "customer": energy[0],
            "storyline": "steel_inflation+capacity_constraint+logistics (flagship, mirrors master prompt SS15)",
            "contract_value": 4_800_000,
            "planned_margin_pct": 22,
            "budget": 3_744_000,
            "forecast_cost": 4_154_000,
            "actual_cost": 3_980_000,
            "eng_hours_planned": 6200,
            "eng_hours_actual": 7450,
            "milestones": "M1 Design (done), M2 Fabrication (done, +3wk late), M3 Installation (in progress), M4 Commissioning (pending)",
            "commentary": (
                "Steel price inflation added ~EUR170k to fabrication cost. Engineering overrun "
                "(~EUR120k) driven by scope clarification cycles with client engineering team. "
                "Expedited freight (~EUR75k) used to recover M2 schedule slip. Milestone M2 delivered "
                "3 weeks late, triggering delayed-milestone cash impact (~EUR45k). Total EBITDA impact "
                "vs. plan: approx. -EUR410k. Recommend pursuing change-order recovery on the scope "
                "clarifications and restricting non-critical engineering scope on remaining phases."
            ),
            "date_start": TODAY - timedelta(days=300),
            "date_end": TODAY + timedelta(days=120),
            "storyline_key": "steel_inflation",
        },
        {
            "name": "Project Orion — Material Handling Upgrade",
            "customer": energy[1] if len(energy) > 1 else energy[0],
            "storyline": "capacity_constraint (shares engineering pool with Atlas)",
            "contract_value": 2_100_000,
            "planned_margin_pct": 26,
            "budget": 1_554_000,
            "forecast_cost": 1_705_000,
            "actual_cost": 1_610_000,
            "eng_hours_planned": 2400,
            "eng_hours_actual": 2850,
            "milestones": "M1 Design (done, +2wk late), M2 Fabrication (in progress)",
            "commentary": (
                "Engineering capacity shared with Project Atlas — Atlas's overrun pulled senior "
                "engineering resources away from Orion during M1, causing a 2-week design delay. "
                "No direct material cost issue; risk is schedule, not margin, for now."
            ),
            "date_start": TODAY - timedelta(days=200),
            "date_end": TODAY + timedelta(days=150),
            "storyline_key": "capacity_constraint",
        },
        {
            "name": "Project Meridian — Certified Reactor Vessel",
            "customer": pharma[0],
            "storyline": "supplier_disruption",
            "contract_value": 1_350_000,
            "planned_margin_pct": 28,
            "budget": 972_000,
            "forecast_cost": 1_040_000,
            "actual_cost": 610_000,
            "eng_hours_planned": 1800,
            "eng_hours_actual": 1150,
            "milestones": "M1 Design (done), M2 Procurement (blocked)",
            "commentary": (
                "Single-source certified-component supplier reported a 6-week delivery disruption "
                "on the pressure-rated fittings required for M2. No qualified alternate supplier "
                "identified yet. Schedule and margin both at risk if disruption extends past 8 weeks."
            ),
            "date_start": TODAY - timedelta(days=90),
            "date_end": TODAY + timedelta(days=200),
            "storyline_key": "supplier_disruption",
        },
        {
            "name": "Project Halcyon — Bioprocessing Line Retrofit",
            "customer": pharma[1] if len(pharma) > 1 else pharma[0],
            "storyline": "change_order_recovery",
            "contract_value": 980_000,
            "planned_margin_pct": 30,
            "budget": 686_000,
            "forecast_cost": 810_000,
            "actual_cost": 720_000,
            "eng_hours_planned": 1400,
            "eng_hours_actual": 1900,
            "milestones": "M1 Design (done, scope expanded), M2 Fabrication (in progress)",
            "commentary": (
                "Client requested additional compliance validation steps mid-design (scope creep), "
                "driving a 500-hour engineering overrun. A change order covering ~60% of the added "
                "cost is in negotiation; if approved, most of the margin dilution is recoverable."
            ),
            "date_start": TODAY - timedelta(days=150),
            "date_end": TODAY + timedelta(days=90),
            "storyline_key": "change_order_recovery",
        },
        {
            "name": "Project Ferrum — Conveyor Line Replacement",
            "customer": midmarket[0],
            "storyline": "customer_distress",
            "contract_value": 420_000,
            "planned_margin_pct": 24,
            "budget": 319_200,
            "forecast_cost": 322_000,
            "actual_cost": 298_000,
            "eng_hours_planned": 600,
            "eng_hours_actual": 615,
            "milestones": "M1 Design (done), M2 Fabrication (done), M3 Installation (done), M4 Invoiced (overdue 45 days)",
            "commentary": (
                "Project delivered on scope and budget. Customer's final milestone payment is 45 days "
                "overdue; customer has also delayed payment on two unrelated invoices this quarter. "
                "Credit risk flag raised — recommend reviewing exposure before accepting the client's "
                "next order."
            ),
            "date_start": TODAY - timedelta(days=250),
            "date_end": TODAY - timedelta(days=20),
            "storyline_key": "customer_distress",
        },
        {
            "name": "Project Solstice — Packaging Line Commissioning",
            "customer": fnb[0],
            "storyline": "warranty_failure",
            "contract_value": 1_600_000,
            "planned_margin_pct": 22,
            "budget": 1_248_000,
            "forecast_cost": 1_310_000,
            "actual_cost": 1_295_000,
            "eng_hours_planned": 2200,
            "eng_hours_actual": 2260,
            "milestones": "M1-M3 (done), M4 Commissioning (failed acceptance test, rework in progress)",
            "commentary": (
                "Line failed commissioning acceptance testing due to a sensor calibration defect. "
                "Rework estimated at ~EUR85k, covered under warranty (not billable). Client "
                "relationship remains positive but future-pipeline risk noted given repeat visits."
            ),
            "date_start": TODAY - timedelta(days=280),
            "date_end": TODAY - timedelta(days=10),
            "storyline_key": "warranty_failure",
        },
        {
            "name": "Project Beacon — Multi-site Utility Retrofit",
            "customer": energy[2] if len(energy) > 2 else energy[0],
            "storyline": "cash_frontload",
            "contract_value": 5_200_000,
            "planned_margin_pct": 20,
            "budget": 4_160_000,
            "forecast_cost": 4_180_000,
            "actual_cost": 1_850_000,
            "eng_hours_planned": 7000,
            "eng_hours_actual": 2400,
            "milestones": "M1 Design (done), M2 Long-lead procurement (in progress) — next milestone billing in 4 months",
            "commentary": (
                "Multi-year contract, on plan for margin. Long-lead procurement for specialized "
                "components required significant upfront spend before the next milestone billing "
                "event — near-term cash exposure, not a profitability issue."
            ),
            "date_start": TODAY - timedelta(days=120),
            "date_end": TODAY + timedelta(days=540),
            "storyline_key": "cash_frontload",
        },
        {
            "name": "Project Riviera — European Cooling System Install",
            "customer": fnb[1] if len(fnb) > 1 else fnb[0],
            "storyline": "fx_exposure",
            "contract_value": 890_000,
            "planned_margin_pct": 27,
            "budget": 649_700,
            "forecast_cost": 668_000,
            "actual_cost": 640_000,
            "eng_hours_planned": 900,
            "eng_hours_actual": 890,
            "milestones": "M1-M2 (done), M3 Installation (in progress)",
            "commentary": (
                "Contract priced in EUR; key thermal components sourced from a USD-invoiced supplier. "
                "USD strengthened ~4% since order placement, absorbing part of the planned margin. "
                "Unhedged position — consider FX hedging policy for future USD-sourced contracts."
            ),
            "date_start": TODAY - timedelta(days=140),
            "date_end": TODAY + timedelta(days=40),
            "storyline_key": "fx_exposure",
        },
        {
            "name": "Project Nexus — Strategic Entry Automation Cell",
            "customer": highgrowth[0],
            "storyline": "strategic_low_margin",
            "contract_value": 610_000,
            "planned_margin_pct": 12,
            "budget": 536_800,
            "forecast_cost": 536_800,
            "actual_cost": 210_000,
            "eng_hours_planned": 800,
            "eng_hours_actual": 340,
            "milestones": "M1 Design (in progress)",
            "commentary": (
                "Accepted at a thinner-than-usual margin to win a strategic new high-growth account "
                "in a target segment. On plan so far; the bet is on future repeat business, not this "
                "project's own economics."
            ),
            "date_start": TODAY - timedelta(days=40),
            "date_end": TODAY + timedelta(days=160),
            "storyline_key": "strategic_low_margin",
        },
        {
            "name": "Project Kinetic — Legacy Thermal System Refresh",
            "customer": midmarket[1] if len(midmarket) > 1 else midmarket[0],
            "storyline": "product_mix_shift",
            "contract_value": 340_000,
            "planned_margin_pct": 24,
            "budget": 258_400,
            "forecast_cost": 258_000,
            "actual_cost": 255_000,
            "eng_hours_planned": 450,
            "eng_hours_actual": 440,
            "milestones": "M1-M3 (done)",
            "commentary": (
                "Straightforward refresh of a legacy thermal system. Demand for this product family "
                "is declining as clients shift budget toward Control & Automation retrofits — this "
                "project is one of the last of its kind in the pipeline for this customer."
            ),
            "date_start": TODAY - timedelta(days=200),
            "date_end": TODAY - timedelta(days=60),
            "storyline_key": "product_mix_shift",
        },
    ]

    # 5 healthy baseline projects — no storyline, on plan.
    healthy_customers = (midmarket[2:5] if len(midmarket) > 4 else midmarket) + fnb[2:3] + energy[3:4]
    baseline_names = [
        "Project Elbrus — Standard Conveyor Installation",
        "Project Marlow — Control Panel Retrofit",
        "Project Windsor — Storage Tank Expansion",
        "Project Alden — Sensor Array Upgrade",
        "Project Castell — Maintenance Kit Rollout",
    ]
    for i, bname in enumerate(baseline_names):
        cust = (healthy_customers[i % len(healthy_customers)] if healthy_customers else midmarket[0])
        contract = rng.randint(150_000, 500_000)
        margin_pct = rng.randint(24, 30)
        budget = int(contract * (1 - margin_pct / 100))
        specs.append(
            {
                "name": bname,
                "customer": cust,
                "storyline": "none (baseline/healthy)",
                "contract_value": contract,
                "planned_margin_pct": margin_pct,
                "budget": budget,
                "forecast_cost": budget,
                "actual_cost": int(budget * rng.uniform(0.85, 1.0)),
                "eng_hours_planned": rng.randint(300, 900),
                "eng_hours_actual": 0,
                "milestones": "On track, no issues reported.",
                "commentary": "Executing on plan. No cost, schedule, or quality issues to date.",
                "date_start": TODAY - timedelta(days=rng.randint(30, 260)),
                "date_end": TODAY + timedelta(days=rng.randint(30, 200)),
                "storyline_key": None,
            }
        )
        specs[-1]["eng_hours_actual"] = int(specs[-1]["eng_hours_planned"] * rng.uniform(0.9, 1.0))
        specs[-1]["pm"] = pm()

    for s in specs:
        s.setdefault("pm", pm())
    return specs


def main() -> None:
    rng = random.Random(2030)
    client = OdooClient()
    customers = load("customers_pilot.json")
    employees = load("employees_pilot.json")

    specs = build_specs(customers, employees, rng)

    to_create = []
    plan = []
    for s in specs:
        to_create.append(
            {
                "name": s["name"],
                "partner_id": s["customer"]["odoo_id"],
                "date_start": s["date_start"].isoformat(),
                "date": s["date_end"].isoformat(),
                "description": describe(s),
            }
        )
        plan.append(
            {
                "name": s["name"],
                "customer": s["customer"]["name"],
                "storyline_key": s["storyline_key"],
                "contract_value": s["contract_value"],
                "planned_margin_pct": s["planned_margin_pct"],
                "budget": s["budget"],
                "forecast_cost": s["forecast_cost"],
                "actual_cost": s["actual_cost"],
                "pm": s["pm"],
            }
        )

    ids = client.create("project.project", to_create)
    for record, project_id in zip(plan, ids):
        record["odoo_id"] = project_id

    write_ground_truth("projects_pilot.json", plan)
    print(f"Created {len(ids)} projects.")


if __name__ == "__main__":
    main()
