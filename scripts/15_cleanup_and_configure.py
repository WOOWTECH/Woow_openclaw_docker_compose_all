#!/usr/bin/env python3
"""
Step 1-5: Complete cleanup of demo data and Taiwan configuration.
1. Remove ALL demo data (products, orders, invoices, contacts, MRP, etc.)
2. Verify all real products are published on eCommerce
3. Configure accounting/ERP/MRP for Taiwan
4. Set all UI to zh_TW
5. Update company info from inzense.com.tw
"""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# STEP 1: Remove ALL demo data
# ================================================================
print("=" * 60)
print("STEP 1: Remove ALL demo data")
print("=" * 60)

# 1a. Cancel and delete demo MRP production orders
print("\n--- MRP Production Orders ---")
try:
    mrp_ids = models.execute_kw(db, uid, password, "mrp.production", "search", [[]])
    if mrp_ids:
        # Cancel first
        for mid in mrp_ids:
            try:
                models.execute_kw(db, uid, password, "mrp.production", "action_cancel", [[mid]])
            except:
                pass
        models.execute_kw(db, uid, password, "mrp.production", "unlink", [mrp_ids])
        print(f"  Deleted {len(mrp_ids)} MRP production orders")
    else:
        print("  No MRP orders to delete")
except Exception as e:
    print(f"  MRP cleanup: {e}")

# 1b. Delete demo BOM (Bill of Materials)
print("\n--- Bill of Materials ---")
try:
    bom_ids = models.execute_kw(db, uid, password, "mrp.bom", "search", [[]])
    if bom_ids:
        models.execute_kw(db, uid, password, "mrp.bom", "unlink", [bom_ids])
        print(f"  Deleted {len(bom_ids)} BOMs")
    else:
        print("  No BOMs to delete")
except Exception as e:
    print(f"  BOM cleanup: {e}")

# 1c. Cancel and delete demo Sale Orders
print("\n--- Sale Orders ---")
try:
    so_ids = models.execute_kw(db, uid, password, "sale.order", "search", [[]])
    if so_ids:
        for sid in so_ids:
            try:
                models.execute_kw(db, uid, password, "sale.order", "action_cancel", [[sid]])
            except:
                pass
        models.execute_kw(db, uid, password, "sale.order", "unlink", [so_ids])
        print(f"  Deleted {len(so_ids)} sale orders")
    else:
        print("  No sale orders to delete")
except Exception as e:
    print(f"  Sale order cleanup: {e}")

# 1d. Cancel and delete demo Purchase Orders
print("\n--- Purchase Orders ---")
try:
    po_ids = models.execute_kw(db, uid, password, "purchase.order", "search", [[]])
    if po_ids:
        for pid in po_ids:
            try:
                models.execute_kw(db, uid, password, "purchase.order", "button_cancel", [[pid]])
            except:
                pass
        models.execute_kw(db, uid, password, "purchase.order", "unlink", [po_ids])
        print(f"  Deleted {len(po_ids)} purchase orders")
    else:
        print("  No purchase orders to delete")
except Exception as e:
    print(f"  Purchase order cleanup: {e}")

# 1e. Delete demo stock picking/moves
print("\n--- Stock Moves ---")
try:
    pick_ids = models.execute_kw(db, uid, password, "stock.picking", "search", [[]])
    if pick_ids:
        for pk in pick_ids:
            try:
                models.execute_kw(db, uid, password, "stock.picking", "action_cancel", [[pk]])
            except:
                pass
        models.execute_kw(db, uid, password, "stock.picking", "unlink", [pick_ids])
        print(f"  Deleted {len(pick_ids)} stock pickings")
except Exception as e:
    print(f"  Stock cleanup: {e}")

# 1f. Cancel and delete demo invoices/account moves
print("\n--- Account Moves (Invoices) ---")
try:
    move_ids = models.execute_kw(db, uid, password, "account.move", "search", [[]])
    if move_ids:
        # Reset to draft first
        for mid in move_ids:
            try:
                models.execute_kw(db, uid, password, "account.move", "button_draft", [[mid]])
            except:
                pass
        # Cancel
        for mid in move_ids:
            try:
                models.execute_kw(db, uid, password, "account.move", "button_cancel", [[mid]])
            except:
                pass
        models.execute_kw(db, uid, password, "account.move", "unlink", [move_ids])
        print(f"  Deleted {len(move_ids)} account moves")
    else:
        print("  No account moves to delete")
