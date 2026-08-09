"""One-off connectivity check for the Odoo ERP Adapter (Epic 02).

Reads credentials from a local .env file (gitignored, never committed).
Does not print the API key.
"""
import os
import xmlrpc.client
from pathlib import Path

def load_env(path: Path) -> dict:
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    env = {**load_env(env_path), **os.environ}

    url = env["ODOO_URL"]
    db = env["ODOO_DB"]
    login = env["ODOO_LOGIN"]
    api_key = env["ODOO_API_KEY"]

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    version = common.version()
    print(f"Server version: {version.get('server_version')}")

    uid = common.authenticate(db, login, api_key, {})
    if not uid:
        print("Authentication FAILED — check ODOO_DB / ODOO_LOGIN / ODOO_API_KEY.")
        return
    print(f"Authenticated. uid={uid}")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    companies = models.execute_kw(
        db, uid, api_key, "res.company", "search_read", [[]], {"fields": ["name"]}
    )
    print(f"Companies visible: {[c['name'] for c in companies]}")


if __name__ == "__main__":
    main()
