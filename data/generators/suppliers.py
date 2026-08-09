"""Pilot supplier generator (Epic 02).

Deliberately concentrates the 'Certified Components' category on very few
suppliers to seed the single-source concentration-risk storyline
(business-domain.md, storyline 2).
"""
from __future__ import annotations

import random

from common import PREFIXES, get_or_create_category, get_country_ids, pick_geo, write_ground_truth
from odoo_client import OdooClient

CATEGORIES = {
    "Raw Materials": {
        "count": 4,
        "words": ["SteelWorks", "Alloys", "Metals", "Materials", "Foundry"],
        "comment": "Commodity price exposure — feeds the steel/alloy inflation storyline.",
        "single_source_risk": False,
    },
    "Electronic Components": {
        "count": 4,
        "words": ["Electronics", "Components", "Circuits", "Semiconductors"],
        "comment": "Lead-time and geopolitical exposure.",
        "single_source_risk": False,
    },
    "Subcontracted Labor": {
        "count": 3,
        "words": ["Fabrication Services", "Installation Partners", "Field Services"],
        "comment": "Regional capacity constraint exposure.",
        "single_source_risk": False,
    },
    "Logistics": {
        "count": 2,
        "words": ["Logistics", "Freight", "Shipping"],
        "comment": "Expedited-shipping cost spike exposure.",
        "single_source_risk": False,
    },
    "Certified Components": {
        "count": 2,
        "words": ["Precision Components", "Certified Systems", "CompliancePart"],
        "comment": "Intentionally concentrated: pressure-rated / compliance-critical parts, few qualified sources.",
        "single_source_risk": True,
    },
}

SUFFIXES = ["Group", "Corp", "Ltd", "GmbH", "SA", "Inc", "Industries"]


def main() -> None:
    rng = random.Random(2027)
    client = OdooClient()
    country_ids = get_country_ids(client)
    category_ids = {cat: get_or_create_category(client, cat) for cat in CATEGORIES}

    to_create = []
    plan = []
    for category, spec in CATEGORIES.items():
        for _ in range(spec["count"]):
            country_id, city = pick_geo(country_ids, rng)
            name = f"{rng.choice(PREFIXES)} {rng.choice(spec['words'])} {rng.choice(SUFFIXES)}"
            to_create.append(
                {
                    "name": name,
                    "is_company": True,
                    "supplier_rank": 1,
                    "country_id": country_id,
                    "city": city,
                    "category_id": [(6, 0, [category_ids[category]])],
                    "comment": f"[{category}] {spec['comment']}",
                }
            )
            plan.append(
                {
                    "name": name,
                    "category": category,
                    "city": city,
                    "single_source_risk": spec["single_source_risk"],
                }
            )

    ids = client.create("res.partner", to_create)
    for record, partner_id in zip(plan, ids):
        record["odoo_id"] = partner_id

    write_ground_truth("suppliers_pilot.json", plan)
    print(f"Created {len(ids)} suppliers.")


if __name__ == "__main__":
    main()
