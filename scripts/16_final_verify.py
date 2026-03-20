#!/usr/bin/env python3
"""Final verification of all configuration."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Chart of accounts
print("--- Taiwan Chart of Accounts ---")
accounts = models.execute_kw(db, uid, password, "account.account", "search_read", [
    []
], {"fields": ["code", "name"], "limit": 15, "order": "code"})
print(f"Total shown: {len(accounts)}")
for a in accounts:
    print(f"  {a['code']} - {a['name']}")

# l10n_tw
tw_mod = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["name", "=", "l10n_tw"]]
], {"fields": ["state", "shortdesc"]})
print(f"\nl10n_tw: {tw_mod}")

# Active taxes
print("\n--- Active Taxes ---")
taxes = models.execute_kw(db, uid, password, "account.tax", "search_read", [
    [["active", "=", True]]
], {"fields": ["name", "amount", "type_tax_use"]})
for t in taxes:
    print(f"  {t['name']} ({t['amount']}%) - {t['type_tax_use']}")

# Products
print("\n--- Products ---")
active = models.execute_kw(db, uid, password, "product.template", "search_count", [[["active", "=", True]]])
published = models.execute_kw(db, uid, password, "product.template", "search_count", [[["website_published", "=", True]]])
with_img = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True], ["image_1920", "!=", False]]
])
print(f"  Active: {active}")
print(f"  Published on eCommerce: {published}")
print(f"  With images: {with_img}")

# Sample products
sample = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["website_published", "=", True], ["image_1920", "!=", False]]
], {"fields": ["name", "list_price", "public_categ_ids"], "limit": 8, "order": "name"})
print("\n  Sample published products:")
for p in sample:
    cats = p["public_categ_ids"]
    print(f"    {p['name'][:50]} - NT${p['list_price']} (cats={len(cats)})")

# Company
company = models.execute_kw(db, uid, password, "res.company", "read", [[1],
    ["name", "country_id", "currency_id", "phone", "email", "website", "street", "city", "zip", "mobile"]])
c = company[0]
print(f"\n--- 公司資訊 ---")
print(f"  名稱: {c['name']}")
print(f"  地址: {c['zip']} {c['street']}")
print(f"  城市: {c['city']}")
print(f"  國家: {c['country_id']}")
print(f"  幣別: {c['currency_id']}")
print(f"  客服電話: {c['phone']}")
print(f"  業務電話: {c['mobile']}")
print(f"  信箱: {c['email']}")
print(f"  網站: {c['website']}")

# Key modules
mods = ["l10n_tw", "account", "mrp", "point_of_sale", "stock", "website_sale", "purchase", "sale_management", "loyalty", "website_blog", "hr", "crm", "calendar", "mail", "project", "contacts"]
print("\n--- 已安裝模組 ---")
for mname in mods:
    m = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["name", "=", mname]]
    ], {"fields": ["state", "shortdesc"]})
    if m:
        status = "OK" if m[0]["state"] == "installed" else m[0]["state"]
        print(f"  [{status}] {m[0]['shortdesc']}")

# Demo data status
print("\n--- Demo 資料清理狀態 ---")
so = models.execute_kw(db, uid, password, "sale.order", "search_count", [[]])
po = models.execute_kw(db, uid, password, "purchase.order", "search_count", [[]])
partners = models.execute_kw(db, uid, password, "res.partner", "search_count", [[]])
print(f"  銷售訂單: {so}")
print(f"  採購訂單: {po}")
print(f"  聯絡人: {partners}")

# Language
print("\n--- 語言設定 ---")
users = models.execute_kw(db, uid, password, "res.users", "search_read", [
    [["active", "=", True]]
], {"fields": ["name", "lang", "tz"]})
for u in users:
    print(f"  {u['name']}: lang={u['lang']}, tz={u['tz']}")

website = models.execute_kw(db, uid, password, "website", "read", [[1], ["name", "default_lang_id", "domain"]])
print(f"\n  網站: {website[0]['name']}")
print(f"  預設語言: {website[0]['default_lang_id']}")
print(f"  網域: {website[0]['domain']}")

print("\n=== 全部設定完成 ===")
