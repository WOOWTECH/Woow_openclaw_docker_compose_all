#!/usr/bin/env python3
"""Configure Minimax API key in Odoo AI module."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

MINIMAX_API_KEY = "sk-api-REqIfH4IGT5c7ZOTg-Ik5tw0HpvuZBN-MOn0N4Up9BMoYEtJdUyY6FEVQLjwxbjLs9VPGEkynqgJ923G-kyHBnMhM_-dgmEHhjV0Wajoe8uRC3flvouxWWE"

# 1. Check ai.config fields
print("--- ai.config fields ---")
fields = models.execute_kw(db, uid, password, "ai.config", "fields_get", [],
    {"attributes": ["string", "type", "selection"]})
for fname, fdata in sorted(fields.items()):
    if fdata["type"] not in ("one2many", "many2many"):
        extra = ""
        if fdata.get("selection"):
            extra = f" sel={fdata['selection']}"
        print(f"  {fname}: {fdata['type']} ({fdata['string']}){extra}")

# 2. Check existing configs
print("\n--- Existing configs ---")
configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [[]],
    {"fields": ["id", "name", "display_name"]})
print(f"  Found: {configs}")

# 3. Try to find the minimax config by name
minimax_configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [
    [["name", "ilike", "minimax"]]
], {"fields": ["id", "name"]})

if minimax_configs:
    config_id = minimax_configs[0]["id"]
    print(f"\n  Minimax config found: ID={config_id}")
    # Read all fields to understand structure
    full = models.execute_kw(db, uid, password, "ai.config", "read", [[config_id]])
    print(f"  Full config: {full[0]}")
    # Set API key
    models.execute_kw(db, uid, password, "ai.config", "write", [[config_id], {
        "api_key": MINIMAX_API_KEY,
    }])
    print("  API key set!")
else:
    print("\n  No Minimax config found, checking all configs...")
    all_configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [[]],
        {"fields": ["id", "name", "api_key"]})
    for c in all_configs:
        print(f"  Config ID={c['id']}: name={c['name']}, has_key={bool(c.get('api_key'))}")

    # If there's a config without a key, set the key
    if all_configs:
        for c in all_configs:
            if "minimax" in c.get("name", "").lower() or "MiniMax" in c.get("name", ""):
                models.execute_kw(db, uid, password, "ai.config", "write", [[c["id"]], {
                    "api_key": MINIMAX_API_KEY,
                }])
                print(f"  Set API key on config ID={c['id']}")
                break

# 4. Verify installed modules
print("\n--- Installed AI modules ---")
ai_mods = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["name", "like", "ai_"], ["state", "=", "installed"]]
], {"fields": ["name", "shortdesc"]})
for m in ai_mods:
    print(f"  [{m['name']}] {m['shortdesc']}")

print("\n=== Done ===")
