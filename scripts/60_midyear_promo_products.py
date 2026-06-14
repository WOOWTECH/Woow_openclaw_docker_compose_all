#!/usr/bin/env python3
"""
Phase 60: Mid-year promotion setup.

1. Enable Pricelist and Loyalty features.
2. Create gift/service products in 贈品系列 category.
3. Verify all products.
"""
import xmlrpc.client
import time

URL = "http://localhost:8069"
DB = "inzense"
PWD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(DB, "admin", PWD, {})
assert uid, "Auth failed"
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


def search(model, domain, limit=0):
    return m.execute_kw(DB, uid, PWD, model, "search", [domain], {"limit": limit})


def search_read(model, domain, fields, limit=0):
    return m.execute_kw(DB, uid, PWD, model, "search_read", [domain],
                        {"fields": fields, "limit": limit})


def create(model, vals):
    return m.execute_kw(DB, uid, PWD, model, "create", [vals])


def write(model, ids, vals):
    return m.execute_kw(DB, uid, PWD, model, "write", [ids, vals])


def read_rec(model, ids, fields):
    return m.execute_kw(DB, uid, PWD, model, "read", [ids, fields])


# ================================================================
# STEP 1: Enable Pricelist and Loyalty features
# ================================================================
print("\n" + "=" * 60)
print("STEP 1: Enable Pricelist and Loyalty features")
print("=" * 60)

# Odoo 18: use group_product_pricelist (no group_sale_pricelist)
# Try settings wizard first, then fallback to ir.config_parameter
try:
    config_id = create("res.config.settings", {})
    print(f"  Created res.config.settings id={config_id}")

    # Try to discover which pricelist fields exist
    settings_fields = m.execute_kw(DB, uid, PWD, "res.config.settings", "fields_get",
                                   [], {"attributes": ["string", "type"]})
    pricelist_fields = {k: v for k, v in settings_fields.items()
                        if "pricelist" in k.lower()}
    loyalty_fields = {k: v for k, v in settings_fields.items()
                      if "loyalty" in k.lower()}
    print(f"  Pricelist-related fields: {list(pricelist_fields.keys())}")
    print(f"  Loyalty-related fields: {list(loyalty_fields.keys())}")

    settings_vals = {}
    if "group_product_pricelist" in pricelist_fields:
        settings_vals["group_product_pricelist"] = True
    if "group_sale_pricelist" in pricelist_fields:
        settings_vals["group_sale_pricelist"] = True
    if "module_loyalty" in loyalty_fields:
        settings_vals["module_loyalty"] = True

    if settings_vals:
        write("res.config.settings", [config_id], settings_vals)
        print(f"  Wrote settings: {list(settings_vals.keys())}")
        m.execute_kw(DB, uid, PWD, "res.config.settings", "execute", [[config_id]])
        print("  Executed settings -- OK")
    else:
        print("  No matching fields found, using fallback")
        raise Exception("No matching fields")

except Exception as e:
    print(f"  Settings wizard: {e}")
    print("  Falling back to ir.config_parameter ...")
    params_to_set = [
        ("sale.use_pricelist", "True"),
        ("product.product_pricelist_setting", "percentage"),
    ]
    for key, val in params_to_set:
        try:
            m.execute_kw(DB, uid, PWD, "ir.config_parameter", "set_param", [key, val])
            print(f"  Set {key} = {val}")
        except Exception as e2:
            print(f"  Failed to set {key}: {e2}")

# Verify pricelist param
try:
    val = m.execute_kw(DB, uid, PWD, "ir.config_parameter", "get_param",
                       ["sale.use_pricelist"])
    print(f"  sale.use_pricelist = {val}")
except Exception:
    pass

# Install loyalty module if needed
print("\n  Checking loyalty module...")
try:
    loyalty_mod = search_read("ir.module.module",
                              [["name", "=", "loyalty"]],
                              ["id", "state"])
    if loyalty_mod:
        state = loyalty_mod[0]["state"]
        print(f"  loyalty module state: {state}")
        if state not in ("installed", "to upgrade"):
            mod_id = loyalty_mod[0]["id"]
            m.execute_kw(DB, uid, PWD, "ir.module.module", "button_immediate_install",
                         [[mod_id]])
            print("  loyalty module install triggered")
    else:
        print("  loyalty module not found in registry")
except Exception as e:
    print(f"  loyalty module check: {e}")


# ================================================================
# STEP 2: Find or create 贈品系列 categories
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Find/create 贈品系列 categories")
print("=" * 60)

