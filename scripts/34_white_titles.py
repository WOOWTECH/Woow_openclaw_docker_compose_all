#!/usr/bin/env python3
"""
Fix ALL page titles on cover/hero images to be WHITE with strong text-shadow.
Checks every page's inline styles and updates the master CSS.
"""
import xmlrpc.client
import json

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

WHITE_SHADOW = "color:#FFFFFF !important;text-shadow:0 3px 12px rgba(0,0,0,0.8),0 1px 4px rgba(0,0,0,0.5) !important"

# ================================================================
# 1. Update Master CSS for ALL cover/hero titles
# ================================================================
print("=" * 60)
print("1. Master CSS: Force white titles on ALL covers")
print("=" * 60)

css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    cd = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cd[0]["arch"]

    white_title_css = """
/* === WHITE TITLES ON ALL COVERS === */
/* Homepage hero */
#wrap > section:first-child h1,
#wrap > section:first-child h2,
#wrap > section:first-child p {
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.5) !important;
}

/* Blog listing page header */
.o_blog_header h1,
.o_blog_header h2 {
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8) !important;
}

/* Blog post cover title */
#o_wblog_post_name,
.o_blog_post_page h1,
.o_blog_cover_title {
    color: #FFFFFF !important;
    font-size: 28px !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.5) !important;
}

/* Blog post cover subtitle */
#o_wblog_post_subtitle,
.o_blog_post_page .lead {
    color: #f0f0f0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6) !important;
}

/* Record cover container - ALL titles inside */
.o_record_cover_container h1,
.o_record_cover_container h2,
.o_record_cover_container h3,
.o_record_cover_container .h1,
.o_record_cover_container .h2 {
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.5) !important;
}

.o_record_cover_container p,
.o_record_cover_container span,
.o_record_cover_container .text-muted {
    color: #f0f0f0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6) !important;
}

/* Activity page hero */
.oe_structure > section:first-child h1,
.oe_structure > section:first-child p {
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8) !important;
}

/* Dark background section titles */
section[style*='27292C'] h1,
section[style*='27292C'] h2,
section[style*='27292C'] h3,
section[style*='27292C'] p {
    color: #FFFFFF !important;
}

/* Blog card listing titles over cover */
.o_blog_post .o_record_cover_container .o_blog_post_title {
    color: #FFFFFF !important;
    text-shadow: 0 3px 12px rgba(0,0,0,0.8) !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* Ensure cover overlay is dark enough */
.o_record_cover_container .o_record_cover_image + div,
.o_record_cover_container::after {
    background: rgba(0,0,0,0.35) !important;
}

/* Blog next/prev post titles */
.o_blog_post_cover_title {
    color: #FFFFFF !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.7) !important;
}

/* Blog author in cover */
.o_record_cover_component {
    color: #f0f0f0 !important;
}
"""

    if "WHITE TITLES ON ALL COVERS" not in arch:
        safe_css = white_title_css.replace("&", "&amp;")
        arch = arch.replace("</style>", safe_css + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
        print("  Added white title CSS for ALL covers")
    else:
        print("  Already has white title CSS")

# ================================================================
# 2. Fix homepage hero inline styles
# ================================================================
print("\n" + "=" * 60)
print("2. Fix homepage hero inline text colors")
print("=" * 60)

hp = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
if hp:
    arch = hp[0]["arch"]
    changed = False

    # Fix the main title - ensure white
    if "color:#D8B772" in arch and "禪香不二" in arch:
        # The title was set to gold, change to white
        arch = arch.replace(
            "font-size:24px;font-weight:600;letter-spacing:3px;text-shadow:0 2px 10px rgba(0,0,0,0.7);color:#D8B772",
            "font-size:28px;font-weight:700;letter-spacing:4px;text-shadow:0 3px 12px rgba(0,0,0,0.8);color:#FFFFFF"
        )
        changed = True

    # Fix subtitle
    if "color:#D8B772;font-family" in arch:
        arch = arch.replace("color:#D8B772;font-family", "color:#FFFFFF;font-family")
        changed = True

    if changed:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1303], {"arch": arch}])
        print("  Fixed homepage hero text to white")
    else:
        print("  Homepage hero already white or different structure")

# ================================================================
# 3. Fix activity page hero inline styles
# ================================================================
print("\n" + "=" * 60)
print("3. Fix activity page hero inline text colors")
print("=" * 60)

act_pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/activity"]]
], {"fields": ["view_id"]})
if act_pages:
    act_id = act_pages[0]["view_id"][0]
    av = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[act_id], ["arch"]])
    if av:
        arch = av[0]["arch"]
        changed = False
        # Ensure hero title is white with shadow
        if 'color:#D8B772;font-size:16px' in arch:
            arch = arch.replace(
                'color:#D8B772;font-size:16px;letter-spacing:2px',
                'color:#FFFFFF;font-size:18px;letter-spacing:2px;text-shadow:0 2px 10px rgba(0,0,0,0.7)'
            )
            changed = True
        if changed:
            models.execute_kw(db, uid, password, "ir.ui.view", "write", [[act_id], {"arch": arch}])
            print("  Fixed activity hero subtitle to white")

# ================================================================
# 4. Fix about page hero inline styles
# ================================================================
print("\n" + "=" * 60)
print("4. Fix about page hero inline text colors")
print("=" * 60)

about_pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/about-us"]]
], {"fields": ["view_id"]})
if about_pages:
    about_id = about_pages[0]["view_id"][0]
    abv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[about_id], ["arch"]])
    if abv:
        arch = abv[0]["arch"]
        # Ensure hero title and subtitle are white
        if 'color: #27292C; font-family' in arch:
            arch = arch.replace(
                "color: #27292C; font-family: 'Montserrat'",
                "color: #FFFFFF; font-family: 'Montserrat'"
            )
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[about_id], {"arch": arch}])
        print("  Fixed about page section labels")

# ================================================================
# 5. Verify
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request

# Check that CSS has white title rules
resp = urllib.request.urlopen("http://localhost:8069/")
html = resp.read().decode()
has_white_css = "WHITE TITLES ON ALL COVERS" in html
has_shadow = "text-shadow: 0 3px 12px" in html
print(f"  Homepage: white_css={has_white_css}, shadow={has_shadow}")

# Check blog
resp2 = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
blog = resp2.read().decode()
has_blog_white = "#FFFFFF" in blog and "o_record_cover" in blog
print(f"  Blog: white_in_css={has_blog_white}")

# Check all pages load
for p in ["/", "/about-us", "/shop", "/contactus", "/activity", "/blog", "/qa"]:
    try:
        r = urllib.request.urlopen(f"http://localhost:8069{p}")
        print(f"  [200] {p}")
    except:
        print(f"  [ERR] {p}")

print("\n=== White titles fix complete ===")
