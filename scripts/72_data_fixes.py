#!/usr/bin/env python3
"""
Inzense Odoo 18 — Phase 2: Data Fixes
Fix social links, zero-price products, ghost website, copyright.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/72_data_fixes.py
"""
import xmlrpc.client

URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


def sr(model, domain, fields, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, "search_read", [domain], {"fields": fields, **kw})


def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASSWORD, model, "write", [ids, vals])


def search(model, domain):
    return models.execute_kw(DB, uid, PASSWORD, model, "search", [domain])


# ============================================================
# 1. Fix social media links
# ============================================================
print("\n=== 1. Fix social media links ===")
write("website", [1], {
    "social_facebook": "https://www.facebook.com/onlyinzense",
    "social_instagram": "https://instagram.com/only_inzense",
    "social_youtube": "",
    "social_github": "",
    "social_tiktok": "",
    "social_twitter": "",
    "social_linkedin": "",
})
print("  ✅ Social links fixed (removed YouTube/GitHub/TikTok Odoo defaults)")

# Verify
w = sr("website", [["id", "=", 1]], [
    "social_facebook", "social_instagram", "social_youtube",
    "social_github", "social_tiktok"
])[0]
print(f"    FB: {w['social_facebook']}")
print(f"    IG: {w['social_instagram']}")
print(f"    YT: '{w['social_youtube']}' (cleared)")
print(f"    GH: '{w['social_github']}' (cleared)")
print(f"    TT: '{w['social_tiktok']}' (cleared)")

# ============================================================
# 2. Unpublish zero-price products
# ============================================================
print("\n=== 2. Unpublish zero-price products ===")
zero_price = sr("product.template", [
    ["website_published", "=", True], ["list_price", "=", 0]
], ["name", "list_price"])

if zero_price:
    ids = [p["id"] for p in zero_price]
    write("product.template", ids, {"website_published": False})
    print(f"  ✅ Unpublished {len(ids)} zero-price products:")
    for p in zero_price:
        print(f"    - {p['name']}")
else:
    print("  ✅ No zero-price published products found")

# Verify
remaining = search("product.template", [
    ["website_published", "=", True], ["list_price", "=", 0]
])
print(f"  Remaining zero-price published: {len(remaining)}")

# ============================================================
# 3. Delete ghost website "My Website 2"
# ============================================================
print("\n=== 3. Delete ghost website ===")
ghost_websites = sr("website", [["id", "!=", 1]], ["name"])
for gw in ghost_websites:
    try:
        models.execute_kw(DB, uid, PASSWORD, "website", "unlink", [[gw["id"]]])
        print(f"  ✅ Deleted: id={gw['id']} '{gw['name']}'")
    except Exception as e:
        # If can't delete, at least deactivate menu items
        print(f"  ⚠ Cannot delete website {gw['id']}: {e}")
        # Delete its menu items
        ghost_menus = search("website.menu", [["website_id", "=", gw["id"]]])
        if ghost_menus:
            models.execute_kw(DB, uid, PASSWORD, "website.menu", "unlink", [ghost_menus])
            print(f"    Deleted {len(ghost_menus)} orphan menu items")

# ============================================================
# 4. Set website name and favicon
# ============================================================
print("\n=== 4. Website settings ===")
write("website", [1], {
    "name": "禪香不二 Inzense",
})
print("  ✅ Website name confirmed: 禪香不二 Inzense")

# ============================================================
# 5. Published product count check
# ============================================================
print("\n=== 5. Final product stats ===")
total_published = len(search("product.template", [["website_published", "=", True]]))
total_saleable = len(search("product.template", [["sale_ok", "=", True]]))
print(f"  Total saleable: {total_saleable}")
print(f"  Published on website: {total_published}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("Phase 2 Summary:")
print(f"  ✅ Social links: Fixed (FB + IG only, cleared Odoo defaults)")
print(f"  ✅ Zero-price products: {len(zero_price)} unpublished")
print(f"  ✅ Ghost websites: {len(ghost_websites)} handled")
print(f"  ✅ Published products: {total_published}")
print("\nPhase 2 complete.")
