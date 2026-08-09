"""Pilot employee generator — Project Managers / Lead Engineers.

These are hr.employee records only (no res.users login), so they don't
consume paid seats on the 1-user subscription (ADR-0002).
"""
from __future__ import annotations

import random

from common import write_ground_truth
from odoo_client import OdooClient

FIRST_NAMES = ["Marc", "Sophie", "Klaus", "Elena", "Youssef", "Anna", "David", "Fatima", "Piotr", "Claire"]
LAST_NAMES = ["Dubois", "Fischer", "Novak", "El Amrani", "Janssen", "Rossi", "Larsen", "Kowalski", "Bernard", "Haddad"]
TITLES = ["Project Manager", "Lead Engineer"]


def main() -> None:
    rng = random.Random(2029)
    client = OdooClient()

    names = rng.sample(
        [f"{f} {l}" for f in FIRST_NAMES for l in LAST_NAMES], k=8
    )
    to_create = []
    plan = []
    for name in names:
        title = TITLES[len(to_create) % 2]
        to_create.append({"name": name, "job_title": title})
        plan.append({"name": name, "job_title": title})

    ids = client.create("hr.employee", to_create)
    for record, emp_id in zip(plan, ids):
        record["odoo_id"] = emp_id

    write_ground_truth("employees_pilot.json", plan)
    print(f"Created {len(ids)} employees.")


if __name__ == "__main__":
    main()
