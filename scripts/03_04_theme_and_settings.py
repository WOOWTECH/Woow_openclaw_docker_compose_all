#!/usr/bin/env python3
"""Phase 3 & 4: Fix CSS theme + Configure logo, favicon, website settings."""
import xmlrpc.client
import base64
import json

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Load image mapping
with open("/tmp/inzense-image-mapping.json") as f:
    img_map = json.load(f)

print("=" * 60)
print("PHASE 3: Fix Custom CSS Theme")
print("=" * 60)

custom_css = r"""
/* ========================================
   Inzense 禪香不二 - Custom Theme CSS
   Matching https://www.inzense.com.tw/
   ======================================== */

/* --- CSS Variables --- */
:root {
    --inzense-primary: #E4916E;
    --inzense-gold: #D8B772;
    --inzense-dark: #27292C;
    --inzense-text: #7A7A7A;
    --inzense-heading: #27292C;
    --inzense-dark-text: #343434;
    --inzense-gray: #54595F;
    --inzense-green: #61CE70;
    --inzense-blue: #13AFF0;
    --inzense-bg-warm: #FBD7B5;
    --inzense-bg-white: #FFFFFF;
}

/* --- Global Typography --- */
body, .o_website_page, #wrapwrap {
    font-family: 'Roboto', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif !important;
    font-size: 14px !important;
    font-weight: 400;
    line-height: 1.8 !important;
    color: var(--inzense-text) !important;
    letter-spacing: 0.3px;
}

h1, h2, h3, h4, h5, h6,
.h1, .h2, .h3, .h4, .h5, .h6 {
    font-family: 'Montserrat', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif !important;
    color: var(--inzense-heading) !important;
    line-height: 1.4 !important;
    font-weight: 600;
}

h1, .h1 { font-size: 36px !important; }
h2, .h2 { font-size: 28px !important; }
h3, .h3 { font-size: 22px !important; }
h4, .h4 { font-size: 18px !important; }

p {
    color: var(--inzense-text);
    line-height: 1.8;
    margin-bottom: 15px;
}

a {
    color: var(--inzense-primary);
    transition: all 0.3s ease;
}
a:hover {
    color: #c97a58;
    text-decoration: none;
}

/* --- Buttons --- */
.btn-primary,
.btn-primary:active,
.btn-primary:focus,
a.btn-primary {
    background-color: var(--inzense-primary) !important;
    border-color: var(--inzense-primary) !important;
    color: #fff !important;
    border-radius: 30px !important;
    padding: 10px 28px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase;
    transition: all 0.3s ease !important;
}
.btn-primary:hover,
a.btn-primary:hover {
    background-color: #c97a58 !important;
    border-color: #c97a58 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(228, 145, 110, 0.35);
}

.btn-secondary,
a.btn-secondary {
    background-color: var(--inzense-gold) !important;
    border-color: var(--inzense-gold) !important;
    color: #fff !important;
    border-radius: 30px !important;
    padding: 10px 28px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
}
.btn-secondary:hover,
a.btn-secondary:hover {
    background-color: #c4a35e !important;
    border-color: #c4a35e !important;
}

/* Outline buttons */
.btn-outline-primary {
    color: var(--inzense-primary) !important;
    border-color: var(--inzense-primary) !important;
    border-radius: 30px !important;
}
.btn-outline-primary:hover {
    background-color: var(--inzense-primary) !important;
    color: #fff !important;
}

/* --- Header/Navbar --- */
header#top {
    background-color: #fff !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
    border-bottom: none !important;
}

header .navbar {
    background-color: #fff !important;
    padding: 8px 0 !important;
}

header .navbar-brand img {
    max-height: 45px !important;
}

header .navbar-nav .nav-link {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--inzense-heading) !important;
    padding: 8px 15px !important;
    letter-spacing: 0.5px;
    transition: color 0.3s ease;
}

header .navbar-nav .nav-link:hover,
header .navbar-nav .nav-link.active {
    color: var(--inzense-primary) !important;
}

/* Dropdown menus */
header .dropdown-menu {
    border: none !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1) !important;
    border-radius: 4px !important;
    padding: 10px 0 !important;
}

header .dropdown-item {
    font-size: 13px !important;
    padding: 6px 20px !important;
    color: var(--inzense-gray) !important;
}

header .dropdown-item:hover {
    background-color: #fdf5ef !important;
    color: var(--inzense-primary) !important;
}

/* --- Footer --- */
footer, #footer {
    background-color: var(--inzense-dark) !important;
    color: #ccc !important;
    padding: 50px 0 20px !important;
    font-size: 13px !important;
}

footer h5, footer .h5,
#footer h5, #footer .h5 {
    color: var(--inzense-gold) !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin-bottom: 15px !important;
    letter-spacing: 1px;
}

footer a, #footer a {
    color: #ccc !important;
    transition: color 0.3s ease;
}

footer a:hover, #footer a:hover {
    color: var(--inzense-gold) !important;
}

footer .o_footer_copyright {
    border-top: 1px solid rgba(255,255,255,0.1) !important;
    margin-top: 30px !important;
    padding-top: 20px !important;
    color: #888 !important;
    font-size: 12px !important;
}

/* --- Section Styling --- */
.inzense-section {
    padding: 70px 0;
}

.inzense-section-title {
    text-align: center;
    margin-bottom: 40px;
}

.inzense-section-title h2 {
    font-size: 30px !important;
    margin-bottom: 8px;
}

.inzense-section-title .subtitle {
    color: var(--inzense-primary);
    font-family: 'Roboto Slab', serif;
    font-size: 14px;
    letter-spacing: 2px;
}

/* Hero/Cover sections */
section.s_cover {
    position: relative;
}

.inzense-hero-overlay {
    background: rgba(0,0,0,0.4);
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
}

.inzense-hero-content {
    position: relative;
    z-index: 2;
    text-align: center;
    padding: 120px 20px;
}

.inzense-hero-content h1 {
    color: #fff !important;
    font-size: 48px !important;
    font-weight: 700 !important;
    letter-spacing: 5px;
    margin-bottom: 15px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.inzense-hero-content .tagline {
    color: var(--inzense-gold);
    font-family: 'Roboto Slab', serif;
    font-size: 20px;
    letter-spacing: 3px;
    margin-bottom: 8px;
}

.inzense-hero-content p {
    color: #eee !important;
    font-size: 16px;
    letter-spacing: 1.5px;
    margin-bottom: 35px;
}

/* --- Product Cards --- */
.oe_product_cart {
    border: none !important;
    border-radius: 8px !important;
    overflow: hidden;
    transition: all 0.3s ease;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

.oe_product_cart:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

.oe_product_cart .product_price {
    color: var(--inzense-primary) !important;
    font-weight: 700 !important;
}

/* --- Category Cards --- */
.inzense-cat-card {
    background: #fff;
    border-radius: 8px;
    padding: 35px 20px;
    text-align: center;
    box-shadow: 0 2px 15px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}

.inzense-cat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.inzense-cat-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #fff;
}

.inzense-cat-card h4 {
    font-size: 18px !important;
    margin-bottom: 10px;
}

.inzense-cat-card p {
    font-size: 13px;
    color: var(--inzense-gray);
}

.inzense-cat-card a {
    color: var(--inzense-primary);
    font-size: 13px;
    font-weight: 600;
}

/* --- Blog Cards --- */
.inzense-blog-card {
    padding: 25px;
    border-bottom: 3px solid var(--inzense-gold);
    transition: all 0.3s ease;
    background: #fff;
}

.inzense-blog-card:hover {
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
}

.inzense-blog-card h4 {
    font-size: 17px !important;
    margin-bottom: 10px;
}

/* --- Quote/Testimonial --- */
.inzense-quote {
    font-family: 'Cormorant Garamond', 'Noto Sans TC', serif;
    font-size: 20px;
    font-style: italic;
    color: var(--inzense-gray);
    line-height: 1.8;
    padding: 20px 40px;
    border-left: 3px solid var(--inzense-gold);
    margin: 30px 0;
}

/* --- Warm Background Section --- */
.inzense-bg-warm {
    background-color: var(--inzense-bg-warm) !important;
}

.inzense-bg-dark {
    background-color: var(--inzense-dark) !important;
}

/* --- Contact Page --- */
.inzense-contact-info h5 {
    color: var(--inzense-primary) !important;
    font-size: 16px !important;
    margin-bottom: 10px;
}

.inzense-location-card {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 25px;
    margin-bottom: 20px;
    border-left: 4px solid var(--inzense-primary);
}

/* --- Responsive --- */
@media (max-width: 767px) {
    .inzense-hero-content h1 {
        font-size: 32px !important;
        letter-spacing: 3px;
    }
    .inzense-hero-content .tagline {
        font-size: 16px;
    }
    .inzense-section {
        padding: 40px 0;
    }
    h2, .h2 {
        font-size: 24px !important;
    }
}

@media (max-width: 1024px) {
    header .navbar-nav .nav-link {
        font-size: 13px !important;
        padding: 6px 10px !important;
    }
}

/* --- Shop page --- */
.o_wsale_products_grid_table_wrapper .oe_product {
    margin-bottom: 20px;
}

.oe_website_sale .oe_product_cart .oe_product_image {
    border-radius: 8px 8px 0 0 !important;
}

/* --- Add to cart button in shop --- */
.oe_website_sale .a-submit,
.oe_website_sale .btn-primary {
    background-color: var(--inzense-primary) !important;
    border-color: var(--inzense-primary) !important;
    border-radius: 30px !important;
}

/* --- Breadcrumbs --- */
.breadcrumb {
    background: transparent !important;
    font-size: 13px;
}

.breadcrumb a {
    color: var(--inzense-primary) !important;
}

/* --- Odoo specific overrides --- */
.o_website_page .container {
    max-width: 1200px;
}

/* Fix Odoo default blue to our primary */
.text-primary { color: var(--inzense-primary) !important; }
.bg-primary { background-color: var(--inzense-primary) !important; }
.border-primary { border-color: var(--inzense-primary) !important; }
.text-secondary { color: var(--inzense-gold) !important; }
.bg-secondary { background-color: var(--inzense-gold) !important; }

/* Override Odoo's default purple/brand color */
.o_main_nav .active > .nav-link,
.o_main_nav .nav-link:hover {
    color: var(--inzense-primary) !important;
}

/* Fix the website editor's theme colors */
.o_we_color_btn.o_we_color_1 { background-color: var(--inzense-primary) !important; }
.o_we_color_btn.o_we_color_2 { background-color: var(--inzense-gold) !important; }
.o_we_color_btn.o_we_color_3 { background-color: var(--inzense-dark) !important; }
.o_we_color_btn.o_we_color_4 { background-color: var(--inzense-bg-warm) !important; }
.o_we_color_btn.o_we_color_5 { background-color: var(--inzense-green) !important; }
"""

