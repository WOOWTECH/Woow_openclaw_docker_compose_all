#!/usr/bin/env python3
"""
Setup Inzense website in Odoo 18 Website module.
Replicates the design and content from inzense.com.tw
"""
import xmlrpc.client
import base64
import sys

url = "http://localhost:8069"
db = "inzense"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
if not uid:
    print("Authentication failed!")
    sys.exit(1)
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

print("=== Setting up Inzense Website ===")

# 1. Configure website settings
website_ids = models.execute_kw(db, uid, password, "website", "search", [[]])
if website_ids:
    website_id = website_ids[0]
    models.execute_kw(db, uid, password, "website", "write", [[website_id], {
        "name": "禪香不二 Inzense",
        "domain": "inzense-odoo.woowtech.io",
        "company_id": 1,
        "default_lang_id": models.execute_kw(db, uid, password, "res.lang", "search", [[["code", "=", "zh_TW"]]])[0],
    }])
    print(f"Website configured: ID={website_id}")

# 2. Set website theme colors via custom CSS
# Color scheme: Primary=#13AFF0, Gold=#D8B772, Dark=#27292C
custom_css = """
/* Inzense Custom Theme - 禪香不二 */
:root {
    --inzense-primary: #13AFF0;
    --inzense-gold: #D8B772;
    --inzense-dark: #27292C;
    --inzense-text: #343434;
    --inzense-gray: #54595F;
}

/* Override Odoo website primary colors */
.o_website_page {
    font-family: 'Roboto', 'Noto Sans TC', sans-serif;
    color: var(--inzense-text);
    letter-spacing: 0.6px;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Montserrat', 'Noto Sans TC', sans-serif;
    color: var(--inzense-dark);
}

.btn-primary {
    background-color: var(--inzense-gold) !important;
    border-color: var(--inzense-gold) !important;
    color: #fff !important;
    letter-spacing: 1px;
    transition: all 0.3s ease;
}

.btn-primary:hover {
    background-color: #c4a35e !important;
    border-color: #c4a35e !important;
}

/* Elegant header */
header .navbar {
    background-color: #fff !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

/* Footer styling */
footer {
    background-color: var(--inzense-dark) !important;
    color: #fff;
}

footer a {
    color: var(--inzense-gold) !important;
}

/* Section spacing */
section.s_text_block,
section.s_image_text,
section.s_three_columns {
    padding: 60px 0;
}
"""

# Create/update custom asset for the CSS
view_ids = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"], ["type", "=", "qweb"]]
])
css_view_content = f"""<template id="inzense_custom_css" inherit_id="website.layout" name="Inzense Custom CSS">
    <xpath expr="//head" position="inside">
        <style>{custom_css}</style>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
    </xpath>
</template>"""

if view_ids:
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [view_ids, {
        "arch": css_view_content,
        "active": True,
    }])
    print("Updated custom CSS view")
else:
    view_id = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
        "name": "Inzense Custom CSS",
        "type": "qweb",
        "arch": css_view_content,
        "key": "website.inzense_custom_css",
        "website_id": website_id,
        "active": True,
    }])
    print(f"Created custom CSS view: ID={view_id}")

