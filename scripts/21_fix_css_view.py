#!/usr/bin/env python3
"""Fix the CSS view to properly inherit from website.layout so it renders."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Check current state
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["name", "=", "Inzense Custom CSS"]]
], {"fields": ["id", "key", "inherit_id", "active", "website_id", "type", "arch"],
    "context": {"active_test": False}})

layout_ids = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["key", "=", "website.layout"]]
])
layout_id = layout_ids[0] if layout_ids else False

print(f"Layout view ID: {layout_id}")
print(f"CSS views found: {len(css_views)}")

for v in css_views:
    print(f"  ID={v['id']}: key={v['key']}, inherit={v['inherit_id']}, active={v['active']}, ws={v['website_id']}")

# The arch must use proper Odoo extension format with xpath
# Delete existing and recreate properly
for v in css_views:
    models.execute_kw(db, uid, password, "ir.ui.view", "unlink", [[v["id"]]])
    print(f"  Deleted old CSS view {v['id']}")

# Read the master CSS from the script
import os
css_file = "/tmp/20_visual_alignment.py"
master_css = ""
if os.path.exists(css_file):
    with open(css_file) as f:
        content = f.read()
    # Extract the CSS between the triple-quote markers
    import re
    match = re.search(r'master_css = r"""(.*?)"""', content, re.DOTALL)
    if match:
        master_css = match.group(1)
        print(f"  Extracted CSS: {len(master_css)} chars")

if not master_css:
    # Fallback: minimal critical CSS
    master_css = """
/* Inzense Theme Override */
:root {
    --o-color-1: #FFFFFF !important;
    --o-color-4: #13AFF0 !important;
    --o-color-5: #D8B772 !important;
    --o-cc1-bg: #FFFFFF !important;
    --o-cc1-btn-primary: #D8B772 !important;
    --o-cc1-link: #13AFF0 !important;
}
header, header .o_colored_level, header .o_cc, .o_header_mobile,
header .navbar, .o_header_mobile .navbar {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
}
header .navbar-brand img { max-height: 80px !important; max-width: 200px !important; }
header .nav-link { font-size: 15px !important; font-weight: 700 !important; color: #000 !important; }
header .nav-link:hover { color: #13AFF0 !important; }
.btn-primary { background-color: #D8B772 !important; border-color: #D8B772 !important;
    border-radius: 36px !important; padding: 14px 40px !important; font-weight: 700 !important;
    letter-spacing: 2px !important; color: #fff !important; }
.btn-primary:hover { background-color: #7E6124 !important; border-color: #7E6124 !important; }
footer, .o_footer { background-color: #27292C !important; }
footer h5 { color: #D8B772 !important; }
.oe_product_cart { border-radius: 4px !important; }
.oe_currency_value, .product_price { color: #D8B772 !important; font-weight: 700 !important; }
.breadcrumb a { color: #13AFF0 !important; }
a { color: #13AFF0; }
a:hover { color: #0d8bcf; }
.text-primary { color: #13AFF0 !important; }
    """
    print(f"  Using fallback CSS: {len(master_css)} chars")

# Escape CSS for XML
master_css_escaped = master_css.replace("&", "&amp;")

# Create with proper Odoo inherit_id extension format
arch = f'''<data inherit_id="website.layout" name="Inzense Custom CSS">
    <xpath expr="//head" position="inside">
        <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&amp;family=Montserrat:wght@400;500;600;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;family=Parisienne&amp;family=Poppins:wght@400;500;600&amp;family=Roboto+Slab:wght@400;500&amp;family=Roboto:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
        <style>{master_css_escaped}</style>
    </xpath>
</data>'''

new_id = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
    "name": "Inzense Custom CSS",
    "type": "qweb",
    "arch": arch,
    "key": "website.inzense_custom_css",
    "inherit_id": layout_id,
    "website_id": 1,
    "active": True,
    "priority": 99,
}])
print(f"Created new CSS view: ID={new_id}, inherit_id={layout_id}")

# Verify it renders
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()

has_style = "#D8B772" in content or "D8B772" in content
has_fonts = "fonts.googleapis" in content
print(f"\nVerification:")
print(f"  Has gold color in page: {has_style}")
print(f"  Has Google Fonts: {has_fonts}")
print(f"  Page size: {len(content)} bytes")

# Check for style tag content
import re
styles = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
for i, s in enumerate(styles):
    if "D8B772" in s or "13AFF0" in s:
        print(f"  Style block {i}: Contains our theme colors ({len(s)} chars)")
        break
else:
    print(f"  WARNING: No style block contains our theme colors")
    print(f"  Total style blocks: {len(styles)}")
    # Maybe it's in a CSS file instead
    css_links = re.findall(r'href="(/web/assets/[^"]+\.css[^"]*)"', content)
    print(f"  CSS asset links: {len(css_links)}")
    for cl in css_links[:3]:
        print(f"    {cl}")

print("\n=== Done ===")
