"""ERP Adapter — Odoo implementation (Epic 02/04, ADR-0002, ADR-0003).

Exposes business-shaped read methods (customers, projects, invoices...)
so the Analytics Engine and, later, the MCP layer never talk XML-RPC or
Odoo field names directly. If Odoo is ever replaced or complemented by
another ERP, only this file changes (master prompt SS6, SS35).
"""
from __future__ import annotations

import os
import xmlrpc.client
from dataclasses import dataclass, field
from datetime import date
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


@dataclass
class Customer:
    id: int
    name: str
    segment: str | None
    city: str | None


@dataclass
class Supplier:
    id: int
    name: str
    category: str | None
    city: str | None


@dataclass
class Product:
    id: int
    name: str
    code: str | None
    family: str | None
    standard_price: float
    list_price: float


@dataclass
class Project:
    id: int
    name: str
    customer_id: int | None
    customer_name: str | None
    date_start: str | None
    date_end: str | None
    description: str | None


@dataclass
class InvoiceLine:
    product_id: int | None
    description: str
    quantity: float
    price_unit: float
    price_subtotal: float


@dataclass
class Move:
    """A posted accounting document: customer invoice, vendor bill, or
    either kind of credit note. `move_type` mirrors Odoo's own values
    (out_invoice, out_refund, in_invoice, in_refund)."""

    id: int
    move_type: str
    partner_id: int
    partner_name: str
    invoice_date: str | None
    amount_total: float
    amount_residual: float
    payment_state: str
    lines: list[InvoiceLine] = field(default_factory=list)


class OdooERPAdapter:
    def __init__(self):
        env = _load_env()
        self.url = env["ODOO_URL"]
        self.db = env["ODOO_DB"]
        self.login = env["ODOO_LOGIN"]
        self.api_key = env["ODOO_API_KEY"]

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.login, self.api_key, {})
        if not self.uid:
            raise RuntimeError("Odoo authentication failed")
        self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def _read(self, model: str, domain: list, fields: list[str]) -> list[dict]:
        return self._models.execute_kw(
            self.db, self.uid, self.api_key, model, "search_read", [domain], {"fields": fields}
        )

    # ---- Master data -------------------------------------------------

    def _category_names(self) -> dict[int, str]:
        rows = self._read("res.partner.category", [], ["name"])
        return {r["id"]: r["name"] for r in rows}

    def get_customers(self) -> list[Customer]:
        # category_id is a many2many on res.partner: search_read returns a
        # bare list of ids, not (id, display_name) pairs like a many2one.
        cat_names = self._category_names()
        rows = self._read(
            "res.partner",
            [["customer_rank", ">", 0]],
            ["name", "category_id", "city"],
        )
        return [
            Customer(
                id=r["id"],
                name=r["name"],
                segment=cat_names.get(r["category_id"][0]) if r["category_id"] else None,
                city=r["city"],
            )
            for r in rows
        ]

    def get_suppliers(self) -> list[Supplier]:
        cat_names = self._category_names()
        rows = self._read(
            "res.partner",
            [["supplier_rank", ">", 0]],
            ["name", "category_id", "city"],
        )
        return [
            Supplier(
                id=r["id"],
                name=r["name"],
                category=cat_names.get(r["category_id"][0]) if r["category_id"] else None,
                city=r["city"],
            )
            for r in rows
        ]

    def get_products(self) -> list[Product]:
        rows = self._read(
            "product.template",
            [["default_code", "!=", False]],
            ["name", "default_code", "categ_id", "standard_price", "list_price"],
        )
        return [
            Product(
                id=r["id"],
                name=r["name"],
                code=r["default_code"] or None,
                family=r["categ_id"][1] if r["categ_id"] else None,
                standard_price=r["standard_price"],
                list_price=r["list_price"],
            )
            for r in rows
        ]

    def get_projects(self) -> list[Project]:
        rows = self._read(
            "project.project",
            [],
            ["name", "partner_id", "date_start", "date", "description"],
        )
        return [
            Project(
                id=r["id"],
                name=r["name"],
                customer_id=r["partner_id"][0] if r["partner_id"] else None,
                customer_name=r["partner_id"][1] if r["partner_id"] else None,
                date_start=r["date_start"],
                date_end=r["date"],
                description=r["description"],
            )
            for r in rows
        ]

    # ---- Transactions --------------------------------------------------

    def _get_moves(self, move_types: list[str], date_from: date | None, date_to: date | None) -> list[Move]:
        domain = [["move_type", "in", move_types], ["state", "=", "posted"]]
        if date_from:
            domain.append(["invoice_date", ">=", date_from.isoformat()])
        if date_to:
            domain.append(["invoice_date", "<=", date_to.isoformat()])
        rows = self._read(
            "account.move",
            domain,
            ["move_type", "partner_id", "invoice_date", "amount_total", "amount_residual", "payment_state"],
        )
        moves = []
        for r in rows:
            line_rows = self._read(
                "account.move.line",
                [["move_id", "=", r["id"]], ["display_type", "=", "product"]],
                ["product_id", "name", "quantity", "price_unit", "price_subtotal"],
            )
            lines = [
                InvoiceLine(
                    product_id=lr["product_id"][0] if lr["product_id"] else None,
                    description=lr["name"],
                    quantity=lr["quantity"],
                    price_unit=lr["price_unit"],
                    price_subtotal=lr["price_subtotal"],
                )
                for lr in line_rows
            ]
            moves.append(
                Move(
                    id=r["id"],
                    move_type=r["move_type"],
                    partner_id=r["partner_id"][0] if r["partner_id"] else None,
                    partner_name=r["partner_id"][1] if r["partner_id"] else None,
                    invoice_date=r["invoice_date"],
                    amount_total=r["amount_total"],
                    amount_residual=r["amount_residual"],
                    payment_state=r["payment_state"],
                    lines=lines,
                )
            )
        return moves

    def get_customer_invoices(self, date_from: date | None = None, date_to: date | None = None) -> list[Move]:
        return self._get_moves(["out_invoice"], date_from, date_to)

    def get_customer_credit_notes(self, date_from: date | None = None, date_to: date | None = None) -> list[Move]:
        return self._get_moves(["out_refund"], date_from, date_to)

    def get_vendor_bills(self, date_from: date | None = None, date_to: date | None = None) -> list[Move]:
        return self._get_moves(["in_invoice"], date_from, date_to)

    def get_vendor_credit_notes(self, date_from: date | None = None, date_to: date | None = None) -> list[Move]:
        return self._get_moves(["in_refund"], date_from, date_to)
