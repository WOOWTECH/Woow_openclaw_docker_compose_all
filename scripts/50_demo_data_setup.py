#!/usr/bin/env python3
"""
Inzense Odoo 18 — Demo Data Setup
Run with: kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
Then: python3 scripts/50_demo_data_setup.py
"""
import xmlrpc.client
import base64
import os
from datetime import datetime, timedelta

# --- Connection ---
URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
print(f"Connected as uid={uid}")


def execute(model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASSWORD, model, method, *args, **kwargs)


def search(model, domain, **kwargs):
    return execute(model, "search", [domain], **kwargs)


def search_read(model, domain, fields=None, **kwargs):
    kw = {}
    if fields:
        kw["fields"] = fields
    kw.update(kwargs)
    return execute(model, "search_read", [domain], kw)


def create(model, vals):
    return execute(model, "create", [vals])


def write(model, ids, vals):
    return execute(model, "write", [ids, vals])


# ============================================================
# Phase 1: Install modules
# ============================================================
print("\n=== Phase 1: Install modules ===")

execute("ir.module.module", "update_list", [])

MODULES_TO_INSTALL = ["sale_management", "account", "point_of_sale", "stock"]
for mod_name in MODULES_TO_INSTALL:
    mod_ids = search("ir.module.module", [["name", "=", mod_name]])
    if not mod_ids:
        print(f"  ERROR: Module {mod_name} not found!")
        continue
    state = search_read("ir.module.module", [["id", "=", mod_ids[0]]], ["state"])[0]["state"]
    if state == "installed":
        print(f"  {mod_name}: already installed")
    else:
        print(f"  Installing {mod_name}...")
        execute("ir.module.module", "button_immediate_install", [mod_ids])
        print(f"  {mod_name}: installed")

print("Phase 1 complete.")

# ============================================================
# Phase 2: Company setup
# ============================================================
print("\n=== Phase 2: Company setup ===")

# Get TWD currency (may be inactive, search with active_test=False)
twd_ids = models.execute_kw(DB, uid, PASSWORD, "res.currency", "search",
                             [[["name", "=", "TWD"]]],
                             {"context": {"active_test": False}})
if not twd_ids:
    print("  WARNING: TWD currency not found, skipping currency setup")
else:
    write("res.currency", twd_ids, {"active": True})
    print(f"  TWD currency activated: id={twd_ids[0]}")

# Get Taiwan country
tw_ids = search("res.country", [["code", "=", "TW"]])

# Update main company
company_ids = search("res.company", [["id", "=", 1]])
company_vals = {
    "name": "禪香不二 Inzense",
    "phone": "0926-926-851",
    "street": "光明路240號2樓之8",
    "city": "台北市北投區",
}
if tw_ids:
    company_vals["country_id"] = tw_ids[0]

# Try setting currency (may fail if journal entries exist)
if twd_ids:
    try:
        write("res.company", company_ids, {"currency_id": twd_ids[0]})
        print(f"  Company currency set to TWD")
    except Exception as e:
        print(f"  WARNING: Cannot change currency (journal entries exist): {e}")

write("res.company", company_ids, company_vals)

# Also update the partner record for the company
company_data = search_read("res.company", [["id", "=", 1]], ["partner_id"])
partner_id = company_data[0]["partner_id"][0]
write("res.partner", [partner_id], {
    "name": "禪香不二 Inzense",
    "phone": "0926-926-851",
    "street": "光明路240號2樓之8",
    "city": "台北市北投區",
})

print("  Company updated: 禪香不二 Inzense")
print("Phase 2 complete.")

# ============================================================
# Phase 3: Products
# ============================================================
print("\n=== Phase 3: Create products ===")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(PROJECT_DIR, "images", "products")


def load_image(filename):
    """Load image file and return base64 encoded string."""
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    print(f"  WARNING: Image not found: {filepath}")
    return False