css_view_content = f'''<t t-name="website.inzense_custom_css" t-inherit="website.layout" t-inherit-mode="extension">
    <xpath expr="//head" position="inside">
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&amp;family=Montserrat:wght@400;500;600;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;family=Parisienne&amp;family=Poppins:wght@400;500;600&amp;family=Roboto+Slab:wght@400;500&amp;family=Roboto:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
        <style type="text/css">{custom_css}</style>
    </xpath>
</t>'''

# Update existing CSS view
css_view_ids = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])

if css_view_ids:
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_view_ids, {
        "arch": css_view_content,
        "active": True,
    }])
    print(f"Updated CSS view ID={css_view_ids[0]}")
else:
    website_ids = models.execute_kw(db, uid, password, "website", "search", [[]])
    vid = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
        "name": "Inzense Custom CSS",
        "type": "qweb",
        "arch": css_view_content,
        "key": "website.inzense_custom_css",
        "website_id": website_ids[0] if website_ids else False,
        "active": True,
    }])
    print(f"Created CSS view ID={vid}")

print("Phase 3 CSS theme: DONE")

print("\n" + "=" * 60)
print("PHASE 4: Logo, Favicon, Website Settings")
print("=" * 60)

# Upload logo to company
with open("/tmp/inzense-images/logo-header.png", "rb") as f:
    logo_data = base64.b64encode(f.read()).decode()

