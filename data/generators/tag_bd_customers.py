"""Tag the customers of the BD/SO batch with a business segment.

The 116 invoices with origin BD/SO/* (created 2026-09-17 by a generator
outside this repo) belong to 24 customers that carry no partner category,
so segment-driven logic (payment behaviour, P&L by segment, concentration)
treated them all as the default Mid-market Industrial. This assigns each one
an explicit segment from docs/domain/business-domain.md, chosen from the
company name and shaped to the domain's target mix (15% large F&B,
10% pharma, 10% energy & utilities, 50% mid-market, 15% high-growth).

Idempotent: a customer that already carries a segment tag is left alone.

    python tag_bd_customers.py --dry-run
    python tag_bd_customers.py
"""
from __future__ import annotations

import argparse

from common import get_or_create_category, write_ground_truth
from odoo_client import OdooClient

SEGMENTS = {
    "Large F&B": ["Fontaine Agro", "Ivry Food Lines", "Dorval Packaging"],
    "Pharma / Life Sciences": ["Castell Pharma Plants", "Keraval Chemicals"],
    "Energy & Utilities": ["Brevan Energy", "Estrel Water Services", "Rocroi Mining"],
    "High-growth New Account": ["Ubaye Trade Partners", "Vannes Trading", "Tessier Distribution"],
    "Mid-market Industrial": [
        "Alcor Process Systems", "Garnier Metalworks", "Halden Logistics", "Jura Precision",
        "Lumen Glassworks", "Morvan Paper", "Nerac Textiles", "Orsay Hydraulics",
        "Pelican Marine Yards", "Quimper Thermal", "Rennes Hydraulics", "Sarlat Cement",
        "Saumur Cranes",
    ],
}
SEGMENT_BY_NAME = {name: seg for seg, names in SEGMENTS.items() for name in names}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    client = OdooClient()

    partners = client.search_read(
        "res.partner", [["customer_rank", ">", 0], ["name", "in", list(SEGMENT_BY_NAME)]],
        ["name", "category_id"],
    )
    found = {p["name"] for p in partners}
    missing = sorted(set(SEGMENT_BY_NAME) - found)
    if missing:
        print(f"Not found in Odoo (skipped): {missing}")

    records = []
    for p in sorted(partners, key=lambda p: p["name"]):
        segment = SEGMENT_BY_NAME[p["name"]]
        status = "already tagged" if p["category_id"] else ("would tag" if args.dry_run else "tag")
        print(f"  {status:<15} {p['name']:<26} -> {segment}")
        if not p["category_id"] and not args.dry_run:
            client.write("res.partner", [p["id"]], {"category_id": [(4, get_or_create_category(client, segment))]})
        records.append({"name": p["name"], "segment": segment, "odoo_id": p["id"], "source": "BD/SO batch"})

    if args.dry_run:
        print("Dry run: nothing written to Odoo.")
        return
    write_ground_truth("customers_bd.json", records)


if __name__ == "__main__":
    main()