# 3. Create Homepage content
homepage_html = """
<div id="wrap" class="oe_structure oe_empty">
    <!-- Hero Section -->
    <section class="s_cover parallax s_parallax_is_fixed pt160 pb160" data-scroll-background-ratio="1" style="background-image: url('/web/image/website.s_cover_default_image'); min-height: 600px; background-color: rgba(39, 41, 44, 0.6);">
        <div class="container text-center">
            <h1 style="color: #fff; font-size: 48px; font-weight: 700; letter-spacing: 3px; margin-bottom: 20px;">禪香不二</h1>
            <p style="color: #D8B772; font-size: 24px; letter-spacing: 2px; margin-bottom: 10px;">精心製作的天然線香</p>
            <p style="color: #fff; font-size: 16px; letter-spacing: 1.5px; margin-bottom: 40px;">結合在地植物香氣，體驗台灣自然之美</p>
            <a href="/shop" class="btn btn-primary btn-lg" style="padding: 15px 40px; font-size: 16px; border-radius: 0;">探索商品</a>
        </div>
    </section>

    <!-- Brand Story Section -->
    <section class="s_text_block pt64 pb64" style="background-color: #fff;">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h2 style="color: #27292C; font-size: 32px; margin-bottom: 20px;">關於 <span style="color: #D8B772;">禪香不二</span></h2>
                    <p style="color: #54595F; font-size: 16px; line-height: 1.8;">
                        禪香不二秉持著對高品質、天然原料的堅持，專注於台灣在地製作。
                        我們的線香採用純天然木本、草本、樹脂漢方配方等香料，不添加任何化學成分或人工香精。
                    </p>
                    <p style="color: #54595F; font-size: 16px; line-height: 1.8;">
                        每一縷香煙，都承載著我們對品質的執著與對自然的敬意。
                    </p>
                    <a href="/about-us" class="btn btn-primary mt-3" style="border-radius: 0; padding: 10px 30px;">了解更多</a>
                </div>
                <div class="col-lg-6">
                    <div style="background: linear-gradient(135deg, #f5f5f5, #e8e8e8); height: 400px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #999; font-size: 18px;">禪香不二品牌形象</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Product Categories Section -->
    <section class="s_three_columns pt64 pb64" style="background-color: #f8f8f8;">
        <div class="container text-center">
            <h2 style="color: #27292C; font-size: 32px; margin-bottom: 10px;">天然香品</h2>
            <p style="color: #D8B772; font-size: 16px; margin-bottom: 40px;">Natural Incense Products</p>
            <div class="row">
                <div class="col-lg-3 col-md-6 mb-4">
                    <div style="background: #fff; padding: 30px 20px; border-radius: 4px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                        <div style="width: 80px; height: 80px; background: #D8B772; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 28px;">香</span>
                        </div>
                        <h4 style="color: #27292C;">線香</h4>
                        <p style="color: #54595F; font-size: 14px;">神明系列・功能系列・脈輪系列・五行系列</p>
                        <a href="/shop" style="color: #D8B772;">瀏覽商品 →</a>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div style="background: #fff; padding: 30px 20px; border-radius: 4px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                        <div style="width: 80px; height: 80px; background: #13AFF0; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 28px;">迷</span>
                        </div>
                        <h4 style="color: #27292C;">迷你香</h4>
                        <p style="color: #54595F; font-size: 14px;">精巧迷你尺寸，方便攜帶使用</p>
                        <a href="/shop" style="color: #D8B772;">瀏覽商品 →</a>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div style="background: #fff; padding: 30px 20px; border-radius: 4px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                        <div style="width: 80px; height: 80px; background: #D8B772; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 28px;">拜</span>
                        </div>
                        <h4 style="color: #27292C;">拜拜用香</h4>
                        <p style="color: #54595F; font-size: 14px;">祈福、敬神專用天然好香</p>
                        <a href="/shop" style="color: #D8B772;">瀏覽商品 →</a>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div style="background: #fff; padding: 30px 20px; border-radius: 4px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                        <div style="width: 80px; height: 80px; background: #13AFF0; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 28px;">筆</span>
                        </div>
                        <h4 style="color: #27292C;">原木筆</h4>
                        <p style="color: #54595F; font-size: 14px;">天然原木手工製作</p>
                        <a href="/shop" style="color: #D8B772;">瀏覽商品 →</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Featured Products Banner -->
    <section class="s_text_block pt64 pb64" style="background-color: #27292C;">
        <div class="container text-center">
            <h2 style="color: #D8B772; font-size: 32px; margin-bottom: 10px;">優惠組合專區</h2>
            <p style="color: #fff; font-size: 16px; margin-bottom: 30px;">精選組合，享受更多優惠</p>
            <a href="/shop" class="btn btn-primary btn-lg" style="border-radius: 0; padding: 12px 35px;">查看優惠</a>
        </div>
    </section>

    <!-- Learning Center Section -->
    <section class="s_three_columns pt64 pb64" style="background-color: #fff;">
        <div class="container text-center">
            <h2 style="color: #27292C; font-size: 32px; margin-bottom: 10px;">香品學堂</h2>
            <p style="color: #D8B772; font-size: 16px; margin-bottom: 40px;">Incense Learning Academy</p>
            <div class="row">
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #D8B772;">
                        <h4 style="color: #27292C;">一縷香的靜心</h4>
                        <p style="color: #54595F; font-size: 14px;">透過焚香的儀式，找到內心的平靜</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #D8B772;">
                        <h4 style="color: #27292C;">香與神明的對話</h4>
                        <p style="color: #54595F; font-size: 14px;">了解各種神明對應的香品選擇</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #D8B772;">
                        <h4 style="color: #27292C;">山醫命卜香</h4>
                        <p style="color: #54595F; font-size: 14px;">香道與中醫、命理的深層連結</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #13AFF0;">
                        <h4 style="color: #27292C;">時節香氣</h4>
                        <p style="color: #54595F; font-size: 14px;">應時節選香，順應自然的養生之道</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #13AFF0;">
                        <h4 style="color: #27292C;">食香知旅</h4>
                        <p style="color: #54595F; font-size: 14px;">美食與香的結合，味覺與嗅覺的饗宴</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-6 mb-4">
                    <div style="padding: 20px; border-bottom: 3px solid #13AFF0;">
                        <h4 style="color: #27292C;">琴棋書畫茶酒花香道</h4>
                        <p style="color: #54595F; font-size: 14px;">傳統雅趣與香道的完美融合</p>
                        <a href="/blog" style="color: #D8B772;">閱讀更多 →</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact / CTA Section -->
    <section class="s_text_block pt64 pb64" style="background: linear-gradient(135deg, #D8B772, #c4a35e);">
        <div class="container text-center">
            <h2 style="color: #fff; font-size: 32px; margin-bottom: 15px;">聯絡我們</h2>
            <p style="color: #fff; font-size: 16px; margin-bottom: 30px;">歡迎洽詢任何關於天然香品的問題</p>
            <a href="/contactus" class="btn btn-lg" style="background: #fff; color: #D8B772; border-radius: 0; padding: 12px 35px; font-weight: 600;">立即聯繫</a>
        </div>
    </section>
</div>
"""