with open("/tmp/inzense-images/logo-full.png", "rb") as f:
    logo_full_data = base64.b64encode(f.read()).decode()

# Set company logo
models.execute_kw(db, uid, password, "res.company", "write", [[1], {
    "name": "禪香不二 Inzense",
    "logo": logo_full_data,
    "phone": "0926-926-851",
    "email": "service@inzense.com.tw",
    "street": "台北市北投區光明路240號2樓之8",
    "city": "台北市",
    "zip": "112",
}])
print("Company logo and info updated")

# Set website favicon and settings
website_ids = models.execute_kw(db, uid, password, "website", "search", [[]])
if website_ids:
    models.execute_kw(db, uid, password, "website", "write", [[website_ids[0]], {
        "name": "禪香不二 Inzense",
        "favicon": logo_data,
        "social_facebook": "https://www.facebook.com/onlyinzense",
        "social_instagram": "https://instagram.com/only_inzense",
    }])
    print(f"Website settings updated: ID={website_ids[0]}")

    # Also set the website logo
    logo_att_id = img_map.get("logo-header.png")
    if logo_att_id:
        models.execute_kw(db, uid, password, "website", "write", [[website_ids[0]], {
            "logo": logo_data,
        }])
        print(f"Website logo set from attachment ID={logo_att_id}")

print("Phase 4 settings: DONE")
