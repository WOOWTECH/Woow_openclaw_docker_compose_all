#!/usr/bin/env python3
"""
PRD v4: Final polish
1. Title text on covers/heroes: 15% larger + white + text-shadow
2. Blog cover images: set actual logo image
3. Fix 'YourCompany' -> '禪香不二'
4. Verify all blog posts have content
"""
import xmlrpc.client
import base64
import os
import json

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# FIX 1: CSS - Title text on covers 15% larger + white + text-shadow
# ================================================================
print("=" * 60)
print("FIX 1: Cover/hero title text styling")
print("=" * 60)

css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])

if css_views:
    css_data = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = css_data[0]["arch"]

    title_css = """
/* === Blog Cover Title Fixes === */

/* Blog list cover - show image background */
.o_record_cover_container {
    min-height: 250px !important;
}

/* Blog post title on cover - 15% bigger + white + shadow */
.o_record_cover_container .o_blog_cover_title,
.o_record_cover_container h1,
.o_record_cover_container h2,
.o_record_cover_container .blog_title {
    color: #FFFFFF !important;
    text-shadow: 0 3px 15px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.6) !important;
    font-size: 115% !important;
}

/* Blog detail page cover title */
.o_blog_post_page .o_record_cover_container h1,
#o_wblog_post_name {
    color: #FFFFFF !important;
    font-size: 32px !important;
    text-shadow: 0 3px 15px rgba(0,0,0,0.8), 0 1px 4px rgba(0,0,0,0.6) !important;
    letter-spacing: 1px;
}

/* Blog cover subtitle */
.o_record_cover_container .text-muted,
.o_record_cover_container p {
    color: #f0f0f0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6) !important;
}

/* Activity page hero title */
.oe_structure section:first-child h1 {
    text-shadow: 0 3px 15px rgba(0,0,0,0.7) !important;
}

/* Blog card in listing - title bigger */
.o_blog_post .o_blog_post_title,
.o_blog_post h5 {
    font-size: 115% !important;
}

/* Blog author line - hide "YourCompany," prefix */
.o_record_cover_component .o_not_editable,
.o_record_cover_component span:first-child {
    font-size: 0 !important;
}
.o_record_cover_component .o_not_editable .o_author_avatar_card ~ span,
.o_record_cover_component span[data-oe-type] {
    font-size: 13px !important;
}

/* Next/prev blog post covers - title styling */
.o_blog_post_cover_title {
    color: #FFFFFF !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.7) !important;
    font-size: 115% !important;
}

/* Fix homepage hero: remove our text overlay since banner has built-in text */
/* The 神明系列BN.jpg already has text baked into the image */
"""

    if "Blog Cover Title Fixes" not in arch:
        # Escape & for XML
        title_css_safe = title_css.replace("&", "&amp;")
        arch = arch.replace("</style>", title_css_safe + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
        print("  Added blog/cover title CSS fixes")
    else:
        print("  Already has blog title fixes")

# ================================================================
# FIX 2: Fix 'YourCompany' -> '禪香不二'
# ================================================================
print("\n" + "=" * 60)
print("FIX 2: Fix company name 'YourCompany'")
print("=" * 60)

# The "YourCompany" text comes from the res.company name
company = models.execute_kw(db, uid, password, "res.company", "read", [[1], ["name"]])
print(f"  Current company name: {company[0]['name']}")

# Also check for "YourCompany" in partner records
yc_partners = models.execute_kw(db, uid, password, "res.partner", "search_read", [
    ["|", ["name", "ilike", "YourCompany"], ["display_name", "ilike", "YourCompany"]]
], {"fields": ["id", "name", "display_name", "company_name"]})
print(f"  Partners with 'YourCompany': {len(yc_partners)}")
for p in yc_partners:
    print(f"    ID={p['id']}: name='{p['name']}', display='{p['display_name']}', company='{p.get('company_name')}'")
    # Fix the company_name field
    updates = {}
    if p.get("company_name") and "YourCompany" in str(p["company_name"]):
        updates["company_name"] = "禪香不二 Inzense"
    if "YourCompany" in str(p.get("name", "")):
        updates["name"] = "禪香不二 Inzense"
    if updates:
        models.execute_kw(db, uid, password, "res.partner", "write", [[p["id"]], updates])
        print(f"    -> Fixed")

# Check if company name itself has YourCompany
if "YourCompany" in company[0]["name"]:
    models.execute_kw(db, uid, password, "res.company", "write", [[1], {"name": "禪香不二 Inzense"}])
    print("  Fixed company name")

# The "YourCompany" in blog might come from res.company or from the blog post's author
# Check the actual company record and its partner
comp_partner = models.execute_kw(db, uid, password, "res.company", "read", [[1], ["partner_id"]])
pid = comp_partner[0]["partner_id"][0]
partner = models.execute_kw(db, uid, password, "res.partner", "read", [[pid], ["name", "company_name", "display_name"]])
print(f"  Company partner: {partner[0]}")

# ================================================================
# FIX 3: Set blog cover images using logo
# ================================================================
print("\n" + "=" * 60)
print("FIX 3: Set blog cover images")
print("=" * 60)

# Find the logo attachment
logo_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_logo-header.png"]]
], {"fields": ["id"]})
logo_id = logo_att[0]["id"] if logo_att else None

