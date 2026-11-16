"""Aging storylines (Epic 02 follow-up): seed the few open documents that
the working-capital storylines need and that the pilot cycle generators do
not produce.

1. Storyline 4 - customer financial distress (Project Ferrum, Crest Systems
   GmbH). The project narrative says: "Customer's final milestone payment is
   45 days overdue; customer has also delayed payment on two unrelated
   invoices this quarter." The pilot paid every Crest invoice, so nothing in
   AR aging backed that sentence. This seeds exactly those three invoices,
   unpaid, 30-day terms.
2. Open payables. Every vendor bill of the pilot is now settled, so AP aging
   was empty. This seeds four bills still inside their terms (0-60 days) and
   one disputed bill from the single-source certified-components supplier
   (storyline 2 - supplier disruption), 95 days old and deliberately unpaid.

Every document carries a `ref` starting with AGING_REF_PREFIX. That marker
is what makes the script idempotent (existing refs are skipped) and what
tells payments_rebalance.py to leave these documents alone.

    python aging_storylines.py --dry-run
    python aging_storylines.py
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta

from common import GROUND_TRUTH_DIR, TODAY, write_ground_truth
from odoo_client import OdooClient

AGING_REF_PREFIX = "AGING/"
TERMS_DAYS = 30


def load(name: str) -> list[dict]:
    return json.loads((GROUND_TRUTH_DIR / name).read_text())


def build_specs() -> list[dict]:
    customers = {c["name"]: c for c in load("customers_pilot.json")}
    suppliers = {s["name"]: s for s in load("suppliers_pilot.json")}
    products = {p["name"]: p for p in load("products_pilot.json")}
    ferrum = next(p for p in load("projects_pilot.json") if p["storyline_key"] == "customer_distress")
    crest = customers[ferrum["customer"]]

    def line(product: str, qty: int, price: float | None = None, cost: bool = False) -> dict:
        p = products[product]
        unit = price if price is not None else (p["standard_price"] if cost else p["list_price"])
        return {"product_id": p["odoo_id"], "quantity": qty, "price_unit": round(unit, 2)}

    m4_amount = round(ferrum["contract_value"] * 0.25, 2)  # final milestone = 25% of contract
    specs = [
        # --- Storyline 4: Crest Systems GmbH, all unpaid --------------------
        {
            "ref": f"{AGING_REF_PREFIX}FERRUM-M4", "move_type": "out_invoice",
            "partner_id": crest["odoo_id"], "partner": crest["name"],
            "days_ago": TERMS_DAYS + 45,  # 45 days overdue on 30-day terms
            "origin": f"{ferrum['name']} - M4 final milestone",
            "lines": [line("Conveyor System MH-102", 1, price=m4_amount)],
            "storyline": "customer_distress",
        },
        {
            "ref": f"{AGING_REF_PREFIX}CREST-SPARES", "move_type": "out_invoice",
            "partner_id": crest["odoo_id"], "partner": crest["name"],
            "days_ago": 62, "origin": "Spare parts order (unrelated to Ferrum)",
            "lines": [line("Spare Parts Bundle SP-100", 3)],
            "storyline": "customer_distress",
        },
        {
            "ref": f"{AGING_REF_PREFIX}CREST-SENSORS", "move_type": "out_invoice",
            "partner_id": crest["odoo_id"], "partner": crest["name"],
            "days_ago": 48, "origin": "Sensor retrofit (unrelated to Ferrum)",
            "lines": [line("Sensor Array CA-100", 2)],
            "storyline": "customer_distress",
        },
        # --- Storyline 2: disputed single-source bill, 95 days, unpaid ------
        {
            "ref": f"{AGING_REF_PREFIX}AP-DISPUTE", "move_type": "in_invoice",
            "partner_id": suppliers["Crest CompliancePart Group"]["odoo_id"],
            "partner": "Crest CompliancePart Group",
            "days_ago": 95, "origin": "Certified components batch - held, delivery dispute",
            "lines": [line("Sensor Array CA-102", 1, cost=True)],
            "storyline": "supplier_disruption",
        },
    ]
    # --- Open payables inside terms (0-60 days) ----------------------------
    for i, (supplier, product, qty, days_ago) in enumerate([
        ("Meridian SteelWorks Inc", "Mixing Tank PV-100", 1, 8),
        ("Delta Electronics Ltd", "SCADA System CA-101", 1, 21),
        ("Anchor Fabrication Services Ltd", "Heat Exchanger TH-100", 2, 38),
        ("Summit Logistics Corp", "Spare Parts Bundle SP-100", 3, 52),
    ], start=1):
        specs.append({
            "ref": f"{AGING_REF_PREFIX}AP-OPEN-{i}", "move_type": "in_invoice",
            "partner_id": suppliers[supplier]["odoo_id"], "partner": supplier,
            "days_ago": days_ago, "origin": "Regular supply, within terms",
            "lines": [line(product, qty, cost=True)],
            "storyline": None,
        })
    return specs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    client = OdooClient()

    existing = {
        r["ref"]: r["id"]
        for r in client.search_read("account.move", [["ref", "=like", f"{AGING_REF_PREFIX}%"]], ["ref"])
    }
    specs = build_specs()
    records = []
    for s in specs:
        inv_date = TODAY - timedelta(days=s["days_ago"])
        rec = {
            "ref": s["ref"], "move_type": s["move_type"], "partner": s["partner"],
            "invoice_date": inv_date.isoformat(),
            "invoice_date_due": (inv_date + timedelta(days=TERMS_DAYS)).isoformat(),
            "days_overdue_at_clock": max(s["days_ago"] - TERMS_DAYS, 0),
            "amount_untaxed": round(sum(l["quantity"] * l["price_unit"] for l in s["lines"]), 2),
            "storyline": s["storyline"], "odoo_id": existing.get(s["ref"]),
        }
        status = "exists" if rec["odoo_id"] else ("would create" if args.dry_run else "create")
        print(f"  {status:<12} {s['ref']:<22} {s['move_type']:<11} {s['partner']:<34} "
              f"{rec['invoice_date']}  EUR {rec['amount_untaxed']:>12,.2f}")
        if rec["odoo_id"] or args.dry_run:
            records.append(rec)
            continue
        move_id = client.create("account.move", [{
            "move_type": s["move_type"], "partner_id": s["partner_id"], "ref": s["ref"],
            "invoice_date": inv_date.isoformat(),
            "invoice_date_due": rec["invoice_date_due"],
            "invoice_origin": s["origin"],
            "invoice_line_ids": [(0, 0, l) for l in s["lines"]],
        }])[0]
        client.execute("account.move", "action_post", [move_id])
        rec["odoo_id"] = move_id
        records.append(rec)

    if args.dry_run:
        print("Dry run: nothing written to Odoo.")
        return
    write_ground_truth("aging_storylines.json", records)


if __name__ == "__main__":
    main()
