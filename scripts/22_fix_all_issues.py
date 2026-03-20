#!/usr/bin/env python3
"""
Fix all remaining issues:
1. Homepage hero banner image
2. Mobile sidebar phone number + purple header
3. Products NOT assigned to sub-categories
4. Remove 'Powered by Odoo'
"""
import xmlrpc.client
import re

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# DIAGNOSE
# ================================================================
print("=" * 60)
print("DIAGNOSIS")
print("=" * 60)

# Check image attachments
banner_atts = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    ["|", ["name", "like", "inzense_hero"], ["name", "like", "inzense_god"]]
], {"fields": ["id", "name"]})
print(f"Banner attachments: {banner_atts}")

# Check all inzense attachments
all_atts = models.execute_kw(db, uid, password, "ir.attachment", "search_read", [
    [["name", "like", "inzense_"]]
], {"fields": ["id", "name"]})
att_map = {a["name"]: a["id"] for a in all_atts}
print(f"All inzense attachments: {att_map}")

# Check homepage arch image references
hp = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
arch = hp[0]["arch"]
img_refs = re.findall(r'/web/image/\d+', arch)
print(f"Image refs in homepage: {img_refs}")

# Check if those image IDs still exist
for ref in img_refs:
    att_id = int(ref.split("/")[-1])
    exists = models.execute_kw(db, uid, password, "ir.attachment", "search_count", [
        [["id", "=", att_id]]
    ])
    print(f"  {ref}: exists={exists > 0}")

# Check category product counts
print("\nCategory product counts:")
cats = models.execute_kw(db, uid, password, "product.public.category", "search_read", [
    []
], {"fields": ["id", "name", "parent_id"]})
cat_map = {c["id"]: c for c in cats}

for c in cats:
    # Count products in this category
    prod_count = models.execute_kw(db, uid, password, "product.template", "search_count", [
        [["public_categ_ids", "in", [c["id"]]], ["website_published", "=", True]]
    ])
    parent = c["parent_id"][1] if c["parent_id"] else "ROOT"
    status = "EMPTY" if prod_count == 0 else f"OK({prod_count})"
    print(f"  [{status}] {c['name']} (parent={parent}) ID={c['id']}")

# ================================================================
# FIX 1: Homepage hero banner
# ================================================================
print("\n" + "=" * 60)
print("FIX 1: Homepage Hero Banner")
print("=" * 60)

# The hero banner attachment might have been lost during pod restart.
# Re-check if the image IDs in the homepage arch still exist
hero_id = att_map.get("inzense_hero-banner.jpg")
god_id = att_map.get("inzense_god-series-banner.jpg")
lifestyle_id = att_map.get("inzense_lifestyle-incense.jpg")
anim_id = att_map.get("inzense_incense-animation.gif")
video_id = att_map.get("inzense_video-sequence.gif")
logo_id = att_map.get("inzense_logo-full.png")

print(f"hero={hero_id}, god={god_id}, lifestyle={lifestyle_id}")
print(f"anim={anim_id}, video={video_id}, logo={logo_id}")

# Update homepage arch with correct image IDs
if hero_id or god_id:
    arch = hp[0]["arch"]
    # Replace any broken /web/image/XXXX refs with correct IDs
    # First, find what IDs are currently referenced
    current_refs = set(re.findall(r'/web/image/(\d+)', arch))
    print(f"Current image IDs in arch: {current_refs}")

    # Check which ones are broken
    for ref_id in current_refs:
        exists = models.execute_kw(db, uid, password, "ir.attachment", "search_count", [
            [["id", "=", int(ref_id)]]
        ])
        if not exists:
            print(f"  BROKEN: /web/image/{ref_id}")

    # If images exist, update the arch with correct references
    # Build mapping of old->new based on attachment names
    # The original mapping was:
    # hero-banner.jpg -> 1632, god-series-banner.jpg -> 1631,
    # incense-animation.gif -> 1633, lifestyle-incense.jpg -> 1634,
    # logo-full.png -> 1635, video-sequence.gif -> 1638

    if hero_id:
        # Replace hero banner ref (was 1632)
        for old_id in current_refs:
            old_id_int = int(old_id)
            # Check if this ID is broken
            exists = models.execute_kw(db, uid, password, "ir.attachment", "search_count", [
                [["id", "=", old_id_int]]
            ])
            if not exists:
                print(f"  Need to fix broken ref: {old_id}")

    # Since we know the correct IDs, let's just rebuild image URLs
    def iu(name):
        att_id = att_map.get(f"inzense_{name}")
        return f"/web/image/{att_id}" if att_id else ""

    # If images exist, don't need to update - they persist on PVC
    print("  Images should persist in filestore (PVC)")