# Find activity images for variety
workshop_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_activity_course-incense-workshop.jpg"]]
], {"fields": ["id"]})
workshop_id = workshop_att[0]["id"] if workshop_att else None

tea_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_activity_course-tea-ceremony.jpg"]]
], {"fields": ["id"]})
tea_id = tea_att[0]["id"] if tea_att else None

incense_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_activity_course-incense-ceremony.jpg"]]
], {"fields": ["id"]})
incense_id = incense_att[0]["id"] if incense_att else None

multi_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_activity_course-multi-sensory.jpg"]]
], {"fields": ["id"]})
multi_id = multi_att[0]["id"] if multi_att else None

lifestyle_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_lifestyle-incense.jpg"]]
], {"fields": ["id"]})
lifestyle_id = lifestyle_att[0]["id"] if lifestyle_att else None

god_att = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "=", "inzense_god-series-banner.jpg"]]
], {"fields": ["id"]})
god_id = god_att[0]["id"] if god_att else None

print(f"  Available images: logo={logo_id}, workshop={workshop_id}, tea={tea_id}, incense={incense_id}, lifestyle={lifestyle_id}, god={god_id}")

# Map tags to cover images for variety
tag_image_map = {}
tags = models.execute_kw(db, uid, password, "blog.tag", "search_read", [[]], {"fields": ["id", "name"]})
for t in tags:
    if "靜心" in t["name"]:
        tag_image_map[t["id"]] = incense_id or lifestyle_id
    elif "神明" in t["name"]:
        tag_image_map[t["id"]] = god_id or lifestyle_id
    elif "山醫" in t["name"] or "命卜" in t["name"]:
        tag_image_map[t["id"]] = multi_id or lifestyle_id
    elif "時節" in t["name"]:
        tag_image_map[t["id"]] = workshop_id or lifestyle_id
    elif "食香" in t["name"]:
        tag_image_map[t["id"]] = tea_id or lifestyle_id
    elif "琴棋" in t["name"]:
        tag_image_map[t["id"]] = incense_id or lifestyle_id

# Set cover for all blog posts
all_posts = models.execute_kw(db, uid, password, "blog.post", "search_read", [
    [["blog_id", "=", 3]]
], {"fields": ["id", "name", "tag_ids", "cover_properties"]})

default_cover_id = lifestyle_id or workshop_id or logo_id
updated = 0

for post in all_posts:
    # Pick image based on tag
    img_id = default_cover_id
    if post["tag_ids"]:
        for tid in post["tag_ids"]:
            if tid in tag_image_map:
                img_id = tag_image_map[tid]
                break

    if img_id:
        cover_props = json.dumps({
            "background-image": f"url('/web/image/{img_id}')",
            "resize_class": "o_record_has_cover o_half_screen_height",
            "opacity": "0.4",
        })
        try:
            models.execute_kw(db, uid, password, "blog.post", "write", [[post["id"]], {
                "cover_properties": cover_props,
            }])
            updated += 1
        except Exception as e:
            print(f"  Error on post {post['id']}: {e}")

