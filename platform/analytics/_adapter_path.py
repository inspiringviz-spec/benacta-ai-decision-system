"""Adds the ERP Adapter to sys.path. Import this before importing `adapter`.

Note: this repo's /platform directory is never turned into an importable
Python package (no platform/__init__.py) — that name would shadow the
Python stdlib `platform` module for anything on sys.path. Modules here
are run/imported as standalone scripts from within their own directory,
same pattern as /data/generators.
"""
import sys
from pathlib import Path

_ODOO_ADAPTER_DIR = Path(__file__).resolve().parents[2] / "integrations" / "odoo"
if str(_ODOO_ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(_ODOO_ADAPTER_DIR))
