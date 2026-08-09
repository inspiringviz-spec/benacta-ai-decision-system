"""Customer / supplier concentration (Epic 04, KPI catalog SS"CFO Agent").
"""
from __future__ import annotations

import _adapter_path  # noqa: F401
from dataclasses import dataclass

from adapter import OdooERPAdapter


@dataclass
class ConcentrationResult:
    total: float
    top_n: int
    top_n_amount: float
    top_n_pct: float
    ranked: list[tuple[str, float]]


def _rank_by_partner(moves, sign: int = 1) -> dict[str, float]:
    totals: dict[str, float] = {}
    for m in moves:
        totals[m.partner_name] = totals.get(m.partner_name, 0.0) + sign * m.amount_total
    return totals


def customer_concentration(adapter: OdooERPAdapter, top_n: int = 10) -> ConcentrationResult:
    invoices = adapter.get_customer_invoices()
    credit_notes = adapter.get_customer_credit_notes()
    totals = _rank_by_partner(invoices, 1)
    for k, v in _rank_by_partner(credit_notes, -1).items():
        totals[k] = totals.get(k, 0.0) + v

    ranked = sorted(totals.items(), key=lambda x: -x[1])
    total = sum(totals.values())
    top_amount = sum(v for _, v in ranked[:top_n])
    return ConcentrationResult(
        total=round(total, 2),
        top_n=top_n,
        top_n_amount=round(top_amount, 2),
        top_n_pct=round(top_amount / total, 4) if total else 0.0,
        ranked=[(k, round(v, 2)) for k, v in ranked],
    )


def supplier_concentration(adapter: OdooERPAdapter, top_n: int = 5) -> ConcentrationResult:
    bills = adapter.get_vendor_bills()
    credit_notes = adapter.get_vendor_credit_notes()
    totals = _rank_by_partner(bills, 1)
    for k, v in _rank_by_partner(credit_notes, -1).items():
        totals[k] = totals.get(k, 0.0) + v

    ranked = sorted(totals.items(), key=lambda x: -x[1])
    total = sum(totals.values())
    top_amount = sum(v for _, v in ranked[:top_n])
    return ConcentrationResult(
        total=round(total, 2),
        top_n=top_n,
        top_n_amount=round(top_amount, 2),
        top_n_pct=round(top_amount / total, 4) if total else 0.0,
        ranked=[(k, round(v, 2)) for k, v in ranked],
    )


if __name__ == "__main__":
    a = OdooERPAdapter()

    cc = customer_concentration(a)
    print(f"Customer concentration: top {cc.top_n} = {cc.top_n_pct:.1%} of EUR {cc.total:,.2f} total revenue")
    for name, amount in cc.ranked[:cc.top_n]:
        print(f"  {name:<32} EUR {amount:>12,.2f}")

    print()
    sc = supplier_concentration(a)
    print(f"Supplier concentration: top {sc.top_n} = {sc.top_n_pct:.1%} of EUR {sc.total:,.2f} total spend")
    for name, amount in sc.ranked[:sc.top_n]:
        print(f"  {name:<32} EUR {amount:>12,.2f}")
