"""Pilot purchase cycle generator (Epic 02): purchase orders -> vendor
bills -> vendor credit notes (avoirs) -> payments.

Steel/alloy suppliers get a mild price escalation over the 36-month
window baked into price_unit, seeding the inflation storyline (storyline 1,
Project Atlas) at the transaction level, not just in the project narrative.
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta

from common import GROUND_TRUTH_DIR, write_ground_truth
from odoo_client import OdooClient

TODAY = date(2026, 8, 9)
WINDOW_DAYS = 36 * 30

N_ORDERS = 20
N_DRAFT_ONLY = 3
N_UNPAID = 2
N_WITH_CREDIT_NOTE = 3

BANK_JOURNAL_NAME = "Bank"


def load(name: str) -> list[dict]:
    return json.loads((GROUND_TRUTH_DIR / name).read_text())


def random_date(rng: random.Random) -> date:
    return TODAY - timedelta(days=rng.randint(0, WINDOW_DAYS))


def inflation_factor(order_date: date, category: str) -> float:
    if category != "Raw Materials":
        return 1.0
    # linear ~18% increase in raw material cost from 36 months ago to today
    age_days = (TODAY - order_date).days
    progress = 1 - (age_days / WINDOW_DAYS)  # 0 = oldest, 1 = most recent
    return 1.0 + 0.18 * progress


def main() -> None:
    rng = random.Random(4001)
    client = OdooClient()
    suppliers = load("suppliers_pilot.json")
    products = load("products_pilot.json")
    bank_journal = client.search("account.journal", [["name", "=", BANK_JOURNAL_NAME]])[0]

    order_states = (
        ["draft"] * N_DRAFT_ONLY
        + ["unpaid"] * N_UNPAID
        + ["paid"] * (N_ORDERS - N_DRAFT_ONLY - N_UNPAID)
    )
    rng.shuffle(order_states)
    credit_note_indices = set(
        rng.sample(
            [i for i, s in enumerate(order_states) if s == "paid"],
            k=min(N_WITH_CREDIT_NOTE, order_states.count("paid")),
        )
    )

    plan = []
    for i in range(N_ORDERS):
        supplier = rng.choice(suppliers)
        n_lines = rng.randint(1, 2)
        lines = rng.sample(products, k=min(n_lines, len(products)))
        order_date = random_date(rng)
        state = order_states[i]
        factor = inflation_factor(order_date, supplier["category"])

        order_lines_cmd = []
        line_summaries = []
        for p in lines:
            qty = rng.randint(1, 4)
            price = round(p["standard_price"] * factor * rng.uniform(0.97, 1.03), 2)
            order_lines_cmd.append(
                (0, 0, {"product_id": p["odoo_id"], "product_qty": qty, "price_unit": price})
            )
            line_summaries.append({"product": p["name"], "qty": qty, "price_unit": price})

        po_id = client.create(
            "purchase.order",
            [{"partner_id": supplier["odoo_id"], "date_order": order_date.isoformat(), "order_line": order_lines_cmd}],
        )[0]

        record = {
            "purchase_order_id": po_id,
            "supplier": supplier["name"],
            "category": supplier["category"],
            "order_date": order_date.isoformat(),
            "state": state,
            "inflation_factor": round(factor, 3),
            "lines": line_summaries,
        }

        if state != "draft":
            client.execute("purchase.order", "button_confirm", [po_id])

            bill_date = order_date + timedelta(days=rng.randint(1, 7))
            bill_id = client.create(
                "account.move",
                [
                    {
                        "move_type": "in_invoice",
                        "partner_id": supplier["odoo_id"],
                        "invoice_date": bill_date.isoformat(),
                        "invoice_origin": f"PO{po_id}",
                        "invoice_line_ids": [
                            (0, 0, {"product_id": p["odoo_id"], "quantity": ls["qty"], "price_unit": ls["price_unit"]})
                            for p, ls in zip(lines, line_summaries)
                        ],
                    }
                ],
            )[0]
            client.execute("account.move", "action_post", [bill_id])
            record["bill_id"] = bill_id
            record["bill_date"] = bill_date.isoformat()

            if i in credit_note_indices:
                cn_line = rng.choice(lines)
                cn_price = next(ls["price_unit"] for p, ls in zip(lines, line_summaries) if p is cn_line)
                cn_date = bill_date + timedelta(days=rng.randint(5, 15))
                cn_id = client.create(
                    "account.move",
                    [
                        {
                            "move_type": "in_refund",
                            "partner_id": supplier["odoo_id"],
                            "invoice_date": cn_date.isoformat(),
                            "ref": f"Vendor credit for PO{po_id}",
                            "invoice_line_ids": [
                                (0, 0, {"product_id": cn_line["odoo_id"], "quantity": 1, "price_unit": cn_price})
                            ],
                        }
                    ],
                )[0]
                client.execute("account.move", "action_post", [cn_id])
                record["credit_note_id"] = cn_id

            if state == "paid":
                payment_date = bill_date + timedelta(days=rng.randint(15, 60))
                wizard_id = client.models.execute_kw(
                    client.db, client.uid, client.api_key,
                    "account.payment.register", "create",
                    [{"journal_id": bank_journal, "payment_date": payment_date.isoformat()}],
                    {"context": {"active_model": "account.move", "active_ids": [bill_id]}},
                )
                client.execute("account.payment.register", "action_create_payments", [wizard_id])
                record["payment_date"] = payment_date.isoformat()

        plan.append(record)

    write_ground_truth("purchase_cycle_pilot.json", plan)
    n_billed = sum(1 for r in plan if "bill_id" in r)
    n_credit = sum(1 for r in plan if "credit_note_id" in r)
    n_paid = sum(1 for r in plan if "payment_date" in r)
    print(f"Orders: {len(plan)} | Billed: {n_billed} | Credit notes: {n_credit} | Paid: {n_paid}")


if __name__ == "__main__":
    main()