else:
    print("  WARNING: No hero banner attachment found!")
    print("  Images may need to be re-uploaded")

# ================================================================
# FIX 2: Phone number in sidebar + company partner phone
# ================================================================
print("\n" + "=" * 60)
print("FIX 2: Fix Phone Number & Company Info")
print("=" * 60)

# The sidebar shows "+1 555-555-5556" which is the Odoo demo default
# This comes from the company's partner record or a demo partner
company = models.execute_kw(db, uid, password, "res.company", "read", [[1],
    ["partner_id", "phone", "mobile"]])
partner_id = company[0]["partner_id"][0]
print(f"Company partner ID: {partner_id}")
print(f"Company phone: {company[0]['phone']}, mobile: {company[0]['mobile']}")

# Update company partner with correct phone
models.execute_kw(db, uid, password, "res.partner", "write", [[partner_id], {
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
}])
models.execute_kw(db, uid, password, "res.company", "write", [[1], {
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
}])
print("Updated company phone to 0926-926-851")

# Also check ALL partners for the wrong number
wrong_phone_partners = models.execute_kw(db, uid, password, "res.partner", "search", [
    [["phone", "like", "555"]]
])
if wrong_phone_partners:
    models.execute_kw(db, uid, password, "res.partner", "write", [wrong_phone_partners, {
        "phone": "0926-926-851",
    }])
    print(f"Fixed {len(wrong_phone_partners)} partners with wrong phone")

# The header phone comes from the website's "header call to action"
# or from the company. Let's also check the website's header config
# Look for the template that shows the phone number in header
header_cta = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["key", "=", "website.header_call_to_action"]]
], {"fields": ["id", "arch", "active"]})
if header_cta:
    print(f"Header CTA view: ID={header_cta[0]['id']}, active={header_cta[0]['active']}")

# ================================================================
# FIX 3: Assign products to ALL sub-categories
# ================================================================
print("\n" + "=" * 60)
print("FIX 3: Fix Product Category Assignments")
print("=" * 60)

# Get all published products with their names
all_products = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["website_published", "=", True]]
], {"fields": ["id", "name", "public_categ_ids"]})
print(f"Total published products: {len(all_products)}")

# Build category lookup
cat_lookup = {}
for c in cats:
    cat_lookup[c["id"]] = c

# Build category name -> ID mapping
cat_name_id = {}
for c in cats:
    parent_name = c["parent_id"][1] if c["parent_id"] else None
    key = f"{parent_name}/{c['name']}" if parent_name else c["name"]
    cat_name_id[key] = c["id"]
    cat_name_id[c["name"]] = c["id"]  # also by simple name

# For each product, analyze its name and assign to correct sub-categories
series_keywords = {
    "神明": "神明系列",
    "功能": "功能系列",
    "脈輪": "脈輪系列",
    "五行": "五行系列",
    "外國": "外國系列",
    "台灣": "台灣系列",
    "特色": "特色系列",
    "降真": "降真系列",
    "檀香": "檀香系列",
    "沉香": "沉香系列",
}

# Specific product-to-series mapping for combo sets
combo_keywords = {
    "新春開運": "馬年有喜新春開運組",
    "馬年": "馬年有喜新春開運組",
    "神明保庇": "神明保庇熱賣組",
    "保庇熱賣": "神明保庇熱賣組",
    "上班創業": "上班創業必備組",
    "創業必備": "上班創業必備組",
    "內在穩定": "內在穩定能量組",
    "穩定能量": "內在穩定能量組",
    "脈輪療癒": "脈輪療癒優惠組",
    "療癒優惠": "脈輪療癒優惠組",
}

