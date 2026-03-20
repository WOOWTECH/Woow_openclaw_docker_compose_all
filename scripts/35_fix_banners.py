#!/usr/bin/env python3
"""
Fix all pages that have plain color banners — add background images.
Pages to fix: blog listing, contact, privacy, return, QA
"""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Get available image IDs
atts = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "like", "inzense_"]]
], {"fields": ["id", "name"]})
att_map = {a["name"].replace("inzense_", ""): a["id"] for a in atts}
print(f"Available images: {att_map}")

lifestyle_id = att_map.get("lifestyle-incense.jpg")
workshop_id = att_map.get("activity_course-incense-workshop.jpg")
god_id = att_map.get("god-series-banner.jpg")
logo_id = att_map.get("logo-full.png")

# ================================================================
# FIX 1: Blog listing page — add banner image via CSS
# ================================================================
print("\n" + "=" * 60)
print("FIX 1: Blog listing page banner")
print("=" * 60)

# The blog header is rendered by Odoo's blog template.
# We can add a background image via CSS targeting .o_blog_header
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    cd = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cd[0]["arch"]

    banner_css = f"""
/* === PAGE BANNER IMAGES === */

/* Blog listing header - add background image */
.o_blog_header {{
    background-image: url('/web/image/{lifestyle_id}') !important;
    background-size: cover !important;
    background-position: center !important;
    position: relative !important;
    min-height: 250px !important;
}}
.o_blog_header::before {{
    content: '' !important;
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0 !important;
    background: rgba(0,0,0,0.5) !important;
    z-index: 0 !important;
}}
.o_blog_header * {{
    position: relative !important;
    z-index: 1 !important;
}}
.o_blog_header h1 {{
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8) !important;
    font-size: 36px !important;
}}
"""

    if "PAGE BANNER IMAGES" not in arch:
        safe_css = banner_css.replace("&", "&amp;")
        arch = arch.replace("</style>", safe_css + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
        print(f"  Added blog header background: /web/image/{lifestyle_id}")
    else:
        print("  Already has banner CSS")

# ================================================================
# FIX 2: Contact page — add hero image
# ================================================================
print("\n" + "=" * 60)
print("FIX 2: Contact page banner")
print("=" * 60)

contact_pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/contactus"]]
], {"fields": ["view_id"]})
if contact_pages:
    cv_id = contact_pages[0]["view_id"][0]
    cv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[cv_id], ["arch"]])
    arch = cv[0]["arch"]

    # Replace plain bg with image bg
    old_hero = 'style="background: #f9f7f4; padding: 60px 0;"'
    new_hero = f'style="position:relative;min-height:250px;overflow:hidden;padding:80px 0;"'
    if old_hero in arch:
        # Add image bg with overlay
        arch = arch.replace(
            old_hero + '>',
            f'{new_hero}>\n'
            f'                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url(/web/image/{lifestyle_id}) center/cover no-repeat;"></div>\n'
            f'                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);"></div>'
        )
        # Fix title color to white
        arch = arch.replace(
            'font-size: 34px; color: #27292C; letter-spacing: 3px; margin-bottom: 10px;">聯絡我們',
            'font-size: 34px; color: #FFFFFF; letter-spacing: 3px; margin-bottom: 10px; text-shadow:0 3px 12px rgba(0,0,0,0.8); position:relative; z-index:2;">聯絡我們'
        )
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[cv_id], {"arch": arch}])
        print(f"  Added contact banner: /web/image/{lifestyle_id}")
    else:
        print("  Contact hero already modified or different structure")

# ================================================================
# FIX 3: Privacy/Return/QA pages — add subtle hero images
# ================================================================
print("\n" + "=" * 60)
print("FIX 3: Policy pages banners")
print("=" * 60)

policy_pages = [
    ("/privacy-policy", "隱私政策"),
    ("/return-policy", "退換貨政策"),
    ("/qa", "常見問題"),
]

for page_url, page_title in policy_pages:
    pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
        [["url", "=", page_url]]
    ], {"fields": ["view_id"]})
    if pages:
        pv_id = pages[0]["view_id"][0]
        pv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[pv_id], ["arch"]])
        arch = pv[0]["arch"]

        old_hero = 'style="background: #f9f7f4; padding: 50px 0;"'
        if old_hero in arch:
            new_hero = f'style="position:relative;min-height:200px;overflow:hidden;padding:70px 0;"'
            arch = arch.replace(
                old_hero + '>',
                f'{new_hero}>\n'
                f'                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url(/web/image/{god_id}) center/cover no-repeat;"></div>\n'
                f'                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.55);"></div>'
            )
            # Fix title to white
            arch = arch.replace(
                f'font-size: 30px; color: #27292C; letter-spacing: 2px;">{page_title}',
                f'font-size: 30px; color: #FFFFFF; letter-spacing: 2px; text-shadow:0 3px 12px rgba(0,0,0,0.8); position:relative; z-index:2;">{page_title}'
            )
            models.execute_kw(db, uid, password, "ir.ui.view", "write", [[pv_id], {"arch": arch}])
            print(f"  {page_url}: Added banner image")
        else:
            print(f"  {page_url}: Already modified or different structure")

# ================================================================
# FIX 4: QA page subtitle
# ================================================================
print("\n" + "=" * 60)
print("FIX 4: QA page subtitle color")
print("=" * 60)

qa_pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/qa"]]
], {"fields": ["view_id"]})
if qa_pages:
    qa_id = qa_pages[0]["view_id"][0]
    qv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[qa_id], ["arch"]])
    arch = qv[0]["arch"]
    # Fix subtitle color if present
    if "Roboto Slab" in arch and "#D8B772" in arch:
        arch = arch.replace("color: #D8B772; font-family: 'Roboto Slab'", "color: #FFFFFF; font-family: 'Roboto Slab'; position:relative; z-index:2; text-shadow:0 2px 8px rgba(0,0,0,0.6)")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[qa_id], {"arch": arch}])
        print("  Fixed QA subtitle to white")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request

# Check blog header
resp = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
blog = resp.read().decode()
has_blog_bg = f"/web/image/{lifestyle_id}" in blog
print(f"  Blog header image: {has_blog_bg}")

# Check other pages
for p in ["/contactus", "/privacy-policy", "/return-policy", "/qa"]:
    resp2 = urllib.request.urlopen(f"http://localhost:8069{p}")
    html = resp2.read().decode()
    has_bg = "/web/image/" in html[:3000] and "background" in html[:3000]
    print(f"  {p}: has_banner_image={has_bg}")

print("\n=== Banner fixes complete ===")
