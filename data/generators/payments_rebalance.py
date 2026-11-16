"""Payments rebalance (Epic 02 follow-up, ADR-0004): give every unpaid
customer invoice / vendor bill a settlement outcome consistent with the
segment payment behaviour in docs/domain/business-domain.md.

Why: the pilot generators only pay the orders they themselves flag as
"paid", and a second batch of 116 customer invoices (origin BD/SO/*, created
2026-09-17 outside this repo) carries no payment at all. Result: almost every
receivable looked open and DSO was meaningless.

What it does, per posted document without any matched payment and dated on
or before --as-of:
  * picks a payment delay from the partner's segment (partner category tag;
    untagged customers are treated as Mid-market Industrial),
  * applies the storyline exceptions (customer distress: recent invoices stay
    overdue; a share of mid-market / high-growth accounts pay late or partially;
    documents seeded by aging_storylines.py, ref AGING/*, are never touched),
  * registers the payment through `account.payment.register` only if the
    resulting payment date is <= --as-of. Documents not yet due stay open and
    feed the 0-30 / 31-60 aging buckets.

Idempotent: documents that already carry a matched payment are skipped and
each document's outcome is drawn from its own seeded stream, so re-running
never pays anything twice and never changes an earlier decision. `--dry-run` prints the plan only.

    python payments_rebalance.py --dry-run
    python payments_rebalance.py [--as-of 2026-08-09] [--seed 4001]
"""
from __future__ import annotations

import argparse
import random
from collections import Counter
from datetime import date, timedelta

import json

from common import GROUND_TRUTH_DIR, TODAY, write_ground_truth
from aging_storylines import AGING_REF_PREFIX
from odoo_client import OdooClient

BANK_JOURNAL_NAME = "Bank"
DEFAULT_SEGMENT = "Mid-market Industrial"

# (delay_min, delay_max, late_share, late_extra_days, partial_share)
# business-domain.md "Payment behavior" column, made quantitative.
CUSTOMER_RULES = {
    "Large F&B": (45, 70, 0.00, 0, 0.00),               # on time, 60-day terms
    "Pharma / Life Sciences": (20, 45, 0.00, 0, 0.00),  # very good
    "Energy & Utilities": (75, 110, 0.00, 0, 0.00),     # slow, 90-day terms, no credit risk
    "Mid-market Industrial": (30, 90, 0.15, 60, 0.05),  # variable, some late payers
    "High-growth New Account": (40, 80, 0.10, 45, 0.05),  # unproven
}
SUPPLIER_DELAY = (20, 55)

# Storyline 4 (customer financial distress) - Project Ferrum's customer.
DISTRESS_CUSTOMER = "Crest Systems GmbH"
DISTRESS_WINDOW_DAYS = 120        # anything newer than this stays unpaid
DISTRESS_OLD_DELAY = (80, 120)    # older invoices were paid, but late


def segment_of(partner_id: int, tags: dict[int, list[str]]) -> str:
    for name in tags.get(partner_id, []):
        if name in CUSTOMER_RULES:
            return name
    return DEFAULT_SEGMENT


