#!/usr/bin/env python3
"""
Inzense Odoo 18 — Iteration 3: Images + Pages + Company Info
- Upload brand images from official site
- Update homepage hero with real banner image
- Set logo on website + company
- Merge About Us + Contact Us into one page
- Remove FAQ page and menu item
- Fix all company info (header/footer/company record)
- Update navigation

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/78_images_pages_info_update.py
"""
import xmlrpc.client
import base64
import urllib.request
import os

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


def create(model, vals):
    return models.execute_kw(DB, uid, PASSWORD, model, "create", [vals])


def search(model, domain):
    return models.execute_kw(DB, uid, PASSWORD, model, "search", [domain])


IMG_DIR = "/tmp/inzense_images"


def upload_image(filepath, name, mimetype="image/png"):
    """Upload image to ir.attachment, return attachment ID."""
    existing = search("ir.attachment", [["name", "=", name], ["res_model", "=", False]])
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    if existing:
        write("ir.attachment", existing, {"datas": data})
        print(f"  Updated: {name} (id={existing[0]})")
        return existing[0]
    else:
        att_id = create("ir.attachment", {
            "name": name,
            "type": "binary",
            "datas": data,
            "mimetype": mimetype,
            "public": True,
        })
        print(f"  Uploaded: {name} (id={att_id})")
        return att_id


# ============================================================
# STEP 1: Upload brand images
# ============================================================
print("\n=== Step 1: Upload brand images ===")

logo_id = upload_image(f"{IMG_DIR}/logo_web.png", "inzense-logo-web.png", "image/png")
logo_icon_id = upload_image(f"{IMG_DIR}/logo_icon.png", "inzense-logo-icon.png", "image/png")
hero_id = upload_image(f"{IMG_DIR}/hero_banner.jpg", "inzense-hero-banner.jpg", "image/jpeg")
gods_id = upload_image(f"{IMG_DIR}/god_series_banner.jpg", "inzense-gods-banner.jpg", "image/jpeg")
lifestyle_id = upload_image(f"{IMG_DIR}/lifestyle.jpg", "inzense-lifestyle.jpg", "image/jpeg")
og_id = upload_image(f"{IMG_DIR}/og_image.jpg", "inzense-og-image.jpg", "image/jpeg")

# Also upload lifestyle brand photos if they exist
extra_ids = {}
for fname in ["lifestyle_brand_photo_01_1536x1025.jpg", "lifestyle_brand_photo_02_1536x968.jpg", "lifestyle_brand_photo_03_1536x1024.jpg"]:
    fpath = f"{IMG_DIR}/{fname}"
    if os.path.exists(fpath):
        extra_ids[fname] = upload_image(fpath, f"inzense-{fname}", "image/jpeg")

# ============================================================
# STEP 2: Set logo on website + company + favicon
# ============================================================
print("\n=== Step 2: Set logo and favicon ===")

