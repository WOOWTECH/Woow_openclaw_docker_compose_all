#!/usr/bin/env python3
"""
Inzense Odoo 18 — Iteration 2: Restore static pages
Creates About Us, FAQ, Privacy Policy, Return Policy pages.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/77_static_pages.py
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


# Find layout view for inherit_id
layout_ids = search("ir.ui.view", [["key", "=", "website.layout"]])
LAYOUT_ID = layout_ids[0]


def create_or_update_page(name, url, key, arch_body):
    """Create a website page with its view, or update if exists."""
    full_arch = f'''<t name="{name}" t-name="{key}">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            {arch_body}
        </div>
    </t>
</t>'''

    # Check if view exists
    existing = sr("ir.ui.view", [["key", "=", key]], ["id"], context={"active_test": False})
    if existing:
        view_id = existing[0]["id"]
        write("ir.ui.view", [view_id], {"arch": full_arch, "active": True})
        print(f"  Updated view: id={view_id}")
    else:
        view_id = create("ir.ui.view", {
            "name": name,
            "type": "qweb",
            "arch": full_arch,
            "key": key,
            "website_id": 1,
            "active": True,
        })
        print(f"  Created view: id={view_id}")

    # Check if page exists
    existing_page = sr("website.page", [["url", "=", url], ["website_id", "=", 1]], ["id"])
    if existing_page:
        write("website.page", [existing_page[0]["id"]], {
            "view_id": view_id,
            "website_published": True,
        })
        print(f"  Updated page: id={existing_page[0]['id']}")
    else:
        page_id = create("website.page", {
            "name": name,
            "url": url,
            "view_id": view_id,
            "website_published": True,
            "website_id": 1,
        })
        print(f"  Created page: id={page_id}")

    return view_id


# ============================================================
# 1. About Us
# ============================================================
print("\n=== 1. 關於我們 (/about-us) ===")
create_or_update_page("關於我們", "/about-us", "website.inzense_about_us", """
<section style="background: linear-gradient(135deg, #27292C 0%, #4a3c2a 100%); padding: 80px 20px; text-align:center;">
    <div class="container">
        <h1 style="color:#FFFFFF; font-size:36px; letter-spacing:4px;">關於 禪香不二</h1>
        <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:18px; font-style:italic;">About Inzense</p>
    </div>
</section>

<section class="inzense-section" style="padding:60px 0;">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-6">
                <p style="color:#D8B772; font-size:12px; text-transform:uppercase; letter-spacing:3px;">Our Story</p>
                <h2>品牌故事</h2>
                <p>禪香不二，源自對天然香品的執著追求。我們堅持以台灣在地植物為基底，結合傳統製香工藝，手工製作每一支線香。</p>
                <p>「不二」意味著唯一、純粹。我們相信，真正的好香不需要化學添加，只需要大自然最純粹的饋贈。</p>
                <blockquote style="border-left:3px solid #D8B772; padding-left:20px; margin:24px 0; font-style:italic; color:#7A7A7A;">
                    「一縷清香，自在生活。用最純粹的香氣，找回內心的平靜。」
                </blockquote>
            </div>
            <div class="col-md-6 text-center">
                <div style="background:#f9f7f4; border-radius:12px; padding:40px;">
                    <i class="fa fa-pagelines" style="font-size:64px; color:#D8B772; margin-bottom:16px; display:block;"></i>
                    <h4>天然 · 手工 · 台灣製造</h4>
                    <p style="color:#7A7A7A; font-size:13px;">每一支線香都經過嚴格品質把關</p>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="inzense-section-warm" style="padding:60px 0; background:#f9f7f4;">
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

<section class="inzense-section" style="padding:40px 0; text-align:center;">
    <div class="container">
        <p style="color:#7A7A7A; font-size:13px;">營業時間：週一至週日 09:00 - 17:00</p>
        <a href="/shop" class="btn btn-primary">探索商品</a>
    </div>
</section>
""")


# ============================================================
# 2. FAQ
# ============================================================
print("\n=== 2. 常見問題 (/qa) ===")
create_or_update_page("常見問題", "/qa", "website.inzense_qa", """
<section style="background: linear-gradient(135deg, #27292C 0%, #4a3c2a 100%); padding: 60px 20px; text-align:center;">
    <div class="container">
        <h1 style="color:#FFFFFF; font-size:32px; letter-spacing:3px;">常見問題</h1>
        <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:16px; font-style:italic;">FAQ</p>
    </div>
</section>

<section class="inzense-section" style="padding:50px 0;">
    <div class="container" style="max-width:800px;">

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：線香是天然的嗎？</h5>
            <p style="color:#7A7A7A;">是的，禪香不二所有線香皆使用天然原料製成，不添加化學香精、黏合劑或人工色素。我們堅持以沉香、檀香、降真香等天然材料手工調配。</p>
        </div>

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：如何下單購買？</h5>
            <p style="color:#7A7A7A;">您可以直接在本網站瀏覽商品並加入購物車結帳。如需大量訂購或企業合作，請聯繫 <a href="mailto:service@inzense.com.tw">service@inzense.com.tw</a>。</p>
        </div>

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：有提供退換貨服務嗎？</h5>
            <p style="color:#7A7A7A;">依照消費者保護法第19條，您享有7天鑑賞期。商品如有瑕疵或不符描述，我們將提供退換貨服務。詳情請參閱<a href="/return-policy">退換貨政策</a>。</p>
        </div>

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：線香的燃燒時間大約多久？</h5>
            <p style="color:#7A7A7A;">迷你香約15-20分鐘，長線香約40-60分鐘，盤香約2-4小時，實際時間因環境通風而異。</p>
        </div>

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：可以批發或經銷嗎？</h5>
            <p style="color:#7A7A7A;">歡迎！我們提供經銷通路合作。請來電 <strong>0911-675-120</strong> 或來信 <a href="mailto:cooperate@inzense.com.tw">cooperate@inzense.com.tw</a> 洽詢。</p>
        </div>

        <div class="inzense-card inzense-card-accent mb-4">
            <h5 style="color:#27292C;">Q：如何成為會員？</h5>
            <p style="color:#7A7A7A;">在本網站註冊帳戶即可成為會員。會員可享有訂單查詢、集點回饋、專屬優惠等服務。<a href="/my">立即註冊 →</a></p>
        </div>

    </div>
