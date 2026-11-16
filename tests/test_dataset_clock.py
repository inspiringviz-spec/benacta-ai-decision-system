"""The synthetic enterprise has one business clock. Generators and
analytics each hold a copy (they live in different import roots); this
keeps them equal so a date moved on one side cannot silently drift."""
import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integrations" / "odoo"))

from adapter import DATASET_AS_OF  # noqa: E402


def _generators_today() -> date:
    # common.py imports odoo_client at module level; load it with its own dir on sys.path.
    gen_dir = ROOT / "data" / "generators"
    sys.path.insert(0, str(gen_dir))
    spec = importlib.util.spec_from_file_location("gen_common", gen_dir / "common.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TODAY


def test_generators_and_analytics_share_the_dataset_clock():
    assert _generators_today() == DATASET_AS_OF == date(2026, 8, 9)


def test_no_module_redefines_the_clock():
    offenders = [
        p.relative_to(ROOT).as_posix()
        for p in list((ROOT / "data").rglob("*.py")) + list((ROOT / "platform").rglob("*.py"))
        if "date(2026, 8, 9)" in p.read_text(encoding="utf-8") and p.name != "common.py"
    ]
    assert offenders == [], offenders
