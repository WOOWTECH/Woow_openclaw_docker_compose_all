#!/usr/bin/env python3
"""
Inzense Odoo 18 — Phase 3+4: Navigation Restructure + Homepage Redesign
Builds 6-item menu with dropdown + 5-section member-focused homepage.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/73_navigation_and_homepage.py
"""
import xmlrpc.client
import urllib.request

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


# ============================================================
# PHASE 3: Navigation Restructure
# ============================================================
print("\n" + "=" * 60)
print("PHASE 3: Navigation Restructure")
print("=" * 60)

# Find the root menu for website 1
root_menus = sr("website.menu", [["website_id", "=", 1], ["parent_id", "=", False]], ["name", "id"])
if root_menus:
    ROOT_MENU_ID = root_menus[0]["id"]
    print(f"  Root menu: id={ROOT_MENU_ID} '{root_menus[0]['name']}'")
else:
    print("  ❌ No root menu found!")
    exit(1)

# Delete ALL existing child menus
print("\n--- Clearing existing menu items ---")
child_menus = search("website.menu", [["website_id", "=", 1], ["parent_id", "!=", False]])
if child_menus:
    models.execute_kw(DB, uid, PASSWORD, "website.menu", "unlink", [child_menus])
    print(f"  Deleted {len(child_menus)} old menu items")

# Key category IDs for dropdown
CATEGORIES = {
    "功能系列": 49,
    "神明系列": 58,
    "檀香系列": 53,
    "沉香系列": 54,
    "脈輪系列": 51,
    "優惠組合": 99,
}

# Create top-level menu items
print("\n--- Creating new menu items ---")

menu_items = [
    {"name": "首頁", "url": "/", "sequence": 10},
    {"name": "商品", "url": "/shop", "sequence": 20},
    {"name": "關於我們", "url": "/about-us", "sequence": 30},
    {"name": "常見問題", "url": "/qa", "sequence": 40},
    {"name": "聯絡我們", "url": "/contactus", "sequence": 50},
    {"name": "會員中心", "url": "/my", "sequence": 60},
]

for item in menu_items:
    mid = create("website.menu", {
        "name": item["name"],
        "url": item["url"],
        "sequence": item["sequence"],
        "parent_id": ROOT_MENU_ID,
        "website_id": 1,
    })
    print(f"  ✅ '{item['name']}' → {item['url']} (id={mid})")

    # Add sub-menus for "商品"
    if item["name"] == "商品":
        shop_parent_id = mid
        sub_seq = 1
        # "全部商品" first
        create("website.menu", {
            "name": "全部商品",
            "url": "/shop",
            "sequence": sub_seq,
            "parent_id": shop_parent_id,
            "website_id": 1,
        })
        sub_seq += 1
        for cat_name, cat_id in CATEGORIES.items():
            create("website.menu", {
                "name": cat_name,
                "url": f"/shop?category={cat_id}",
                "sequence": sub_seq,
                "parent_id": shop_parent_id,
                "website_id": 1,
            })
            sub_seq += 1
        print(f"    + {len(CATEGORIES) + 1} dropdown items under 商品")

# Verify
print("\n--- Final menu structure ---")
final_menus = sr("website.menu", [["website_id", "=", 1]], ["name", "url", "sequence", "parent_id"], order="sequence")
for m in final_menus:
    indent = "    " if m["parent_id"] else "  "
    print(f"{indent}{m['name']} → {m['url']}")

# ============================================================
# PHASE 4: Homepage Redesign
# ============================================================
print("\n" + "=" * 60)
print("PHASE 4: Homepage Redesign")
print("=" * 60)

# Build the 5-section homepage HTML
HOMEPAGE_HTML = """
<div id="wrap" class="oe_structure">

    <!-- Section 1: Hero Banner (CSS gradient, no image dependency) -->
    <section class="inzense-hero" style="min-height:480px; background: linear-gradient(135deg, #27292C 0%, #3d3f42 40%, #4a3c2a 100%); padding: 140px 20px 120px;">
        <div class="container text-center">
            <h1 style="color:#FFFFFF; font-size:42px; font-weight:600; letter-spacing:6px; margin-bottom:16px; text-shadow: 0 2px 8px rgba(0,0,0,0.4);">
                禪香不二
            </h1>
            <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:20px; font-style:italic; letter-spacing:3px; margin-bottom:8px;">
                Inzense
            </p>
            <p style="color:#cccccc; font-size:15px; letter-spacing:2px; margin-bottom:36px;">
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
                    <span class="inzense-value-item">
                        <i class="fa fa-leaf"></i> 天然製香 品質保證
                    </span>
                </div>
                <div class="col-md-4 py-2">
                    <span class="inzense-value-item">
                        <i class="fa fa-star"></i> 會員專屬優惠
                    </span>
                </div>
                <div class="col-md-4 py-2">
                    <span class="inzense-value-item">
                        <i class="fa fa-gift"></i> 積點回饋 禮遇常客
                    </span>
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

    <!-- Section 5: Final CTA Banner -->
    <section class="inzense-cta-banner" style="background: linear-gradient(135deg, #4a3c2a 0%, #27292C 100%); padding:80px 20px;">
        <div class="container text-center">
            <h2 style="color:#FFFFFF !important; font-size:28px; margin-bottom:12px; text-shadow: 0 2px 8px rgba(0,0,0,0.4);">
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

# Find and update homepage view
hp_views = sr("ir.ui.view", [["key", "=", "website.homepage"]], ["id", "arch_db"])
if not hp_views:
    print("  ❌ Cannot find homepage view!")
    exit(1)

hp_view_id = hp_views[0]["id"]
print(f"  Homepage view ID: {hp_view_id}")

# Build the full template
HOMEPAGE_ARCH = f'''<t name="Home" t-name="website.homepage">
    <t t-call="website.layout">
        <t t-set="pageName" t-value="'homepage'"/>
        {HOMEPAGE_HTML}
    </t>
</t>'''

write("ir.ui.view", [hp_view_id], {"arch": HOMEPAGE_ARCH})
print("  ✅ Homepage updated with 5-section design")

# ============================================================
# Verify
# ============================================================
print("\n=== Verification ===")
resp = urllib.request.urlopen(f"{URL}/")
content = resp.read().decode()

checks = {
    "禪香不二": "禪香不二" in content,
    "會員中心": "會員中心" in content,
    "依系列選購": "依系列選購" in content,
    "登入我的帳戶": "登入我的帳戶" in content,
    "開始購物": "開始購物" in content,
    "/shop?category=": "/shop?category=" in content,
    "/my link": '"/my"' in content,
    "Gold color": "D8B772" in content,
    "Cyan color": "13AFF0" in content,
}

all_pass = True
for check_name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")
    if not result:
        all_pass = False

print(f"\n  Page size: {len(content):,} bytes")
print(f"  All checks passed: {'✅ YES' if all_pass else '❌ NO'}")
print("\nPhase 3+4 complete.")
