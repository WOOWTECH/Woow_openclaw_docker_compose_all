#!/usr/bin/env python3
"""Test AI module setup and create assistant."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Verify config
config = models.execute_kw(db, uid, password, "ai.config", "read", [[2],
    ["name", "type", "api_key", "model", "base_url"]])
c = config[0]
print(f"Config: name={c['name']}, type={c['type']}, model={c['model']}")
print(f"  API key set: {bool(c['api_key'])}")
print(f"  Base URL: {c['base_url']}")

# Check AI assistants
assistants = models.execute_kw(db, uid, password, "ai.assistant", "search_read", [[]],
    {"fields": ["id", "name", "ai_config_id"]})
print(f"\nAI Assistants: {len(assistants)}")
for a in assistants:
    print(f"  ID={a['id']}: {a['name']} config={a['ai_config_id']}")

if not assistants:
    print("\nCreating test assistant...")
    try:
        asst_id = models.execute_kw(db, uid, password, "ai.assistant", "create", [{
            "name": "Inzense AI",
            "ai_config_id": 2,
            "system_prompt": "You are Inzense AI assistant.",
        }])
        print(f"  Created: ID={asst_id}")
    except Exception as e:
        print(f"  Error: {e}")

# Installed modules summary
mods = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["name", "in", ["ai_base_gt", "ai_minimax_connector_gt", "ai_mail_gt"]], ["state", "=", "installed"]]
], {"fields": ["name", "shortdesc"]})
print(f"\nInstalled AI modules: {len(mods)}")
for m in mods:
    print(f"  [OK] {m['name']}: {m['shortdesc']}")

import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/web/login")
print(f"\nSite: HTTP {resp.status}")
print("\n=== DONE ===")
