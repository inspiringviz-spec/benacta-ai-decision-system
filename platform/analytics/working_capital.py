"""Cash / AR-AP aging / working capital (Epic 04, KPI catalog).

Settlement signal (ADR-0004): this instance's bank journal has no
outstanding account, so Odoo 18+ registers payments without a journal
entry. The accounting `amount_residual` of an `in_payment` invoice stays at
the full amount until a bank statement is reconciled, which never happens
in this synthetic enterprise. The ERP Adapter therefore derives
`effective_residual` from the matched payments, and everything here uses
that field. `amount_residual` is kept on the Move for traceability only.
"""
from __future__ import annotations

import _adapter_path  # noqa: F401
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from adapter import DATASET_AS_OF, OdooERPAdapter

BUCKETS = [(0, 30), (31, 60), (61, 90), (91, None)]


@dataclass
class AgingResult:
    as_of: date
    total_outstanding: float
    buckets: dict[str, float]
    open_documents: int = 0
    settled_documents: int = 0
    excluded_unsettled_no_date: int = 0
    document_ids: list[int] = field(default_factory=list)


def _bucket_label(days: int) -> str:
    for lo, hi in BUCKETS:
        if hi is None or lo <= days <= hi:
            if hi is None:
                return f"{lo}+"
            return f"{lo}-{hi}"
    return "unknown"


def _aging(moves, as_of: date) -> AgingResult:
    """Age the unsettled part of each document by its invoice date.

    A document with `effective_residual <= 0` is settled and never
    contributes, whatever Odoo's `payment_state` label says. Documents
    dated after `as_of` are ignored (not yet issued at the reference date).
    """
    buckets = {_bucket_label(lo): 0.0 for lo, hi in BUCKETS}
    total = 0.0
    open_docs: list[int] = []
    settled = 0
    no_date = 0
    for m in moves:
        if m.is_settled:
            settled += 1
            continue
        if not m.invoice_date:
            no_date += 1
            continue
        inv_date = datetime.strptime(m.invoice_date, "%Y-%m-%d").date()
        days = (as_of - inv_date).days
        if days < 0:
            continue
        buckets[_bucket_label(days)] += m.effective_residual
        total += m.effective_residual
        open_docs.append(m.id)
    return AgingResult(
        as_of=as_of,
        total_outstanding=round(total, 2),
        buckets={k: round(v, 2) for k, v in buckets.items()},
        open_documents=len(open_docs),
        settled_documents=settled,
        excluded_unsettled_no_date=no_date,
        document_ids=open_docs,
    )


def ar_aging(adapter: OdooERPAdapter, as_of: date | None = None) -> AgingResult:
    return _aging(adapter.get_customer_invoices(), as_of or DATASET_AS_OF)


def ap_aging(adapter: OdooERPAdapter, as_of: date | None = None) -> AgingResult:
    return _aging(adapter.get_vendor_bills(), as_of or DATASET_AS_OF)


def dso(adapter: OdooERPAdapter, period_days: int = 90, as_of: date | None = None) -> float:
    """Days Sales Outstanding, approximated over the trailing `period_days`:
    open receivables at `as_of` divided by the revenue invoiced in the
    period, scaled to days."""
    as_of = as_of or DATASET_AS_OF
    period_start = as_of - timedelta(days=period_days)
    invoices = adapter.get_customer_invoices(date_from=period_start, date_to=as_of)
    revenue = sum(m.amount_total for m in invoices)
    ar = ar_aging(adapter, as_of).total_outstanding
    if revenue == 0:
        return 0.0
    return round((ar / revenue) * period_days, 1)


if __name__ == "__main__":
    import sys

    # Usage: python working_capital.py [YYYY-MM-DD]   (default: dataset clock)
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else DATASET_AS_OF
    a = OdooERPAdapter()

    ar = ar_aging(a, today)
    print(f"As of {today} - AR outstanding: EUR {ar.total_outstanding:,.2f} "
          f"({ar.open_documents} open, {ar.settled_documents} settled)")
    for bucket, amount in ar.buckets.items():
        print(f"  {bucket:<10} EUR {amount:>14,.2f}")

    ap = ap_aging(a, today)
    print(f"\nAP outstanding: EUR {ap.total_outstanding:,.2f} "
          f"({ap.open_documents} open, {ap.settled_documents} settled)")
    for bucket, amount in ap.buckets.items():
        print(f"  {bucket:<10} EUR {amount:>14,.2f}")

    print(f"\nWorking capital (AR - AP): EUR {ar.total_outstanding - ap.total_outstanding:,.2f}")
    print(f"DSO (trailing 90d): {dso(a, as_of=today)} days")
