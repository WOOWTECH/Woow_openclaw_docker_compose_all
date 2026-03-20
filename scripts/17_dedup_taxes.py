#!/usr/bin/env python3
"""Clean up duplicate taxes and deactivate demo users."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Clean up duplicate taxes
print("--- Active Taxes ---")
taxes = models.execute_kw(db, uid, password, "account.tax", "search_read", [
    [["active", "=", True]]
], {"fields": ["id", "name", "amount", "type_tax_use"]})
for t in taxes:
    print(f"  ID={t['id']}: {t['name']} ({t['amount']}%) - {t['type_tax_use']}")

# Deactivate our manually created duplicates (keep l10n_tw ones)
manual_ids = []
for t in taxes:
    if t["name"] in ["營業稅 5%", "進項稅額 5%"]:
        manual_ids.append(t["id"])
if manual_ids:
    models.execute_kw(db, uid, password, "account.tax", "write", [manual_ids, {"active": False}])
    print(f"\nDeactivated {len(manual_ids)} duplicate taxes")

# 2. Deactivate demo users (keep only admin uid=2)
print("\n--- Demo Users ---")
demo_users = models.execute_kw(db, uid, password, "res.users", "search_read", [
    [["id", "not in", [1, 2]], ["active", "=", True]]
], {"fields": ["id", "name", "login"]})
for u in demo_users:
    print(f"  Deactivating: {u['name']} ({u['login']})")
    try:
        models.execute_kw(db, uid, password, "res.users", "write", [[u["id"]], {"active": False}])
    except Exception as e:
        print(f"    Failed: {e}")

# Final tax check
print("\n--- Final Active Taxes ---")
final_taxes = models.execute_kw(db, uid, password, "account.tax", "search_read", [
    [["active", "=", True]]
], {"fields": ["name", "amount", "type_tax_use"]})
for t in final_taxes:
    print(f"  {t['name']} ({t['amount']}%) - {t['type_tax_use']}")

# Final user check
print("\n--- Active Users ---")
active_users = models.execute_kw(db, uid, password, "res.users", "search_read", [
    [["active", "=", True]]
], {"fields": ["name", "login", "lang", "tz"]})
for u in active_users:
    print(f"  {u['name']} ({u['login']}) lang={u['lang']} tz={u['tz']}")

print("\nDone!")