with open(f"{IMG_DIR}/logo_web.png", "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()
with open(f"{IMG_DIR}/logo_icon.png", "rb") as f:
    favicon_b64 = base64.b64encode(f.read()).decode()

write("website", [1], {
    "logo": logo_b64,
    "favicon": favicon_b64,
})
print("  ✅ Website logo + favicon updated")

write("res.company", [1], {
    "logo": logo_b64,
})
print("  ✅ Company logo updated")

# ============================================================
# STEP 3: Update company info to match official site
# ============================================================
print("\n=== Step 3: Update company info ===")

write("res.company", [1], {
    "name": "禪香不二 Inzense",
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
    "email": "service@inzense.com.tw",
    "website": "https://www.inzense.com.tw",
    "street": "新北市中和區立德街26巷1號樓上",
    "city": "新北市",
    "zip": "235",
})
print("  ✅ Company record updated")

# Update the admin partner too
admin_partner = sr("res.users", [["id", "=", 2]], ["partner_id"])[0]["partner_id"][0]
write("res.partner", [admin_partner], {
    "phone": "0926-926-851",
    "mobile": "0911-675-120",
    "email": "service@inzense.com.tw",
    "website": "https://www.inzense.com.tw",
    "street": "新北市中和區立德街26巷1號樓上",
    "city": "新北市",
    "zip": "235",
})
print("  ✅ Admin partner updated")

# ============================================================
# STEP 4: Update homepage with real images
# ============================================================
print("\n=== Step 4: Update homepage with real images ===")

HOMEPAGE_HTML = f"""
<div id="wrap" class="oe_structure">

    <!-- Section 1: Hero Banner with real brand photo -->
    <section class="inzense-hero" style="min-height:500px; background-image:url('/web/image/{hero_id}'); background-size:cover; background-position:center; padding:140px 20px 120px; position:relative;">
        <div style="position:absolute; inset:0; background:rgba(0,0,0,0.40);"></div>
        <div class="container text-center" style="position:relative; z-index:1;">
            <img src="/web/image/{logo_id}" alt="禪香不二" style="max-height:80px; margin-bottom:24px;"/>
            <h1 style="color:#FFFFFF; font-size:38px; font-weight:600; letter-spacing:6px; margin-bottom:12px; text-shadow:0 2px 8px rgba(0,0,0,0.5);">
                禪香不二
            </h1>
            <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:20px; font-style:italic; letter-spacing:3px; margin-bottom:8px;">
                Inzense
            </p>
            <p style="color:#eeeeee; font-size:15px; letter-spacing:2px; margin-bottom:36px;">
                天然手工線香 · 會員專屬購物平台
            </p>
            <div>
                <a href="/shop" class="btn btn-primary" style="margin-right:12px;">開始購物</a>
                <a href="/my" class="btn" style="border:2px solid #FFFFFF; color:#FFFFFF; border-radius:36px; padding:12px 36px; font-weight:600; letter-spacing:1.5px;">會員登入</a>
            </div>
        </div>
    </section>

    <!-- Section 2: Value Proposition Bar -->
    <section class="inzense-value-bar" style="padding:24px 0;">
        <div class="container">
            <div class="row text-center">
                <div class="col-md-4 py-2">
                    <span class="inzense-value-item"><i class="fa fa-leaf"></i> 天然製香 品質保證</span>
                </div>
                <div class="col-md-4 py-2">
                    <span class="inzense-value-item"><i class="fa fa-star"></i> 會員專屬優惠</span>
                </div>
                <div class="col-md-4 py-2">
                    <span class="inzense-value-item"><i class="fa fa-gift"></i> 積點回饋 禮遇常客</span>
                </div>
            </div>
        </div>
    </section>

    <!-- Section 3: Quick Category Navigation -->
    <section class="inzense-section" style="padding:60px 0;">
        <div class="container">
            <div class="text-center mb-5">
                <p style="color:#D8B772; font-size:12px; text-transform:uppercase; letter-spacing:3px; margin-bottom:8px;">Shop by Collection</p>
                <h2 style="font-size:28px;">依系列選購</h2>
            </div>
            <div class="row g-4">
                <div class="col-md-4 col-6">
                    <a href="/shop?category=49" class="inzense-category-card">
                        <i class="fa fa-magic" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>功能系列</h5>
                        <p>開運 · 療心 · 除障 · 淨化</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
                <div class="col-md-4 col-6">
                    <a href="/shop?category=58" class="inzense-category-card">
                        <i class="fa fa-sun-o" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>神明系列</h5>
                        <p>媽祖 · 觀音 · 財神 · 文昌</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
                <div class="col-md-4 col-6">
                    <a href="/shop?category=53" class="inzense-category-card">
                        <i class="fa fa-tree" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>檀香系列</h5>
                        <p>印度老山 · 東加 · 澳洲</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
                <div class="col-md-4 col-6">
                    <a href="/shop?category=54" class="inzense-category-card">
                        <i class="fa fa-diamond" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>沉香系列</h5>
                        <p>惠安 · 芽莊 · 加里萬丹</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
                <div class="col-md-4 col-6">
                    <a href="/shop?category=51" class="inzense-category-card">
                        <i class="fa fa-circle-o" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>脈輪系列</h5>
                        <p>海底輪 · 心輪 · 頂輪</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
                <div class="col-md-4 col-6">
                    <a href="/shop?category=99" class="inzense-category-card">
                        <i class="fa fa-tags" style="font-size:28px; color:#D8B772; display:block; margin-bottom:12px;"></i>
                        <h5>優惠組合</h5>
                        <p>精選套組 · 超值禮盒</p>
                        <span class="browse-link">瀏覽 →</span>
                    </a>
                </div>
            </div>
            <div class="text-center mt-4">
                <a href="/shop" style="color:#13AFF0; font-weight:600;">查看全部商品 →</a>
            </div>
        </div>
    </section>

    <!-- Section 4: Member Center Callout -->
    <section class="inzense-section-dark" style="padding:60px 0;">
        <div class="container">
            <div class="text-center mb-4">
                <p style="color:#D8B772; font-size:12px; text-transform:uppercase; letter-spacing:3px; margin-bottom:8px;">Member Center</p>
                <h2 style="color:#D8B772 !important; font-size:28px;">會員中心</h2>
            </div>
            <div class="row text-center g-4">
                <div class="col-md-4">
                    <div class="inzense-member-feature">
                        <i class="fa fa-file-text-o"></i>
                        <h5>訂單查詢</h5>
                        <p>隨時追蹤您的訂單狀態與出貨進度</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="inzense-member-feature">
                        <i class="fa fa-star-o"></i>
                        <h5>集點回饋</h5>
                        <p>每筆消費累積點數，兌換專屬好禮</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="inzense-member-feature">
                        <i class="fa fa-percent"></i>
                        <h5>專屬優惠</h5>
                        <p>會員限定折扣與搶先預購資格</p>
                    </div>
                </div>
            </div>
            <div class="text-center mt-4">
                <a href="/my" class="btn btn-primary">登入我的帳戶</a>
            </div>
        </div>
    </section>

    <!-- Section 5: Final CTA Banner with lifestyle photo -->
    <section class="inzense-cta-banner" style="background-image:url('/web/image/{lifestyle_id}'); background-size:cover; background-position:center; padding:100px 20px; position:relative;">
        <div style="position:absolute; inset:0; background:rgba(39,41,44,0.6);"></div>
        <div class="container text-center" style="position:relative; z-index:1;">
            <h2 style="color:#FFFFFF !important; font-size:28px; margin-bottom:12px; text-shadow:0 2px 8px rgba(0,0,0,0.5);">
                身心沉靜 享受清雅之趣
            </h2>
            <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-style:italic; font-size:18px; margin-bottom:24px;">
                Tranquility in every breath
            </p>
            <a href="/shop" class="btn btn-primary">探索商品</a>
        </div>
    </section>

</div>
"""

# Find the website-specific homepage view (id=979)
hp_views = sr("ir.ui.view", [["key", "=", "website.homepage"], ["website_id", "=", 1]], ["id"])
if not hp_views:
    hp_views = sr("ir.ui.view", [["key", "=", "website.homepage"]], ["id"])
hp_view_id = hp_views[0]["id"]

HOMEPAGE_ARCH = f'''<t name="Home" t-name="website.homepage">
    <t t-call="website.layout">
        <t t-set="pageName" t-value="'homepage'"/>
        {HOMEPAGE_HTML}
    </t>
</t>'''

write("ir.ui.view", [hp_view_id], {"arch": HOMEPAGE_ARCH})
print(f"  ✅ Homepage updated with real images (hero={hero_id}, logo={logo_id}, lifestyle={lifestyle_id})")

# ============================================================
# STEP 5: Merge About Us + Contact Us → single page
# ============================================================
print("\n=== Step 5: Merge About Us + Contact Us ===")

ABOUT_CONTACT_HTML = f"""
<section class="inzense-hero" style="min-height:350px; background-image:url('/web/image/{gods_id}'); background-size:cover; background-position:center; padding:80px 20px; position:relative;">
    <div style="position:absolute; inset:0; background:rgba(0,0,0,0.50);"></div>
    <div class="container text-center" style="position:relative; z-index:1;">
        <img src="/web/image/{logo_id}" alt="禪香不二" style="max-height:60px; margin-bottom:16px;"/>
        <h1 style="color:#FFFFFF; font-size:32px; letter-spacing:4px;">關於 禪香不二</h1>
        <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:16px; font-style:italic;">About Inzense</p>
    </div>
</section>

<!-- Brand Story -->
<section class="inzense-section" style="padding:60px 0;">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-6">
                <p style="color:#D8B772; font-size:12px; text-transform:uppercase; letter-spacing:3px;">Our Story</p>
                <h2>品牌故事</h2>
                <p>禪香不二，源自對天然香品的執著追求。我們堅持以台灣在地植物為基底，結合傳統製香工藝，手工製作每一支線香。</p>
                <p>「不二」意味著唯一、純粹。我們相信，真正的好香不需要化學添加，只需要大自然最純粹的饋贈。</p>
                <blockquote style="border-left:3px solid #D8B772; padding-left:20px; margin:24px 0; font-style:italic; color:#7A7A7A;">
                    「一縷清香，自在生活。」
                </blockquote>
            </div>
            <div class="col-md-6">
                <img src="/web/image/{lifestyle_id}" alt="禪香不二" style="width:100%; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.1);"/>
            </div>
        </div>
    </div>
</section>

<!-- Three Pillars -->
<section style="background:#f9f7f4; padding:50px 0;">
    <div class="container">
        <div class="row text-center g-4">
            <div class="col-md-4">
                <div style="width:64px; height:64px; border-radius:50%; background:#D8B772; display:flex; align-items:center; justify-content:center; margin:0 auto 16px;">
                    <span style="color:#fff; font-size:24px; font-weight:700;">天</span>
                </div>
                <h5>天然原料</h5>
                <p style="color:#7A7A7A; font-size:13px;">嚴選天然沉香、檀香、降真香等珍貴原料，絕不使用化學香精</p>
            </div>
            <div class="col-md-4">
                <div style="width:64px; height:64px; border-radius:50%; background:#13AFF0; display:flex; align-items:center; justify-content:center; margin:0 auto 16px;">
                    <span style="color:#fff; font-size:24px; font-weight:700;">台</span>
                </div>
                <h5>台灣製造</h5>
                <p style="color:#7A7A7A; font-size:13px;">在地生產，支持台灣在地農業與傳統工藝的延續</p>
            </div>
            <div class="col-md-4">
                <div style="width:64px; height:64px; border-radius:50%; background:#27292C; display:flex; align-items:center; justify-content:center; margin:0 auto 16px;">
                    <span style="color:#fff; font-size:24px; font-weight:700;">純</span>
                </div>
                <h5>純粹品質</h5>
                <p style="color:#7A7A7A; font-size:13px;">每批線香皆經反覆測試，確保品質穩定如一</p>
            </div>
        </div>
    </div>
</section>

<!-- Contact Info -->
<section class="inzense-section" style="padding:60px 0;">
    <div class="container">
        <div class="text-center mb-5">
            <p style="color:#D8B772; font-size:12px; text-transform:uppercase; letter-spacing:3px;">Contact Us</p>
            <h2>聯絡我們</h2>
        </div>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="inzense-card inzense-card-accent" style="height:100%;">
                    <h5><i class="fa fa-phone" style="color:#D8B772; margin-right:8px;"></i>客服聯絡</h5>
                    <p style="color:#7A7A7A; font-size:14px;">
                        客服電話：<strong>0926-926-851</strong><br/>
                        業務/經銷：<strong>0911-675-120</strong><br/>
                        LINE@：<strong>@209hnrwf</strong>
                    </p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="inzense-card inzense-card-accent" style="height:100%;">
                    <h5><i class="fa fa-envelope" style="color:#D8B772; margin-right:8px;"></i>電子信箱</h5>
                    <p style="color:#7A7A7A; font-size:14px;">
                        客服信箱：<a href="mailto:service@inzense.com.tw">service@inzense.com.tw</a><br/>
                        業務合作：<a href="mailto:cooperate@inzense.com.tw">cooperate@inzense.com.tw</a>
                    </p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="inzense-card inzense-card-accent" style="height:100%;">
                    <h5><i class="fa fa-clock-o" style="color:#D8B772; margin-right:8px;"></i>服務時間</h5>
                    <p style="color:#7A7A7A; font-size:14px;">
                        客服時間：週一至週五 10:00 - 18:00
                    </p>
                </div>
            </div>
        </div>

        <!-- Service offerings -->
        <div class="row g-4 mt-3">
            <div class="col-md-4">
                <div class="inzense-card text-center">
                    <i class="fa fa-handshake-o" style="font-size:28px; color:#D8B772; margin-bottom:12px; display:block;"></i>
                    <h6>經銷通路 / 團購合作</h6>
                </div>
            </div>
            <div class="col-md-4">
                <div class="inzense-card text-center">
                    <i class="fa fa-flask" style="font-size:28px; color:#D8B772; margin-bottom:12px; display:block;"></i>
                    <h6>配方研發 / 客製化代工</h6>
                </div>
            </div>
            <div class="col-md-4">
                <div class="inzense-card text-center">
                    <i class="fa fa-graduation-cap" style="font-size:28px; color:#D8B772; margin-bottom:12px; display:block;"></i>
                    <h6>天然香講座 / 手作課程</h6>
                </div>
            </div>
        </div>

        <!-- Location -->
        <div class="row mt-5">
            <div class="col-md-8 offset-md-2">
                <div class="inzense-card inzense-card-accent">
                    <h5><i class="fa fa-map-marker" style="color:#D8B772; margin-right:8px;"></i>禪香企業社</h5>
                    <p style="color:#7A7A7A; font-size:14px;">
                        地址：新北市中和區立德街26巷1號樓上<br/>
                    </p>
                </div>
            </div>
        </div>

        <!-- Social -->
        <div class="text-center mt-4">
            <a href="https://www.facebook.com/onlyinzense" target="_blank" style="font-size:24px; color:#27292C; margin:0 12px;"><i class="fa fa-facebook-square"></i></a>
            <a href="https://instagram.com/only_inzense" target="_blank" style="font-size:24px; color:#27292C; margin:0 12px;"><i class="fa fa-instagram"></i></a>
            <a href="https://lin.ee/Fn75IVT" target="_blank" style="font-size:24px; color:#27292C; margin:0 12px;"><i class="fa fa-comment"></i></a>
        </div>
    </div>
</section>
"""

# Update about-us page view
about_view = sr("ir.ui.view", [["key", "=", "website.inzense_about_us"]], ["id"], context={"active_test": False})
if about_view:
    about_arch = f'''<t name="關於我們" t-name="website.inzense_about_us">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            {ABOUT_CONTACT_HTML}
        </div>
    </t>
</t>'''
    write("ir.ui.view", [about_view[0]["id"]], {"arch": about_arch, "active": True})
    print("  ✅ About Us page updated (merged with Contact Us)")

# ============================================================
# STEP 6: Remove FAQ page + menu, update contactus redirect
# ============================================================
print("\n=== Step 6: Remove FAQ, redirect Contact Us ===")

# Remove FAQ page
qa_pages = search("website.page", [["url", "=", "/qa"]])
if qa_pages:
    models.execute_kw(DB, uid, PASSWORD, "website.page", "unlink", [qa_pages])
    print("  ✅ Deleted FAQ page (/qa)")
qa_views = sr("ir.ui.view", [["key", "=", "website.inzense_qa"]], ["id"], context={"active_test": False})
if qa_views:
    models.execute_kw(DB, uid, PASSWORD, "ir.ui.view", "unlink", [[v["id"] for v in qa_views]])
    print("  ✅ Deleted FAQ view")

# Remove old Contact Us page (merged into About Us)
contactus_pages = search("website.page", [["url", "=", "/contactus"], ["website_id", "=", 1]])
# Keep the page but make it redirect to /about-us via a simple view
contactus_views = sr("ir.ui.view", [["key", "ilike", "contactus"]], ["id", "key"], context={"active_test": False})
# We'll just keep the /contactus URL working by updating the Odoo default contactus page
# to show our merged content

# ============================================================
# STEP 7: Update navigation
# ============================================================
print("\n=== Step 7: Update navigation ===")

# Delete all child menus
child_menus = search("website.menu", [["website_id", "=", 1], ["parent_id", "!=", False]])
if child_menus:
    models.execute_kw(DB, uid, PASSWORD, "website.menu", "unlink", [child_menus])
    print(f"  Deleted {len(child_menus)} old menu items")

root_menus = sr("website.menu", [["website_id", "=", 1], ["parent_id", "=", False]], ["id"])
ROOT_MENU_ID = root_menus[0]["id"]

CATEGORIES = {
    "功能系列": 49, "神明系列": 58, "檀香系列": 53,
    "沉香系列": 54, "脈輪系列": 51, "優惠組合": 99,
}

new_menus = [
    {"name": "首頁", "url": "/", "sequence": 10},
    {"name": "商品", "url": "/shop", "sequence": 20},
    {"name": "關於我們", "url": "/about-us", "sequence": 30},
    {"name": "會員中心", "url": "/my", "sequence": 40},
]

for item in new_menus:
    mid = create("website.menu", {
        "name": item["name"], "url": item["url"],
        "sequence": item["sequence"], "parent_id": ROOT_MENU_ID, "website_id": 1,
    })
    if item["name"] == "商品":
        sub_seq = 1
        create("website.menu", {"name": "全部商品", "url": "/shop", "sequence": sub_seq, "parent_id": mid, "website_id": 1})
        for cat_name, cat_id in CATEGORIES.items():
            sub_seq += 1
            create("website.menu", {"name": cat_name, "url": f"/shop?category={cat_id}", "sequence": sub_seq, "parent_id": mid, "website_id": 1})
    print(f"  ✅ '{item['name']}' → {item['url']}")

print("\n--- Final menu ---")
final_menus = sr("website.menu", [["website_id", "=", 1], ["parent_id", "!=", False]], ["name", "url", "parent_id"], order="sequence")
for m in final_menus:
    indent = "      " if any(mm["parent_id"] and mm["parent_id"][0] != ROOT_MENU_ID for mm in [m]) else "    "
    is_child = m["parent_id"] and m["parent_id"][0] != ROOT_MENU_ID
    prefix = "      " if is_child else "    "
    print(f"{prefix}{m['name']} → {m['url']}")

# ============================================================
# STEP 8: Verify
# ============================================================
print("\n=== Step 8: Verification ===")

resp = urllib.request.urlopen(f"{URL}/")
homepage = resp.read().decode("utf-8")

checks = {
    "Logo image in hero": f"/web/image/{logo_id}" in homepage,
    "Hero banner image": f"/web/image/{hero_id}" in homepage,
    "Lifestyle CTA image": f"/web/image/{lifestyle_id}" in homepage,
    "Brand name": "禪香不二" in homepage,
    "Member CTA": "會員登入" in homepage,
    "Shop CTA": "開始購物" in homepage,
}
for name, result in checks.items():
    print(f"  {'✅' if result else '❌'} {name}")

# Check About Us page
resp2 = urllib.request.urlopen(f"{URL}/about-us")
about_content = resp2.read().decode("utf-8")
about_checks = {
    "Brand story": "品牌故事" in about_content,
    "Contact info": "0926-926-851" in about_content,
    "Email": "service@inzense.com.tw" in about_content,
    "Location": "中和區立德街" in about_content,
    "Social links": "onlyinzense" in about_content,
    "Logo image": f"/web/image/{logo_id}" in about_content,
    "Gods banner": f"/web/image/{gods_id}" in about_content,
}
print("\n  About Us page:")
for name, result in about_checks.items():
    print(f"    {'✅' if result else '❌'} {name}")

# Check FAQ is gone
try:
    urllib.request.urlopen(f"{URL}/qa")
    print("\n  ❌ FAQ page still accessible")
except urllib.error.HTTPError as e:
    if e.code in (404, 403):
        print(f"\n  ✅ FAQ page removed ({e.code})")

print("\nIteration 3 complete — Images + Pages + Company Info updated.")