# Internal product categories
CATEGORIES = ["功能系列", "脈輪系列", "五行系列", "拜拜用香", "優惠組合", "年節禮盒"]
cat_ids = {}
for cat_name in CATEGORIES:
    existing = search("product.category", [["name", "=", cat_name]])
    if existing:
        cat_ids[cat_name] = existing[0]
    else:
        cat_ids[cat_name] = create("product.category", {"name": cat_name})
    print(f"  Category: {cat_name} (id={cat_ids[cat_name]})")

# Products definition
PRODUCTS = [
    {"name": "線香功能系列 – 善緣香", "price": 899, "category": "功能系列",
     "image": "線香功能系列＿封面圖＿善緣香.jpg"},
    {"name": "線香功能系列 – 財神香", "price": 899, "category": "功能系列",
     "image": "線香功能系列＿封面圖＿財神香.jpg"},
    {"name": "線香功能系列 – 三清檀香", "price": 650, "category": "功能系列",
     "image": "三清檀香.jpg"},
    {"name": "線香脈輪系列 – 心輪香", "price": 750, "category": "脈輪系列",
     "image": "心輪香線香-scaled.jpg"},
    {"name": "線香五行系列 – 木神香", "price": 750, "category": "五行系列",
     "image": "木神香＿封面圖.jpg"},
    {"name": "柬埔寨沉香", "price": 1200, "category": "拜拜用香",
     "image": "柬埔寨沉香.jpg"},
    {"name": "巴拉圭綠檀", "price": 1000, "category": "拜拜用香",
     "image": "巴拉圭綠檀.jpg"},
    {"name": "決策穩心組", "price": 807, "category": "優惠組合",
     "image": "251016-組合系列商品圖_決策穩心組.jpg"},
    {"name": "穩定能量組", "price": 712, "category": "優惠組合",
     "image": "251016-組合系列商品圖_穩定能量組.jpg"},
    {"name": "神馬都順 全能順遂組合", "price": 2888, "category": "年節禮盒",
     "image": "260113-年節禮盒_詳情頁_神馬都順_1（5）-scaled.jpeg"},
]

product_ids = {}  # name -> product.product id
product_tmpl_ids = {}  # name -> product.template id

for p in PRODUCTS:
    existing = search("product.template", [["name", "=", p["name"]]])
    if existing:
        tmpl_id = existing[0]
        print(f"  Product exists: {p['name']} (tmpl_id={tmpl_id})")
    else:
        vals = {
            "name": p["name"],
            "list_price": p["price"],
            "type": "consu",
            "is_storable": True,  # Enable stock tracking in Odoo 18
            "sale_ok": True,
            "purchase_ok": True,
            "categ_id": cat_ids[p["category"]],
            "available_in_pos": True,
        }
        img = load_image(p["image"])
        if img:
            vals["image_1920"] = img
        tmpl_id = create("product.template", vals)
        print(f"  Created: {p['name']} (tmpl_id={tmpl_id})")

    product_tmpl_ids[p["name"]] = tmpl_id
    # Ensure product is storable
    write("product.template", [tmpl_id], {"is_storable": True})
    # Get the product.product id
    pp_ids = search("product.product", [["product_tmpl_id", "=", tmpl_id]])
    if pp_ids:
        product_ids[p["name"]] = pp_ids[0]

print(f"  Total products: {len(product_ids)}")
print("Phase 3 complete.")

# ============================================================
# Phase 4: Portal customer
# ============================================================
print("\n=== Phase 4: Create portal customer ===")

PORTAL_EMAIL = "portal@inzense.com.tw"

existing_partner = search("res.partner", [["email", "=", PORTAL_EMAIL]])
if existing_partner:
    portal_partner_id = existing_partner[0]
    print(f"  Partner exists: id={portal_partner_id}")
else:
    portal_partner_id = create("res.partner", {
        "name": "禪香不二 展示客戶",
        "email": PORTAL_EMAIL,
        "phone": "0912-345-678",
        "customer_rank": 1,
    })
    print(f"  Created partner: id={portal_partner_id}")

# Create portal user
existing_user = search("res.users", [["login", "=", PORTAL_EMAIL]])
if existing_user:
    portal_user_id = existing_user[0]
    print(f"  User exists: id={portal_user_id}")
