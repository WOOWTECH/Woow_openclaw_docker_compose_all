#!/usr/bin/env python3
"""
1. Change blog listing banner to real workshop photo (course-incense-workshop.jpg)
2. Add global rounded corners (border-radius) to ALL images site-wide
"""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Get image IDs
atts = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "like", "inzense_"]]
], {"fields": ["id", "name"]})
att_map = {a["name"].replace("inzense_", ""): a["id"] for a in atts}
print(f"Images: {att_map}")

workshop_id = att_map.get("activity_course-incense-workshop.jpg", 5697)
print(f"Workshop photo ID: {workshop_id}")

# ================================================================
# FIX 1: Blog banner - use workshop photo
# ================================================================
print("\n" + "=" * 60)
print("FIX 1: Blog listing banner -> workshop photo")
print("=" * 60)

css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    cd = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cd[0]["arch"]

    # Replace the lifestyle image with workshop image in blog header
    lifestyle_id = att_map.get("lifestyle-incense.jpg", 1634)
    old_ref = f"/web/image/{lifestyle_id}"
    new_ref = f"/web/image/{workshop_id}"

    # Only replace in the blog header CSS rule
    if f"o_blog_header" in arch and old_ref in arch:
        # Find and replace only in the blog header section
        arch = arch.replace(
            f"background-image: url('{old_ref}') !important",
            f"background-image: url('{new_ref}') !important"
        )
        print(f"  Changed blog header bg: {old_ref} -> {new_ref}")

    # ================================================================
    # FIX 2: Global rounded corners on ALL images
    # ================================================================
    print("\n" + "=" * 60)
    print("FIX 2: Global rounded corners on all images")
    print("=" * 60)

    rounded_css = """
/* === GLOBAL ROUNDED CORNERS === */

/* All content images */
#wrap img,
.oe_structure img,
.o_blog_post img,
article img {
    border-radius: 12px !important;
}

/* Product images */
.oe_product_cart img,
.oe_product_image img,
.o_wsale_product_images img,
#product_detail img {
    border-radius: 12px !important;
}

/* Product card container */
.oe_product_cart .oe_product_image {
    border-radius: 12px 12px 0 0 !important;
    overflow: hidden !important;
}

/* Blog cover images */
.o_record_cover_container,
.o_record_cover_image {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Blog post listing cards */
.o_blog_post .o_record_cover_container {
    border-radius: 12px !important;
}

/* Homepage section images */
.oe_structure section img.img-fluid {
    border-radius: 12px !important;
}

/* Activity page course images */
.oe_structure img[alt*="課程"],
.oe_structure img[alt*="course"],
.oe_structure img[alt*="系列"] {
    border-radius: 12px !important;
}

/* About page images */
.oe_structure img[alt*="禪香"],
.oe_structure img[alt*="Matt"] {
    border-radius: 12px !important;
}

/* Hero/banner sections - rounded bottom corners */
#wrap > section:first-child,
.oe_structure > section:first-child {
    border-radius: 0 0 12px 12px !important;
    overflow: hidden !important;
}

/* Blog header rounded bottom */
.o_blog_header {
    border-radius: 0 0 12px 12px !important;
    overflow: hidden !important;
}

/* Page banner sections (contact, policy pages) */
.oe_structure > section:first-child {
    overflow: hidden !important;
}

/* Video embed rounded */
iframe[src*="youtube"] {
    border-radius: 12px !important;
}

/* Footer - no rounded corners (full width) */
footer img,
#bottom img {
    border-radius: 0 !important;
}

/* Logo in header - no rounding */
header img {
    border-radius: 0 !important;
}

/* Carousel/slider images */
.carousel-item img {
    border-radius: 12px !important;
}
"""

    if "GLOBAL ROUNDED CORNERS" not in arch:
        safe_css = rounded_css.replace("&", "&amp;")
        arch = arch.replace("</style>", safe_css + "\n</style>")
        print("  Added global rounded corners CSS")
    else:
        print("  Already has rounded corners CSS")

    # Write the updated CSS
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
    print("  CSS view updated")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request

# Blog header
resp = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
blog = resp.read().decode()
has_workshop = f"/web/image/{workshop_id}" in blog
has_rounded = "border-radius: 12px" in blog
print(f"  Blog: workshop_photo={has_workshop}, rounded_css={has_rounded}")

# Homepage
resp2 = urllib.request.urlopen("http://localhost:8069/")
home = resp2.read().decode()
has_rounded_home = "GLOBAL ROUNDED CORNERS" in home
print(f"  Homepage: rounded_css={has_rounded_home}")

# Activity
resp3 = urllib.request.urlopen("http://localhost:8069/activity")
act = resp3.read().decode()
has_rounded_act = "border-radius: 12px" in act
print(f"  Activity: rounded_css={has_rounded_act}")

# Shop
resp4 = urllib.request.urlopen("http://localhost:8069/shop")
shop = resp4.read().decode()
has_rounded_shop = "border-radius: 12px" in shop
print(f"  Shop: rounded_css={has_rounded_shop}")

# All pages status
for p in ["/", "/about-us", "/shop", "/contactus", "/activity", "/blog", "/qa"]:
    try:
        r = urllib.request.urlopen(f"http://localhost:8069{p}")
        print(f"  [200] {p}")
    except:
        print(f"  [ERR] {p}")

print("\n=== Done ===")
