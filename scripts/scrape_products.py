#!/usr/bin/env python3
"""Scrape all product data from inzense.com.tw for Odoo import."""
import json
import re
import sys
import time
import urllib.request
import urllib.parse
import html as html_mod

PRODUCT_URLS_FILE = "/tmp/product_urls.txt"
OUTPUT_FILE = "/tmp/inzense_products.json"
IMAGE_URLS_FILE = "/tmp/product_image_urls.txt"

with open(PRODUCT_URLS_FILE) as f:
    product_urls = [u.strip() for u in f if u.strip()]

print(f"Total product URLs: {len(product_urls)}")

products = []
all_image_urls = set()
errors = []

for i, purl in enumerate(product_urls):
    try:
        req = urllib.request.Request(purl, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        errors.append(f"{purl}: {e}")
        continue

    # Extract product name from og:title or <title>
    name_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if not name_match:
        name_match = re.search(r'<title>([^<]+)</title>', html)
    name = name_match.group(1).strip() if name_match else ""
    # Clean name: remove " - 禪香不二" suffix
    name = re.sub(r'\s*[-–]\s*禪香不二.*$', '', name)
    name = re.sub(r'\s*[-–]\s*Inzense.*$', '', name, flags=re.I)

    # Extract price
    price_match = re.search(r'"price":\s*"?(\d[\d,.]*)"?', html)
    price = 0
    if price_match:
        price = float(price_match.group(1).replace(",", ""))
    else:
        # Try woocommerce price
        price_match2 = re.search(r'class="woocommerce-Price-amount[^"]*"[^>]*>.*?(\d[\d,]*)', html, re.DOTALL)
        if price_match2:
            price = float(price_match2.group(1).replace(",", ""))

    # Extract sale price
    sale_price = 0
    sale_match = re.search(r'"lowPrice":\s*"?(\d[\d,.]*)"?', html)
    if sale_match:
        sale_price = float(sale_match.group(1).replace(",", ""))

    # Extract categories from breadcrumb or JSON-LD
    categories = []
    cat_matches = re.findall(r'"category":\s*"([^"]+)"', html)
    if cat_matches:
        for cm in cat_matches:
            for c in cm.split(" > "):
                c = c.strip()
                if c and c not in categories and c != "首頁":
                    categories.append(c)

    # Extract description
    desc_match = re.search(r'<meta\s+property="og:description"\s+content="([^"]*)"', html)
    description = html_mod.unescape(desc_match.group(1).strip()) if desc_match else ""

    # Extract images - og:image and gallery
    images = []
    og_img = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
    if og_img:
        images.append(og_img.group(1))

    # Gallery images from woocommerce
    gallery_imgs = re.findall(r'data-large_image="(https://www\.inzense\.com\.tw/wp-content/uploads/[^"]+)"', html)
    images.extend(gallery_imgs)

    # Also check src attributes
    src_imgs = re.findall(r'src="(https://www\.inzense\.com\.tw/wp-content/uploads/[^"]+\.(?:jpg|jpeg|png|gif))"', html)
    for si in src_imgs:
        # Skip thumbnails
        if re.search(r'-\d+x\d+\.', si):
            continue
        if si not in images:
            images.append(si)

    # Deduplicate images
    seen = set()
    unique_images = []
    for img in images:
        # Normalize: remove -scaled suffix variations
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
            all_image_urls.add(img)

    # Extract SKU
    sku_match = re.search(r'"sku":\s*"([^"]*)"', html)
    sku = sku_match.group(1) if sku_match else ""

    product = {
        "url": purl,
        "name": name,
        "price": price,
        "sale_price": sale_price,
        "categories": categories,
        "description": description,
        "images": unique_images,
        "sku": sku,
    }
    products.append(product)

    if (i + 1) % 20 == 0:
        print(f"  Processed {i+1}/{len(product_urls)} products...")
        time.sleep(0.5)

# Save products JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

# Save all unique image URLs
with open(IMAGE_URLS_FILE, "w") as f:
    for u in sorted(all_image_urls):
        f.write(u + "\n")

print(f"\n=== Scraping Complete ===")
print(f"Products scraped: {len(products)}")
print(f"Errors: {len(errors)}")
print(f"Unique image URLs: {len(all_image_urls)}")
print(f"Products JSON: {OUTPUT_FILE}")
print(f"Image URLs: {IMAGE_URLS_FILE}")

if errors:
    print(f"\nFirst 5 errors:")
    for e in errors[:5]:
        print(f"  {e}")

# Print summary by category
cat_count = {}
for p in products:
    for c in p["categories"]:
        cat_count[c] = cat_count.get(c, 0) + 1
print(f"\nCategories found:")
for c, n in sorted(cat_count.items(), key=lambda x: -x[1])[:20]:
    print(f"  {c}: {n} products")