else:
    # Get portal group
    portal_group = search("res.groups", [["category_id.name", "=", "User types"],
                                          ["name", "like", "Portal"]])
    portal_user_id = create("res.users", {
        "name": "禪香不二 展示客戶",
        "login": PORTAL_EMAIL,
        "password": "portal",
        "partner_id": portal_partner_id,
        "groups_id": [(6, 0, portal_group)] if portal_group else [],
    })
    print(f"  Created user: id={portal_user_id}")

print("Phase 4 complete.")

# ============================================================
# Phase 5: Warehouses and resupply
# ============================================================
print("\n=== Phase 5: Warehouses and resupply routes ===")

# Get or update the default warehouse as central
default_wh = search_read("stock.warehouse", [["company_id", "=", 1]], ["id", "name"])
central_wh_id = default_wh[0]["id"] if default_wh else None

if central_wh_id:
    write("stock.warehouse", [central_wh_id], {
        "name": "禪香不二 中央倉庫",
        "code": "中央",
    })
    print(f"  Updated central warehouse: id={central_wh_id}")

STORE_WAREHOUSES = [
    {"name": "信義旗艦店倉庫", "code": "信義"},
    {"name": "板橋店倉庫", "code": "板橋"},
    {"name": "台中店倉庫", "code": "台中"},
]

store_wh_ids = {}
for wh in STORE_WAREHOUSES:
    existing = search("stock.warehouse", [["name", "=", wh["name"]]])
    if existing:
        store_wh_ids[wh["name"]] = existing[0]
        print(f"  Warehouse exists: {wh['name']} (id={existing[0]})")
    else:
        wh_id = create("stock.warehouse", {
            "name": wh["name"],
            "code": wh["code"],
            "resupply_wh_ids": [(6, 0, [central_wh_id])] if central_wh_id else [],
        })
        store_wh_ids[wh["name"]] = wh_id
        print(f"  Created warehouse: {wh['name']} (id={wh_id})")

print("Phase 5 complete.")

# ============================================================
# Phase 6: POS configuration
# ============================================================
print("\n=== Phase 6: POS configuration ===")

# Create POS categories
POS_CATEGORIES = ["功能系列", "脈輪系列", "五行系列", "拜拜用香", "優惠組合"]
pos_cat_ids = {}
for cat_name in POS_CATEGORIES:
    existing = search("pos.category", [["name", "=", cat_name]])
    if existing:
        pos_cat_ids[cat_name] = existing[0]
    else:
        pos_cat_ids[cat_name] = create("pos.category", {"name": cat_name})
    print(f"  POS Category: {cat_name} (id={pos_cat_ids[cat_name]})")

# Assign POS categories to products
PRODUCT_POS_CAT = {
    "線香功能系列 – 善緣香": "功能系列",
    "線香功能系列 – 財神香": "功能系列",
    "線香功能系列 – 三清檀香": "功能系列",
    "線香脈輪系列 – 心輪香": "脈輪系列",
    "線香五行系列 – 木神香": "五行系列",
    "柬埔寨沉香": "拜拜用香",
    "巴拉圭綠檀": "拜拜用香",
    "決策穩心組": "優惠組合",
    "穩定能量組": "優惠組合",
    "神馬都順 全能順遂組合": "優惠組合",
}

for prod_name, pos_cat_name in PRODUCT_POS_CAT.items():
    if prod_name in product_tmpl_ids and pos_cat_name in pos_cat_ids:
        write("product.template", [product_tmpl_ids[prod_name]], {
            "pos_categ_ids": [(4, pos_cat_ids[pos_cat_name])],
        })

# Close any open POS sessions before creating new configs
default_pos = search("pos.config", [])
if default_pos:
    for pid in default_pos:
        open_sessions = search("pos.session", [["config_id", "=", pid],
                                                 ["state", "!=", "closed"]])
        for sid in open_sessions:
            try:
                execute("pos.session", "action_pos_session_closing_control", [sid])
            except Exception:
                pass

POS_STORES = [
    {"name": "禪香不二 信義旗艦店", "warehouse": "信義旗艦店倉庫"},
    {"name": "禪香不二 板橋店", "warehouse": "板橋店倉庫"},
    {"name": "禪香不二 台中店", "warehouse": "台中店倉庫"},
]