</section>
""")


# ============================================================
# 3. Privacy Policy
# ============================================================
print("\n=== 3. 隱私政策 (/privacy-policy) ===")
create_or_update_page("隱私政策", "/privacy-policy", "website.inzense_privacy", """
<section style="background: linear-gradient(135deg, #27292C 0%, #4a3c2a 100%); padding: 60px 20px; text-align:center;">
    <div class="container">
        <h1 style="color:#FFFFFF; font-size:32px; letter-spacing:3px;">隱私權政策</h1>
        <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:16px; font-style:italic;">Privacy Policy</p>
    </div>
</section>

<section class="inzense-section" style="padding:50px 0;">
    <div class="container" style="max-width:800px;">
        <h4>資料蒐集範圍</h4>
        <p style="color:#7A7A7A;">當您在禪香不二網站進行購物、註冊會員或訂閱時，我們可能會蒐集以下資料：姓名、電子信箱、電話號碼、配送地址、付款資訊。</p>

        <h4 class="mt-4">資料使用目的</h4>
        <p style="color:#7A7A7A;">您的個人資料僅用於：訂單處理與配送、客戶服務與售後支援、會員積點與優惠通知、改善我們的產品與服務品質。</p>

        <h4 class="mt-4">資料保護</h4>
        <p style="color:#7A7A7A;">我們採用業界標準的安全措施保護您的個人資料，包括 SSL 加密傳輸和安全的資料儲存環境。我們不會將您的個人資料出售或出租予第三方。</p>

        <h4 class="mt-4">Cookie 使用</h4>
        <p style="color:#7A7A7A;">本網站使用 Cookie 技術以提供更好的瀏覽體驗、記住您的登入狀態和購物車內容。您可以透過瀏覽器設定管理 Cookie。</p>

        <h4 class="mt-4">聯絡我們</h4>
        <p style="color:#7A7A7A;">如對隱私權政策有任何疑問，請聯繫：<a href="mailto:service@inzense.com.tw">service@inzense.com.tw</a></p>
    </div>
</section>
""")


# ============================================================
# 4. Return Policy
# ============================================================
print("\n=== 4. 退換貨政策 (/return-policy) ===")
create_or_update_page("退換貨政策", "/return-policy", "website.inzense_return", """
<section style="background: linear-gradient(135deg, #27292C 0%, #4a3c2a 100%); padding: 60px 20px; text-align:center;">
    <div class="container">
        <h1 style="color:#FFFFFF; font-size:32px; letter-spacing:3px;">退換貨政策</h1>
        <p style="color:#D8B772; font-family:'Cormorant Garamond',serif; font-size:16px; font-style:italic;">Return Policy</p>
    </div>
</section>

<section class="inzense-section" style="padding:50px 0;">
    <div class="container" style="max-width:800px;">
        <h4>七天鑑賞期</h4>
        <p style="color:#7A7A7A;">依據消費者保護法第19條，自收到商品隔日起算7天內，您可無條件申請退貨。商品需維持全新、未拆封且完整包裝狀態。</p>

        <h4 class="mt-4">退貨條件</h4>
        <ul style="color:#7A7A7A;">
            <li>商品未經使用、未拆封</li>
            <li>原始包裝完整（含贈品、配件）</li>
            <li>附上訂單編號及購買憑證</li>
            <li>非客製化或特殊訂製商品</li>
        </ul>

        <h4 class="mt-4">退款方式</h4>
        <p style="color:#7A7A7A;">退貨確認後，我們將於14個工作天內完成退款。退款將以原付款方式退回。</p>

        <h4 class="mt-4">換貨服務</h4>
        <p style="color:#7A7A7A;">如需換貨（規格、品項），請聯繫客服安排。換貨商品將於收到退回商品後3-5個工作天寄出。</p>

        <h4 class="mt-4">退貨地址</h4>
        <p style="color:#7A7A7A;">新北市中和區立德街26巷1號樓上<br/>收件人：禪香不二 客服部<br/>電話：0926-926-851</p>

        <h4 class="mt-4">聯繫客服</h4>
        <p style="color:#7A7A7A;">客服信箱：<a href="mailto:service@inzense.com.tw">service@inzense.com.tw</a><br/>LINE@：<strong>@209hnrwf</strong></p>
    </div>
</section>
""")


# ============================================================
# Verify all pages
# ============================================================
print("\n=== Verification ===")
for path in ["/about-us", "/qa", "/privacy-policy", "/return-policy"]:
    try:
        resp = urllib.request.urlopen(f"{URL}{path}", timeout=5)
        code = resp.getcode()
        content = resp.read().decode("utf-8")
        has_brand = "禪香不二" in content
        print(f"  {path}: {code} {'✅' if code == 200 and has_brand else '❌'} (size={len(content):,})")
    except urllib.error.HTTPError as e:
        print(f"  {path}: {e.code} ❌")

print("\nStatic pages creation complete.")
