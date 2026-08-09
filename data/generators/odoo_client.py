"""Shared Odoo XML-RPC client for the synthetic data generators (Epic 02).

Credentials come from the repo-root .env (gitignored, never committed).
"""
from __future__ import annotations

import os
import xmlrpc.client
from pathlib import Path


def _load_env() -> dict:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    values = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return {**values, **os.environ}


class OdooClient:
    def __init__(self):
        env = _load_env()
        self.url = env["ODOO_URL"]
        self.db = env["ODOO_DB"]
        self.login = env["ODOO_LOGIN"]
        self.api_key = env["ODOO_API_KEY"]

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.login, self.api_key, {})
        if not self.uid:
            raise RuntimeError("Odoo authentication failed — check .env")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def create(self, model: str, values_list: list[dict]) -> list[int]:
        """Batch-create records; returns the created ids in order."""
        ids = []
        for values in values_list:
            ids.append(
                self.models.execute_kw(
                    self.db, self.uid, self.api_key, model, "create", [values]
                )
            )
        return ids

    def search_read(self, model: str, domain: list, fields: list[str]) -> list[dict]:
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "search_read", [domain], {"fields": fields}
        )

    def search(self, model: str, domain: list) -> list[int]:
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "search", [domain]
        )

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, "write", [ids, values]
        )

    def execute(self, model: str, method: str, ids: list[int], *args, **kwargs):
        """Call an arbitrary model method (e.g. action_confirm, action_post)."""
        params = [ids, *args]
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, method, params, kwargs
        )

    def call(self, model: str, method: str, *args, **kwargs):
        """Call a method that isn't record-bound (e.g. create_invoices helpers)."""
        return self.models.execute_kw(
            self.db, self.uid, self.api_key, model, method, list(args), kwargs
        )
