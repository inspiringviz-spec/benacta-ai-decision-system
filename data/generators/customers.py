"""Pilot customer generator (Epic 02).

Creates a small batch of customers across the 5 segments defined in
docs/domain/business-domain.md, to validate the model and the Odoo
write path before scaling to the full ~500.
"""
from __future__ import annotations

import random

from common import get_or_create_category, get_country_ids, pick_geo, write_ground_truth
from odoo_client import OdooClient

SEGMENTS = {
    "Large F&B": {
        "count": 4,
        "words": ["Foods", "Dairy", "Beverages", "Nutrition", "AgriProcessing"],
        "comment": "Long sales cycles, strict specs, good payment behavior (60-day terms).",
    },
    "Pharma / Life Sciences": {
        "count": 3,
        "words": ["Pharma", "BioSciences", "Therapeutics", "Labs", "MedTech"],
        "comment": "Smaller volume, highest compliance bar, sticky relationships.",
    },
    "Energy & Utilities": {
        "count": 3,
        "words": ["Energy", "Power", "Utilities", "Grid", "Renewables"],
        "comment": "Large multi-year contracts, milestone-billed, slow 90-day payment.",
    },
    "Mid-market Industrial": {
        "count": 12,
        "words": ["Industries", "Manufacturing", "Metalworks", "Fabrication", "Systems"],
        "comment": "Higher volume of smaller projects, price-sensitive, variable payment behavior.",
    },
    "High-growth New Account": {
        "count": 3,
        "words": ["Dynamics", "Innovations", "Robotics", "Technologies", "Ventures"],
        "comment": "Fast-growing, attractive future pipeline, thin credit history.",
    },
}

SUFFIXES = ["Group", "Corp", "Ltd", "GmbH", "SA", "Inc", "Holdings"]


def main() -> None:
    rng = random.Random(2026)
    client = OdooClient()
    country_ids = get_country_ids(client)

    from common import PREFIXES

    category_ids = {seg: get_or_create_category(client, seg) for seg in SEGMENTS}

    to_create = []
    plan = []
    for segment, spec in SEGMENTS.items():
        for _ in range(spec["count"]):
            country_id, city = pick_geo(country_ids, rng)
            name = f"{rng.choice(PREFIXES)} {rng.choice(spec['words'])} {rng.choice(SUFFIXES)}"
            to_create.append(
                {
                    "name": name,
                    "is_company": True,
                    "customer_rank": 1,
                    "country_id": country_id,
                    "city": city,
                    "category_id": [(6, 0, [category_ids[segment]])],
                    "comment": f"[{segment}] {spec['comment']}",
                }
            )
            plan.append({"name": name, "segment": segment, "city": city})

    ids = client.create("res.partner", to_create)
    for record, partner_id in zip(plan, ids):
        record["odoo_id"] = partner_id

    write_ground_truth("customers_pilot.json", plan)
    print(f"Created {len(ids)} customers.")


if __name__ == "__main__":
    main()
