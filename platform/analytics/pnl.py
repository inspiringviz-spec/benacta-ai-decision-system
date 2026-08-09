"""P&L / margin calculations (Epic 04, master prompt SS11).

Deterministic only — no LLM involved. COGS is a proxy: product standard_price
x quantity (no inventory valuation is configured on this Odoo instance),
which matches the target margins set when products were priced in Epic 02.
This is a documented approximation for the prototype, not a limitation
agents should ever need to know about — they just call these functions.
"""
from __future__ import annotations

import _adapter_path  # noqa: F401  (sets up sys.path for the import below)
from dataclasses import dataclass
from datetime import date

from adapter import Move, OdooERPAdapter, Product


@dataclass
class PnLResult:
    revenue: float
    cogs: float
    gross_margin: float
    gross_margin_pct: float
    by_segment: dict[str, float]
    by_product_family: dict[str, float]


def _net_lines(invoices: list[Move], credit_notes: list[Move]):
    """Yield (line, sign) — +1 for invoice lines, -1 for credit note lines."""
    for m in invoices:
        for line in m.lines:
            yield m, line, 1
    for m in credit_notes:
        for line in m.lines:
            yield m, line, -1


def compute_pnl(
    adapter: OdooERPAdapter, date_from: date | None = None, date_to: date | None = None
) -> PnLResult:
    products: dict[int, Product] = {p.id: p for p in adapter.get_products()}
    customers_by_id = {c.id: c for c in adapter.get_customers()}

    invoices = adapter.get_customer_invoices(date_from, date_to)
    credit_notes = adapter.get_customer_credit_notes(date_from, date_to)

    revenue = 0.0
    cogs = 0.0
    by_segment: dict[str, float] = {}
    by_family: dict[str, float] = {}

    for move, line, sign in _net_lines(invoices, credit_notes):
        amount = sign * line.price_subtotal
        revenue += amount

        product = products.get(line.product_id)
        cost = sign * (product.standard_price * line.quantity if product else 0.0)
        cogs += cost

        customer = customers_by_id.get(move.partner_id)
        segment = customer.segment if customer else "Unknown"
        by_segment[segment] = by_segment.get(segment, 0.0) + amount

        family = product.family if product else "Unknown"
        by_family[family] = by_family.get(family, 0.0) + amount

    gross_margin = revenue - cogs
    gross_margin_pct = (gross_margin / revenue) if revenue else 0.0

    return PnLResult(
        revenue=round(revenue, 2),
        cogs=round(cogs, 2),
        gross_margin=round(gross_margin, 2),
        gross_margin_pct=round(gross_margin_pct, 4),
        by_segment={k: round(v, 2) for k, v in by_segment.items()},
        by_product_family={k: round(v, 2) for k, v in by_family.items()},
    )


if __name__ == "__main__":
    result = compute_pnl(OdooERPAdapter())
    print(f"Revenue:            EUR {result.revenue:,.2f}")
    print(f"COGS:                EUR {result.cogs:,.2f}")
    print(f"Gross margin:        EUR {result.gross_margin:,.2f} ({result.gross_margin_pct:.1%})")
    print("\nBy segment:")
    for k, v in sorted(result.by_segment.items(), key=lambda x: -x[1]):
        print(f"  {k:<28} EUR {v:>14,.2f}")
    print("\nBy product family:")
    for k, v in sorted(result.by_product_family.items(), key=lambda x: -x[1]):
        print(f"  {k:<28} EUR {v:>14,.2f}")
