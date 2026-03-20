#!/usr/bin/env python3
"""
PRD Implementation: Complete visual alignment to match inzense.com.tw
Fixes: color palette, header, mobile menu, buttons, typography, all pages.
"""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# FIX 1: Master CSS — Correct Color Palette
# ================================================================
print("=" * 60)
print("FIX 1: Corrected Master CSS")
print("=" * 60)

master_css = r"""
/* ============================================
   Inzense 禪香不二 - Visual Alignment CSS
   Matching https://www.inzense.com.tw/
   KEY COLORS:
     Cyan accent: #13AFF0 (links, hover, active)
     Gold CTA: #D8B772 (buttons)
     Dark gold hover: #7E6124
     Dark: #27292C (headings, footer bg)
     White: #FFFFFF (header bg)
   ============================================ */

/* --- Override Odoo Color System --- */
:root {
    --o-color-1: #FFFFFF !important;
    --o-color-2: #f9f7f4 !important;
    --o-color-3: #27292C !important;
    --o-color-4: #13AFF0 !important;
    --o-color-5: #D8B772 !important;

    --o-color-1-btn-primary: #D8B772 !important;
    --o-color-1-btn-primary-border: #D8B772 !important;
    --o-color-1-btn-secondary: #13AFF0 !important;
    --o-color-1-btn-secondary-border: #13AFF0 !important;

    --o-cc1-bg: #FFFFFF !important;
    --o-cc1-btn-primary: #D8B772 !important;
    --o-cc1-btn-primary-border: #D8B772 !important;
    --o-cc1-text: #27292C !important;
    --o-cc1-headings: #27292C !important;
    --o-cc1-link: #13AFF0 !important;

    --o-cc3-bg: #27292C !important;
    --o-cc3-text: #CCCCCC !important;
    --o-cc3-headings: #D8B772 !important;
    --o-cc3-link: #D8B772 !important;
}

/* --- Global Typography --- */
body, #wrapwrap {
    font-family: 'Roboto', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.8 !important;
    color: #343434 !important;
}

h1, h2, h3, h4, h5, h6,
.h1, .h2, .h3, .h4, .h5, .h6 {
    font-family: 'Montserrat', 'Noto Sans TC', sans-serif !important;
    color: #27292C !important;
    line-height: 1.4 !important;
    font-weight: 600;
}

a { color: #13AFF0; transition: all 0.3s ease; }
a:hover { color: #0d8bcf; text-decoration: none; }

/* --- HEADER — FORCE WHITE on ALL devices --- */
#wrapwrap header,
#wrapwrap header.o_colored_level,
#wrapwrap header .o_colored_level,
#wrapwrap header[data-bs-theme],
header, header#top,
header .navbar,
header .o_header_standard,
header .o_colored_level,
header .o_cc,
header .o_cc1,
header .o_cc.o_cc1,
header .o_header_mobile,
header .o_header_mobile .navbar,
.o_header_mobile,
.o_header_mobile .navbar {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #27292C !important;
    border-bottom: 1px solid #f0f0f0 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05) !important;
}

/* Logo */
header .navbar-brand img {
    max-height: 80px !important;
    max-width: 200px !important;
}
@media (max-width: 991px) {
    header .navbar-brand img { max-height: 55px !important; }
}
@media (max-width: 575px) {
    header .navbar-brand img { max-height: 40px !important; }
}

/* Desktop Nav Links */
header .navbar-nav .nav-link,
header .nav-link {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #000000 !important;
    padding: 8px 18px !important;
    letter-spacing: 0.5px;
    transition: color 0.3s ease;
}
header .navbar-nav .nav-link:hover,
header .nav-link:hover,
header .navbar-nav .nav-link.active,
.o_main_nav .active > .nav-link,
.o_main_nav .nav-link:hover,
.o_main_nav .nav-link.active {
    color: #13AFF0 !important;
}

/* Dropdown */
header .dropdown-menu {
    border: none !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1) !important;
    border-radius: 4px !important;
    padding: 8px 0 !important;
}
header .dropdown-item {
    font-size: 13px !important;
    padding: 7px 20px !important;
    color: #54595F !important;
}
header .dropdown-item:hover {
    background-color: #f0f8ff !important;
    color: #13AFF0 !important;
}

/* --- Mobile Sidebar / Offcanvas --- */
.offcanvas, .offcanvas-start,
#top_menu_collapse_mobile,
.o_main_nav .offcanvas {
    background-color: #FFFFFF !important;
}
.offcanvas-header {
    background-color: #27292C !important;
    color: #fff !important;
    padding: 15px 20px !important;
}
.offcanvas-header .btn-close {
    filter: invert(1) !important;
}
.offcanvas .nav-link,
.offcanvas .dropdown-toggle,
#top_menu_collapse_mobile .nav-link {
    color: #27292C !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    border-bottom: 1px solid #f0f0f0 !important;
}
.offcanvas .nav-link:hover,
.offcanvas .dropdown-toggle:hover {
    color: #13AFF0 !important;
    background-color: #f0f8ff !important;
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
    color: #13AFF0 !important;
    background-color: #f0f8ff !important;
}

/* Mobile hamburger icon */
header .navbar-toggler {
    border: none !important;
    color: #27292C !important;
    padding: 4px 8px !important;
}

/* --- BUTTONS — Gold CTA --- */
.btn-primary,
.btn-primary:active,
.btn-primary:focus,
a.btn-primary {
    background-color: #D8B772 !important;
    border-color: #D8B772 !important;
    color: #fff !important;
    border-radius: 36px !important;
    padding: 14px 40px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    transition: all 0.3s ease !important;
}
.btn-primary:hover,
a.btn-primary:hover {
    background-color: #7E6124 !important;
    border-color: #7E6124 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(216,183,114,0.35);
}

.btn-secondary, a.btn-secondary {
    background-color: #13AFF0 !important;
    border-color: #13AFF0 !important;
    color: #fff !important;
    border-radius: 36px !important;
    padding: 14px 40px !important;
    font-weight: 700 !important;
}
.btn-secondary:hover, a.btn-secondary:hover {
    background-color: #0d8bcf !important;
    border-color: #0d8bcf !important;
}

/* Outline buttons (for dark bg CTAs) */
.btn-outline-light,
.inzense-btn-outline {
    background: transparent !important;
    border: 2px solid #fff !important;
    color: #fff !important;
    border-radius: 30px !important;
    padding: 14px 40px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
}
.btn-outline-light:hover,
.inzense-btn-outline:hover {
    background: #fff !important;
    color: #000 !important;
}

/* --- FOOTER --- */
footer, #bottom, .o_footer {
    background-color: #27292C !important;
    color: #ccc !important;
    font-size: 13px !important;
}
footer h5, footer .h5, #bottom h5 {
    color: #D8B772 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase;
    margin-bottom: 15px !important;
}
footer a, #bottom a { color: #ccc !important; }
footer a:hover, #bottom a:hover { color: #D8B772 !important; }
footer .o_footer_copyright,
.o_footer_copyright {
    border-top: 1px solid rgba(255,255,255,0.1) !important;
    margin-top: 30px !important;
    padding-top: 15px !important;
    color: #666 !important;
    font-size: 12px !important;
}

/* --- PRODUCT CARDS (Shop Page) --- */
.oe_product_cart {
    border: none !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    overflow: hidden;
}
.oe_product_cart:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}

/* Product title - left aligned */
.oe_product_cart .card-body,
.oe_product_cart .product_name {
    text-align: left !important;
}
.oe_product_cart .product_name span {
    font-weight: 400 !important;
    font-size: 14px !important;
}

/* Product price */
.oe_product_cart .product_price,
.oe_product .product_price,
.oe_currency_value,
.product_price .oe_price {
    color: #D8B772 !important;
    font-weight: 700 !important;
}

/* Shop "Add to Cart" — squared style for grid */
.oe_website_sale .oe_product_cart .a-submit,
.oe_website_sale .oe_product_cart .btn-primary {
    border-radius: 4px !important;
    padding: 8px 16px !important;
    font-size: 12px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase;
}

/* Shop category sidebar */
.o_wsale_products_categories .nav-link {
    color: #27292C !important;
    font-size: 15px !important;
    padding: 6px 0 !important;
}
.o_wsale_products_categories .nav-link:hover,
.o_wsale_products_categories .nav-link.active {
    color: #13AFF0 !important;
    font-weight: 600;
}

/* Breadcrumbs */
.breadcrumb { background: transparent !important; font-size: 13px; }
.breadcrumb a { color: #13AFF0 !important; }

/* --- Blog Cards --- */
.inzense-blog-card {
    padding: 25px;
    border-bottom: 3px solid #D8B772;
    background: #fff;
    transition: all 0.3s ease;
}
.inzense-blog-card:hover {
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

/* --- Homepage decorative section labels --- */
.inzense-section-label {
    font-family: 'Montserrat', sans-serif;
    font-size: 18px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #27292C;
    margin-bottom: 8px;
}

/* --- Contact Page --- */
.inzense-location-card {
    background: #fff;
    border-radius: 8px;
    padding: 25px;
    border-left: 4px solid #13AFF0;
    margin-bottom: 20px;
}

/* --- Override Odoo default purple/blue everywhere --- */
.text-primary { color: #13AFF0 !important; }
.bg-primary { background-color: #D8B772 !important; }
.border-primary { border-color: #D8B772 !important; }
.text-secondary { color: #D8B772 !important; }
.bg-secondary { background-color: #13AFF0 !important; }

/* --- Responsive --- */
@media (max-width: 767px) {
    h1, .h1 { font-size: 26px !important; }
    h2, .h2 { font-size: 22px !important; }
    .btn-primary, a.btn-primary {
        padding: 10px 28px !important;
        font-size: 13px !important;
    }
}

/* --- Product detail page --- */
.oe_website_sale #product_detail .product_price {
    color: #D8B772 !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}
.oe_website_sale #product_detail .a-submit,
.oe_website_sale #product_detail .btn-primary {
    border-radius: 36px !important;
    padding: 14px 40px !important;
}

/* --- Cart page --- */
.oe_website_sale .oe_cart .btn-primary {
    border-radius: 36px !important;
}

/* --- Searchbar --- */
.o_searchbar_form .btn {
    background-color: #D8B772 !important;
    border-color: #D8B772 !important;
    border-radius: 0 4px 4px 0 !important;
}
"""