except Exception as e:
    print(f"  Account move cleanup: {e}")

# 1g. Delete demo account.payment
print("\n--- Payments ---")
try:
    pay_ids = models.execute_kw(db, uid, password, "account.payment", "search", [[]])
    if pay_ids:
        for pid in pay_ids:
            try:
                models.execute_kw(db, uid, password, "account.payment", "action_draft", [[pid]])
            except:
                pass
        models.execute_kw(db, uid, password, "account.payment", "unlink", [pay_ids])
        print(f"  Deleted {len(pay_ids)} payments")
except Exception as e:
    print(f"  Payment cleanup: {e}")

# 1h. Delete demo products (non-Chinese, non-inzense)
print("\n--- Demo Products ---")
# Get all our real product IDs (Chinese names)
real_prod_ids = models.execute_kw(db, uid, password, "product.template", "search", [
    ["|", "|", "|", "|", "|", "|", "|",
     ["name", "ilike", "線香"],
     ["name", "ilike", "迷你香"],
     ["name", "ilike", "系列"],
     ["name", "ilike", "組合"],
     ["name", "ilike", "拜拜"],
     ["name", "ilike", "原木筆"],
     ["name", "ilike", "福石"],
     ["name", "ilike", "香"],
    ]
])
print(f"  Real products (to keep): {len(real_prod_ids)}")

all_prod_ids = models.execute_kw(db, uid, password, "product.template", "search", [[]])
demo_prod_ids = [pid for pid in all_prod_ids if pid not in real_prod_ids]
print(f"  Demo products (to delete): {len(demo_prod_ids)}")

if demo_prod_ids:
    # First archive (deactivate)
    models.execute_kw(db, uid, password, "product.template", "write", [demo_prod_ids, {
        "active": False,
        "sale_ok": False,
        "purchase_ok": False,
        "website_published": False,
    }])
    # Then try to delete
    deleted = 0
    for pid in demo_prod_ids:
        try:
            models.execute_kw(db, uid, password, "product.template", "unlink", [[pid]])
            deleted += 1
        except:
            pass
    print(f"  Deleted {deleted} demo products, archived {len(demo_prod_ids) - deleted}")

# 1i. Clean demo contacts (keep admin, inzense company, and OdooBot)
print("\n--- Demo Contacts ---")
keep_partner_ids = [1, 2, 3]  # OdooBot, Admin, Company
real_partners = models.execute_kw(db, uid, password, "res.partner", "search", [
    ["|", ["name", "ilike", "inzense"], ["name", "ilike", "禪香"]]
])
keep_partner_ids.extend(real_partners)

demo_partners = models.execute_kw(db, uid, password, "res.partner", "search", [
    [["id", "not in", keep_partner_ids], ["id", ">", 3]]
])
if demo_partners:
    deleted = 0
    for pid in demo_partners:
        try:
            models.execute_kw(db, uid, password, "res.partner", "unlink", [[pid]])
            deleted += 1
        except:
            pass
    print(f"  Deleted {deleted}/{len(demo_partners)} demo contacts")
else:
    print("  No demo contacts to delete")

# 1j. Delete demo projects/tasks
print("\n--- Projects ---")
try:
    proj_ids = models.execute_kw(db, uid, password, "project.project", "search", [[]])
    if proj_ids:
        task_ids = models.execute_kw(db, uid, password, "project.task", "search", [[]])
        if task_ids:
            models.execute_kw(db, uid, password, "project.task", "unlink", [task_ids])
            print(f"  Deleted {len(task_ids)} tasks")
        models.execute_kw(db, uid, password, "project.project", "unlink", [proj_ids])
        print(f"  Deleted {len(proj_ids)} projects")
except Exception as e:
    print(f"  Project cleanup: {e}")

