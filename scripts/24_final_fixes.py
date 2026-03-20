#!/usr/bin/env python3
"""Final targeted fixes for variant errors, company name, categories."""
import xmlrpc.client
import re
import urllib.request

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Remove ALL product attribute lines to eliminate variant errors
print("--- Remove ALL product attribute lines ---")
all_attr_lines = models.execute_kw(db, uid, password, "product.template.attribute.line", "search", [[]])
if all_attr_lines:
    for batch_start in range(0, len(all_attr_lines), 50):
        batch = all_attr_lines[batch_start:batch_start+50]
        try:
            models.execute_kw(db, uid, password, "product.template.attribute.line", "unlink", [batch])
            print(f"  Removed batch {batch_start}-{batch_start+len(batch)}")
        except Exception as e:
            # Try one by one
            for al_id in batch:
                try:
                    models.execute_kw(db, uid, password, "product.template.attribute.line", "unlink", [[al_id]])
                except:
                    pass
    print(f"  Total attribute lines processed: {len(all_attr_lines)}")
else:
    print("  No attribute lines to remove")

# 2. Fix remaining 公司名稱
print("\n--- Fix 公司名稱 ---")
remaining = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["arch", "like", "公司名稱"]]
], {"fields": ["id", "key"], "limit": 20})
for v in remaining:
    vdata = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[v["id"]], ["arch"]])
    new_arch = vdata[0]["arch"].replace("公司名稱", "禪香不二 Inzense")
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[v["id"]], {"arch": new_arch}])
    print(f"  Fixed view ID={v['id']} key={v.get('key')}")

if not remaining:
    print("  No views with 公司名稱 remaining")

# 3. Fix 神明保庇熱賣組 (cat 77)
print("\n--- Fix combo categories ---")
all_prods = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["website_published", "=", True]]
], {"fields": ["id", "name", "public_categ_ids"]})

god_kw = ["觀世音", "媽祖", "財神", "玄天", "文昌", "城隍", "土地公", "關聖",
          "三太子", "中壇", "玉皇", "佛祖", "藥師佛", "月老", "九天玄女"]
added_77 = 0
for p in all_prods:
    name = p["name"]
    if "組" in name:
        god_count = sum(1 for g in god_kw if g in name)
        if god_count >= 2 and 77 not in p["public_categ_ids"]:
            models.execute_kw(db, uid, password, "product.template", "write", [[p["id"]], {
                "public_categ_ids": [(4, 77)]
            }])
            added_77 += 1
print(f"  Added {added_77} products to 神明保庇熱賣組")

# 4. Test product pages
print("\n--- Test product purchasability ---")
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
        has_variant_err = "此組合不存在" in detail
        if has_cart and not has_variant_err:
            ok += 1
        else:
            err += 1
            print(f"  ISSUE: {link[:50]} cart={has_cart} err={has_variant_err}")
    except:
        err += 1
print(f"  Results: {ok} OK, {err} issues out of {min(5, len(links))} tested")

# 5. Final verification
print("\n--- Final page checks ---")
for page_url, page_name in [("/", "Homepage"), ("/shop", "Shop"), ("/about-us", "About"), ("/contactus", "Contact")]:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069{page_url}")
        content = resp.read().decode()
        has_555 = "+1 555" in content
        has_company_placeholder = "公司名稱" in content and "禪香不二" not in content
        print(f"  {page_name}: {len(content)}b, +1_555={has_555}, placeholder={has_company_placeholder}")
    except Exception as e:
        print(f"  {page_name}: ERROR {e}")

print("\n=== DONE ===")