# --- product.category (internal) ---
gift_cats = search("product.category", [["name", "=", "贈品系列"]])
if gift_cats:
    gift_cat = gift_cats[0]
    print(f"  product.category  '贈品系列' exists: id={gift_cat}")
else:
    gift_cat = create("product.category", {"name": "贈品系列"})
    print(f"  product.category  '贈品系列' created: id={gift_cat}")

# --- product.public.category (eCommerce) ---
gift_pub_cats = search("product.public.category", [["name", "=", "贈品系列"]])
if gift_pub_cats:
    gift_pub_cat = gift_pub_cats[0]
    print(f"  product.public.category '贈品系列' exists: id={gift_pub_cat}")
else:
    gift_pub_cat = create("product.public.category", {"name": "贈品系列"})
    print(f"  product.public.category '贈品系列' created: id={gift_pub_cat}")

# --- pos.category ---
gift_pos_cats = search("pos.category", [["name", "=", "贈品系列"]])
if gift_pos_cats:
    gift_pos_cat = gift_pos_cats[0]
    print(f"  pos.category      '贈品系列' exists: id={gift_pos_cat}")
else:
    gift_pos_cat = create("pos.category", {"name": "贈品系列"})
    print(f"  pos.category      '贈品系列' created: id={gift_pos_cat}")


# ================================================================
# STEP 3: Define products
# ================================================================
PHYSICAL_GIFTS = [
    ("GIFT-AMBER-CANDY",      "特製琥珀糖",                             200,   80),
    ("GIFT-WAGASHI",           "特製和菓子",                             250,  100),
    ("GIFT-SANDALWOOD-BLOCK",  "印度老山檀香大塊料",                     2000,  800),
    ("GIFT-PUERH-CAKE",        "千年古樹普洱茶餅",                       1500,  600),
    ("GIFT-BLACK-TEA-CAKE",    "千年古樹紅茶餅",                         1500,  600),
    ("GIFT-WHITE-TEA-CAKE",    "千年古樹白茶餅",                         1500,  600),
    ("COMBO-MINI-3",           "功能迷你香三入組合（幸運+善緣+財神）",    1050,  450),
    ("GIFT-INCENSE-BOX",       "木製臥香盒香插組",                       300,  120),
]

SERVICE_GIFTS = [
    ("SVC-DIVINATION-1",    "占卜1題",                     300,   300),
    ("SVC-DIVINATION-2",    "占卜2題",                     500,   500),
    ("SVC-DIVINATION-3",    "占卜3題",                     800,   800),
    ("SVC-ANNUAL-CONSULT",  "流年諮詢1小時",               1280,  1280),
    ("SVC-FLOWER-PRAYER",   "鮮花代俸祈福（1人份）",       500,   500),
    ("SVC-CHANTING-36",     "誦經36遍",                    800,   800),
    ("SVC-CHANTING-72",     "誦經72遍",                    1280,  1280),
    ("SVC-WORKSHOP-BASIC",  "天然香椎手作課（初階）",       1500,   800),
    ("SVC-WORKSHOP-ADV",    "天然香椎手作課（進階）",       2500,  1200),
]


# ================================================================
# STEP 4: Create products (get-or-create by default_code)
# ================================================================
print("\n" + "=" * 60)
print("STEP 3: Create gift/service products")
print("=" * 60)

created_ids = []
skipped = 0


def ensure_product(sku, name, price, cost, is_service):
    """Get-or-create a product.template by default_code (SKU)."""
    global skipped

    # Search by default_code OR name to handle partial creates
    existing = search_read("product.template",
                           ["|", ["default_code", "=", sku], ["name", "=", name]],
                           ["id", "name", "default_code"])
    if existing:
        pid = existing[0]["id"]
        print(f"  EXISTS  {sku:25s}  id={pid}  ({existing[0]['name']})")
        # Ensure fields are up to date
        update_vals = {
            "default_code": sku,
            "list_price": price,
            "standard_price": cost,
            "categ_id": gift_cat,
            "public_categ_ids": [(6, 0, [gift_pub_cat])],
            "pos_categ_ids": [(6, 0, [gift_pos_cat])],
            "available_in_pos": True,
            "sale_ok": True,
        }
        # Try website published fields (may not exist if website module not installed)
        try:
            write("product.template", [pid], update_vals)
        except Exception:
            pass
        try:
            write("product.template", [pid], {
                "website_published": True,
                "is_published": True,
            })
        except Exception:
            pass
        skipped += 1
        created_ids.append(pid)
        return pid

    prod_type = "service" if is_service else "consu"
    vals = {
        "name": name,
        "default_code": sku,
        "barcode": sku,
        "list_price": price,
        "standard_price": cost,
        "type": prod_type,
        "sale_ok": True,
        "purchase_ok": is_service,
        "categ_id": gift_cat,
        "public_categ_ids": [(6, 0, [gift_pub_cat])],
        "pos_categ_ids": [(6, 0, [gift_pos_cat])],
        "available_in_pos": True,
    }
    pid = create("product.template", vals)
    print(f"  CREATE  {sku:25s}  id={pid}  {name}")

    # Try to set website published
    try:
        write("product.template", [pid], {
            "website_published": True,
            "is_published": True,
        })
    except Exception:
        pass

    # For physical products, set is_storable after creation
    if not is_service:
        try:
            write("product.template", [pid], {"is_storable": True})
            print(f"          -> set is_storable=True")
        except Exception as e:
            print(f"          -> is_storable note: {e}")

    created_ids.append(pid)
    return pid


