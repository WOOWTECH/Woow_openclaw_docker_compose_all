#!/usr/bin/env python3
"""
Inzense Odoo 18 — Phase 1: Master CSS Consolidation
Single authoritative CSS source — replaces all previous CSS layers.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/71_master_css_consolidation.py
"""
import xmlrpc.client
import urllib.request
import re

URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


def sr(model, domain, fields, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, "search_read", [domain], {"fields": fields, **kw})


def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASSWORD, model, "write", [ids, vals])


# ============================================================
# Step 1: Delete ALL existing Inzense CSS views
# ============================================================
print("\n=== Step 1: Clean up old CSS views ===")
old_css = sr("ir.ui.view", ["|", "|",
    ["key", "ilike", "inzense_custom_css"],
    ["key", "ilike", "inzense_custom"],
    ["name", "ilike", "Inzense Custom CSS"],
], ["id", "key", "name"], context={"active_test": False})

for v in old_css:
    if "birthday" in (v.get("key") or ""):
        continue  # Keep the birthday field view
    try:
        models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "unlink", [[v["id"]]])
        print(f"  Deleted: id={v['id']} key={v['key']}")
    except Exception as e:
        print(f"  Cannot delete id={v['id']}: {e}")

# ============================================================
# Step 2: Find layout view inherit_id
# ============================================================
print("\n=== Step 2: Find layout view ===")
layout_ids = models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "search", [
    [["key", "=", "website.layout"]]
])
layout_id = layout_ids[0] if layout_ids else False
print(f"  Layout view ID: {layout_id}")
assert layout_id, "Cannot find website.layout view"

# ============================================================
# Step 3: Create master CSS
# ============================================================
print("\n=== Step 3: Create master CSS view ===")

