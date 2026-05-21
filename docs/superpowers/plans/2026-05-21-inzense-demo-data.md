# Inzense Demo Data Build-out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the clean Inzense Odoo 18 instance with demo data: 10 products, portal customer, 10 sales/invoices, loyalty/coupon/gift card/e-wallet records, 3 POS stores, and 4 warehouses with resupply routes.

**Architecture:** A single Python script (`scripts/50_demo_data_setup.py`) connects to Odoo via XML-RPC (port-forwarded from K3s), installs modules, and creates all demo data in sequence. This follows the existing project pattern established by scripts 02-49.

**Tech Stack:** Python 3, XML-RPC (`xmlrpc.client`), kubectl port-forward, Odoo 18 API

**Spec:** `docs/superpowers/specs/2026-05-21-inzense-demo-data-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/50_demo_data_setup.py` | Main script: installs modules, creates all demo data via XML-RPC |

The script is monolithic by design (following existing pattern in `scripts/`). All 9 setup phases run in order within a single file.

---

### Task 1: Create the script skeleton and install modules

**Files:**
- Create: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Create script with XML-RPC connection and module installation**

```python
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
```

- [ ] **Step 2: Test module installation**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
cd "/var/tmp/vibe-kanban/worktrees/d488-inzense-odoo-18/k3s project"
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: All 4 modules installed (or "already installed"). No errors.

- [ ] **Step 3: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data script: Phase 1 — module installation"
```

---

### Task 2: Company setup and product creation

**Files:**
- Modify: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Add Phase 2 (company) and Phase 3 (products)**

Append to the script after Phase 1:

```python
# ============================================================
# Phase 2: Company setup
# ============================================================
print("\n=== Phase 2: Company setup ===")

# Get TWD currency
twd_ids = search("res.currency", [["name", "=", "TWD"]])
if not twd_ids:
    print("  WARNING: TWD currency not found, skipping currency setup")
else:
    # Activate TWD if not active
    write("res.currency", twd_ids, {"active": True})

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
if twd_ids:
    company_vals["currency_id"] = twd_ids[0]
if tw_ids:
    company_vals["country_id"] = tw_ids[0]
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
            "type": "product",  # storable in Odoo 18
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
    # Get the product.product id
    pp_ids = search("product.product", [["product_tmpl_id", "=", tmpl_id]])
    if pp_ids:
        product_ids[p["name"]] = pp_ids[0]

print(f"  Total products: {len(product_ids)}")
print("Phase 3 complete.")
```

- [ ] **Step 2: Verify image files exist**

```bash
cd "/var/tmp/vibe-kanban/worktrees/d488-inzense-odoo-18/k3s project"
for f in "線香功能系列＿封面圖＿善緣香.jpg" "三清檀香.jpg" "心輪香線香-scaled.jpg" "木神香＿封面圖.jpg" "柬埔寨沉香.jpg" "巴拉圭綠檀.jpg" "251016-組合系列商品圖_決策穩心組.jpg" "251016-組合系列商品圖_穩定能量組.jpg" "260113-年節禮盒_詳情頁_神馬都順_1（5）-scaled.jpeg"; do
  test -f "images/products/$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: All files show "OK". For `線香功能系列＿封面圖＿財神香.jpg`, check if a variant filename exists and update the script accordingly.

- [ ] **Step 3: Run and verify**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: Company updated, 6 categories created, 10 products created with images.

- [ ] **Step 4: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data: Phase 2-3 — company setup and 10 products"
```

---

### Task 3: Portal customer and warehouses

**Files:**
- Modify: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Add Phase 4 (portal customer) and Phase 5 (warehouses)**

Append after Phase 3:

```python
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
```

- [ ] **Step 2: Run and verify**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: Portal customer created, 3 store warehouses created with resupply from central warehouse.

- [ ] **Step 3: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data: Phase 4-5 — portal customer and warehouses"
```

---

### Task 4: POS configuration and initial stock

**Files:**
- Modify: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Add Phase 6 (POS) and Phase 7 (stock)**

Append after Phase 5:

```python
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

# Delete any default POS configs
default_pos = search("pos.config", [])
if default_pos:
    for pid in default_pos:
        # Close any open sessions
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
    # Get the picking type for this warehouse
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

    pos_id = create("pos.config", vals)
    pos_config_ids[store["name"]] = pos_id
    print(f"  Created POS: {store['name']} (id={pos_id})")

print("Phase 6 complete.")

# ============================================================
# Phase 7: Initial stock levels
# ============================================================
print("\n=== Phase 7: Set initial stock levels ===")

# Get all warehouse stock locations
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
        # Set quant directly
        existing_quant = search("stock.quant", [
            ["product_id", "=", pp_id],
            ["location_id", "=", location_id],
        ])
        if existing_quant:
            write("stock.quant", existing_quant, {
                "inventory_quantity": qty,
            })
            execute("stock.quant", "action_apply_inventory", [existing_quant])
        else:
            quant_id = create("stock.quant", {
                "product_id": pp_id,
                "location_id": location_id,
                "inventory_quantity": qty,
            })
            execute("stock.quant", "action_apply_inventory", [[quant_id]])
    print(f"  {wh_name}: {qty} units per product set")

print("Phase 7 complete.")
```

- [ ] **Step 2: Run and verify**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: 3 POS configs created, stock levels set for all 4 warehouses.

