"""Working capital / aging (Epic 04) — settlement signal per ADR-0004.

Offline tests exercise the pure logic with fake moves. The integration
tests at the bottom need the local .env and hit the live Odoo instance.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "analytics"))
sys.path.insert(0, str(ROOT / "integrations" / "odoo"))

from adapter import Move, OdooERPAdapter  # noqa: E402
from working_capital import _aging, ar_aging, ap_aging, dso  # noqa: E402

AS_OF = date(2026, 11, 16)


def _move(id_, total, residual, invoice_date, paid=0.0):
    return Move(
        id=id_, move_type="out_invoice", partner_id=1, partner_name="X",
        invoice_date=invoice_date, amount_total=total, amount_residual=total,
        payment_state="in_payment" if paid else "not_paid",
        amount_paid=paid, effective_residual=residual,
    )


# ---- offline: adapter settlement rule ---------------------------------

def test_settlement_uses_matched_payments_when_odoo_has_no_journal_entry():
    row = {"amount_total": 1000.0, "amount_residual": 1000.0, "matched_payment_ids": [7]}
    payments = {7: {"amount": 1000.0, "date": "2026-06-03", "state": "paid"}}
    paid, residual, last = OdooERPAdapter._settlement(row, payments)
    assert (paid, residual, last) == (1000.0, 0.0, "2026-06-03")


def test_settlement_partial_payment_leaves_remainder_open():
    row = {"amount_total": 1000.0, "amount_residual": 1000.0, "matched_payment_ids": [7, 8]}
    payments = {7: {"amount": 300.0, "date": "2026-05-01", "state": "paid"},
                8: {"amount": 200.0, "date": "2026-06-01", "state": "in_process"}}
    paid, residual, last = OdooERPAdapter._settlement(row, payments)
    assert (paid, residual, last) == (500.0, 500.0, "2026-06-01")


def test_settlement_ignores_payments_not_in_settling_state():
    # _get_matched_payments filters drafts/cancelled out, so they are absent from `payments`
    row = {"amount_total": 1000.0, "amount_residual": 1000.0, "matched_payment_ids": [9]}
    paid, residual, last = OdooERPAdapter._settlement(row, {})
    assert (paid, residual, last) == (0.0, 1000.0, None)


def test_settlement_trusts_accounting_residual_when_odoo_reconciled():
    # Outstanding account configured: Odoo already reduced amount_residual.
    # The same payment must not be counted twice.
    row = {"amount_total": 1000.0, "amount_residual": 250.0, "matched_payment_ids": [7]}
    payments = {7: {"amount": 750.0, "date": "2026-06-03", "state": "paid"}}
    paid, residual, _ = OdooERPAdapter._settlement(row, payments)
    assert (paid, residual) == (750.0, 250.0)


def test_settlement_caps_overpayment_at_invoice_total():
    row = {"amount_total": 1000.0, "amount_residual": 1000.0, "matched_payment_ids": [7]}
    payments = {7: {"amount": 1200.0, "date": "2026-06-03", "state": "paid"}}
    paid, residual, _ = OdooERPAdapter._settlement(row, payments)
    assert (paid, residual) == (1000.0, 0.0)


# ---- offline: aging --------------------------------------------------

def test_aging_excludes_settled_documents_whatever_payment_state_says():
    moves = [
        _move(1, 1000, 0.0, "2026-10-01", paid=1000),   # in_payment, fully covered
        _move(2, 500, 500.0, "2026-10-20"),             # 27 days
        _move(3, 800, 800.0, "2026-09-01"),             # 76 days
        _move(4, 300, 300.0, "2026-01-15"),             # 305 days
    ]
    r = _aging(moves, AS_OF)
    assert r.total_outstanding == 1600.0
    assert r.buckets == {"0-30": 500.0, "31-60": 0.0, "61-90": 800.0, "91+": 300.0}
    assert r.open_documents == 3 and r.settled_documents == 1
    assert r.document_ids == [2, 3, 4]


def test_aging_buckets_sum_to_total_and_future_dated_docs_are_ignored():
    moves = [_move(1, 100, 100.0, "2026-12-01"), _move(2, 100, 40.0, "2026-11-16")]
    r = _aging(moves, AS_OF)
    assert r.total_outstanding == 40.0
    assert abs(sum(r.buckets.values()) - r.total_outstanding) < 0.01


def test_aging_skips_unsettled_docs_without_invoice_date_but_counts_them():
    r = _aging([_move(1, 100, 100.0, None)], AS_OF)
    assert r.total_outstanding == 0.0 and r.excluded_unsettled_no_date == 1


# ---- integration (live Odoo) -----------------------------------------

@pytest.fixture(scope="module")
def adapter():
    try:
        return OdooERPAdapter()
    except (FileNotFoundError, KeyError, RuntimeError) as exc:  # no .env / no network
        pytest.skip(f"live Odoo not available: {exc}")


def test_live_in_payment_invoices_are_settled_in_the_adapter(adapter):
    invoices = adapter.get_customer_invoices()
    in_payment = [m for m in invoices if m.payment_state == "in_payment"]
    assert in_payment, "dataset should contain in_payment invoices"
    # Odoo's accounting residual is still the full amount (no outstanding account)...
    assert all(m.amount_residual == m.amount_total for m in in_payment)
    # ...but every one of them is covered by matched payments.
    assert all(m.is_settled and m.matched_payment_ids for m in in_payment)


def test_live_ar_outstanding_is_below_total_invoiced(adapter):
    invoices = adapter.get_customer_invoices()
    r = ar_aging(adapter, AS_OF)
    assert 0 < r.total_outstanding < sum(m.amount_total for m in invoices)
    assert r.settled_documents > 0
    assert abs(sum(r.buckets.values()) - r.total_outstanding) < 0.01


def test_live_ap_and_dso_are_computable(adapter):
    assert ap_aging(adapter, AS_OF).total_outstanding >= 0
    assert dso(adapter, as_of=AS_OF) >= 0