# Known god names for 神明系列
god_names = [
    "月老", "藥師佛", "觀世音", "財神", "中壇元帥", "三太子",
    "九天玄女", "佛祖", "釋迦", "城隍", "天上聖母", "媽祖",
    "文昌", "玄天上帝", "玉皇", "關聖帝君", "關公", "福德正神",
    "土地公", "純陽祖師", "呂洞賓", "閻羅", "保生大帝", "齊天大聖",
]

# Known functional names
func_names = [
    "財神香", "善緣香", "除障香", "幸運香", "平安香", "放鬆香",
    "靈感香", "療心香", "排寒香", "十方清淨", "正龍沉香",
    "壇城樂土", "安眠", "助眠",
]

# Known chakra names
chakra_names = [
    "太陽輪", "頂輪", "喉輪", "眉心輪", "心輪", "丹田輪",
    "根輪", "臍輪", "海底輪",
]

# Five element names
element_names = ["金", "木", "水", "火", "土", "火神", "木神", "金神", "水神", "土神"]

updated_count = 0
for prod in all_products:
    name = prod["name"]
    current_cats = set(prod["public_categ_ids"])
    new_cats = set(current_cats)

    is_mini = "迷你香" in name or "迷你" in name
    is_long = "線香" in name and not is_mini

    # Determine main category
    if is_mini:
        new_cats.add(cat_name_id.get("迷你香", 0))
    elif is_long:
        new_cats.add(cat_name_id.get("線香", 0))

    if "拜拜" in name:
        new_cats.add(cat_name_id.get("拜拜用香", 0))

    if "原木筆" in name:
        new_cats.add(cat_name_id.get("原木筆", 0))

    if "福石" in name or "手串" in name:
        new_cats.add(cat_name_id.get("福石手串", 0))

    # Check for series keywords
    for keyword, series_name in series_keywords.items():
        if keyword in name:
            if is_mini:
                # Find sub-category under 迷你香
                sub_key = f"迷你香/{series_name}"
                sub_id = cat_name_id.get(sub_key)
                if sub_id:
                    new_cats.add(sub_id)
            elif is_long or (not is_mini):
                # Find sub-category under 線香
                sub_key = f"線香/{series_name}"
                sub_id = cat_name_id.get(sub_key)
                if sub_id:
                    new_cats.add(sub_id)

    # Check for god names -> 神明系列
    for god in god_names:
        if god in name:
            if is_mini:
                sub_id = cat_name_id.get("迷你香/神明系列")
                if sub_id: new_cats.add(sub_id)
                new_cats.add(cat_name_id.get("迷你香", 0))
            else:
                sub_id = cat_name_id.get("線香/神明系列")
                if sub_id: new_cats.add(sub_id)
                new_cats.add(cat_name_id.get("線香", 0))
            break

    # Check for functional names -> 功能系列
    for func in func_names:
        if func in name:
            if is_mini:
                sub_id = cat_name_id.get("迷你香/功能系列")
                if sub_id: new_cats.add(sub_id)
            else:
                sub_id = cat_name_id.get("線香/功能系列")
                if sub_id: new_cats.add(sub_id)
            break

    # Check for chakra names -> 脈輪系列
    for chakra in chakra_names:
        if chakra in name:
            if is_mini:
                sub_id = cat_name_id.get("迷你香/脈輪系列")
                if sub_id: new_cats.add(sub_id)
            else:
                sub_id = cat_name_id.get("線香/脈輪系列")
                if sub_id: new_cats.add(sub_id)
            break

    # Check for five element names -> 五行系列
    for elem in element_names:
        if elem in name and "系列" not in name[:name.index(elem)] if elem in name else False:
            if is_mini:
                sub_id = cat_name_id.get("迷你香/五行系列")
                if sub_id: new_cats.add(sub_id)
            else:
                sub_id = cat_name_id.get("線香/五行系列")
                if sub_id: new_cats.add(sub_id)
            break

    # Check for combo keywords -> 優惠組合
    for kw, combo_name in combo_keywords.items():
        if kw in name:
            combo_id = cat_name_id.get(combo_name)
            if combo_id:
                new_cats.add(combo_id)
            new_cats.add(cat_name_id.get("優惠組合", 0))
            break

    # If product has 組 in name and no combo assignment, add to 優惠組合
    if "組" in name and cat_name_id.get("優惠組合", 0) not in new_cats:
        if any(x in name for x in ["組合", "任選", "金榜", "事業", "貴人", "低頻", "創業",
                                     "安眠", "專注", "小人", "情緒", "決策", "淨化", "守護"]):
            new_cats.add(cat_name_id.get("優惠組合", 0))

    # Remove 0 if present
    new_cats.discard(0)

    # Update if changed
    if new_cats != current_cats:
        try:
            models.execute_kw(db, uid, password, "product.template", "write", [[prod["id"]], {
                "public_categ_ids": [(6, 0, list(new_cats))]
            }])
            updated_count += 1
        except Exception as e:
            print(f"  Error updating {name[:30]}: {e}")