css_view_content = f'''<t t-name="website.inzense_custom_css" t-inherit="website.layout" t-inherit-mode="extension">
    <xpath expr="//head" position="inside">
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&amp;family=Montserrat:wght@400;500;600;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;family=Parisienne&amp;family=Poppins:wght@400;500;600&amp;family=Roboto+Slab:wght@400;500&amp;family=Roboto:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
        <style type="text/css">{master_css}</style>
    </xpath>
</t>'''

css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
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

# ================================================================
# FIX 2: Homepage — Update inline styles to match corrected palette
# ================================================================
print("\n" + "=" * 60)
print("FIX 2: Homepage inline style corrections")
print("=" * 60)

# Get current homepage arch
hp_view = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
if hp_view:
    arch = hp_view[0]["arch"]
    original_len = len(arch)

    # Fix inline colors
    arch = arch.replace("color:#D8B772;font-family:'Roboto Slab'", "color:#27292C;font-family:'Montserrat'")
    arch = arch.replace("font-size:13px;letter-spacing:3px;text-transform:uppercase", "font-size:16px;letter-spacing:0.8px;text-transform:uppercase")
    arch = arch.replace("color:#E4916E;font-weight:600", "color:#13AFF0;font-weight:600")
    arch = arch.replace("style=\"color:#E4916E;", "style=\"color:#13AFF0;")
    arch = arch.replace("background-color:#E4916E", "background:linear-gradient(180deg,#D8B772 0%,#B5994E 100%)")
    arch = arch.replace("background:#D8B772;color:#fff;border-radius:30px", "background:transparent;border:2px solid #fff;color:#fff;border-radius:30px")
    # Fix hero height
    arch = arch.replace("min-height:550px", "min-height:680px")
    arch = arch.replace("padding:160px 20px 140px", "padding:200px 20px 180px")

    if len(arch) != original_len:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1303], {"arch": arch}])
        print(f"  Updated homepage: {original_len} -> {len(arch)} chars")
    else:
        print("  Homepage arch unchanged (already correct or different structure)")

