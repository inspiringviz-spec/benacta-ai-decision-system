"""Pilot sales cycle generator (Epic 02): quotations -> orders -> invoices
-> credit notes (avoirs) -> payments, spread across a 36-month window,
with payment delay driven by customer segment (business-domain.md).
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from common import GROUND_TRUTH_DIR, write_ground_truth
from odoo_client import OdooClient

TODAY = date(2026, 8, 9)
WINDOW_DAYS = 36 * 30

PAYMENT_DELAY_BY_SEGMENT = {
    "Large F&B": (15, 45),
    "Pharma / Life Sciences": (10, 40),
    "Energy & Utilities": (60, 100),
    "Mid-market Industrial": (20, 90),
    "High-growth New Account": (30, 75),
}

N_ORDERS = 30
N_DRAFT_ONLY = 5
N_UNPAID = 3
N_WITH_CREDIT_NOTE = 4

BANK_JOURNAL_NAME = "Bank"


def load(name: str) -> list[dict]:
    return json.loads((GROUND_TRUTH_DIR / name).read_text())


def random_date(rng: random.Random) -> date:
    return TODAY - timedelta(days=rng.randint(0, WINDOW_DAYS))


def main() -> None:
    rng = random.Random(3001)
    client = OdooClient()
    customers = load("customers_pilot.json")
    products = load("products_pilot.json")

    bank_journal = client.search("account.journal", [["name", "=", BANK_JOURNAL_NAME]])[0]

    # index status assignment
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
        customer = rng.choice(customers)
        n_lines = rng.randint(1, 3)
        lines = rng.sample(products, k=min(n_lines, len(products)))
        order_date = random_date(rng)
        state = order_states[i]

        order_lines_cmd = []
        line_summaries = []
        for p in lines:
            qty = rng.randint(1, 5)
            price = round(p["list_price"] * rng.uniform(0.92, 1.02), 2)
            order_lines_cmd.append(
                (0, 0, {"product_id": p["odoo_id"], "product_uom_qty": qty, "price_unit": price})
            )
            line_summaries.append({"product": p["name"], "qty": qty, "price_unit": price})

        so_id = client.create(
            "sale.order",
            [
                {
                    "partner_id": customer["odoo_id"],
                    "date_order": order_date.isoformat(),
                    "order_line": order_lines_cmd,
                }
            ],
        )[0]

        record = {
            "sale_order_id": so_id,
            "customer": customer["name"],
            "segment": customer["segment"],
            "order_date": order_date.isoformat(),
            "state": state,
            "lines": line_summaries,
        }

        if state != "draft":
            client.execute("sale.order", "action_confirm", [so_id])

            invoice_date = order_date + timedelta(days=rng.randint(1, 5))
            inv_id = client.create(
                "account.move",
                [
                    {
                        "move_type": "out_invoice",
                        "partner_id": customer["odoo_id"],
                        "invoice_date": invoice_date.isoformat(),
                        "invoice_origin": f"SO{so_id}",
                        "invoice_line_ids": [
                            (0, 0, {"product_id": p["odoo_id"], "quantity": ls["qty"], "price_unit": ls["price_unit"]})
                            for p, ls in zip(lines, line_summaries)
                        ],
                    }
                ],
            )[0]
            client.execute("account.move", "action_post", [inv_id])
            record["invoice_id"] = inv_id
            record["invoice_date"] = invoice_date.isoformat()

            if i in credit_note_indices:
                cn_line = rng.choice(lines)
                cn_qty = 1
                cn_price = next(ls["price_unit"] for p, ls in zip(lines, line_summaries) if p is cn_line)
                cn_date = invoice_date + timedelta(days=rng.randint(5, 20))
                cn_id = client.create(
                    "account.move",
                    [
                        {
                            "move_type": "out_refund",
                            "partner_id": customer["odoo_id"],
                            "invoice_date": cn_date.isoformat(),
                            "ref": f"Credit note for INV origin SO{so_id}",
                            "invoice_line_ids": [
                                (0, 0, {"product_id": cn_line["odoo_id"], "quantity": cn_qty, "price_unit": cn_price})
                            ],
                        }
                    ],
                )[0]
                client.execute("account.move", "action_post", [cn_id])
                record["credit_note_id"] = cn_id

            if state == "paid":
                delay_range = PAYMENT_DELAY_BY_SEGMENT[customer["segment"]]
                payment_date = invoice_date + timedelta(days=rng.randint(*delay_range))
                wizard_id = client.models.execute_kw(
                    client.db, client.uid, client.api_key,
                    "account.payment.register", "create",
                    [{"journal_id": bank_journal, "payment_date": payment_date.isoformat()}],
                    {"context": {"active_model": "account.move", "active_ids": [inv_id]}},
                )
                client.execute("account.payment.register", "action_create_payments", [wizard_id])
                record["payment_date"] = payment_date.isoformat()

        plan.append(record)

    write_ground_truth("sales_cycle_pilot.json", plan)
    n_invoiced = sum(1 for r in plan if "invoice_id" in r)
    n_credit = sum(1 for r in plan if "credit_note_id" in r)
    n_paid = sum(1 for r in plan if "payment_date" in r)
    print(f"Orders: {len(plan)} | Invoiced: {n_invoiced} | Credit notes: {n_credit} | Paid: {n_paid}")


if __name__ == "__main__":
    main()
