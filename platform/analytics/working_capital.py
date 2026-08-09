"""Cash / AR-AP aging / working capital (Epic 04, KPI catalog).

Note: `payment_state == 'in_payment'` still carries a non-zero
amount_residual on this instance (payments are registered but not bank-
reconciled — ADR-0002 / roadmap "known simplification"). We treat only
`amount_residual > 0` as "outstanding" regardless of payment_state label,
which is the financially correct signal.
"""
from __future__ import annotations

import _adapter_path  # noqa: F401
from dataclasses import dataclass
from datetime import date, datetime

from adapter import OdooERPAdapter

TODAY = date(2026, 8, 9)
BUCKETS = [(0, 30), (31, 60), (61, 90), (91, None)]


@dataclass
class AgingResult:
    total_outstanding: float
    buckets: dict[str, float]


def _bucket_label(days: int) -> str:
    for lo, hi in BUCKETS:
        if hi is None or lo <= days <= hi:
            if hi is None:
                return f"{lo}+"
            return f"{lo}-{hi}"
    return "unknown"


def _aging(moves) -> AgingResult:
    buckets = {_bucket_label(lo): 0.0 for lo, hi in BUCKETS}
    total = 0.0
    for m in moves:
        if not m.invoice_date or m.amount_residual <= 0:
            continue
        inv_date = datetime.strptime(m.invoice_date, "%Y-%m-%d").date()
        days = (TODAY - inv_date).days
        buckets[_bucket_label(days)] += m.amount_residual
        total += m.amount_residual
    return AgingResult(total_outstanding=round(total, 2), buckets={k: round(v, 2) for k, v in buckets.items()})


def ar_aging(adapter: OdooERPAdapter) -> AgingResult:
    return _aging(adapter.get_customer_invoices())


def ap_aging(adapter: OdooERPAdapter) -> AgingResult:
    return _aging(adapter.get_vendor_bills())


def dso(adapter: OdooERPAdapter, period_days: int = 90) -> float:
    """Days Sales Outstanding, approximated over the trailing `period_days`."""
    from datetime import timedelta

    period_start = TODAY - timedelta(days=period_days)
    invoices = adapter.get_customer_invoices(date_from=period_start, date_to=TODAY)
    revenue = sum(m.amount_total for m in invoices)
    ar = ar_aging(adapter).total_outstanding
    if revenue == 0:
        return 0.0
    return round((ar / revenue) * period_days, 1)


if __name__ == "__main__":
    a = OdooERPAdapter()

    ar = ar_aging(a)
    print(f"AR outstanding: EUR {ar.total_outstanding:,.2f}")
    for bucket, amount in ar.buckets.items():
        print(f"  {bucket:<10} EUR {amount:>12,.2f}")

    ap = ap_aging(a)
    print(f"\nAP outstanding: EUR {ap.total_outstanding:,.2f}")
    for bucket, amount in ap.buckets.items():
        print(f"  {bucket:<10} EUR {amount:>12,.2f}")

    print(f"\nWorking capital (AR - AP): EUR {ar.total_outstanding - ap.total_outstanding:,.2f}")
    print(f"DSO (trailing 90d): {dso(a)} days")