# 1k. Delete demo HR employees (keep admin)
print("\n--- Employees ---")
try:
    emp_ids = models.execute_kw(db, uid, password, "hr.employee", "search", [
        [["id", ">", 1]]
    ])
    if emp_ids:
        models.execute_kw(db, uid, password, "hr.employee", "unlink", [emp_ids])
        print(f"  Deleted {len(emp_ids)} demo employees")
except Exception as e:
    print(f"  Employee cleanup: {e}")

# 1l. Delete demo CRM leads
print("\n--- CRM Leads ---")
try:
    lead_ids = models.execute_kw(db, uid, password, "crm.lead", "search", [[]])
    if lead_ids:
        models.execute_kw(db, uid, password, "crm.lead", "unlink", [lead_ids])
        print(f"  Deleted {len(lead_ids)} CRM leads")
except Exception as e:
    print(f"  CRM cleanup: {e}")

# 1m. Delete demo calendar events
print("\n--- Calendar Events ---")
try:
    event_ids = models.execute_kw(db, uid, password, "calendar.event", "search", [[]])
    if event_ids:
        models.execute_kw(db, uid, password, "calendar.event", "unlink", [event_ids])
        print(f"  Deleted {len(event_ids)} calendar events")
except Exception as e:
    print(f"  Calendar cleanup: {e}")

# 1n. Delete demo POS orders
print("\n--- POS Orders ---")
try:
    pos_ids = models.execute_kw(db, uid, password, "pos.order", "search", [[]])
    if pos_ids:
        models.execute_kw(db, uid, password, "pos.order", "unlink", [pos_ids])
        print(f"  Deleted {len(pos_ids)} POS orders")
except Exception as e:
    print(f"  POS cleanup: {e}")

# 1o. Delete demo loyalty programs (keep any we create later)
print("\n--- Demo Loyalty Programs ---")
try:
    loy_ids = models.execute_kw(db, uid, password, "loyalty.program", "search", [[]])
    if loy_ids:
        models.execute_kw(db, uid, password, "loyalty.program", "unlink", [loy_ids])
        print(f"  Deleted {len(loy_ids)} loyalty programs")
except Exception as e:
    print(f"  Loyalty cleanup: {e}")

print("\n" + "=" * 60)
print("STEP 1 COMPLETE: Demo data removed")
print("=" * 60)

# ================================================================
# STEP 2: Verify ALL real products are published on eCommerce
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Verify and publish all products on eCommerce")
print("=" * 60)

# Get all remaining real products
remaining_prods = models.execute_kw(db, uid, password, "product.template", "search", [
    [["active", "=", True]]
])
print(f"Total active products: {len(remaining_prods)}")

# Publish all on website
unpublished = models.execute_kw(db, uid, password, "product.template", "search", [
    [["active", "=", True], ["website_published", "=", False]]
])
if unpublished:
    models.execute_kw(db, uid, password, "product.template", "write", [unpublished, {
        "website_published": True,
        "is_published": True,
        "sale_ok": True,
    }])
    print(f"Published {len(unpublished)} previously unpublished products")

# Verify
published_count = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True]]
])
with_image = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True], ["image_1920", "!=", False]]
])
print(f"Published on eCommerce: {published_count}")
print(f"With product images: {with_image}")

# Check products without public categories
no_cat = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True], ["public_categ_ids", "=", False]]
])
print(f"Published without categories: {no_cat}")

print("\n" + "=" * 60)
print("STEP 3: Configure accounting/ERP/MRP for Taiwan")
print("=" * 60)

# 3a. Install Taiwan accounting module (l10n_tw) if available
print("\n--- Taiwan Localization ---")
tw_module = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
    [["name", "=", "l10n_tw"]]
], {"fields": ["id", "state", "shortdesc"]})
if tw_module:
    if tw_module[0]["state"] != "installed":
        print(f"  Installing Taiwan accounting: {tw_module[0]['shortdesc']}")
        try:
            models.execute_kw(db, uid, password, "ir.module.module", "button_immediate_install", [[tw_module[0]["id"]]])
            print("  Taiwan accounting module installed!")
        except Exception as e:
            print(f"  Install failed: {e}")
    else:
        print(f"  Taiwan accounting already installed: {tw_module[0]['shortdesc']}")