# 4. Update the homepage
page_ids = models.execute_kw(db, uid, password, "website.page", "search", [
    [["url", "=", "/"], ["website_id", "=", website_id]]
])
if not page_ids:
    page_ids = models.execute_kw(db, uid, password, "website.page", "search", [
        [["url", "=", "/"]]
    ])

if page_ids:
    # Get the view_id for the homepage
    page_data = models.execute_kw(db, uid, password, "website.page", "read", [page_ids, ["view_id"]])
    if page_data:
        view_id = page_data[0]["view_id"][0]
        print(f"Found homepage view: {view_id}")
else:
    print("Homepage not found, will create via view")

# 5. Create About Us page
about_html = """
<div id="wrap" class="oe_structure oe_empty">
    <section class="s_text_block pt64 pb32" style="background-color: #f8f8f8;">
        <div class="container text-center">
            <h1 style="color: #27292C; font-size: 40px; margin-bottom: 10px;">關於 <span style="color: #D8B772;">禪香不二</span></h1>
            <p style="color: #D8B772; font-size: 18px;">About Inzense</p>
        </div>
    </section>

    <section class="s_text_block pt64 pb64">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h2 style="color: #27292C; margin-bottom: 20px;">我們的故事</h2>
                    <p style="color: #54595F; font-size: 16px; line-height: 2;">
                        禪香不二秉持著對高品質、天然原料的堅持，專注於台灣在地製作。
                        我們的線香採用純天然木本、草本、樹脂漢方配方等香料，不添加任何化學成分或人工香精。
                    </p>
                    <p style="color: #54595F; font-size: 16px; line-height: 2;">
                        結合在地植物香氣，體驗台灣自然之美。每一支線香都是我們用心製作的成果，
                        希望為您帶來最純淨、最自然的焚香體驗。
                    </p>
                </div>
                <div class="col-lg-6">
                    <div style="background: linear-gradient(135deg, #f5f5f5, #e8e8e8); height: 350px; display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                        <p style="color: #999;">品牌故事圖片</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="s_three_columns pt64 pb64" style="background-color: #f8f8f8;">
        <div class="container text-center">
            <h2 style="color: #27292C; margin-bottom: 40px;">我們的堅持</h2>
            <div class="row">
                <div class="col-lg-4 mb-4">
                    <div style="padding: 30px;">
                        <div style="width: 70px; height: 70px; background: #D8B772; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 24px;">天</span>
                        </div>
                        <h4 style="color: #27292C;">天然原料</h4>
                        <p style="color: #54595F;">堅持使用純天然木本、草本、樹脂等原料</p>
                    </div>
                </div>
                <div class="col-lg-4 mb-4">
                    <div style="padding: 30px;">
                        <div style="width: 70px; height: 70px; background: #13AFF0; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 24px;">台</span>
                        </div>
                        <h4 style="color: #27292C;">台灣在地製作</h4>
                        <p style="color: #54595F;">專注於台灣在地生產製造</p>
                    </div>
                </div>
                <div class="col-lg-4 mb-4">
                    <div style="padding: 30px;">
                        <div style="width: 70px; height: 70px; background: #D8B772; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: #fff; font-size: 24px;">純</span>
                        </div>
                        <h4 style="color: #27292C;">零化學添加</h4>
                        <p style="color: #54595F;">不添加任何化學成分或人工香精</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
</div>
"""