print("\n--- Physical gifts (storable) ---")
for sku, name, price, cost in PHYSICAL_GIFTS:
    ensure_product(sku, name, price, cost, is_service=False)

print("\n--- Service gifts ---")
for sku, name, price, cost in SERVICE_GIFTS:
    ensure_product(sku, name, price, cost, is_service=True)


# ================================================================
# STEP 5: Create product.barcode QR records
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Create product.barcode QR records")
print("=" * 60)

try:
    all_skus = [sku for sku, *_ in PHYSICAL_GIFTS] + [sku for sku, *_ in SERVICE_GIFTS]
    variants = search_read("product.product",
                           [["default_code", "in", all_skus]],
                           ["id", "name", "default_code", "barcode"])
    print(f"  Found {len(variants)} product.product variants")

    barcode_created = 0
    barcode_model_exists = True
    for v in variants:
        sku = v["default_code"]
        if not sku or not barcode_model_exists:
            continue
        try:
            existing_bc = search("product.barcode",
                                 [["product_id", "=", v["id"]]])
            if existing_bc:
                continue
            create("product.barcode", {
                "product_id": v["id"],
                "barcode": sku,
            })
            barcode_created += 1
        except Exception as e:
            err_str = str(e).lower()
            if "product.barcode" in err_str or "not found" in err_str or "no model" in err_str:
                print(f"  product.barcode model not available, skipping")
                barcode_model_exists = False
            else:
                print(f"  barcode for {sku}: {e}")

    print(f"  Created {barcode_created} product.barcode records")
except Exception as e:
    print(f"  product.barcode step skipped: {e}")


# ================================================================
# STEP 6: Verification
# ================================================================
print("\n" + "=" * 60)
print("STEP 5: VERIFICATION")
print("=" * 60)

all_skus = [sku for sku, *_ in PHYSICAL_GIFTS] + [sku for sku, *_ in SERVICE_GIFTS]

products = search_read("product.template",
                       [["default_code", "in", all_skus]],
                       ["id", "name", "default_code", "list_price",
                        "standard_price", "type", "available_in_pos",
                        "categ_id", "sale_ok"],
                       limit=50)

print(f"\n  {'SKU':25s} {'Name':35s} {'Price':>7s} {'Cost':>7s} {'Type':10s} {'POS':>4s}")
print("  " + "-" * 93)
for p in sorted(products, key=lambda x: x["default_code"] or ""):
    sku = p["default_code"] or "N/A"
    name = p["name"][:35]
    price = f"{p['list_price']:.0f}"
    cost = f"{p['standard_price']:.0f}"
    ptype = p["type"]
    pos = "Y" if p.get("available_in_pos") else "N"
    print(f"  {sku:25s} {name:35s} {price:>7s} {cost:>7s} {ptype:10s} {pos:>4s}")

total_expected = len(PHYSICAL_GIFTS) + len(SERVICE_GIFTS)
total_found = len(products)
print(f"\n  Expected: {total_expected}  |  Found: {total_found}  |  "
      f"New: {total_found - skipped}  |  Updated: {skipped}")

if total_found == total_expected:
    print("\n  *** ALL 17 PRODUCTS VERIFIED SUCCESSFULLY ***")
else:
    missing = set(all_skus) - {p["default_code"] for p in products}
    print(f"\n  *** WARNING: Missing products: {missing} ***")

# POS check
pos_count = sum(1 for p in products if p.get("available_in_pos"))
print(f"\n  POS availability: {pos_count}/{total_found} products available in POS")

print("\nDone!")
