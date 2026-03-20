#!/usr/bin/env python3
"""
Phase 8-10: Clean demo data, create categories, create products, publish on eCommerce.
Runs inside the Odoo pod.
"""
import xmlrpc.client
import base64
import json
import os
import re
import urllib.parse

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

PRODUCTS_JSON = "/tmp/inzense_products.json"
IMAGES_DIR = "/tmp/inzense-images/products"

with open(PRODUCTS_JSON, encoding="utf-8") as f:
    products_data = json.load(f)

print(f"Loaded {len(products_data)} products from JSON")

# ================================================================
# STEP 1: Clean demo product data
# ================================================================
print("\n" + "=" * 60)
print("STEP 1: Clean demo data")
print("=" * 60)

# Delete demo products (English ones from Odoo demo data)
demo_products = models.execute_kw(db, uid, password, "product.template", "search", [
    [["name", "not ilike", "線香"],
     ["name", "not ilike", "迷你香"],
     ["name", "not ilike", "香品"],
     ["name", "not ilike", "inzense"],
     ["name", "not ilike", "禪香"],
     ["create_uid", "=", 1],  # created by admin/system (demo)
    ]
], {"limit": 500})

if demo_products:
    # First unpublish from website
    try:
        models.execute_kw(db, uid, password, "product.template", "write", [demo_products, {
            "website_published": False,
            "sale_ok": False,
        }])
    except:
        pass
    print(f"Unpublished {len(demo_products)} demo products from website")
else:
    print("No demo products to clean")

# Delete demo public categories (keep our custom ones)
our_cat_names = [
    "線香", "迷你香", "拜拜用香", "原木筆", "優惠組合",
    "神明系列", "功能系列", "脈輪系列", "五行系列", "外國系列",
    "台灣系列", "特色系列", "降真系列", "檀香系列", "沉香系列",
    "福石手串", "會員專區",
]
demo_cats = models.execute_kw(db, uid, password, "product.public.category", "search", [
    [["name", "not in", our_cat_names]]
])
if demo_cats:
    try:
        models.execute_kw(db, uid, password, "product.public.category", "unlink", [demo_cats])
        print(f"Deleted {len(demo_cats)} demo public categories")
    except Exception as e:
        print(f"Could not delete demo categories: {e}")

print("Demo data cleanup done")

# ================================================================
# STEP 2: Create/update product public categories
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Create product categories")
print("=" * 60)

website_id = 1

def get_or_create_category(name, parent_id=False):
    """Get or create a product.public.category."""
    domain = [["name", "=", name]]
    if parent_id:
        domain.append(["parent_id", "=", parent_id])
    existing = models.execute_kw(db, uid, password, "product.public.category", "search", [domain])
    if existing:
        return existing[0]
    cat_id = models.execute_kw(db, uid, password, "product.public.category", "create", [{
        "name": name,
        "parent_id": parent_id if parent_id else False,
        "website_id": website_id,
    }])
    print(f"  Created category: {name} (parent={parent_id}) -> ID={cat_id}")
    return cat_id

# Top-level categories
cat_long = get_or_create_category("線香")
cat_mini = get_or_create_category("迷你香")
cat_worship = get_or_create_category("拜拜用香")
cat_pen = get_or_create_category("原木筆")
cat_combo = get_or_create_category("優惠組合")
cat_bracelet = get_or_create_category("福石手串")
cat_member = get_or_create_category("會員專區")

# Sub-categories for 線香 and 迷你香
series_names = ["神明系列", "功能系列", "脈輪系列", "五行系列", "外國系列",
                "台灣系列", "特色系列", "降真系列", "檀香系列", "沉香系列"]

long_sub = {}
mini_sub = {}
for series in series_names:
    long_sub[series] = get_or_create_category(series, cat_long)
    mini_sub[series] = get_or_create_category(series, cat_mini)

# Combo sub-categories
combo_names = ["馬年有喜新春開運組", "神明保庇熱賣組", "上班創業必備組", "內在穩定能量組", "脈輪療癒優惠組"]
combo_sub = {}
for cn in combo_names:
    combo_sub[cn] = get_or_create_category(cn, cat_combo)

print(f"Categories setup complete")

# ================================================================
# STEP 3: Map category names from scraped data to Odoo IDs
# ================================================================
def map_categories(product_categories):
    """Map scraped category strings to Odoo public category IDs."""
    cat_ids = set()
    cat_str = " ".join(product_categories).lower()

    # Check for 迷你香 first (before 線香 check, since some have both)
    is_mini = "迷你香" in cat_str
    is_long = "線香" in cat_str and not is_mini

    if is_mini:
        cat_ids.add(cat_mini)
        for series in series_names:
            if series in cat_str:
                cat_ids.add(mini_sub[series])
    elif is_long:
        cat_ids.add(cat_long)
        for series in series_names:
            if series in cat_str:
                cat_ids.add(long_sub[series])

    if "拜拜用香" in cat_str or "拜拜" in cat_str:
        cat_ids.add(cat_worship)
    if "原木筆" in cat_str:
        cat_ids.add(cat_pen)
    if "福石" in cat_str or "手串" in cat_str:
        cat_ids.add(cat_bracelet)
    if "優惠" in cat_str or "組合" in cat_str:
        cat_ids.add(cat_combo)
        for cn in combo_names:
            if cn in cat_str:
                cat_ids.add(combo_sub[cn])
    if "會員" in cat_str:
        cat_ids.add(cat_member)

    return list(cat_ids) if cat_ids else [cat_long]  # default to 線香