def plan_document(doc: dict, segment: str, seed: int, as_of: date) -> dict:
    # One RNG stream per document, keyed on its id: the outcome of a document
    # never depends on which other documents are still unpaid, so re-running
    # after a partial run (or after new documents appear) reproduces the same
    # plan for every document already seen.
    rng = random.Random(f"{seed}:{doc['id']}")
    inv_date = date.fromisoformat(doc["invoice_date"])
    rec = {
        "move_id": doc["id"], "name": doc["name"], "move_type": doc["move_type"],
        "partner": doc["partner_id"][1], "segment": segment,
        "invoice_date": doc["invoice_date"], "amount_total": doc["amount_total"],
        "outcome": None, "payment_date": None, "amount_paid": 0.0,
    }
    if doc["move_type"] == "in_invoice":
        delay = rng.randint(*SUPPLIER_DELAY)
        outcome, amount = "paid", doc["amount_total"]
    elif doc["partner_id"][1] == DISTRESS_CUSTOMER:
        if (as_of - inv_date).days <= DISTRESS_WINDOW_DAYS:
            rec["outcome"] = "distress_unpaid"
            return rec
        delay = rng.randint(*DISTRESS_OLD_DELAY)
        outcome, amount = "paid_late", doc["amount_total"]
    else:
        lo, hi, late_share, late_extra, partial_share = CUSTOMER_RULES[segment]
        delay = rng.randint(lo, hi)
        roll = rng.random()
        if roll < partial_share:
            outcome = "partial"
            amount = round(doc["amount_total"] * rng.uniform(0.5, 0.8), 2)
        elif roll < partial_share + late_share:
            outcome, amount = "paid_late", doc["amount_total"]
            delay += rng.randint(late_extra // 2, late_extra)
        else:
            outcome, amount = "paid", doc["amount_total"]
    pay_date = inv_date + timedelta(days=delay)
    if pay_date > as_of:
        rec["outcome"] = "not_yet_due"
        rec["payment_date"] = pay_date.isoformat()
        return rec
    rec.update(outcome=outcome, payment_date=pay_date.isoformat(), amount_paid=amount)
    return rec


def register_payment(client: OdooClient, bank_journal: int, move_id: int, pay_date: str, amount: float) -> int:
    wizard_id = client.models.execute_kw(
        client.db, client.uid, client.api_key,
        "account.payment.register", "create",
        [{"journal_id": bank_journal, "payment_date": pay_date, "amount": amount}],
        {"context": {"active_model": "account.move", "active_ids": [move_id]}},
    )
    # action_create_payments returns an action dict (or None, which XML-RPC
    # cannot marshal): read the payment back from the invoice instead.
    try:
        client.models.execute_kw(
            client.db, client.uid, client.api_key,
            "account.payment.register", "action_create_payments", [[wizard_id]],
        )
    except Exception as exc:  # noqa: BLE001
        if "cannot marshal None" not in str(exc):
            raise
    matched = client.search_read("account.move", [["id", "=", move_id]], ["matched_payment_ids"])[0]
    return matched["matched_payment_ids"][-1] if matched["matched_payment_ids"] else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of", type=date.fromisoformat, default=TODAY)
    ap.add_argument("--seed", type=int, default=4001)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    client = OdooClient()

    tags: dict[int, list[str]] = {}
    for c in client.search_read("res.partner.category", [], ["name", "partner_ids"]):
        for pid in c["partner_ids"]:
            tags.setdefault(pid, []).append(c["name"])

    docs = client.search_read(
        "account.move",
        [["move_type", "in", ["out_invoice", "in_invoice"]], ["state", "=", "posted"],
         ["matched_payment_ids", "=", False], ["invoice_date", "<=", args.as_of.isoformat()]],
        ["name", "move_type", "partner_id", "invoice_date", "amount_total", "ref"],
    )
    # Documents seeded by aging_storylines.py are open on purpose.
    docs = [d for d in docs if not (d["ref"] or "").startswith(AGING_REF_PREFIX)]
    docs.sort(key=lambda d: (d["invoice_date"], d["id"]))
    plan = [plan_document(d, segment_of(d["partner_id"][0], tags), args.seed, args.as_of) for d in docs]

    by_outcome = Counter(p["outcome"] for p in plan)
    to_pay = [p for p in plan if p["amount_paid"] > 0]
    print(f"As of {args.as_of}: {len(docs)} unpaid documents -> {dict(by_outcome)}")
    print(f"Payments to register: {len(to_pay)} for EUR {sum(p['amount_paid'] for p in to_pay):,.2f}")
    for seg, n in sorted(Counter(p["segment"] for p in plan if p["move_type"] == "out_invoice").items()):
        paid = sum(1 for p in to_pay if p["segment"] == seg and p["move_type"] == "out_invoice")
        print(f"  {seg:<26} {paid:>3}/{n:<3} customer invoices paid by as-of")
    if args.dry_run:
        print("Dry run: nothing written to Odoo.")
        return

    bank_journal = client.search("account.journal", [["name", "=", BANK_JOURNAL_NAME]])[0]
    for i, p in enumerate(to_pay, 1):
        p["payment_id"] = register_payment(client, bank_journal, p["move_id"], p["payment_date"], p["amount_paid"])
        if i % 20 == 0 or i == len(to_pay):
            print(f"  registered {i}/{len(to_pay)}")
    # Merge with earlier runs so the ground truth keeps every registered payment.
    gt_name = f"payments_rebalance_{args.as_of.isoformat()}.json"
    gt_path = GROUND_TRUTH_DIR / gt_name
    merged = {r["move_id"]: r for r in (json.loads(gt_path.read_text()) if gt_path.exists() else [])}
    for r in plan:
        if r.get("payment_id") or r["move_id"] not in merged:
            merged[r["move_id"]] = r
    write_ground_truth(gt_name, sorted(merged.values(), key=lambda r: (r["invoice_date"], r["move_id"])))


if __name__ == "__main__":
    main()
