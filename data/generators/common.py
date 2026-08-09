"""Shared helpers for the pilot data generators."""
from __future__ import annotations

import json
import random
from pathlib import Path

from odoo_client import OdooClient

GROUND_TRUTH_DIR = Path(__file__).resolve().parents[1] / "ground-truth"
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

PREFIXES = [
    "Nord", "Atlantic", "Meridian", "Continental", "Global", "Alpine", "Delta",
    "Vertex", "Union", "Prime", "Apex", "Sterling", "Horizon", "Titan",
    "Cascade", "Summit", "Anchor", "Beacon", "Crest", "Vantage",
]

COUNTRY_CITIES = {
    "FR": ["Lyon", "Nantes", "Toulouse", "Lille"],
    "DE": ["Stuttgart", "Essen", "Mannheim"],
    "BE": ["Antwerp", "Liège"],
    "NL": ["Rotterdam", "Eindhoven"],
    "US": ["Houston", "Charlotte", "Cleveland"],
    "PL": ["Katowice", "Gdansk"],
    "MA": ["Casablanca", "Tanger"],
    "AE": ["Dubai"],
}


def get_or_create_category(client: OdooClient, name: str) -> int:
    return get_or_create_by_name(client, "res.partner.category", name)


def get_or_create_by_name(client: OdooClient, model: str, name: str) -> int:
    existing = client.search(model, [["name", "=", name]])
    if existing:
        return existing[0]
    return client.create(model, [{"name": name}])[0]


def get_country_ids(client: OdooClient) -> dict:
    rows = client.search_read(
        "res.country", [["code", "in", list(COUNTRY_CITIES.keys())]], ["code"]
    )
    return {r["code"]: r["id"] for r in rows}


def pick_geo(country_ids: dict, rng: random.Random) -> tuple[int, str]:
    code = rng.choice(list(country_ids.keys()))
    city = rng.choice(COUNTRY_CITIES[code])
    return country_ids[code], city


def write_ground_truth(filename: str, records: list[dict]) -> None:
    path = GROUND_TRUTH_DIR / filename
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Ground truth written: {path} ({len(records)} records)")
