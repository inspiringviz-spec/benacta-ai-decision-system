"""Unit tests for the Analytics Engine (Epic 04) against known-correct values.

Requires .env (local, gitignored) with live Odoo credentials — these are
integration tests against the real prototype dataset, not offline unit
tests. Run from the repo root: python -m pytest tests/test_analytics.py -v
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "analytics"))
sys.path.insert(0, str(ROOT / "integrations" / "odoo"))

from adapter import OdooERPAdapter  # noqa: E402
from pnl import compute_pnl  # noqa: E402
from concentration import customer_concentration, supplier_concentration  # noqa: E402
from project_profitability import compute_project_profitability  # noqa: E402
from variance import actual_vs_budget  # noqa: E402


def test_pnl_gross_margin_is_internally_consistent():
    result = compute_pnl(OdooERPAdapter())
    assert result.revenue > 0
    assert abs(result.gross_margin - (result.revenue - result.cogs)) < 0.01
    assert 0.0 < result.gross_margin_pct < 1.0


def test_pnl_segment_breakdown_sums_to_total():
    result = compute_pnl(OdooERPAdapter())
    assert abs(sum(result.by_segment.values()) - result.revenue) < 0.01


def test_customer_concentration_top_n_le_total():
    result = customer_concentration(OdooERPAdapter(), top_n=10)
    assert result.top_n_amount <= result.total + 0.01
    assert 0.0 <= result.top_n_pct <= 1.0


def test_supplier_concentration_top_n_le_total():
    result = supplier_concentration(OdooERPAdapter(), top_n=5)
    assert result.top_n_amount <= result.total + 0.01


def test_project_atlas_matches_master_prompt_example():
    """Project Atlas was designed to mirror master prompt SS15 exactly:
    EUR 4.8M contract, -EUR410k cost variance vs. budget."""
    rows = compute_project_profitability()
    atlas = next(r for r in rows if r.name.startswith("Project Atlas"))
    assert atlas.contract_value == 4_800_000
    assert atlas.cost_variance == 410_000


def test_automated_production_lines_shows_cost_overrun_vs_budget():
    """The Atlas/Orion storyline is designed to make this family run over
    budget on cost — the variance engine should surface it without being
    told where to look."""
    rows = actual_vs_budget(OdooERPAdapter())
    apl = next(r for r in rows if r.family == "Automated Production Lines")
    assert apl.cost_variance > 0
    assert apl.cost_variance_pct > 0.05  # more than a rounding blip


def test_all_projects_have_positive_forecast_margin_pct_or_are_flagged():
    """Every project should be profitable on paper (even the problem
    cases are still forecast-positive — they're deteriorating, not
    loss-making, matching the storyline design)."""
    rows = compute_project_profitability()
    for r in rows:
        assert r.forecast_margin_pct > 0, f"{r.name} has non-positive forecast margin"
