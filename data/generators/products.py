"""Pilot product generator (Epic 02).

Creates a small batch across the 6 product families / Business Units in
docs/domain/business-domain.md, with cost/price set to hit each family's
target gross margin.
"""
from __future__ import annotations

import random

from common import get_or_create_by_name, write_ground_truth
from odoo_client import OdooClient

FAMILIES = {
    "Process Vessels & Tanks": {
        "count": 4,
        "code": "PV",
        "names": ["Pressure Vessel", "Mixing Tank", "Storage Tank"],
        "cost_range": (50_000, 150_000),
        "target_margin": 0.25,
    },
    "Material Handling Systems": {
        "count": 3,
        "code": "MH",
        "names": ["Conveyor System", "Palletizer", "Sorting Unit"],
        "cost_range": (30_000, 90_000),
        "target_margin": 0.25,
    },
    "Automated Production Lines": {
        "count": 3,
        "code": "PL",
        "names": ["Assembly Line", "Packaging Line", "Robotic Cell"],
        "cost_range": (200_000, 600_000),
        "target_margin": 0.22,
    },
    "Industrial Thermal Systems": {
        "count": 3,
        "code": "TH",
        "names": ["Heat Exchanger", "Industrial HVAC Unit", "Cooling System"],
        "cost_range": (40_000, 120_000),
        "target_margin": 0.30,
    },
    "Control & Automation Systems": {
        "count": 4,
        "code": "CA",
        "names": ["PLC Control Panel", "SCADA System", "Sensor Array"],
        "cost_range": (10_000, 60_000),
        "target_margin": 0.40,
    },
    "Spare Parts & Maintenance Kits": {
        "count": 3,
        "code": "SP",
        "names": ["Maintenance Kit", "Spare Parts Bundle"],
        "cost_range": (500, 8_000),
        "target_margin": 0.45,
    },
}


def main() -> None:
    rng = random.Random(2028)
    client = OdooClient()
    category_ids = {fam: get_or_create_by_name(client, "product.category", fam) for fam in FAMILIES}

    to_create = []
    plan = []
    for family, spec in FAMILIES.items():
        for i in range(spec["count"]):
            base_name = rng.choice(spec["names"])
            ref = f"{spec['code']}-{100 + i}"
            name = f"{base_name} {ref}"
            cost = round(rng.uniform(*spec["cost_range"]), 2)
            price = round(cost / (1 - spec["target_margin"]), 2)
            to_create.append(
                {
                    "name": name,
                    "default_code": ref,
                    "categ_id": category_ids[family],
                    "standard_price": cost,
                    "list_price": price,
                    "sale_ok": True,
                    "purchase_ok": True,
                }
            )
            plan.append(
                {
                    "name": name,
                    "family": family,
                    "standard_price": cost,
                    "list_price": price,
                    "target_margin": spec["target_margin"],
                }
            )

    ids = client.create("product.template", to_create)
    for record, product_id in zip(plan, ids):
        record["odoo_id"] = product_id

    write_ground_truth("products_pilot.json", plan)
    print(f"Created {len(ids)} products.")


if __name__ == "__main__":
    main()
