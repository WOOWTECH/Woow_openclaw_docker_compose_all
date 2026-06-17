#!/usr/bin/env python3
"""
Inzense Odoo 18 — Phase 0: Baseline Audit
Captures current frontend state for comparison after each optimization phase.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/70_audit_current_state.py
"""
import xmlrpc.client
import json
import urllib.request

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


def search(model, domain):
    return models.execute_kw(DB, uid, PASSWORD, model, "search", [domain])


audit = {}

# ============================================================
# 1. CSS Views
# ============================================================
print("\n=== 1. CSS Views (ir.ui.view with 'inzense' or 'custom_css') ===")
css_views = sr("ir.ui.view", ["|", "|",
    ["key", "ilike", "inzense"],
    ["key", "ilike", "custom_css"],
    ["name", "ilike", "inzense"]
], ["name", "key", "active", "inherit_id", "priority", "type", "arch_db"])
audit["css_views"] = []
for v in css_views:
    arch_preview = (v.get("arch_db") or "")[:200]
    print(f"  id={v['id']} key={v['key']} active={v['active']} name={v['name']}")
    print(f"    inherit={v['inherit_id']} priority={v['priority']}")
    print(f"    arch preview: {arch_preview}...")
    audit["css_views"].append({
        "id": v["id"], "key": v["key"], "name": v["name"],
        "active": v["active"], "priority": v["priority"],
        "inherit_id": v["inherit_id"],
        "arch_length": len(v.get("arch_db") or ""),
    })

# ============================================================
# 2. Website Settings
# ============================================================
print("\n=== 2. Website Settings ===")
websites = sr("website", [], [
    "name", "domain", "social_facebook", "social_instagram",
    "social_youtube", "social_github", "social_tiktok", "social_twitter",
    "social_linkedin", "default_lang_id", "logo",
])
for w in websites:
    print(f"  id={w['id']} name={w['name']} domain={w['domain']}")
    print(f"    fb={w['social_facebook']} ig={w['social_instagram']}")
    print(f"    yt={w['social_youtube']} gh={w['social_github']} tt={w['social_tiktok']}")
    print(f"    tw={w['social_twitter']} li={w['social_linkedin']}")
audit["websites"] = [{k: v for k, v in w.items() if k != "logo"} for w in websites]

# ============================================================
# 3. Menu Structure
# ============================================================
print("\n=== 3. Menu Structure ===")
menus = sr("website.menu", [["website_id", "=", 1]], [
    "name", "url", "sequence", "parent_id", "new_window"
], order="sequence")
audit["menus"] = []
for m in menus:
    indent = "    " if m["parent_id"] else "  "
    print(f"{indent}seq={m['sequence']} '{m['name']}' → {m['url']} (parent={m['parent_id']})")
    audit["menus"].append(m)

# ============================================================
# 4. Published Pages
# ============================================================
print("\n=== 4. Published Pages ===")
pages = sr("website.page", [["website_published", "=", True], ["website_id", "=", 1]], [
    "name", "url", "website_published",
])
audit["published_pages"] = []
for p in pages:
    print(f"  '{p['name']}' → {p['url']}")
    audit["published_pages"].append(p)
print(f"  Total: {len(pages)} published pages")

# ============================================================
# 5. Product Stats
# ============================================================
print("\n=== 5. Product Stats ===")
total_products = len(search("product.template", [["sale_ok", "=", True]]))
published = len(search("product.template", [["website_published", "=", True]]))
zero_price = sr("product.template", [
    ["website_published", "=", True], ["list_price", "=", 0]
], ["name", "list_price"])
audit["products"] = {
    "total_saleable": total_products,
    "published": published,
    "zero_price_published": len(zero_price),
    "zero_price_names": [p["name"] for p in zero_price],
}
print(f"  Total saleable: {total_products}")
print(f"  Published on website: {published}")
print(f"  Zero-price published: {len(zero_price)}")
for p in zero_price:
    print(f"    - {p['name']}")

# ============================================================
# 6. Product Categories (public)
# ============================================================
print("\n=== 6. Public Product Categories ===")
cats = sr("product.public.category", [], ["name", "parent_id", "sequence", "website_id"])
audit["categories"] = []
top_level = [c for c in cats if not c["parent_id"]]
children = [c for c in cats if c["parent_id"]]
print(f"  Top-level: {len(top_level)}")
for c in sorted(top_level, key=lambda x: x["sequence"]):
    child_count = len([ch for ch in children if ch["parent_id"] and ch["parent_id"][0] == c["id"]])
    print(f"    {c['name']} (id={c['id']}, {child_count} children)")
    audit["categories"].append({"id": c["id"], "name": c["name"], "children": child_count})