- [ ] **Step 3: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data: Phase 6-7 — POS configuration and stock levels"
```

---

### Task 5: Sales orders and invoices

**Files:**
- Modify: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Add Phase 8 (sales orders and invoices)**

Append after Phase 7:

```python
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

# Get a payment journal (bank)
bank_journal = search("account.journal", [["type", "=", "bank"], ["company_id", "=", 1]])
if not bank_journal:
    bank_journal = search("account.journal", [["type", "=", "cash"], ["company_id", "=", 1]])

sale_order_ids = []

for i, order in enumerate(ORDERS, 1):
    order_date = (today - timedelta(days=order["days_ago"])).strftime("%Y-%m-%d")

    # Create sale order
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

    # Confirm the order
    execute("sale.order", "action_confirm", [[so_id]])

    # Create invoice
    invoice_result = execute("sale.order", "_create_invoices", [[so_id]])

    # Post the invoice
    if invoice_result:
        inv_ids = invoice_result if isinstance(invoice_result, list) else [invoice_result]
        for inv_id in inv_ids:
            # Set invoice date
            write("account.move", [inv_id], {"invoice_date": order_date, "date": order_date})
            execute("account.move", "action_post", [[inv_id]])

            # Register payment
            if bank_journal:
                try:
                    # Use the payment register wizard
                    ctx = {"active_model": "account.move", "active_ids": [inv_id]}
                    wiz_id = models.execute_kw(
                        DB, uid, PASSWORD,
                        "account.payment.register", "create",
                        [{"journal_id": bank_journal[0]}],
                        {"context": ctx}
                    )
                    models.execute_kw(
                        DB, uid, PASSWORD,
                        "account.payment.register", "action_create_payments",
                        [[wiz_id]],
                        {"context": ctx}
                    )
                except Exception as e:
                    print(f"  WARNING: Payment failed for order #{i}: {e}")

    print(f"  Order #{i}: SO id={so_id}, date={order_date}")

print(f"  Total orders: {len(sale_order_ids)}")
print("Phase 8 complete.")
```

- [ ] **Step 2: Run and verify**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: 10 sale orders created, confirmed, invoiced, and paid.

- [ ] **Step 3: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data: Phase 8 — sales orders and invoices"
```

---

### Task 6: Loyalty, coupons, gift cards, and e-wallet

**Files:**
- Modify: `scripts/50_demo_data_setup.py`

- [ ] **Step 1: Add Phase 9 (member center / loyalty data)**

Append after Phase 8:

```python
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
            "reward_point_amount": 0.01,  # 1 point per 100 TWD = 0.01 per 1 TWD
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

    # Create loyalty card with points for portal customer
    card_id = create("loyalty.card", {
        "program_id": loyalty_id,
        "partner_id": portal_partner_id,
        "points": 210,  # ~NT$21,000 total spend / 100
    })
    print(f"    Created loyalty card: {210} points")
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

    # Generate 3 coupons
    for j in range(3):
        code = f"INZENSE-{2024+j:04d}"
        card_id = create("loyalty.card", {
            "program_id": coupon_prog_id,
            "partner_id": portal_partner_id,
            "code": code,
            "points": 0 if j == 0 else 1,  # first one used (0 points), others available (1 point)
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

    # Card A: 500 balance (1000 original, 500 used)
    create("loyalty.card", {
        "program_id": gc_prog_id,
        "partner_id": portal_partner_id,
        "code": "GIFT-A-500",
        "points": 500,
    })
    print("    Gift card A: NT$500 balance")

    # Card B: 2000 balance (unused)
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
```

- [ ] **Step 2: Run full script end-to-end**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
sleep 3
python3 scripts/50_demo_data_setup.py
kill %1 2>/dev/null
```

Expected: All 9 phases complete without errors. Final output shows "All demo data setup complete!"

- [ ] **Step 3: Commit**

```bash
git add scripts/50_demo_data_setup.py
git commit -m "Add demo data: Phase 9 — loyalty, coupons, gift cards, e-wallet"
```

---

### Task 7: End-to-end verification via Playwright

**Files:** None (verification only)

- [ ] **Step 1: Verify backend via Playwright**

```bash
playwright-cli open https://inzense-odoo.woowtech.io/web/login
# Login as admin
playwright-cli fill e15 "admin"
playwright-cli fill e18 "admin"
playwright-cli click e20
# Check key areas
playwright-cli screenshot --filename=verify-backend.png
```

Verify:
- Company name shows "禪香不二 Inzense"
- Products visible in backend (navigate to Sales > Products)
- Sales orders visible (navigate to Sales > Orders)
- POS configs visible (navigate to Point of Sale)
- Warehouses visible (navigate to Inventory > Configuration > Warehouses)

- [ ] **Step 2: Verify portal login**

```bash
playwright-cli goto https://inzense-odoo.woowtech.io/web/login
# Login as portal user
playwright-cli fill e15 "portal@inzense.com.tw"
playwright-cli fill e18 "portal"
playwright-cli click e20
playwright-cli screenshot --filename=verify-portal.png
```

Expected: Portal user can login and see their orders/member center.

- [ ] **Step 3: Clean up test artifacts and final commit**

```bash
rm -f verify-backend.png verify-portal.png
rm -rf .playwright-cli/
git add scripts/50_demo_data_setup.py
git commit -m "Complete Inzense demo data setup script — all 9 phases verified"
```