# 6. Create website menu structure
print("\n=== Setting up navigation menu ===")

# Get existing menu
menu_ids = models.execute_kw(db, uid, password, "website.menu", "search", [
    [["website_id", "=", website_id], ["parent_id", "=", False]]
])

# Get the top menu
top_menu_ids = models.execute_kw(db, uid, password, "website.menu", "search", [
    [["website_id", "=", website_id], ["name", "=", "Top Menu for Website 1"]]
])

if not top_menu_ids:
    top_menu_ids = models.execute_kw(db, uid, password, "website.menu", "search", [
        [["website_id", "=", website_id], ["parent_id", "=", False]]
    ])

if top_menu_ids:
    parent_menu_id = top_menu_ids[0]
    print(f"Found top menu: {parent_menu_id}")

    # Delete existing child menus
    child_ids = models.execute_kw(db, uid, password, "website.menu", "search", [
        [["parent_id", "=", parent_menu_id], ["website_id", "=", website_id]]
    ])
    if child_ids:
        models.execute_kw(db, uid, password, "website.menu", "unlink", [child_ids])
        print(f"Deleted {len(child_ids)} existing menu items")

    # Create new menu items matching inzense.com.tw
    menus = [
        {"name": "首頁", "url": "/", "sequence": 10},
        {"name": "關於我們", "url": "/about-us", "sequence": 20},
        {"name": "優惠組合專區", "url": "/shop", "sequence": 30},
        {"name": "天然香品", "url": "/shop", "sequence": 40},
        {"name": "課程與活動", "url": "/event", "sequence": 50},
        {"name": "香品學堂", "url": "/blog", "sequence": 60},
        {"name": "聯絡我們", "url": "/contactus", "sequence": 70},
    ]

    for menu in menus:
        menu_id = models.execute_kw(db, uid, password, "website.menu", "create", [{
            "name": menu["name"],
            "url": menu["url"],
            "sequence": menu["sequence"],
            "parent_id": parent_menu_id,
            "website_id": website_id,
        }])
        print(f"  Created menu: {menu['name']} -> {menu['url']}")

    # Create submenu for 天然香品
    incense_menu_ids = models.execute_kw(db, uid, password, "website.menu", "search", [
        [["name", "=", "天然香品"], ["website_id", "=", website_id]]
    ])
    if incense_menu_ids:
        sub_categories = [
            {"name": "線香", "url": "/shop?category=線香", "sequence": 1},
            {"name": "迷你香", "url": "/shop?category=迷你香", "sequence": 2},
            {"name": "拜拜用香", "url": "/shop?category=拜拜用香", "sequence": 3},
            {"name": "原木筆", "url": "/shop?category=原木筆", "sequence": 4},
        ]
        for sub in sub_categories:
            models.execute_kw(db, uid, password, "website.menu", "create", [{
                "name": sub["name"],
                "url": sub["url"],
                "sequence": sub["sequence"],
                "parent_id": incense_menu_ids[0],
                "website_id": website_id,
            }])
            print(f"    Submenu: {sub['name']}")

print("\n=== Setting up eCommerce product categories ===")

# Create product public categories for the shop
categories = [
    "線香",
    "迷你香",
    "拜拜用香",
    "原木筆",
    "優惠組合",
]

sub_categories_map = {
    "線香": ["神明系列", "功能系列", "脈輪系列", "五行系列", "外國系列", "台灣系列", "特色系列", "降真系列", "檀香系列", "沉香系列"],
    "迷你香": ["神明系列", "功能系列", "脈輪系列", "五行系列"],
}

