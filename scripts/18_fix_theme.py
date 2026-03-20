#!/usr/bin/env python3
"""Fix theme colors, mobile sidebar, price display, and overall visual consistency."""
import xmlrpc.client
import json

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

img = {}

print("=" * 60)
print("FIX 1: Theme Colors & Visual")
print("=" * 60)

# The Odoo 18 website uses SCSS variables for theming.
# The purple header comes from the default Odoo theme preset.
# We need to override the SCSS color variables via a custom asset.

# First check what presets/options are active
option_views = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["key", "like", "website.option"]]
], {"fields": ["id", "key", "active"], "limit": 30})
print("Active website options:")
for v in option_views:
    if v["active"]:
        print(f"  {v['key']}")

# Check for header color preset
header_views = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    ["|", ["key", "like", "header"], ["key", "like", "navbar"]]
], {"fields": ["id", "key", "active", "name"], "limit": 30})
print(f"\nHeader views: {len(header_views)}")
for v in header_views:
    if v["active"]:
        print(f"  [active] ID={v['id']}: {v['key']} - {v['name']}")

# The key fix: update the CSS to override Odoo's default purple/primary colors
# Odoo 18 uses CSS custom properties: --o-color-1 through --o-color-5
# and --o-cc1-btn-primary, etc.

print("\n--- Updating master CSS override ---")

# Find our custom CSS view
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])