else:
    print("  l10n_tw module not found, will configure manually")

# 3b. Set company country and fiscal settings
print("\n--- Company Fiscal Settings ---")
tw_country_ids = models.execute_kw(db, uid, password, "res.country", "search", [[["code", "=", "TW"]]])
tw_country_id = tw_country_ids[0] if tw_country_ids else False

# Find TWD currency
twd_ids = models.execute_kw(db, uid, password, "res.currency", "search", [[["name", "=", "TWD"]]])
if not twd_ids:
    # TWD might exist but inactive
    twd_ids = models.execute_kw(db, uid, password, "res.currency", "search", [
        [["name", "=", "TWD"], ["active", "=", False]]
    ], {"context": {"active_test": False}})
    if twd_ids:
        models.execute_kw(db, uid, password, "res.currency", "write", [twd_ids, {"active": True}])
        print(f"  Activated TWD currency: ID={twd_ids[0]}")

if twd_ids:
    twd_id = twd_ids[0]
    print(f"  TWD currency ID: {twd_id}")
else:
    # Create TWD
    twd_id = models.execute_kw(db, uid, password, "res.currency", "create", [{
        "name": "TWD",
        "symbol": "NT$",
        "rounding": 1.0,
        "decimal_places": 0,
        "position": "before",
        "active": True,
    }])
    print(f"  Created TWD currency: ID={twd_id}")

# 3c. Create Taiwan tax (5% VAT)
print("\n--- Taiwan Tax (5% 營業稅) ---")
existing_tax = models.execute_kw(db, uid, password, "account.tax", "search", [
    [["name", "ilike", "營業稅"], ["company_id", "=", 1]]
])
if not existing_tax:
    existing_tax = models.execute_kw(db, uid, password, "account.tax", "search", [
        [["name", "ilike", "5%"], ["company_id", "=", 1]]
    ])

if not existing_tax:
    try:
        tax_id = models.execute_kw(db, uid, password, "account.tax", "create", [{
            "name": "營業稅 5%",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": 5.0,
            "company_id": 1,
            "description": "TW VAT 5%",
        }])
        print(f"  Created sales tax: 營業稅 5% (ID={tax_id})")

        # Also create purchase tax
        ptax_id = models.execute_kw(db, uid, password, "account.tax", "create", [{
            "name": "進項稅 5%",
            "type_tax_use": "purchase",
            "amount_type": "percent",
            "amount": 5.0,
            "company_id": 1,
            "description": "TW Input Tax 5%",
        }])
        print(f"  Created purchase tax: 進項稅 5% (ID={ptax_id})")
    except Exception as e:
        print(f"  Tax creation: {e}")
else:
    print(f"  Tax already exists: IDs={existing_tax}")

# 3d. Set company fiscal year and accounting settings
print("\n--- Fiscal Settings ---")
models.execute_kw(db, uid, password, "res.company", "write", [[1], {
    "country_id": tw_country_id,
    "fiscalyear_last_day": 31,
    "fiscalyear_last_month": "12",
}])
print("  Fiscal year set to Jan-Dec (calendar year)")

# ================================================================
# STEP 4: Set ALL UI language to zh_TW
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Set all UI to Traditional Chinese (zh_TW)")
print("=" * 60)

# 4a. Set default language for the system
try:
    # Get the zh_TW language record
    zh_lang = models.execute_kw(db, uid, password, "res.lang", "search_read", [
        [["code", "=", "zh_TW"]]
    ], {"fields": ["id", "name", "active"]})
    if zh_lang:
        print(f"  zh_TW language: active={zh_lang[0]['active']}")

    # Set as default for the website
    models.execute_kw(db, uid, password, "website", "write", [[1], {
        "default_lang_id": zh_lang[0]["id"] if zh_lang else False,
    }])
    print("  Website default language set to zh_TW")
except Exception as e:
    print(f"  Language setup: {e}")

