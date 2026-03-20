#!/usr/bin/env python3
"""Fix product prices - prices were stored as TWD values in USD currency field.
Change pricelists back to USD (matching stored list_price) OR adjust exchange rate."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Check current state
company = models.execute_kw(db, uid, password, "res.company", "read", [[1], ["currency_id"]])
print(f"Company currency: {company[0]['currency_id']}")

sample = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["website_published", "=", True], ["image_1920", "!=", False]]
], {"fields": ["name", "list_price"], "limit": 5, "order": "name"})
print("Sample products (list_price):")
for p in sample:
    print(f"  {p['name'][:50]} - {p['list_price']}")

# The issue: list_price is stored in company currency (USD=1).
# We scraped TWD prices and stored them directly in list_price.
# e.g. list_price=999 means USD 999, which converts to TWD 32,000!
#
# Solution: Set pricelist currency back to USD (=company currency),
# which means prices display as-is without conversion.
# Then change the currency SYMBOL to show NT$ instead of $.

# Get USD currency
usd_ids = models.execute_kw(db, uid, password, "res.currency", "search", [[["name", "=", "USD"]]])
usd_id = usd_ids[0] if usd_ids else 1

# Update all pricelists to use USD (company currency = no conversion)
pricelist_ids = models.execute_kw(db, uid, password, "product.pricelist", "search", [[]])
for pl_id in pricelist_ids:
    try:
        models.execute_kw(db, uid, password, "product.pricelist", "write", [[pl_id], {
            "currency_id": usd_id,
        }])
    except Exception as e:
        print(f"  Pricelist {pl_id}: {e}")

print(f"Set {len(pricelist_ids)} pricelists to USD (no conversion)")

# Now change USD symbol to NT$ so it displays correctly
models.execute_kw(db, uid, password, "res.currency", "write", [[usd_id], {
    "symbol": "NT$",
    "position": "before",
    "decimal_places": 0,
    "rounding": 1.0,
}])
print("Changed USD display symbol to 'NT$' with 0 decimal places")

# Verify
pl_data = models.execute_kw(db, uid, password, "product.pricelist", "search_read", [
    []
], {"fields": ["name", "currency_id"]})
for pl in pl_data:
    print(f"  Pricelist: {pl['name']} -> {pl['currency_id']}")

# Check a product price display
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/shop")
content = resp.read().decode()
import re
prices = re.findall(r'oe_currency_value"[^>]*>([^<]+)', content)
print(f"\nShop page prices: {prices[:5]}")

# Check if NT$ shows
nt_display = "NT$" in content
print(f"NT$ symbol on shop: {nt_display}")

print("\n=== Price fix done ===")
