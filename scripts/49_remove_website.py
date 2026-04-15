#!/usr/bin/env python3
"""Remove website and all related modules (blog, ecommerce already removed)."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Find all installed website-related modules
print("=== INSTALLED WEBSITE MODULES ===")
website_mods = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["state", "=", "installed"],
     "|", "|", "|",
     ["name", "like", "website"],
     ["name", "like", "blog"],
     ["name", "like", "ecommerce"],
     ["name", "like", "portal"],
    ]
], {"fields": ["name", "shortdesc"], "order": "name"})
for m in website_mods:
    print(f"  {m['name']}: {m['shortdesc']}")

# 2. Find modules depending on 'website'
print("\n=== DEPENDS ON 'website' ===")
deps = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["state", "=", "installed"], ["dependencies_id.name", "=", "website"]]
], {"fields": ["name", "shortdesc"]})
for d in deps:
    print(f"  {d['name']}: {d['shortdesc']}")

# 3. Build removal list - website + all dependents
NEVER_REMOVE = {"base", "base_setup", "web", "mail", "account", "stock",
                "sale_management", "sale", "purchase", "point_of_sale",
                "contacts", "calendar", "hr", "loyalty", "l10n_tw",
                "ai_base_gt", "ai_minimax_connector_gt", "ai_mail_gt",
                "hide_menu_user", "odoo_color_customizer", "sh_document_management",
                "barcode_scanner_base", "barcode_scanner_sale",
                "barcode_scanner_stock", "barcode_scanner_purchase",
                "ws_origin_fix", "iap", "bus", "portal"}

to_remove = set()
for m in website_mods:
    if m["name"] not in NEVER_REMOVE:
        to_remove.add(m["name"])
for d in deps:
    if d["name"] not in NEVER_REMOVE:
        to_remove.add(d["name"])

# Add the main targets
to_remove.add("website")

# Remove protected
to_remove -= NEVER_REMOVE

print(f"\n=== TO REMOVE ({len(to_remove)}) ===")
print(f"  {sorted(to_remove)}")

# 4. Uninstall - leaf modules first, repeat
removed = set()
for round_num in range(10):
    remaining = to_remove - removed
    if not remaining:
        break

    print(f"\n--- Round {round_num+1} ({len(remaining)} remaining) ---")
    progress = False

    for mod_name in sorted(remaining):
        mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
            [["name", "=", mod_name], ["state", "=", "installed"]]
        ], {"fields": ["id", "shortdesc"]})

        if not mod:
            removed.add(mod_name)
            progress = True
            continue

        print(f"  Uninstalling {mod_name}...")
        try:
            models.execute_kw(db, uid, password, "ir.module.module",
                            "button_immediate_uninstall", [[mod[0]["id"]]])
            removed.add(mod_name)
            progress = True
            print(f"    OK!")
        except Exception as e:
            err = str(e)[:100]
            print(f"    SKIP: {err}")

    if not progress:
        print("  No progress, stopping")
        break

# 5. Verify
print("\n=== VERIFICATION ===")
still_installed = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["state", "=", "installed"], ["name", "like", "website"]]
], {"fields": ["name"]})
if still_installed:
    print(f"Still installed: {[m['name'] for m in still_installed]}")
else:
    print("All website modules removed!")

not_removed = to_remove - removed
if not_removed:
    print(f"Could not remove: {not_removed}")

# Health check
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8069/web/login")
    print(f"\nSite: HTTP {resp.status}")
except Exception as e:
    print(f"\nSite: {e}")