# 4b. Set ALL users to zh_TW
all_users = models.execute_kw(db, uid, password, "res.users", "search", [[["active", "=", True]]])
models.execute_kw(db, uid, password, "res.users", "write", [all_users, {
    "lang": "zh_TW",
    "tz": "Asia/Taipei",
}])
print(f"  Updated {len(all_users)} users to zh_TW / Asia/Taipei")

# 4c. Set all partners to zh_TW
all_partners = models.execute_kw(db, uid, password, "res.partner", "search", [[]])
models.execute_kw(db, uid, password, "res.partner", "write", [all_partners, {
    "lang": "zh_TW",
}])
print(f"  Updated {len(all_partners)} partners to zh_TW")

# 4d. Ensure English is NOT the default (only zh_TW)
try:
    en_lang = models.execute_kw(db, uid, password, "res.lang", "search", [
        [["code", "=", "en_US"], ["active", "=", True]]
    ])
    if en_lang:
        # Keep English active but not default
        print("  English (en_US) kept active as secondary language")
except:
    pass

# ================================================================
# STEP 5: Update company info from inzense.com.tw
# ================================================================
print("\n" + "=" * 60)
print("STEP 5: Update company info from inzense.com.tw")
print("=" * 60)

models.execute_kw(db, uid, password, "res.company", "write", [[1], {
    "name": "禪香不二 Inzense",
    "street": "台北市北投區光明路240號2樓之8",
    "street2": "",
    "city": "台北市",
    "state_id": False,
    "zip": "112",
    "country_id": tw_country_id,
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
    "email": "service@inzense.com.tw",
    "website": "https://www.inzense.com.tw",
}])
print("  Company basic info updated")

# Update partner record for the company
company_partner = models.execute_kw(db, uid, password, "res.company", "read", [[1], ["partner_id"]])
partner_id = company_partner[0]["partner_id"][0]
models.execute_kw(db, uid, password, "res.partner", "write", [[partner_id], {
    "name": "禪香不二 Inzense",
    "street": "台北市北投區光明路240號2樓之8",
    "city": "台北市",
    "zip": "112",
    "country_id": tw_country_id,
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
    "email": "service@inzense.com.tw",
    "website": "https://www.inzense.com.tw",
    "lang": "zh_TW",
    "tz": "Asia/Taipei",
}])
print("  Company partner record updated")

# Set social media
models.execute_kw(db, uid, password, "website", "write", [[1], {
    "social_facebook": "https://www.facebook.com/onlyinzense",
    "social_instagram": "https://instagram.com/only_inzense",
}])
print("  Social media links set")

# ================================================================
# FINAL VERIFICATION
# ================================================================
print("\n" + "=" * 60)
print("FINAL VERIFICATION")
print("=" * 60)

# Count remaining items
prods = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["active", "=", True]]
])
published = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["website_published", "=", True]]
])
partners = models.execute_kw(db, uid, password, "res.partner", "search_count", [[]])
so_count = models.execute_kw(db, uid, password, "sale.order", "search_count", [[]])

try:
    invoice_count = models.execute_kw(db, uid, password, "account.move", "search_count", [[]])
except:
    invoice_count = "N/A"

company = models.execute_kw(db, uid, password, "res.company", "read", [[1],
    ["name", "country_id", "currency_id", "phone", "email"]])

print(f"  Products (active): {prods}")
print(f"  Products (published on eCommerce): {published}")
print(f"  Partners: {partners}")
print(f"  Sale orders: {so_count}")
print(f"  Invoices: {invoice_count}")
print(f"  Company: {company[0]['name']}")
print(f"  Country: {company[0]['country_id']}")
print(f"  Currency: {company[0]['currency_id']}")
print(f"  Phone: {company[0]['phone']}")
print(f"  Email: {company[0]['email']}")

# Check taxes
taxes = models.execute_kw(db, uid, password, "account.tax", "search_read", [
    [["company_id", "=", 1]]
], {"fields": ["name", "amount", "type_tax_use"], "limit": 10})
print(f"\n  Taxes configured:")
for t in taxes:
    print(f"    {t['name']} ({t['amount']}%) - {t['type_tax_use']}")

print("\n=== ALL STEPS COMPLETE ===")
