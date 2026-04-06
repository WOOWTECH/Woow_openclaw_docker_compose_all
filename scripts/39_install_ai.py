#!/usr/bin/env python3
"""Install AI assistant modules and configure Minimax API."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Update module list
print("Updating module list...")
models.execute_kw(db, uid, password, "base.module.update", "create", [{}])
update_ids = models.execute_kw(db, uid, password, "base.module.update", "search", [[]])
if update_ids:
    models.execute_kw(db, uid, password, "base.module.update", "update_module", [update_ids])
print("Done")

# Install modules in order
install_order = [
    "ai_base_gt",
    "ai_minimax_connector_gt",
    "ai_mail_gt",
]

for mod_name in install_order:
    mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["name", "=", mod_name]]
    ], {"fields": ["id", "state"]})
    if mod:
        if mod[0]["state"] == "installed":
            print(f"[OK] {mod_name} already installed")
        else:
            print(f"Installing {mod_name}...")
            try:
                models.execute_kw(db, uid, password, "ir.module.module", "button_immediate_install", [[mod[0]["id"]]])
                print(f"  {mod_name} installed!")
            except Exception as e:
                print(f"  Error: {e}")
    else:
        print(f"[NOT FOUND] {mod_name}")

# Configure Minimax API
print("\n--- Configuring Minimax API ---")
MINIMAX_API_KEY = "sk-api-REqIfH4IGT5c7ZOTg-Ik5tw0HpvuZBN-MOn0N4Up9BMoYEtJdUyY6FEVQLjwxbjLs9VPGEkynqgJ923G-kyHBnMhM_-dgmEHhjV0Wajoe8uRC3flvouxWWE"

# Find the Minimax AI config record
configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [
    [["provider_type", "=", "minimax"]]
], {"fields": ["id", "name", "provider_type", "api_key"]})

if configs:
    print(f"  Found Minimax config: ID={configs[0]['id']}, name={configs[0]['name']}")
    models.execute_kw(db, uid, password, "ai.config", "write", [[configs[0]["id"]], {
        "api_key": MINIMAX_API_KEY,
    }])
    print("  API key set!")
else:
    # Try to find any config
    all_configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [
        []
    ], {"fields": ["id", "name", "provider_type"]})
    print(f"  All AI configs: {all_configs}")

    # Create Minimax config if needed
    if not any(c.get("provider_type") == "minimax" for c in all_configs):
        try:
            config_id = models.execute_kw(db, uid, password, "ai.config", "create", [{
                "name": "Minimax",
                "provider_type": "minimax",
                "api_key": MINIMAX_API_KEY,
            }])
            print(f"  Created Minimax config: ID={config_id}")
        except Exception as e:
            print(f"  Create error: {e}")

# Final verification
print("\n--- Final Status ---")
all_ai = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["name", "like", "ai_"], ["state", "=", "installed"]]
], {"fields": ["name", "shortdesc"]})
print(f"Installed AI modules: {len(all_ai)}")
for m in all_ai:
    print(f"  {m['name']}: {m['shortdesc']}")

configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [
    []
], {"fields": ["id", "name", "provider_type"]})
print(f"\nAI Configs: {configs}")
