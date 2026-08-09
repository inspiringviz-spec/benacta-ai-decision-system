"""Project profitability (Epic 04, master prompt SS11 + SS7).

Reads planned figures (contract value, budget, planned margin) from
platform/analytics/data/project_budgets.json — visible planning data,
distinct from the hidden storyline labels in data/ground-truth (SS7:
"do not directly label every anomaly for the AI").
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_BUDGETS_PATH = Path(__file__).resolve().parent / "data" / "project_budgets.json"


@dataclass
class ProjectProfitability:
    name: str
    customer: str
    contract_value: float
    budget: float
    forecast_cost: float
    actual_cost: float
    planned_margin_pct: float
    forecast_margin: float
    forecast_margin_pct: float
    cost_variance: float
    cost_variance_pct: float


def load_project_budgets() -> list[dict]:
    return json.loads(_BUDGETS_PATH.read_text())


def compute_project_profitability() -> list[ProjectProfitability]:
    results = []
    for p in load_project_budgets():
        forecast_margin = p["contract_value"] - p["forecast_cost"]
        forecast_margin_pct = forecast_margin / p["contract_value"] if p["contract_value"] else 0.0
        cost_variance = p["forecast_cost"] - p["budget"]
        cost_variance_pct = cost_variance / p["budget"] if p["budget"] else 0.0
        results.append(
            ProjectProfitability(
                name=p["name"],
                customer=p["customer"],
                contract_value=p["contract_value"],
                budget=p["budget"],
                forecast_cost=p["forecast_cost"],
                actual_cost=p["actual_cost"],
                planned_margin_pct=p["planned_margin_pct"] / 100,
                forecast_margin=round(forecast_margin, 2),
                forecast_margin_pct=round(forecast_margin_pct, 4),
                cost_variance=round(cost_variance, 2),
                cost_variance_pct=round(cost_variance_pct, 4),
            )
        )
    return results


if __name__ == "__main__":
    rows = compute_project_profitability()
    rows.sort(key=lambda r: r.cost_variance, reverse=True)
    print(f"{'Project':<38} {'Contract':>12} {'Fcst Margin%':>13} {'Cost Var':>12} {'Cost Var%':>10}")
    for r in rows:
        print(
            f"{r.name:<38} {r.contract_value:>12,.0f} {r.forecast_margin_pct:>12.1%} "
            f"{r.cost_variance:>12,.0f} {r.cost_variance_pct:>9.1%}"
        )