pos_config_ids = {}
for store in POS_STORES:
    existing = search("pos.config", [["name", "=", store["name"]]])
    if existing:
        pos_config_ids[store["name"]] = existing[0]
        print(f"  POS exists: {store['name']} (id={existing[0]})")
        continue

    wh_id = store_wh_ids.get(store["warehouse"])
    picking_type = []
    if wh_id:
        picking_type = search("stock.picking.type", [
            ["warehouse_id", "=", wh_id],
            ["code", "=", "outgoing"],
        ])

    vals = {
        "name": store["name"],
        "module_pos_restaurant": False,
    }
    if picking_type:
        vals["picking_type_id"] = picking_type[0]
    if wh_id:
        vals["warehouse_id"] = wh_id

    pos_id = create("pos.config", vals)
    pos_config_ids[store["name"]] = pos_id
    print(f"  Created POS: {store['name']} (id={pos_id})")

print("Phase 6 complete.")

# ============================================================
# Phase 7: Initial stock levels
# ============================================================
print("\n=== Phase 7: Set initial stock levels ===")

all_warehouses = search_read("stock.warehouse", [["company_id", "=", 1]],
                              ["name", "lot_stock_id"])
wh_stock_locations = {}
for wh in all_warehouses:
    wh_stock_locations[wh["name"]] = wh["lot_stock_id"][0]

STOCK_LEVELS = {
    "禪香不二 中央倉庫": 1000,
    "信義旗艦店倉庫": 100,
    "板橋店倉庫": 100,
    "台中店倉庫": 100,
}

for wh_name, qty in STOCK_LEVELS.items():
    location_id = wh_stock_locations.get(wh_name)
    if not location_id:
        print(f"  WARNING: Warehouse location not found: {wh_name}")
        continue
    for prod_name, pp_id in product_ids.items():
        existing_quant = search("stock.quant", [
            ["product_id", "=", pp_id],
            ["location_id", "=", location_id],
        ])
        try:
            if existing_quant:
                write("stock.quant", existing_quant, {"inventory_quantity": qty})
                execute("stock.quant", "action_apply_inventory", [existing_quant])
            else:
                quant_id = create("stock.quant", {
                    "product_id": pp_id,
                    "location_id": location_id,
                    "inventory_quantity": qty,
                })
                execute("stock.quant", "action_apply_inventory", [[quant_id]])
        except Exception:
            pass  # action_apply_inventory returns None, XML-RPC can't serialize it
    print(f"  {wh_name}: {qty} units per product set")

print("Phase 7 complete.")

# ============================================================
# Phase 8: Sales orders and invoices
# ============================================================
print("\n=== Phase 8: Sales orders and invoices ===")

today = datetime.now()

ORDERS = [
    {"days_ago": 30, "lines": [("線香功能系列 – 善緣香", 2)]},
    {"days_ago": 27, "lines": [("線香功能系列 – 財神香", 1), ("線香功能系列 – 三清檀香", 1)]},
    {"days_ago": 24, "lines": [("線香脈輪系列 – 心輪香", 3)]},
    {"days_ago": 21, "lines": [("線香五行系列 – 木神香", 1), ("柬埔寨沉香", 1)]},
    {"days_ago": 18, "lines": [("巴拉圭綠檀", 2)]},
    {"days_ago": 15, "lines": [("決策穩心組", 1), ("線香功能系列 – 善緣香", 1)]},
    {"days_ago": 12, "lines": [("穩定能量組", 2), ("線香功能系列 – 財神香", 1)]},
    {"days_ago": 9, "lines": [("神馬都順 全能順遂組合", 1)]},
    {"days_ago": 6, "lines": [("線香功能系列 – 三清檀香", 2), ("線香脈輪系列 – 心輪香", 1)]},
    {"days_ago": 3, "lines": [("線香功能系列 – 善緣香", 1), ("線香五行系列 – 木神香", 1),
                               ("巴拉圭綠檀", 1)]},
]