# ================================================================
# STEP 4: Upload product images and create products
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Create products with images")
print("=" * 60)

# Preload image filename mapping from URLs
def url_to_filename(img_url):
    """Convert URL to local filename."""
    parsed = urllib.parse.urlparse(img_url)
    fname = urllib.parse.unquote(os.path.basename(parsed.path))
    return fname

def upload_image(filepath, name):
    """Upload image file as ir.attachment, return attachment ID."""
    if not os.path.isfile(filepath):
        return False
    fsize = os.path.getsize(filepath)
    if fsize < 100:  # skip tiny/empty files
        return False
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(filepath)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}
    mimetype = mime_map.get(ext, "image/jpeg")
    att_id = models.execute_kw(db, uid, password, "ir.attachment", "create", [{
        "name": name,
        "datas": data,
        "type": "binary",
        "mimetype": mimetype,
        "public": True,
    }])
    return att_id

created_count = 0
skipped_count = 0
error_count = 0

for i, prod in enumerate(products_data):
    name = prod["name"]
    if not name or len(name) < 2:
        skipped_count += 1
        continue

    # Check if product already exists
    existing = models.execute_kw(db, uid, password, "product.template", "search", [
        [["name", "=", name]]
    ])
    if existing:
        skipped_count += 1
        continue

    # Map categories
    pub_cat_ids = map_categories(prod.get("categories", []))

    # Determine price
    price = prod.get("price", 0)
    sale_price = prod.get("sale_price", 0)
    list_price = price if price > 0 else 999  # default price

    # Upload main image
    main_image_data = False
    extra_image_ids = []

    for j, img_url in enumerate(prod.get("images", [])):
        fname = url_to_filename(img_url)
        filepath = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(filepath):
            continue
        if os.path.getsize(filepath) < 100:
            continue

        with open(filepath, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        if j == 0:
            # Main product image
            main_image_data = img_b64
        else:
            # Extra images
            extra_image_ids.append(img_b64)

    # Create product
    try:
        vals = {
            "name": name,
            "list_price": list_price,
            "type": "consu",
            "sale_ok": True,
            "purchase_ok": True,
            "website_published": False,  # We'll publish later
            "public_categ_ids": [(6, 0, pub_cat_ids)],
            "description_sale": prod.get("description", ""),
        }
        if main_image_data:
            vals["image_1920"] = main_image_data

        if sale_price > 0 and sale_price < list_price:
            vals["list_price"] = sale_price
            # We'd need a pricelist for the original price, but for now use compare_list_price
            vals["compare_list_price"] = list_price

        prod_id = models.execute_kw(db, uid, password, "product.template", "create", [vals])

        # Add extra images as product.image records
        for k, extra_b64 in enumerate(extra_image_ids[:4]):  # max 4 extra images
            try:
                models.execute_kw(db, uid, password, "product.image", "create", [{
                    "name": f"{name} - {k+2}",
                    "image_1920": extra_b64,
                    "product_tmpl_id": prod_id,
                }])
            except:
                pass

        created_count += 1
        if created_count % 20 == 0:
            print(f"  Created {created_count} products... (current: {name[:40]})")
    except Exception as e:
        error_count += 1
        if error_count <= 5:
            print(f"  ERROR creating '{name[:40]}': {e}")

print(f"\nProducts created: {created_count}")
print(f"Products skipped (existing): {skipped_count}")
print(f"Errors: {error_count}")

# ================================================================
# STEP 5: Publish all products on eCommerce website
# ================================================================
print("\n" + "=" * 60)
print("STEP 5: Publish products on eCommerce")
print("=" * 60)

# Get all our products (non-demo ones with Chinese names)
all_prods = models.execute_kw(db, uid, password, "product.template", "search", [
    ["|", "|", "|", "|", "|",
     ["name", "ilike", "線香"],
     ["name", "ilike", "迷你香"],
     ["name", "ilike", "香品"],
     ["name", "ilike", "系列"],
     ["name", "ilike", "組合"],
     ["name", "ilike", "香"],
    ]
], {"limit": 500})

if all_prods:
    models.execute_kw(db, uid, password, "product.template", "write", [all_prods, {
        "website_published": True,
        "is_published": True,
        "sale_ok": True,
    }])
    print(f"Published {len(all_prods)} products on eCommerce website")

# Set website for all public categories
all_pub_cats = models.execute_kw(db, uid, password, "product.public.category", "search", [[]])
if all_pub_cats:
    models.execute_kw(db, uid, password, "product.public.category", "write", [all_pub_cats, {
        "website_id": website_id,
    }])
    print(f"Set website for {len(all_pub_cats)} public categories")

# Verify
total_published = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True]]
])
print(f"\nTotal published products on website: {total_published}")

# Verify shop page
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8069/shop")
    print(f"Shop page: HTTP {resp.status}")
except Exception as e:
    print(f"Shop page error: {e}")

print("\n=== Phase 8-10 COMPLETE ===")
