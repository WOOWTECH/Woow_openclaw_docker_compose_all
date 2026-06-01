#!/usr/bin/env python3
"""
Phase 56: Reorganize product categories based on inventory spreadsheet structure.

New hierarchy:
  主類別 (系列) = top-level categories from the 「系列」 column:
    功能系列, 特色系列, 脈輪系列, 五行系列, 檀香系列, 沉香系列,
    台灣系列, 外國系列, 降真系列, 神明系列

  次類別 (產品型態) = sub-categories from sheet names, nested under each 系列:
    長線香, 迷你香, 拜拜用香, 盤香

Runs inside the Odoo pod or with port-forward.
"""
import xmlrpc.client

URL = "http://localhost:8069"
DB = "inzense"
PWD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, "admin", PWD, {})
assert uid, "Auth failed"
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")

website_id = 1

# ================================================================
# STEP 1: Define new category hierarchy
# ================================================================
print("\n" + "=" * 60)
print("STEP 1: Define new category hierarchy")
print("=" * 60)

# 主類別 (系列) — top level
SERIES = [
    "功能系列",
    "特色系列",
    "脈輪系列",
    "五行系列",
    "檀香系列",
    "沉香系列",
    "台灣系列",
    "外國系列",
    "降真系列",
    "神明系列",
]

# 次類別 (產品型態) — sub-categories under each 系列
PRODUCT_TYPES = [
    "長線香",
    "迷你香",
    "拜拜用香",
    "盤香",
]

# ================================================================
# STEP 2: Delete all existing public categories
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Clean existing public categories")
print("=" * 60)

existing_cats = m.execute_kw(DB, uid, PWD, "product.public.category", "search", [[]])
if existing_cats:
    # Unlink products from categories first
    all_prods = m.execute_kw(DB, uid, PWD, "product.template", "search", [
        [["public_categ_ids", "!=", False]]
    ])
    if all_prods:
        m.execute_kw(DB, uid, PWD, "product.template", "write", [all_prods, {
            "public_categ_ids": [(5, 0, 0)],  # clear all
        }])
        print(f"  Cleared categories from {len(all_prods)} products")

    # Delete children first (to avoid FK constraint)
    children = m.execute_kw(DB, uid, PWD, "product.public.category", "search", [
        [["parent_id", "!=", False]]
    ])
    if children:
        m.execute_kw(DB, uid, PWD, "product.public.category", "unlink", [children])
        print(f"  Deleted {len(children)} child categories")

    parents = m.execute_kw(DB, uid, PWD, "product.public.category", "search", [[]])
    if parents:
        m.execute_kw(DB, uid, PWD, "product.public.category", "unlink", [parents])
        print(f"  Deleted {len(parents)} parent categories")
else:
    print("  No existing categories")

# ================================================================
# STEP 3: Create new category hierarchy
# ================================================================
print("\n" + "=" * 60)
print("STEP 3: Create new category hierarchy")
print("=" * 60)

# Create 主類別 (series) as top-level
series_ids = {}
for series_name in SERIES:
    cat_id = m.execute_kw(DB, uid, PWD, "product.public.category", "create", [{
        "name": series_name,
        "website_id": website_id,
        "sequence": SERIES.index(series_name) + 1,
    }])
    series_ids[series_name] = cat_id
    print(f"  Created 主類別: {series_name} (id={cat_id})")

# Create 次類別 (product types) under each 主類別
sub_ids = {}  # key = (series_name, product_type) -> cat_id
for series_name in SERIES:
    parent_id = series_ids[series_name]
    for pt_name in PRODUCT_TYPES:
        cat_id = m.execute_kw(DB, uid, PWD, "product.public.category", "create", [{
            "name": pt_name,
            "parent_id": parent_id,
            "website_id": website_id,
            "sequence": PRODUCT_TYPES.index(pt_name) + 1,
        }])
        sub_ids[(series_name, pt_name)] = cat_id

print(f"  Created {len(SERIES)} 主類別 × {len(PRODUCT_TYPES)} 次類別 = {len(sub_ids)} sub-categories")

# Also create a top-level "優惠組合" category (not in the series structure)
combo_id = m.execute_kw(DB, uid, PWD, "product.public.category", "create", [{
    "name": "優惠組合",
    "website_id": website_id,
    "sequence": len(SERIES) + 1,
}])
print(f"  Created 主類別: 優惠組合 (id={combo_id})")

# ================================================================
# STEP 4: Assign products to categories
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Assign products to categories")
print("=" * 60)

# Product name mapping rules:
# - "長線香 – XXX" -> product_type=長線香, series from default_code prefix
# - "迷你香 – XXX" -> product_type=迷你香
# - "拜拜用香 – XXX" -> product_type=拜拜用香
# - "盤香 – XXX" -> product_type=盤香