bank_journal = search("account.journal", [["type", "=", "bank"], ["company_id", "=", 1]])
if not bank_journal:
    bank_journal = search("account.journal", [["type", "=", "cash"], ["company_id", "=", 1]])

sale_order_ids = []

for i, order in enumerate(ORDERS, 1):
    order_date = (today - timedelta(days=order["days_ago"])).strftime("%Y-%m-%d")

    order_lines = []
    for prod_name, qty in order["lines"]:
        pp_id = product_ids.get(prod_name)
        if not pp_id:
            print(f"  WARNING: Product not found: {prod_name}")
            continue
        order_lines.append((0, 0, {
            "product_id": pp_id,
            "product_uom_qty": qty,
        }))

    so_id = create("sale.order", {
        "partner_id": portal_partner_id,
        "date_order": order_date,
        "order_line": order_lines,
    })
    sale_order_ids.append(so_id)

    # Confirm
    execute("sale.order", "action_confirm", [[so_id]])

    # Create invoice via wizard (may throw XML-RPC None serialization error, but invoice is still created)
    try:
        ctx = {"active_model": "sale.order", "active_ids": [so_id], "active_id": so_id}
        wiz_id = models.execute_kw(DB, uid, PASSWORD,
            "sale.advance.payment.inv", "create", [{}], {"context": ctx})
        models.execute_kw(DB, uid, PASSWORD,
            "sale.advance.payment.inv", "create_invoices", [[wiz_id]], {"context": ctx})
    except Exception:
        pass  # Invoice is created despite XML-RPC serialization error

    print(f"  Order #{i}: SO id={so_id}, date={order_date}")

print(f"  Total orders: {len(sale_order_ids)}")

# Post all draft invoices and register payments
print("  Processing invoices...")
for i, so_id in enumerate(sale_order_ids, 1):
    order_date = (today - timedelta(days=ORDERS[i-1]["days_ago"])).strftime("%Y-%m-%d")
    so_data = search_read("sale.order", [["id", "=", so_id]], ["invoice_ids"])
    inv_ids = so_data[0]["invoice_ids"] if so_data else []

    for inv_id in inv_ids:
        try:
            # Check if already posted
            inv_data = search_read("account.move", [["id", "=", inv_id]], ["state"])
            if inv_data and inv_data[0]["state"] == "draft":
                write("account.move", [inv_id], {"invoice_date": order_date, "date": order_date})
                execute("account.move", "action_post", [[inv_id]])

            # Register payment if not paid
            inv_data = search_read("account.move", [["id", "=", inv_id]], ["payment_state"])
            if inv_data and inv_data[0]["payment_state"] == "not_paid" and bank_journal:
                pay_ctx = {"active_model": "account.move", "active_ids": [inv_id]}
                pay_wiz_id = models.execute_kw(DB, uid, PASSWORD,
                    "account.payment.register", "create",
                    [{"journal_id": bank_journal[0]}], {"context": pay_ctx})
                models.execute_kw(DB, uid, PASSWORD,
                    "account.payment.register", "action_create_payments",
                    [[pay_wiz_id]], {"context": pay_ctx})
            print(f"    Invoice for order #{i}: posted & paid")
        except Exception as e:
            print(f"    WARNING: Invoice #{i} processing: {e}")

print("Phase 8 complete.")

# ============================================================
# Phase 9: Loyalty / Coupons / Gift Cards / E-Wallet
# ============================================================
print("\n=== Phase 9: Loyalty, coupons, gift cards, e-wallet ===")

# --- 9a: Loyalty program (集點卡) ---
print("  Setting up loyalty program...")
existing_loyalty = search("loyalty.program", [["name", "=", "禪香不二 集點卡"]])
if not existing_loyalty:
    loyalty_id = create("loyalty.program", {
        "name": "禪香不二 集點卡",
        "program_type": "loyalty",
        "trigger": "auto",
        "applies_on": "current",
        "rule_ids": [(0, 0, {
            "reward_point_mode": "money",
            "reward_point_amount": 0.01,
        })],
        "reward_ids": [(0, 0, {
            "reward_type": "discount",
            "discount": 1,
            "discount_mode": "per_point",
            "discount_applicability": "order",
            "required_points": 1,
        })],
    })
    print(f"    Created loyalty program: id={loyalty_id}")

    create("loyalty.card", {
        "program_id": loyalty_id,
        "partner_id": portal_partner_id,
        "points": 210,
    })
    print("    Created loyalty card: 210 points")