# Build comprehensive CSS that overrides ALL Odoo theme colors
master_css = r"""
/* ============================================
   Inzense 禪香不二 - Master Theme Override
   Matches https://www.inzense.com.tw/
   ============================================ */

/* --- Override Odoo's Color System --- */
:root {
    /* Odoo color palette override */
    --o-color-1: #FFFFFF !important;
    --o-color-2: #f9f7f4 !important;
    --o-color-3: #27292C !important;
    --o-color-4: #E4916E !important;
    --o-color-5: #D8B772 !important;

    /* Button colors */
    --o-color-1-btn-primary: #E4916E !important;
    --o-color-1-btn-primary-border: #E4916E !important;
    --o-color-1-btn-secondary: #D8B772 !important;
    --o-color-1-btn-secondary-border: #D8B772 !important;

    /* Text colors */
    --o-color-1-text: #7A7A7A !important;
    --o-color-1-headings: #27292C !important;

    /* Header background */
    --o-cc1-bg: #FFFFFF !important;
    --o-cc1-btn-primary: #E4916E !important;
    --o-cc1-btn-primary-border: #E4916E !important;
    --o-cc1-text: #27292C !important;
    --o-cc1-headings: #27292C !important;
    --o-cc1-link: #E4916E !important;

    /* Footer */
    --o-cc3-bg: #27292C !important;
    --o-cc3-text: #CCCCCC !important;
    --o-cc3-headings: #D8B772 !important;
    --o-cc3-link: #D8B772 !important;

    /* Brand colors */
    --inzense-primary: #E4916E;
    --inzense-gold: #D8B772;
    --inzense-dark: #27292C;
    --inzense-text: #7A7A7A;
    --inzense-heading: #27292C;
    --inzense-bg-warm: #FBD7B5;
}

/* --- Global Typography --- */
body, #wrapwrap {
    font-family: 'Roboto', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.8 !important;
    color: #7A7A7A !important;
}

h1, h2, h3, h4, h5, h6,
.h1, .h2, .h3, .h4, .h5, .h6 {
    font-family: 'Montserrat', 'Noto Sans TC', sans-serif !important;
    color: #27292C !important;
    line-height: 1.4 !important;
    font-weight: 600;
}

/* --- Header / Navbar - FORCE WHITE --- */
header, header#top,
header .navbar,
header .o_header_standard,
header .o_colored_level,
header .o_cc {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #27292C !important;
}

header .navbar-brand img {
    max-height: 45px !important;
}

header .navbar-nav .nav-link,
header .nav-link {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #27292C !important;
    letter-spacing: 0.5px;
}

header .navbar-nav .nav-link:hover,
header .nav-link:hover {
    color: #E4916E !important;
}

/* --- Mobile Header - FORCE WHITE --- */
header .o_header_mobile,
header .o_header_mobile .navbar,
.o_header_mobile {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
}

/* --- Mobile Sidebar / Off-canvas Menu --- */
.o_header_mobile .offcanvas,
.offcanvas,
.offcanvas-start,
#top_menu_collapse_mobile,
.o_main_nav .offcanvas {
    background-color: #FFFFFF !important;
}

.offcanvas .nav-link,
.offcanvas .dropdown-toggle,
#top_menu_collapse_mobile .nav-link {
    color: #27292C !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    padding: 12px 20px !important;
    border-bottom: 1px solid #f0f0f0 !important;
}

.offcanvas .nav-link:hover,
.offcanvas .dropdown-toggle:hover {
    color: #E4916E !important;
    background-color: #fdf5ef !important;
}

.offcanvas .dropdown-menu {
    background: #f9f7f4 !important;
    border: none !important;
    box-shadow: none !important;
}

.offcanvas .dropdown-item {
    color: #54595F !important;
    font-size: 14px !important;
    padding: 8px 30px !important;
}

.offcanvas .dropdown-item:hover {
    color: #E4916E !important;
    background-color: #fdf5ef !important;
}

/* Mobile sidebar header */
.offcanvas-header {
    background-color: #27292C !important;
    color: #fff !important;
}

.offcanvas-header .btn-close {
    filter: invert(1) !important;
}

/* --- Buttons --- */
.btn-primary,
.btn-primary:active,
.btn-primary:focus,
a.btn-primary {
    background-color: #E4916E !important;
    border-color: #E4916E !important;
    color: #fff !important;
    border-radius: 30px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
}
.btn-primary:hover,
a.btn-primary:hover {
    background-color: #c97a58 !important;
    border-color: #c97a58 !important;
}

.btn-secondary,
a.btn-secondary {
    background-color: #D8B772 !important;
    border-color: #D8B772 !important;
    color: #fff !important;
    border-radius: 30px !important;
}

/* --- Product Cards --- */
.oe_product_cart {
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
}
.oe_product_cart:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

/* Product price color */
.oe_product_cart .product_price,
.oe_product .product_price,
.oe_currency_value,
.product_price .oe_price {
    color: #E4916E !important;
    font-weight: 700 !important;
}

/* --- Shop page --- */
.oe_website_sale .o_wsale_products_grid_table_wrapper .oe_product {
    margin-bottom: 20px;
}

/* Shop sidebar / category filters */
.o_wsale_products_categories .nav-link {
    color: #27292C !important;
    font-size: 14px !important;
}
.o_wsale_products_categories .nav-link:hover,
.o_wsale_products_categories .nav-link.active {
    color: #E4916E !important;
    font-weight: 600;
}

/* Add to cart button */
.oe_website_sale .a-submit,
.oe_website_sale .btn-primary,
.js_add_cart {
    background-color: #E4916E !important;
    border-color: #E4916E !important;
    border-radius: 30px !important;
}

/* --- Footer --- */
footer, #bottom, .o_footer {
    background-color: #27292C !important;
    color: #ccc !important;
}

footer h5, footer .h5 {
    color: #D8B772 !important;
}

footer a {
    color: #ccc !important;
}
footer a:hover {
    color: #D8B772 !important;
}

/* --- Dropdown menus --- */
.dropdown-menu {
    border: none !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1) !important;
    border-radius: 4px !important;
}

.dropdown-item:hover {
    background-color: #fdf5ef !important;
    color: #E4916E !important;
}

/* --- Breadcrumbs --- */
.breadcrumb a {
    color: #E4916E !important;
}

/* --- Blog cards --- */
.inzense-blog-card {
    padding: 25px;
    border-bottom: 3px solid #D8B772;
    background: #fff;
    transition: all 0.3s ease;
}
.inzense-blog-card:hover {
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
}

/* --- Contact page location cards --- */
.inzense-location-card {
    background: #fff;
    border-radius: 8px;
    padding: 25px;
    border-left: 4px solid #E4916E;
}

/* --- Fix Odoo primary color references --- */
.text-primary { color: #E4916E !important; }
.bg-primary { background-color: #E4916E !important; }
.border-primary { border-color: #E4916E !important; }
.bg-secondary { background-color: #D8B772 !important; }

/* Override any Odoo purple/blue */
.o_main_nav .active > .nav-link,
.o_main_nav .nav-link:hover,
.o_main_nav .nav-link.active {
    color: #E4916E !important;
}

/* --- Responsive --- */
@media (max-width: 991px) {
    header .navbar-toggler {
        border: none !important;
        color: #27292C !important;
    }
    header .navbar-toggler-icon {
        filter: none !important;
    }
}

@media (max-width: 767px) {
    h1 { font-size: 28px !important; }
    h2 { font-size: 22px !important; }
}

/* --- Ensure eCommerce search works on mobile --- */
.o_wsale_products_searchbar_form {
    margin-bottom: 15px;
}

/* --- Price format --- */
.oe_website_sale .oe_price .oe_currency_value {
    font-size: 18px !important;
}
"""

