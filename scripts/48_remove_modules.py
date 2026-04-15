#!/usr/bin/env python3
"""
Safely remove CRM, MRP, Project, Website Blog, and eCommerce modules.
Analyzes dependencies first, then uninstalls in correct reverse-dependency order.
"""
import xmlrpc.client
import sys

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# STEP 1: DEPENDENCY ANALYSIS
# ================================================================
print("=" * 60)
print("STEP 1: Dependency Analysis")
print("=" * 60)

# Core targets to remove
targets = ["crm", "mrp", "project", "website_blog", "website_sale"]

# Find ALL installed modules that depend on ANY of our targets
all_to_remove = set()
for target in targets:
    all_to_remove.add(target)
    # Find dependents recursively
    dependents = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["state", "=", "installed"], ["dependencies_id.name", "=", target]]
    ], {"fields": ["name", "shortdesc"]})
    for d in dependents:
        all_to_remove.add(d["name"])
        print(f"  {target} <- {d['name']} ({d['shortdesc']})")
        # Check 2nd level dependents
        deps2 = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
            [["state", "=", "installed"], ["dependencies_id.name", "=", d["name"]]]
        ], {"fields": ["name", "shortdesc"]})
        for d2 in deps2:
            all_to_remove.add(d2["name"])
            print(f"    {d['name']} <- {d2['name']} ({d2['shortdesc']})")

# Safety check: make sure we don't remove critical modules
NEVER_REMOVE = {"base", "base_setup", "web", "mail", "account", "stock",
                "sale_management", "sale", "purchase", "point_of_sale",
                "contacts", "calendar", "hr", "loyalty", "website", "l10n_tw",
                "ai_base_gt", "ai_minimax_connector_gt", "ai_mail_gt",
                "hide_menu_user", "odoo_color_customizer", "sh_document_management",
                "barcode_scanner_base", "barcode_scanner_sale",
                "barcode_scanner_stock", "barcode_scanner_purchase",
                "ws_origin_fix", "iap"}

conflicts = all_to_remove & NEVER_REMOVE
if conflicts:
    print(f"\n  WARNING: These would be removed but are protected: {conflicts}")
    all_to_remove -= conflicts

print(f"\n  Total modules to remove: {len(all_to_remove)}")
print(f"  Modules: {sorted(all_to_remove)}")

# ================================================================
# STEP 2: UNINSTALL IN REVERSE DEPENDENCY ORDER
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Uninstall modules")
print("=" * 60)

# Uninstall leaf modules first (those that nothing depends on)
# Repeat until all are removed
removed = set()
max_rounds = 10
for round_num in range(max_rounds):
    remaining = all_to_remove - removed
    if not remaining:
        break

    print(f"\n--- Round {round_num + 1} (remaining: {len(remaining)}) ---")
    progress = False

    for mod_name in sorted(remaining):
        # Check if any other remaining module depends on this one
        dependents_still = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
            [["state", "=", "installed"],
             ["dependencies_id.name", "=", mod_name],
             ["name", "not in", list(removed)]]
        ], {"fields": ["name"]})

        # Filter: only count dependents that are NOT in our remove list or already removed
        blocking = [d["name"] for d in dependents_still
                    if d["name"] not in removed and d["name"] not in all_to_remove]

        if blocking:
            print(f"  SKIP {mod_name} (blocked by: {blocking})")
            continue

        # Safe to uninstall
        mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
            [["name", "=", mod_name], ["state", "=", "installed"]]
        ], {"fields": ["id", "shortdesc"]})

        if not mod:
            removed.add(mod_name)
            continue

        print(f"  Uninstalling {mod_name} ({mod[0]['shortdesc']})...")
        try:
            models.execute_kw(db, uid, password, "ir.module.module",
                            "button_immediate_uninstall", [[mod[0]["id"]]])
            removed.add(mod_name)
            progress = True
            print(f"    OK!")
        except Exception as e:
            err = str(e)[:120]
            print(f"    ERROR: {err}")
            # If it fails, mark as attempted but don't block others
            if "already" in err.lower() or "not installed" in err.lower():
                removed.add(mod_name)
                progress = True

    if not progress and remaining == all_to_remove - removed:
        print(f"  No progress made, stopping.")
        break

# ================================================================
# STEP 3: VERIFY
# ================================================================
print("\n" + "=" * 60)
print("STEP 3: Verification")
print("=" * 60)

print(f"\nRemoved: {len(removed)}")
not_removed = all_to_remove - removed
if not_removed:
    print(f"NOT removed: {not_removed}")

# Check final installed modules
print("\nInstalled modules:")
installed = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["state", "=", "installed"], ["name", "not like", "base_%"],
     ["name", "not like", "web_%"], ["name", "not like", "auth_%"]]
], {"fields": ["name", "shortdesc"], "order": "name"})

for m in installed:
    is_target = m["name"] in targets
    marker = " *** SHOULD BE REMOVED" if is_target else ""
    print(f"  {m['name']}: {m['shortdesc']}{marker}")

# Health check
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8069/web/login")
    print(f"\nSite health: HTTP {resp.status}")
except Exception as e:
    print(f"\nSite health: ERROR {e}")

print("\n=== Done ===")