# default_code prefix -> series mapping
CODE_TO_SERIES = {
    "LIE": "功能系列",
    "MIE": "功能系列",
    "LID": "特色系列",
    "MID": "特色系列",
    "LIC": "脈輪系列",
    "MIC": "脈輪系列",
    "LIFE": "五行系列",
    "MIFE": "五行系列",
    "LIS": "檀香系列",
    "MIS": "檀香系列",
    "IS0": "檀香系列",  # IS01x, IS02x, IS04, IS05
    "IS01": "檀香系列",
    "IS02": "檀香系列",
    "IS03": "降真系列",  # IS031, IS032 = 非洲降真檀香
    "IS04": "檀香系列",
    "IS05": "檀香系列",
    "IS06": "沉香系列",  # IS061, IS062 = 柬埔寨沉香
    "IS07": "沉香系列",
    "IS08": "沉香系列",
    "IS09": "沉香系列",
    "LIA": "沉香系列",
    "MIA": "沉香系列",
    "LIT": "台灣系列",
    "MIT": "台灣系列",
    "LIF": "外國系列",
    "MIF": "外國系列",
    "LIAP": "降真系列",
    "MIAP": "降真系列",
    "ICAP": "降真系列",
    "ICS": "檀香系列",
    "ICA": "沉香系列",
    "LIG": "神明系列",
    "MIG": "神明系列",
}

# Product name prefix -> product_type
def get_product_type(name):
    """Determine product type from product name."""
    if name.startswith("長線香"):
        return "長線香"
    elif name.startswith("迷你香"):
        return "迷你香"
    elif name.startswith("拜拜用香"):
        return "拜拜用香"
    elif name.startswith("盤香"):
        return "盤香"
    return None

def get_series_from_code(code):
    """Determine series from default_code prefix."""
    if not code:
        return None
    # Try longer prefixes first (e.g. LIAP before LIA, LIFE before LI)
    for prefix in sorted(CODE_TO_SERIES.keys(), key=len, reverse=True):
        if code.startswith(prefix):
            return CODE_TO_SERIES[prefix]
    return None

# Get all products
all_products = m.execute_kw(DB, uid, PWD, "product.template", "search_read", [
    [["sale_ok", "=", True]]
], {"fields": ["id", "name", "default_code"], "order": "id asc", "limit": 500})

assigned = 0
unmatched = []

for prod in all_products:
    pid = prod["id"]
    name = prod["name"]
    code = prod["default_code"] or ""

    product_type = get_product_type(name)
    series = get_series_from_code(code)

    # Fallback: try to guess series from product name
    if not series:
        name_lower = name
        for s in SERIES:
            if s.replace("系列", "") in name_lower:
                series = s
                break
        # Specific name-based fallback
        if not series:
            if "尤加利" in name:
                series = "外國系列"

    if not product_type or not series:
        # Check if it's a combo product
        if "組" in name or "組合" in name:
            m.execute_kw(DB, uid, PWD, "product.template", "write", [[pid], {
                "public_categ_ids": [(6, 0, [combo_id])],
            }])
            assigned += 1
            continue
        unmatched.append({"id": pid, "name": name, "code": code, "type": product_type, "series": series})
        continue

    # Get category IDs: both the 主類別 and 次類別
    cat_ids = []
    if series in series_ids:
        cat_ids.append(series_ids[series])
    sub_key = (series, product_type)
    if sub_key in sub_ids:
        cat_ids.append(sub_ids[sub_key])

    if cat_ids:
        m.execute_kw(DB, uid, PWD, "product.template", "write", [[pid], {
            "public_categ_ids": [(6, 0, cat_ids)],
        }])
        assigned += 1

print(f"\nAssigned categories to {assigned} products")

if unmatched:
    print(f"\nUnmatched products ({len(unmatched)}):")
    for u in unmatched:
        print(f"  id={u['id']:4d} | code={u['code']:<12} | type={u['type']} | series={u['series']} | {u['name'][:50]}")

# ================================================================
# STEP 5: Verify and report
# ================================================================
print("\n" + "=" * 60)
print("STEP 5: Category report")
print("=" * 60)

# Get all categories with product counts
all_cats = m.execute_kw(DB, uid, PWD, "product.public.category", "search_read", [
    []
], {"fields": ["id", "name", "parent_id", "product_tmpl_ids"], "order": "sequence asc, id asc"})

print(f"\n{'Category':<35} {'ID':>4} {'Products':>8}")
print("-" * 50)

for cat in all_cats:
    parent = cat["parent_id"]
    indent = "  " if parent else ""
    parent_name = f" ({parent[1]})" if parent else ""
    prod_count = len(cat.get("product_tmpl_ids", []))
    print(f"{indent}{cat['name']:<33} {cat['id']:>4} {prod_count:>8}")

print(f"\nTotal categories: {len(all_cats)}")
print(f"Total products assigned: {assigned}")

print("\n=== Phase 56 COMPLETE ===")
