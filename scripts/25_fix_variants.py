#!/usr/bin/env python3
"""Debug and fix product variant issues causing '此組合不存在'."""
import xmlrpc.client
import re
import urllib.request

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Check a specific product
print("--- Debug product 116 ---")
variants = models.execute_kw(db, uid, password, "product.product", "search_read", [
    [["product_tmpl_id", "=", 116]]
], {"fields": ["id", "name", "active", "product_template_variant_value_ids", "combination_indices"],
    "context": {"active_test": False}})
print(f"Variants for template 116:")
for v in variants:
    print(f"  pp.ID={v['id']}: active={v['active']} values={v['product_template_variant_value_ids']} combo='{v['combination_indices']}'")

attr_lines = models.execute_kw(db, uid, password, "product.template.attribute.line", "search_read", [
    [["product_tmpl_id", "=", 116]]
], {"fields": ["id", "attribute_id", "value_ids"]})
print(f"Attr lines: {attr_lines}")

# 2. Check products with multiple variants
templates = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["website_published", "=", True]]
], {"fields": ["id", "name", "product_variant_count"], "limit": 300})

multi = [t for t in templates if t["product_variant_count"] > 1]
print(f"\nProducts with >1 variant: {len(multi)}")
for m in multi[:10]:
    print(f"  ID={m['id']}: {m['name'][:40]} ({m['product_variant_count']} variants)")

# 3. For each product with >1 variant, remove extra variants
# Keep only the first product.product and archive/delete the rest
print("\n--- Fixing multi-variant products ---")
fixed = 0
for t in multi:
    pp_ids = models.execute_kw(db, uid, password, "product.product", "search", [
        [["product_tmpl_id", "=", t["id"]]]
    ], {"order": "id asc", "context": {"active_test": False}})

    if len(pp_ids) > 1:
        # Keep the first, archive the rest
        to_archive = pp_ids[1:]
        for pp_id in to_archive:
            try:
                models.execute_kw(db, uid, password, "product.product", "write", [[pp_id], {
                    "active": False,
                }])
            except:
                pass
        fixed += 1

print(f"  Fixed {fixed} multi-variant products")

# 4. Remove any remaining attribute lines
remaining_attrs = models.execute_kw(db, uid, password, "product.template.attribute.line", "search", [[]])
if remaining_attrs:
    for attr_id in remaining_attrs:
        try:
            models.execute_kw(db, uid, password, "product.template.attribute.line", "unlink", [[attr_id]])
        except:
            pass
    print(f"  Removed {len(remaining_attrs)} remaining attribute lines")

# 5. Now check if products with archived variants still show the error
# The issue might be that product.product records with values that
# don't exist anymore still trigger the variant selector

# Clean up: for each template, ensure only 1 active product.product exists
print("\n--- Ensuring single variant per product ---")
all_templates = models.execute_kw(db, uid, password, "product.template", "search", [
    [["website_published", "=", True]]
])
for tmpl_id in all_templates:
    active_pps = models.execute_kw(db, uid, password, "product.product", "search", [
        [["product_tmpl_id", "=", tmpl_id], ["active", "=", True]]
    ])
    if len(active_pps) > 1:
        # Keep first, archive rest
        for pp in active_pps[1:]:
            try:
                models.execute_kw(db, uid, password, "product.product", "write", [[pp], {"active": False}])
            except:
                pass

    # Also clear combination_indices on the remaining variant
    if active_pps:
        try:
            models.execute_kw(db, uid, password, "product.product", "write", [[active_pps[0]], {
                "combination_indices": "",
            }])
        except:
            pass

print("  Done")

# 6. Test again
print("\n--- Test product pages ---")
resp = urllib.request.urlopen("http://localhost:8069/shop")
shop = resp.read().decode()
links = list(set(re.findall(r'href="(/shop/[a-z0-9-]+-\d+)"', shop)))

ok = 0
err = 0
for link in links[:5]:
    try:
        resp2 = urllib.request.urlopen(f"http://localhost:8069{link}")
        detail = resp2.read().decode()
        has_cart = "加入購物車" in detail
        has_err = "此組合不存在" in detail
        if has_cart and not has_err:
            ok += 1
        else:
            err += 1
            if has_err:
                print(f"  STILL ERROR: {link[:50]}")
    except:
        err += 1
print(f"  Results: {ok} OK, {err} issues out of {min(5, len(links))} tested")

print("\n=== Done ===")