MASTER_CSS = """
/* ============================================================
   Inzense Master Theme — Single Source of Truth
   Colors: Gold #D8B772 | Cyan #13AFF0 | Dark #27292C
   Fonts: Cormorant Garamond (headings) | Roboto (body)
   ============================================================ */

/* --- Odoo Color Variable Overrides --- */
:root {
    --o-color-1: #FFFFFF;
    --o-color-2: #f9f7f4;
    --o-color-3: #27292C;
    --o-color-4: #13AFF0;
    --o-color-5: #D8B772;
    --o-cc1-bg: #FFFFFF;
    --o-cc1-btn-primary: #D8B772;
    --o-cc1-link: #13AFF0;
    --o-cc3-bg: #27292C;
    --o-cc3-headings: #D8B772;
    --o-cc3-link: #D8B772;
    --inzense-gold: #D8B772;
    --inzense-gold-hover: #7E6124;
    --inzense-cyan: #13AFF0;
    --inzense-cyan-hover: #0d8bcf;
    --inzense-dark: #27292C;
    --inzense-text: #343434;
    --inzense-bg-warm: #f9f7f4;
}

/* --- Global Typography --- */
body, #wrapwrap {
    font-family: 'Roboto', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif !important;
    font-size: 14px;
    line-height: 1.8;
    color: #343434;
}
h1, h2, h3 {
    font-family: 'Cormorant Garamond', 'Noto Sans TC', serif !important;
    color: #27292C;
    font-weight: 600;
    line-height: 1.4;
}
h4, h5, h6 {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif !important;
    color: #27292C;
    font-weight: 600;
}
a { color: #13AFF0; transition: color 0.2s; }
a:hover { color: #0d8bcf; text-decoration: none; }

/* --- Header (White, Clean) --- */
#wrapwrap header, header#top, header .navbar,
header .o_header_standard, header .o_colored_level,
header .o_cc, header .o_cc1, .o_header_mobile,
.o_header_mobile .navbar {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border-bottom: 1px solid #f0f0f0 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05) !important;
}
header .navbar-brand img {
    max-height: 80px !important;
    max-width: 200px !important;
    object-fit: contain;
}
header .nav-link, header .nav-item > a {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #27292C !important;
    letter-spacing: 0.5px;
    transition: color 0.2s;
}
header .nav-link:hover, header .nav-item > a:hover {
    color: #13AFF0 !important;
}
header .nav-link.active, header .nav-item.active > a {
    color: #13AFF0 !important;
}
header .dropdown-menu {
    border: 1px solid #f0f0f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border-radius: 4px;
}
header .dropdown-item:hover {
    background-color: #f0f8ff;
    color: #13AFF0;
}

/* --- Mobile Header & Offcanvas --- */
.o_header_mobile .navbar-toggler {
    border: none !important;
    color: #27292C;
}
.offcanvas, .offcanvas-body {
    background: #FFFFFF !important;
}
.offcanvas-header {
    background: #27292C !important;
    color: #FFFFFF !important;
}
.offcanvas-header .btn-close {
    filter: invert(1) !important;
}
.offcanvas .nav-link {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #27292C !important;
    padding: 12px 16px !important;
    border-bottom: 1px solid #f0f0f0;
}
.offcanvas .nav-link:hover {
    color: #13AFF0 !important;
    background: #f0f8ff;
}

/* --- Buttons --- */
.btn-primary, .btn-primary.rounded-circle {
    background-color: #D8B772 !important;
    border-color: #D8B772 !important;
    border-radius: 36px !important;
    padding: 12px 36px !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    color: #FFFFFF !important;
    transition: all 0.3s;
}
.btn-primary:hover, .btn-primary:focus {
    background-color: #7E6124 !important;
    border-color: #7E6124 !important;
    color: #FFFFFF !important;
}
.btn-secondary {
    background-color: #13AFF0 !important;
    border-color: #13AFF0 !important;
    border-radius: 36px !important;
    color: #FFFFFF !important;
}
.btn-secondary:hover {
    background-color: #0d8bcf !important;
    border-color: #0d8bcf !important;
}

/* --- Footer --- */
footer, #bottom, .o_footer, main ~ footer {
    background-color: #27292C !important;
    color: #cccccc !important;
}
footer h5, footer h4 {
    color: #D8B772 !important;
    font-family: 'Roboto', sans-serif !important;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 16px;
}
footer a { color: #cccccc !important; }
footer a:hover { color: #D8B772 !important; }
footer .o_footer_copyright {
    border-top: 1px solid rgba(255,255,255,0.1);
    color: #666;
    font-size: 12px;
}

/* Hide Odoo branding */
.o_footer_copyright_name, a[href*="odoo.com"],
.o_powered_by, footer a[href*="odoo"],
.o_footer_copyright .o_footer_powered_by,
footer .text-muted a[href*="odoo"] {
    display: none !important;
}

/* --- Product Cards (Shop) --- */
.oe_product_cart {
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    overflow: hidden;
}
.oe_product_cart:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
.oe_product_cart .oe_product_image {
    aspect-ratio: 1 / 1;
    overflow: hidden;
    background: #f9f7f4;
}
.oe_product_cart .oe_product_image img {
    object-fit: cover;
    width: 100%;
    height: 100%;
}
.oe_product_cart .product_price .oe_price,
.oe_product_cart .oe_currency_value {
    color: #D8B772 !important;
    font-weight: 700 !important;
    font-size: 18px;
}
.oe_product_cart h6 a {
    color: #27292C !important;
    font-weight: 500;
}
.oe_product_cart h6 a:hover {
    color: #13AFF0 !important;
}

/* --- Shop Category Sidebar --- */
#products_grid_before .nav-link {
    color: #27292C;
    font-weight: 500;
    padding: 8px 12px;
    border-radius: 4px;
    transition: all 0.2s;
}
#products_grid_before .nav-link:hover,
#products_grid_before .nav-link.active {
    color: #13AFF0 !important;
    background: #f0f8ff;
}

/* --- Product Detail Page --- */
#product_detail .product_price .oe_price,
#product_detail .oe_default_price {
    font-size: 28px !important;
    color: #D8B772 !important;
    font-weight: 700 !important;
}
#product_detail .css_not_available_msg { display: none; }

/* --- Breadcrumb --- */
.breadcrumb a { color: #13AFF0 !important; }
.breadcrumb-item.active { color: #7A7A7A; }

/* --- Odoo Color Utility Overrides --- */
.text-primary { color: #13AFF0 !important; }
.bg-primary { background-color: #D8B772 !important; }
.bg-secondary { background-color: #13AFF0 !important; }

/* --- Inzense Custom Classes --- */
.inzense-hero {
    position: relative;
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}
.inzense-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.45);
}
.inzense-hero > * { position: relative; z-index: 1; }

.inzense-section { padding: 60px 0; }
.inzense-section-warm { background-color: #f9f7f4; }
.inzense-section-dark {
    background-color: #27292C;
    color: #FFFFFF;
}
.inzense-section-dark h2,
.inzense-section-dark h3 { color: #D8B772 !important; }
.inzense-section-dark p { color: #cccccc; }

.inzense-gold { color: #D8B772 !important; }
.inzense-cyan { color: #13AFF0 !important; }

.inzense-card {
    background: #FFFFFF;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s;
}
.inzense-card:hover { transform: translateY(-2px); }

.inzense-card-accent {
    border-left: 4px solid #D8B772;
}

.inzense-category-card {
    background: #f9f7f4;
    border-radius: 8px;
    padding: 28px 20px;
    text-align: center;
    transition: all 0.3s;
    text-decoration: none !important;
    display: block;
}
.inzense-category-card:hover {
    background: #FFFFFF;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    transform: translateY(-3px);
}
.inzense-category-card h5 {
    color: #27292C !important;
    margin-bottom: 8px;
}
.inzense-category-card p {
    color: #7A7A7A;
    font-size: 13px;
    margin-bottom: 0;
}
.inzense-category-card .browse-link {
    color: #13AFF0;
    font-weight: 600;
    font-size: 13px;
}

.inzense-member-feature {
    text-align: center;
    padding: 20px;
}
.inzense-member-feature i {
    font-size: 32px;
    color: #D8B772;
    margin-bottom: 12px;
}
.inzense-member-feature h5 { color: #FFFFFF !important; font-size: 16px; }
.inzense-member-feature p { color: #aaaaaa; font-size: 13px; }

.inzense-testimonial {
    background: #f9f7f4;
    border-left: 4px solid #D8B772;
    border-radius: 0 8px 8px 0;
    padding: 20px 24px;
}
.inzense-testimonial .author {
    color: #D8B772;
    font-weight: 600;
    font-size: 13px;
    margin-top: 8px;
}

/* --- Value Bar --- */
.inzense-value-bar {
    background: #f9f7f4;
    padding: 20px 0;
    text-align: center;
}
.inzense-value-item {
    font-size: 14px;
    font-weight: 600;
    color: #27292C;
    letter-spacing: 1px;
}
.inzense-value-item i { color: #D8B772; margin-right: 6px; }

/* --- CTA Banner --- */
.inzense-cta-banner {
    position: relative;
    background-size: cover;
    background-position: center;
    padding: 80px 20px;
    text-align: center;
}
.inzense-cta-banner::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(39,41,44,0.6);
}
.inzense-cta-banner > * { position: relative; z-index: 1; }
.inzense-cta-banner h2 {
    color: #FFFFFF !important;
    font-size: 28px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.inzense-cta-banner p {
    color: #D8B772;
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 18px;
}

/* --- Portal / Member Center --- */
.o_portal .breadcrumb { background: transparent; }
.o_portal_my_doc_table th { background: #f9f7f4; color: #27292C; }
.o_portal_my_doc_table .badge {
    background-color: #D8B772 !important;
    color: #FFFFFF;
}

/* --- Performance --- */
#wrap > section:nth-child(n+3) {
    content-visibility: auto;
    contain-intrinsic-size: auto 500px;
}
.oe_product { content-visibility: auto; contain-intrinsic-size: auto 350px; }

/* --- Responsive --- */
@media (max-width: 768px) {
    header .navbar-brand img { max-height: 50px !important; max-width: 140px !important; }
    h1 { font-size: 24px !important; }
    h2 { font-size: 20px !important; }
    .inzense-hero { min-height: 320px !important; padding: 60px 16px !important; }
    .inzense-section { padding: 40px 0; }
    .btn-primary { padding: 10px 28px !important; font-size: 14px !important; }
    .oe_product_cart .oe_product_image { aspect-ratio: 1/1; }
}
@media (max-width: 480px) {
    header .navbar-brand img { max-height: 40px !important; max-width: 120px !important; }
    .inzense-hero { min-height: 280px !important; }
}
"""