print(f"  Total sub-categories: {len(children)}")

# ============================================================
# 7. Installed Website Modules
# ============================================================
print("\n=== 7. Website-related Modules ===")
web_modules = sr("ir.module.module", [
    ["state", "=", "installed"],
    "|", "|", "|",
    ["name", "ilike", "website"],
    ["name", "ilike", "theme"],
    ["name", "ilike", "blog"],
    ["name", "ilike", "portal"],
], ["name", "state", "shortdesc"])
audit["modules"] = []
for m in sorted(web_modules, key=lambda x: x["name"]):
    print(f"  {m['name']} ({m['shortdesc']})")
    audit["modules"].append({"name": m["name"], "desc": m["shortdesc"]})

# ============================================================
# 8. Homepage View
# ============================================================
print("\n=== 8. Homepage View ===")
hp = sr("ir.ui.view", [["key", "=", "website.homepage"]], ["id", "active", "arch_db"])
if hp:
    arch = hp[0].get("arch_db") or ""
    audit["homepage"] = {
        "view_id": hp[0]["id"],
        "active": hp[0]["active"],
        "arch_length": len(arch),
        "has_E4916E": "#E4916E" in arch or "#e4916e" in arch,
        "has_D8B772": "#D8B772" in arch or "#d8b772" in arch,
        "has_13AFF0": "#13AFF0" in arch or "#13aff0" in arch,
        "section_count": arch.count("<section"),
    }
    print(f"  view_id={hp[0]['id']} active={hp[0]['active']} arch_length={len(arch)}")
    print(f"  Sections: {audit['homepage']['section_count']}")
    print(f"  Has #E4916E (wrong): {audit['homepage']['has_E4916E']}")
    print(f"  Has #D8B772 (gold): {audit['homepage']['has_D8B772']}")
    print(f"  Has #13AFF0 (cyan): {audit['homepage']['has_13AFF0']}")
else:
    audit["homepage"] = {"error": "No homepage view found"}
    print("  ❌ No homepage view found with key 'website.homepage'")

# ============================================================
# 9. Footer View
# ============================================================
print("\n=== 9. Footer Custom View ===")
footer = sr("ir.ui.view", [["key", "ilike", "footer"]], ["name", "key", "active", "inherit_id"])
audit["footer_views"] = []
for f in footer:
    print(f"  id={f['id']} key={f['key']} active={f['active']} name={f['name']}")
    audit["footer_views"].append(f)

# ============================================================
# 10. HTTP Page Checks
# ============================================================
print("\n=== 10. HTTP Page Status ===")
pages_to_check = ["/", "/shop", "/about-us", "/contactus", "/qa",
                   "/privacy-policy", "/return-policy", "/my", "/activity"]
audit["http_status"] = {}
for page in pages_to_check:
    try:
        req = urllib.request.Request(f"{URL}{page}", method="HEAD")
        resp = urllib.request.urlopen(req, timeout=5)
        status = resp.getcode()
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        status = str(e)
    print(f"  {page}: {status}")
    audit["http_status"][page] = status

# ============================================================
# 11. Color Audit — Check for wrong #E4916E in all views
# ============================================================
print("\n=== 11. Wrong Color (#E4916E) Scan ===")
all_views_with_wrong_color = sr("ir.ui.view", [
    ["arch_db", "ilike", "E4916E"], ["active", "=", True]
], ["name", "key"])
audit["wrong_color_views"] = []
for v in all_views_with_wrong_color:
    print(f"  ⚠ id={v['id']} key={v['key']} name={v['name']}")
    audit["wrong_color_views"].append({"id": v["id"], "key": v["key"], "name": v["name"]})
print(f"  Total views with #E4916E: {len(all_views_with_wrong_color)}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("AUDIT SUMMARY")
print("=" * 60)
print(f"  CSS Views: {len(audit['css_views'])} found")
print(f"  Websites: {len(audit['websites'])}")
print(f"  Menu Items: {len(audit['menus'])}")
print(f"  Published Pages: {len(audit['published_pages'])}")
print(f"  Products Published: {audit['products']['published']}")
print(f"  Zero-Price Published: {audit['products']['zero_price_published']}")
print(f"  Top-Level Categories: {len(audit['categories'])}")
print(f"  Website Modules: {len(audit['modules'])}")
print(f"  Views with wrong #E4916E: {len(audit['wrong_color_views'])}")

# Save audit JSON
audit_path = "/tmp/inzense_audit_baseline.json"
with open(audit_path, "w") as f:
    json.dump(audit, f, ensure_ascii=False, indent=2, default=str)
print(f"\n  Audit saved to: {audit_path}")
print("\nPhase 0 complete.")