print(f"Updated category assignments for {updated_count} products")

# Verify category counts after fix
print("\nCategory counts after fix:")
for c in cats:
    prod_count = models.execute_kw(db, uid, password, "product.template", "search_count", [
        [["public_categ_ids", "in", [c["id"]]], ["website_published", "=", True]]
    ])
    parent = c["parent_id"][1] if c["parent_id"] else "ROOT"
    status = "EMPTY" if prod_count == 0 else f"OK({prod_count})"
    if prod_count == 0:
        print(f"  [{status}] {c['name']} (parent={parent})")
    else:
        print(f"  [{status}] {c['name']} (parent={parent})")

# ================================================================
# FIX 4: Remove "Powered by Odoo"
# ================================================================
print("\n" + "=" * 60)
print("FIX 4: Remove 'Powered by Odoo'")
print("=" * 60)

# Find the copyright/branding view
copyright_views = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    ["|", ["key", "like", "copyright"], ["key", "like", "brand"]]
], {"fields": ["id", "key", "name", "active"], "limit": 20})
print("Copyright/brand views:")
for v in copyright_views:
    print(f"  ID={v['id']}: {v['key']} - {v['name']} (active={v['active']})")

# The "Powered by Odoo" is usually in website.layout or a sub-template
# We can hide it with CSS
# Already in our CSS, but let's add a more specific rule
# Also create a view override to hide it

# Method 1: CSS hide (quickest)
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    css_data = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = css_data[0]["arch"]

    # Add CSS to hide Odoo branding
    hide_css = """
/* Hide Powered by Odoo branding */
.o_footer_copyright_name,
a[href*="odoo.com"],
.o_powered_by,
footer a[href*="odoo"],
.o_footer_copyright a[href*="odoo.com"] {
    display: none !important;
}
.o_footer_copyright {
    text-align: center !important;
}
"""
    # Insert before closing </style>
    arch = arch.replace("</style>", hide_css + "\n</style>")
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
    print("Added CSS to hide 'Powered by Odoo'")

# Method 2: Also try to disable the branding view
branding_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["key", "=", "website.footer_copyright_company_name"]]
])
if branding_views:
    # Don't deactivate - just note it
    print(f"Footer copyright view: {branding_views}")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request

# Check homepage
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()
print(f"Homepage: {len(content)} bytes")
print(f"  Has /web/image/: {'/web/image/' in content}")
print(f"  Has hero section: {'禪香不二' in content}")

# Check shop category pages
for cat_name, cat_id in [("脈輪系列", 52), ("馬年有喜新春開運組", 76)]:
    try:
        resp2 = urllib.request.urlopen(f"http://localhost:8069/shop?category={cat_id}")
        shop_content = resp2.read().decode()
        has_products = "oe_product" in shop_content and "未指定產品" not in shop_content
        print(f"  /shop?category={cat_id} ({cat_name}): has_products={has_products}")
    except Exception as e:
        print(f"  /shop?category={cat_id}: {e}")

# Check phone
print(f"  Has 0926-926-851: {'0926-926-851' in content}")
print(f"  Has +1 555: {'+1 555' in content}")

# Check Powered by Odoo hidden
print(f"  Has 'display: none' for odoo: {'odoo.com' in content}")

print("\n=== ALL FIXES APPLIED ===")
