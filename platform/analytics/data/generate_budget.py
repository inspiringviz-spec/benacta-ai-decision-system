"""Epic 03 (Planning Model) — pragmatic scope for this pass: a BUDGET
version at Business-Unit x Month grain for the trailing 12 months,
derived independently of actuals (as a real budget would be — set at
the start of the year) but seeded from each family's actual scale so
the numbers are realistic.

Revenue and cost biases are set per family to reflect the causal
storylines already baked into the transaction data (business-domain.md):
Automated Production Lines (home of Atlas/Orion) is budgeted to cost
LESS than what actually landed; Control & Automation is budgeted to
sell LESS than what actually landed (storyline 10, growing family).

Quarterly reforecasts (§8 "Current vs Previous Forecast") are an
explicit next step, not built in this pass.
"""
from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "integrations" / "odoo"))

from adapter import OdooERPAdapter  # noqa: E402
from pnl import compute_monthly_by_family  # noqa: E402

TODAY = date(2026, 8, 9)
FY_START = TODAY - timedelta(days=365)

# revenue_bias > 1 means actual beat budget; cost_bias > 1 means actual cost
# overran budget. Both are "what really happened vs. what was planned".
FAMILY_BIAS = {
    "Automated Production Lines": {"revenue_bias": 1.02, "cost_bias": 1.14},  # Atlas/Orion overruns
    "Control & Automation Systems": {"revenue_bias": 1.10, "cost_bias": 1.03},  # growing family
    "Industrial Thermal Systems": {"revenue_bias": 0.92, "cost_bias": 1.01},  # declining family
    "Process Vessels & Tanks": {"revenue_bias": 1.0, "cost_bias": 1.0},
    "Material Handling Systems": {"revenue_bias": 1.0, "cost_bias": 1.0},
    "Spare Parts & Maintenance Kits": {"revenue_bias": 1.03, "cost_bias": 0.99},
}


def month_range(start: date, end: date) -> list[str]:
    months = []
    cur = date(start.year, start.month, 1)
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        cur = date(cur.year + (1 if cur.month == 12 else 0), 1 if cur.month == 12 else cur.month + 1, 1)
    return months


def main() -> None:
    rng = random.Random(5001)
    adapter = OdooERPAdapter()
    actuals = compute_monthly_by_family(adapter, date_from=FY_START, date_to=TODAY)
    months = month_range(FY_START, TODAY)

    # Annual actual per family, to size a sensible monthly budget.
    annual_actual: dict[str, dict[str, float]] = {}
    for (month, family), vals in actuals.items():
        b = annual_actual.setdefault(family, {"revenue": 0.0, "cogs": 0.0})
        b["revenue"] += vals["revenue"]
        b["cogs"] += vals["cogs"]

    budget_rows = []
    for family, totals in annual_actual.items():
        bias = FAMILY_BIAS.get(family, {"revenue_bias": 1.0, "cost_bias": 1.0})
        annual_revenue_budget = totals["revenue"] / bias["revenue_bias"] if totals["revenue"] else 0.0
        annual_cost_budget = totals["cogs"] / bias["cost_bias"] if totals["cogs"] else 0.0

        # Spread across the 12 months with mild seasonality + noise, not flat.
        weights = [1.0 + 0.15 * rng.uniform(-1, 1) for _ in months]
        weight_sum = sum(weights)
        for m, w in zip(months, weights):
            budget_rows.append(
                {
                    "month": m,
                    "family": family,
                    "revenue_budget": round(annual_revenue_budget * w / weight_sum, 2),
                    "cost_budget": round(annual_cost_budget * w / weight_sum, 2),
                }
            )

    out_path = Path(__file__).resolve().parent / "budget.json"
    out_path.write_text(json.dumps(budget_rows, indent=2))
    print(f"Wrote {len(budget_rows)} budget rows ({len(annual_actual)} families x {len(months)} months) to {out_path}")


if __name__ == "__main__":
    main()
