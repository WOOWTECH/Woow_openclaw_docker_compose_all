#!/usr/bin/env python3
"""Debug the product page error message."""
import urllib.request
import re

resp = urllib.request.urlopen("http://localhost:8069/shop/xian-xiang-gong-neng-xi-lie-pai-han-xiang-116")
html = resp.read().decode()

# Find the error message context
idx = html.find("此組合不存在")
if idx > 0:
    context = html[max(0,idx-500):idx+300]
    context = re.sub(r'\s+', ' ', context)
    print("Error context:")
    print(context[:800])
    print()
else:
    print("'此組合不存在' NOT found in page")

# Check for css_not_available
idx2 = html.find("css_not_available_msg")
if idx2 > 0:
    context2 = html[max(0,idx2-200):idx2+400]
    context2 = re.sub(r'\s+', ' ', context2)
    print("css_not_available context:")
    print(context2[:600])
else:
    print("css_not_available_msg NOT found")

# Check if add to cart exists
print(f"\nHas 加入購物車: {'加入購物車' in html}")
print(f"Has js_add_cart: {'js_add_cart' in html}")
print(f"Has a-submit: {'a-submit' in html}")

# Check the product_detail section
detail = re.search(r'id="product_detail"(.*?)id="o_product_terms', html, re.DOTALL)
if detail:
    d = detail.group(1)
    d_clean = re.sub(r'<[^>]+>', ' ', d)
    d_clean = re.sub(r'\s+', ' ', d_clean).strip()
    print(f"\nProduct detail text: {d_clean[:500]}")