# ================================================================
# FIX 3: About page — Update inline styles
# ================================================================
print("\n" + "=" * 60)
print("FIX 3: About page style corrections")
print("=" * 60)

about_views = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/about-us"]]
], {"fields": ["view_id"]})
if about_views:
    about_view_id = about_views[0]["view_id"][0]
    av = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[about_view_id], ["arch"]])
    if av:
        arch = av[0]["arch"]
        arch = arch.replace("color: #D8B772; font-family: 'Roboto Slab'", "color: #27292C; font-family: 'Montserrat'")
        arch = arch.replace("font-size: 13px; letter-spacing: 3px; text-transform: uppercase", "font-size: 16px; letter-spacing: 0.8px; text-transform: uppercase")
        arch = arch.replace("background: #E4916E;", "background: #D8B772;")
        arch = arch.replace("color: #E4916E;", "color: #13AFF0;")
        arch = arch.replace("background: #61CE70;", "background: #13AFF0;")
        # Fix heading font
        arch = arch.replace("font-size: 28px; margin-bottom: 20px; color: #27292C;\">品牌故事",
                          "font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 500; letter-spacing: 2.4px; margin-bottom: 20px; color: #27292C;\">品牌故事")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[about_view_id], {"arch": arch}])
        print(f"  Updated about page view ID={about_view_id}")