print(f"  Updated cover images for {updated}/{len(all_posts)} posts")

# ================================================================
# FIX 4: Verify all blog posts have content
# ================================================================
print("\n" + "=" * 60)
print("FIX 4: Verify blog post content")
print("=" * 60)

empty_posts = models.execute_kw(db, uid, password, "blog.post", "search_read", [
    [["blog_id", "=", 3]]
], {"fields": ["id", "name", "content", "website_published"]})

empty_count = 0
for p in empty_posts:
    content = p.get("content", "") or ""
    if len(content.strip()) < 20:
        empty_count += 1
        print(f"  EMPTY: {p['name'][:40]} (content={len(content)} chars)")

if empty_count == 0:
    print(f"  All {len(empty_posts)} posts have content")
else:
    print(f"  {empty_count} posts have insufficient content")

# ================================================================
# FIX 5: Homepage hero - remove redundant text overlay
# ================================================================
print("\n" + "=" * 60)
print("FIX 5: Simplify homepage hero (banner has built-in text)")
print("=" * 60)

hp = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
if hp:
    arch = hp[0]["arch"]
    # The banner image (神明系列BN.jpg) already has Chinese text baked in
    # Our overlay text ("禪香不二 精心製作的天然線香") clashes with the banner text
    # Solution: remove the overlapping title/subtitle, keep only the CTA button
    # and the logo (which is smaller and doesn't overlap)

    # Reduce overlay to let banner show through more
    arch = arch.replace("rgba(0,0,0,0.50)", "rgba(0,0,0,0.30)")

    # Make our text smaller and more subtle since banner has its own text
    old_title = "font-size:42px;font-weight:700;letter-spacing:6px;text-shadow:0 3px 15px rgba(0,0,0,0.7)"
    new_title = "font-size:24px;font-weight:600;letter-spacing:3px;text-shadow:0 2px 10px rgba(0,0,0,0.7);color:#D8B772"
    arch = arch.replace(old_title, new_title)

    # Subtitle - make it white and readable
    arch = arch.replace(
        "color:#D8B772;font-family:'Roboto Slab',serif;font-size:18px;letter-spacing:3px",
        "color:#fff;font-family:'Roboto Slab',serif;font-size:14px;letter-spacing:2px;text-shadow:0 2px 8px rgba(0,0,0,0.6)"
    )

    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1303], {"arch": arch}])
    print("  Simplified homepage hero text to complement banner image")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request
import re

# Blog listing
resp = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
blog_html = resp.read().decode()
has_cover_img = "/web/image/" in blog_html and "o_record_cover" in blog_html
has_yourcompany = "YourCompany" in blog_html
print(f"  Blog list: cover images={has_cover_img}, YourCompany={has_yourcompany}")

# Blog detail
post_links = re.findall(r'href="(/blog/[^"]+/[^"]+)"', blog_html)
if post_links:
    resp2 = urllib.request.urlopen(f"http://localhost:8069{post_links[0]}")
    detail = resp2.read().decode()
    has_title_shadow = "text-shadow" in detail
    has_cover = "o_record_has_cover" in detail
    print(f"  Blog detail: title_shadow={has_title_shadow}, has_cover={has_cover}")

# Homepage
resp3 = urllib.request.urlopen("http://localhost:8069/")
home = resp3.read().decode()
print(f"  Homepage: {len(home)} bytes, has banner={'/web/image/1631' in home}")

# Activity
resp4 = urllib.request.urlopen("http://localhost:8069/activity")
act = resp4.read().decode()
has_courses = all(c in act for c in ["天然香椎手作課程", "生活茶道入門", "生活香道入門"])
print(f"  Activity: {len(act)} bytes, courses={has_courses}")

print("\n=== ALL FIXES APPLIED ===")
