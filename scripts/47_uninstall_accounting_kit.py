#!/usr/bin/env python3
"""Uninstall base_accounting_kit and base_account_budget modules."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Uninstall in reverse dependency order: budget first, then kit
for mod_name in ["base_account_budget", "base_accounting_kit"]:
    mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["name", "=", mod_name]]
    ], {"fields": ["id", "state", "shortdesc"]})
    if mod and mod[0]["state"] == "installed":
        print(f"Uninstalling {mod[0]['shortdesc']} ({mod_name})...")
        try:
            models.execute_kw(db, uid, password, "ir.module.module", "button_immediate_uninstall", [[mod[0]["id"]]])
            print(f"  Done!")
        except Exception as e:
            print(f"  Error: {str(e)[:150]}")
    elif mod:
        print(f"{mod_name}: already {mod[0]['state']}")
    else:
        print(f"{mod_name}: not found")

# Verify
print("\nFinal status:")
for mod_name in ["base_accounting_kit", "base_account_budget"]:
    mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["name", "=", mod_name]]
    ], {"fields": ["state", "shortdesc"]})
    if mod:
        print(f"  {mod[0]['shortdesc']}: {mod[0]['state']}")