# ================================================================
# FIX 4: Contact page — Fix accent colors
# ================================================================
print("\n" + "=" * 60)
print("FIX 4: Contact page corrections")
print("=" * 60)

contact_views = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/contactus"]]
], {"fields": ["view_id"]})
if contact_views:
    cv_id = contact_views[0]["view_id"][0]
    cv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[cv_id], ["arch"]])
    if cv:
        arch = cv[0]["arch"]
        arch = arch.replace("color: #E4916E;", "color: #13AFF0;")
        arch = arch.replace("color: #D8B772; font-family: 'Roboto Slab'", "color: #27292C; font-family: 'Montserrat'")
        arch = arch.replace("font-size: 13px; letter-spacing: 3px; text-transform: uppercase", "font-size: 16px; letter-spacing: 0.8px; text-transform: uppercase")
        arch = arch.replace("border-left: 4px solid #E4916E", "border-left: 4px solid #13AFF0")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[cv_id], {"arch": arch}])
        print(f"  Updated contact page view ID={cv_id}")

# ================================================================
# FIX 5: Activity page — Fix colors
# ================================================================
print("\n" + "=" * 60)
print("FIX 5: Activity page corrections")
print("=" * 60)

activity_views = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/activity"]]
], {"fields": ["view_id"]})
if activity_views:
    act_id = activity_views[0]["view_id"][0]
    actv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[act_id], ["arch"]])
    if actv:
        arch = actv[0]["arch"]
        arch = arch.replace("background: #E4916E;", "background: #D8B772;")
        arch = arch.replace("color: #E4916E;", "color: #13AFF0;")
        arch = arch.replace("background: #61CE70;", "background: #13AFF0;")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[act_id], {"arch": arch}])
        print(f"  Updated activity page view ID={act_id}")

# ================================================================
# FIX 6: Footer — Use Font Awesome icons for social
# ================================================================
print("\n" + "=" * 60)
print("FIX 6: Footer social icon fix")
print("=" * 60)

footer_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["key", "=", "website.footer_custom"], ["website_id", "=", 1]]
])
if footer_views:
    fv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [footer_views, ["arch"]])
    if fv:
        arch = fv[0]["arch"]
        # Replace text social links with FA icons
        arch = arch.replace(
            '<a href="https://www.facebook.com/onlyinzense" target="_blank" style="color:#D8B772;margin-right:15px;">Facebook</a>',
            '<a href="https://www.facebook.com/onlyinzense" target="_blank" style="color:#D8B772;margin-right:15px;font-size:18px;"><i class="fa fa-facebook-square"></i></a>'
        )
        arch = arch.replace(
            '<a href="https://instagram.com/only_inzense" target="_blank" style="color:#D8B772;">Instagram</a>',
            '<a href="https://instagram.com/only_inzense" target="_blank" style="color:#D8B772;font-size:18px;"><i class="fa fa-instagram"></i></a>'
        )
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [footer_views, {"arch": arch}])
        print(f"  Updated footer with social icons")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()

checks = {
    "#D8B772": "Gold CTA color",
    "#13AFF0": "Cyan accent color",
    "#FFFFFF !important": "White header override",
    "Montserrat": "Montserrat font loaded",
    "Parisienne": "Parisienne font loaded",
    "border-radius: 36px": "36px button radius",
    "font-weight: 700": "Bold nav font",
    "max-height: 80px": "Large logo",
}

for text, desc in checks.items():
    found = text in content
    print(f"  [{'OK' if found else 'MISS'}] {desc}")

print("\n=== Visual alignment complete ===")
print("Clear browser cache (Ctrl+Shift+R) to see changes.")