else:
    loyalty_id = existing_loyalty[0]
    print(f"    Loyalty program exists: id={loyalty_id}")

# --- 9b: Coupon program (優惠券) ---
print("  Setting up coupon program...")
existing_coupon = search("loyalty.program", [["name", "=", "滿千折百"]])
if not existing_coupon:
    coupon_prog_id = create("loyalty.program", {
        "name": "滿千折百",
        "program_type": "coupons",
        "trigger": "with_code",
        "applies_on": "current",
        "rule_ids": [(0, 0, {
            "minimum_amount": 1000,
        })],
        "reward_ids": [(0, 0, {
            "reward_type": "discount",
            "discount": 100,
            "discount_mode": "per_order",
            "discount_applicability": "order",
            "required_points": 1,
        })],
    })
    print(f"    Created coupon program: id={coupon_prog_id}")

    for j in range(3):
        code = f"INZENSE-{2024+j:04d}"
        create("loyalty.card", {
            "program_id": coupon_prog_id,
            "partner_id": portal_partner_id,
            "code": code,
            "points": 0 if j == 0 else 1,
        })
        status = "used" if j == 0 else "available"
        print(f"    Coupon {code}: {status}")
else:
    coupon_prog_id = existing_coupon[0]
    print(f"    Coupon program exists: id={coupon_prog_id}")

# --- 9c: Gift card program (禮品卡) ---
print("  Setting up gift card program...")
existing_gc = search("loyalty.program", [["name", "=", "禪香不二 禮品卡"]])
if not existing_gc:
    gc_prog_id = create("loyalty.program", {
        "name": "禪香不二 禮品卡",
        "program_type": "gift_card",
        "trigger": "auto",
        "applies_on": "future",
        "rule_ids": [],
        "reward_ids": [(0, 0, {
            "reward_type": "discount",
            "discount": 1,
            "discount_mode": "per_point",
            "discount_applicability": "order",
            "required_points": 1,
        })],
    })
    print(f"    Created gift card program: id={gc_prog_id}")

    create("loyalty.card", {
        "program_id": gc_prog_id,
        "partner_id": portal_partner_id,
        "code": "GIFT-A-500",
        "points": 500,
    })
    print("    Gift card A: NT$500 balance")

    create("loyalty.card", {
        "program_id": gc_prog_id,
        "partner_id": portal_partner_id,
        "code": "GIFT-B-2000",
        "points": 2000,
    })
    print("    Gift card B: NT$2,000 balance")
else:
    gc_prog_id = existing_gc[0]
    print(f"    Gift card program exists: id={gc_prog_id}")

# --- 9d: E-Wallet (電子錢包) ---
print("  Setting up e-wallet program...")
existing_ew = search("loyalty.program", [["name", "=", "禪香不二 電子錢包"]])
if not existing_ew:
    ew_prog_id = create("loyalty.program", {
        "name": "禪香不二 電子錢包",
        "program_type": "ewallet",
        "trigger": "auto",
        "applies_on": "future",
        "rule_ids": [(0, 0, {
            "reward_point_mode": "money",
            "reward_point_amount": 1,
        })],
        "reward_ids": [(0, 0, {
            "reward_type": "discount",
            "discount": 1,
            "discount_mode": "per_point",
            "discount_applicability": "order",
            "required_points": 1,
        })],
    })
    print(f"    Created e-wallet program: id={ew_prog_id}")

    create("loyalty.card", {
        "program_id": ew_prog_id,
        "partner_id": portal_partner_id,
        "points": 3000,
    })
    print("    E-wallet balance: NT$3,000")
else:
    ew_prog_id = existing_ew[0]
    print(f"    E-wallet program exists: id={ew_prog_id}")

print("Phase 9 complete.")
print("\n========================================")
print("All demo data setup complete!")
print("========================================")