for cat_name in categories:
    existing = models.execute_kw(db, uid, password, "product.public.category", "search", [
        [["name", "=", cat_name]]
    ])
    if not existing:
        cat_id = models.execute_kw(db, uid, password, "product.public.category", "create", [{
            "name": cat_name,
            "website_id": website_id,
        }])
        print(f"Created category: {cat_name} (ID={cat_id})")

        # Create subcategories
        if cat_name in sub_categories_map:
            for sub_name in sub_categories_map[cat_name]:
                sub_id = models.execute_kw(db, uid, password, "product.public.category", "create", [{
                    "name": sub_name,
                    "parent_id": cat_id,
                    "website_id": website_id,
                }])
                print(f"  Subcategory: {sub_name}")
    else:
        print(f"Category {cat_name} already exists")

print("\n=== Setting up Blog ===")

# Create blog for 香品學堂
blog_ids = models.execute_kw(db, uid, password, "blog.blog", "search", [
    [["website_id", "=", website_id]]
])
if blog_ids:
    models.execute_kw(db, uid, password, "blog.blog", "write", [[blog_ids[0]], {
        "name": "香品學堂",
    }])
    blog_id = blog_ids[0]
    print(f"Updated blog: 香品學堂 (ID={blog_id})")
else:
    blog_id = models.execute_kw(db, uid, password, "blog.blog", "create", [{
        "name": "香品學堂",
        "website_id": website_id,
    }])
    print(f"Created blog: 香品學堂 (ID={blog_id})")

# Create blog posts
blog_posts = [
    {"name": "一縷香的靜心", "subtitle": "透過焚香的儀式，找到內心的平靜",
     "content": "<p>焚香自古以來就是修行者靜心的方式。一縷輕煙緩緩升起，帶著天然草木的清香，讓心靈在忙碌的生活中找到片刻的寧靜。</p><p>禪香不二的天然線香，採用純天然原料製作，讓您在靜心冥想時，享受最純粹的香氣體驗。</p>"},
    {"name": "香與神明的對話", "subtitle": "了解各種神明對應的香品選擇",
     "content": "<p>在台灣的傳統信仰中，焚香是與神明溝通的重要媒介。不同的神明有不同的香品偏好，選擇正確的香品，可以讓您的祈禱更加靈驗。</p><p>禪香不二的神明系列線香，根據傳統典籍和匠師經驗，為您精選最適合各路神明的香品配方。</p>"},
    {"name": "山醫命卜香", "subtitle": "香道與中醫、命理的深層連結",
     "content": "<p>中國傳統文化中，山、醫、命、卜、相五術與香道有著深厚的淵源。從中醫的角度，不同的香料具有不同的藥性和功效。</p><p>禪香不二的功能系列線香，融合中醫藥理與香道傳統，為您帶來身心靈的全方位調理。</p>"},
    {"name": "時節香氣", "subtitle": "應時節選香，順應自然的養生之道",
     "content": "<p>四季更迭，萬物變化。順應時節選擇適合的香品，是古人養生智慧的體現。</p><p>春天適合清新的草本香氣，夏天宜用涼爽的薄荷檀香，秋天品味溫潤的沉香，冬天則以暖身的肉桂丁香為佳。</p>"},
    {"name": "食香知旅", "subtitle": "美食與香的結合，味覺與嗅覺的饗宴",
     "content": "<p>香料不僅可以焚燒，在美食中也扮演著重要的角色。從肉桂到八角，從檀香到沉香，這些珍貴的天然香料在中式料理中有著悠久的使用歷史。</p>"},
    {"name": "琴棋書畫茶酒花香道", "subtitle": "傳統雅趣與香道的完美融合",
     "content": "<p>琴棋書畫、品茗飲酒、插花焚香，這些傳統文人的雅趣生活，在現代社會中依然有著深遠的意義。</p><p>焚一炷好香，品一杯清茶，在裊裊輕煙中感受古人的生活美學。</p>"},
]

for post_data in blog_posts:
    existing = models.execute_kw(db, uid, password, "blog.post", "search", [
        [["name", "=", post_data["name"]]]
    ])
    if not existing:
        post_id = models.execute_kw(db, uid, password, "blog.post", "create", [{
            "blog_id": blog_id,
            "name": post_data["name"],
            "subtitle": post_data["subtitle"],
            "content": post_data["content"],
            "website_published": True,
            "website_id": website_id,
        }])
        print(f"Created blog post: {post_data['name']}")
    else:
        print(f"Blog post {post_data['name']} already exists")

print("\n=== Website setup complete! ===")
print(f"Website URL: https://inzense-odoo.woowtech.io")
print(f"Admin login: admin / admin")