css_view_content = f'''<t t-name="website.inzense_custom_css" t-inherit="website.layout" t-inherit-mode="extension">
    <xpath expr="//head" position="inside">
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&amp;family=Montserrat:wght@400;500;600;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;family=Parisienne&amp;family=Poppins:wght@400;500;600&amp;family=Roboto+Slab:wght@400;500&amp;family=Roboto:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
        <style type="text/css">{master_css}</style>
    </xpath>
</t>'''

if css_views:
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {
        "arch": css_view_content,
        "active": True,
    }])
    print(f"Updated CSS view: IDs={css_views}")
else:
    vid = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
        "name": "Inzense Custom CSS",
        "type": "qweb",
        "arch": css_view_content,
        "key": "website.inzense_custom_css",
        "inherit_id": 1305,
        "website_id": 1,
        "active": True,
    }])
    print(f"Created CSS view: ID={vid}")

print("\n" + "=" * 60)
print("FIX 2: Product Price Currency Display")
print("=" * 60)

# Set product pricelist to use TWD
pricelist_ids = models.execute_kw(db, uid, password, "product.pricelist", "search", [[]])
twd_ids = models.execute_kw(db, uid, password, "res.currency", "search", [[["name", "=", "TWD"]]])
twd_id = twd_ids[0] if twd_ids else False

if twd_id and pricelist_ids:
    for pl_id in pricelist_ids:
        try:
            models.execute_kw(db, uid, password, "product.pricelist", "write", [[pl_id], {
                "currency_id": twd_id,
            }])
        except Exception as e:
            print(f"  Pricelist {pl_id}: {e}")
    print(f"Updated {len(pricelist_ids)} pricelists to TWD")

    # Read pricelist to verify
    pl_data = models.execute_kw(db, uid, password, "product.pricelist", "search_read", [
        []
    ], {"fields": ["name", "currency_id"]})
    for pl in pl_data:
        print(f"  {pl['name']}: {pl['currency_id']}")

# Also update the website's default pricelist
models.execute_kw(db, uid, password, "website", "write", [[1], {
    "pricelist_id": pricelist_ids[0] if pricelist_ids else False,
}])
print("Website default pricelist updated")

print("\n" + "=" * 60)
print("FIX 3: Verify Mobile Menu Items")
print("=" * 60)

# Check menu items exist for website 1
menus = models.execute_kw(db, uid, password, "website.menu", "search_read", [
    [["website_id", "=", 1]]
], {"fields": ["id", "name", "url", "parent_id", "sequence"], "order": "sequence"})
print(f"Total menu items: {len(menus)}")
top_menus = [m for m in menus if m["parent_id"] and m["parent_id"][0] == 4]
print(f"Top-level menu items: {len(top_menus)}")
for m in top_menus:
    print(f"  seq={m['sequence']}: {m['name']} -> {m['url']}")

# The mobile menu should work with the same menu items
# The issue might be that the offcanvas template is not picking up items
# Let's verify by checking the actual HTML
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()

# Check for mobile nav items
import re
mobile_nav = re.search(r'o_header_mobile.*?</header>', content, re.DOTALL)
if mobile_nav:
    nav_text = mobile_nav.group(0)
    has_items = any(name in nav_text for name in ["首頁", "關於我們", "天然香品"])
    print(f"\nMobile header has menu items: {has_items}")
    # Count nav-links in mobile header
    mobile_links = re.findall(r'nav-link', nav_text)
    print(f"Mobile nav-link count: {len(mobile_links)}")
else:
    print("\nNo mobile header found")

# Check desktop nav
desktop_nav = re.search(r'd-none d-lg-block.*?</nav>', content, re.DOTALL)
if desktop_nav:
    desk_text = desktop_nav.group(0)
    desk_links = re.findall(r'nav-link', desk_text)
    print(f"Desktop nav-link count: {len(desk_links)}")

print("\n=== Theme fixes applied ===")
print("Please clear browser cache and reload to see changes.")