# Escape for XML
css_escaped = MASTER_CSS.replace("&", "&amp;")

arch = f'''<data inherit_id="website.layout" name="Inzense Custom CSS">
    <xpath expr="//head" position="inside">
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;family=Roboto:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
        <style>{css_escaped}</style>
    </xpath>
</data>'''

new_id = models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "create", [{
    "name": "Inzense Custom CSS",
    "type": "qweb",
    "arch": arch,
    "key": "website.inzense_custom_css",
    "inherit_id": layout_id,
    "website_id": 1,
    "active": True,
    "priority": 99,
}])
print(f"  ✅ Created CSS view: id={new_id}, inherit_id={layout_id}")

# ============================================================
# Step 4: Verify rendering
# ============================================================
print("\n=== Step 4: Verify CSS renders ===")
resp = urllib.request.urlopen(f"{URL}/")
content = resp.read().decode()

has_gold = "D8B772" in content
has_cyan = "13AFF0" in content
has_fonts = "fonts.googleapis" in content
has_wrong = "E4916E" in content

print(f"  Gold #D8B772 in page: {'✅' if has_gold else '❌'}")
print(f"  Cyan #13AFF0 in page: {'✅' if has_cyan else '❌'}")
print(f"  Google Fonts loaded: {'✅' if has_fonts else '❌'}")
print(f"  Wrong #E4916E absent: {'✅' if not has_wrong else '❌ STILL PRESENT'}")

# Check style blocks
styles = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
for i, s in enumerate(styles):
    if "D8B772" in s or "inzense" in s.lower():
        print(f"  ✅ Found Inzense CSS in style block {i} ({len(s)} chars)")
        break
else:
    print(f"  ⚠ Inzense CSS not found in {len(styles)} style blocks")

print(f"\n  Page size: {len(content):,} bytes")
print("\nPhase 1 complete.")
