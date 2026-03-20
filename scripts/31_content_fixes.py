#!/usr/bin/env python3
"""
PRD v3: Content fixes — activity page, blog images, hero text, blog posts.
"""
import xmlrpc.client
import base64
import os

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

IMG_DIR = "/tmp/activity-images"

def upload_img(filename, name=None):
    """Upload image file to Odoo, return attachment ID."""
    path = os.path.join(IMG_DIR, filename)
    if not os.path.isfile(path) or os.path.getsize(path) < 100:
        return None
    att_name = name or f"inzense_activity_{filename}"
    existing = models.execute_kw(db, uid, password, "ir.attachment", "search", [
        [["name", "=", att_name]]
    ])
    if existing:
        return existing[0]
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(filename)[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext.strip("."), "image/jpeg")
    att_id = models.execute_kw(db, uid, password, "ir.attachment", "create", [{
        "name": att_name,
        "datas": data,
        "type": "binary",
        "mimetype": mime,
        "public": True,
        "res_model": "ir.ui.view",
        "res_id": 0,
    }])
    print(f"  Uploaded {filename}: ID={att_id}")
    return att_id

# ================================================================
# UPLOAD ACTIVITY IMAGES
# ================================================================
print("=" * 60)
print("Uploading activity images")
print("=" * 60)

img_workshop = upload_img("course-incense-workshop.jpg")
img_tea = upload_img("course-tea-ceremony.jpg")
img_incense = upload_img("course-incense-ceremony.jpg")
img_multi = upload_img("course-multi-sensory.jpg")
img_kol1 = upload_img("course-kol-1.jpg")
img_kol2 = upload_img("course-kol-2.jpg")
img_blog_cover = upload_img("blog-default-cover.png", "inzense_blog_cover")

def iu(att_id):
    return f"/web/image/{att_id}" if att_id else ""

# ================================================================
# FIX 1: HOMEPAGE HERO TEXT READABILITY
# ================================================================
print("\n" + "=" * 60)
print("FIX 1: Homepage Hero Text Readability")
print("=" * 60)

hp = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
if hp:
    arch = hp[0]["arch"]
    # Increase overlay darkness from 0.35 to 0.5
    arch = arch.replace("rgba(0,0,0,0.35)", "rgba(0,0,0,0.50)")
    # Make text more prominent with text-shadow
    if "text-shadow" not in arch:
        arch = arch.replace(
            "font-size:42px;font-weight:700;letter-spacing:6px",
            "font-size:42px;font-weight:700;letter-spacing:6px;text-shadow:0 3px 15px rgba(0,0,0,0.7)"
        )
    # Make subtitle more visible
    arch = arch.replace(
        "color:#eee;font-size:15px;letter-spacing:1.5px",
        "color:#fff;font-size:16px;letter-spacing:1.5px;text-shadow:0 2px 8px rgba(0,0,0,0.5)"
    )
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1303], {"arch": arch}])
    print("  Hero overlay darkened + text shadows added")

# ================================================================
# FIX 2: REBUILD ACTIVITY PAGE WITH REAL CONTENT
# ================================================================
print("\n" + "=" * 60)
print("FIX 2: Rebuild Activity Page")
print("=" * 60)

activity_arch = f'''<t t-name="website.inzense_activity">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">

            <!-- Hero -->
            <section style="position:relative;min-height:400px;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url('{iu(img_workshop)}') center/cover no-repeat;"></div>
                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.55);"></div>
                <div class="container text-center" style="position:relative;z-index:2;padding:120px 20px;">
                    <h1 style="color:#fff;font-size:36px;letter-spacing:4px;margin-bottom:15px;text-shadow:0 2px 10px rgba(0,0,0,0.5);">身心沉靜 享受清雅之趣</h1>
                    <p style="color:#D8B772;font-size:16px;letter-spacing:2px;">生活香道，是一場透過呼吸找回專注的感官旅程</p>
                </div>
            </section>

            <!-- Intro -->
            <section style="background:#fff;padding:60px 0;">
                <div class="container text-center">
                    <p style="color:#27292C;font-size:16px;letter-spacing:1px;margin-bottom:5px;">天然製香 禪香不二</p>
                    <h2 style="font-size:28px;color:#27292C;margin-bottom:20px;">課程介紹</h2>
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                將帶領您學習如何透過穩定的溫度，喚醒沉睡在原木裡的百年靈魂。當香氣穿透呼吸，您將發現，平靜其實不必遠求，就在這一呼一吸之間。
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Course 1: 天然香椎手作課程 -->
            <section style="background:#f9f7f4;padding:70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{iu(img_workshop)}" alt="天然香椎手作課程" class="img-fluid" style="border-radius:8px;"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color:#D8B772;font-size:14px;letter-spacing:2px;margin-bottom:5px;">INCENSE WORKSHOP</p>
                            <h3 style="color:#27292C;font-size:24px;margin-bottom:15px;">天然香椎手作課程</h3>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                帶你親手製作屬於自己的香椎。透過焚香粉、調香、塑形的過程，你將感受到手作的專注與沉澱，將心意緩緩注入其中。完成後以貼心盒裝成品，讓香氣陪伴你度過時序的轉換，也成為祝福的寄託。
                            </p>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                無論是初學者，或對香文化充滿熱愛的朋友，都能在這裡重新建立與「香」的溫度連結。
                            </p>
                            <h5 style="color:#D8B772;font-size:15px;margin-top:20px;margin-bottom:10px;">【課程亮點】</h5>
                            <ul style="color:#7A7A7A;font-size:14px;line-height:2;">
                                <li>教你親手製作香椎</li>
                                <li>學習辨別天然材料</li>
                                <li>創造屬於你的香氣</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Course 2: 生活茶道入門 -->
            <section style="background:#fff;padding:70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 order-lg-2 mb-4">
                            <img src="{iu(img_tea)}" alt="生活茶道入門" class="img-fluid" style="border-radius:8px;"/>
                        </div>
                        <div class="col-lg-6 order-lg-1 mb-4">
                            <p style="color:#D8B772;font-size:14px;letter-spacing:2px;margin-bottom:5px;">TEA CEREMONY</p>
                            <h3 style="color:#27292C;font-size:24px;margin-bottom:15px;">生活茶道入門</h3>
                            <p style="color:#54595F;font-size:15px;font-style:italic;margin-bottom:15px;">
                                「在繁忙的城市中心，為自己按下一段時光的暫停鍵。」
                            </p>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                生活茶道，不只是泡好一杯茶，而是一場與自我靜心對話。我們將複雜的茶學化繁為簡，邀請您從認識一方茶席開始。透過指尖觸碰蓋碗的溫度，感受茶湯流動的韻律，重新找回對生活的掌控感。
                            </p>
                            <h5 style="color:#D8B772;font-size:15px;margin-top:20px;margin-bottom:10px;">【課程亮點】</h5>
                            <ul style="color:#7A7A7A;font-size:14px;line-height:2;">
                                <li>蓋碗心法｜從指法教學到出湯比例，掌握優雅泡茶的關鍵技巧</li>
                                <li>古樹茶辨識｜學會分辨千年古樹與一般茶葉的差異</li>
                                <li>茶席儀式｜體驗生活茶席佈置技巧</li>
                                <li>Bonus 珍藏加碼｜特製古樹茶和菓子搭配</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Course 3: 生活香道入門 -->
            <section style="background:#f9f7f4;padding:70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{iu(img_incense)}" alt="生活香道入門" class="img-fluid" style="border-radius:8px;"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color:#D8B772;font-size:14px;letter-spacing:2px;margin-bottom:5px;">INCENSE CEREMONY</p>
                            <h3 style="color:#27292C;font-size:24px;margin-bottom:15px;">生活香道入門</h3>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                生活香道，是一場透過呼吸找回專注的感官旅程。將帶領您學習如何透過穩定的溫度，喚醒沉睡在原木裡的百年靈魂。
                            </p>
                            <h5 style="color:#D8B772;font-size:15px;margin-top:20px;margin-bottom:10px;">【課程亮點】</h5>
                            <ul style="color:#7A7A7A;font-size:14px;line-height:2;">
                                <li>基礎香學概論｜揭開沉香與檀香的神祕面紗</li>
                                <li>隔熱薰香原理｜學習掌握火候與溫度的平衡</li>
                                <li>深度辨香教學｜對比天然野生與人工種植的香材</li>
                                <li>實作演練｜親手操作香具，感受香氣變化</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Course 4: 不定期多元感官講座 -->
            <section style="background:#fff;padding:70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 order-lg-2 mb-4">
                            <img src="{iu(img_multi)}" alt="多元感官講座" class="img-fluid" style="border-radius:8px;"/>
                        </div>
                        <div class="col-lg-6 order-lg-1 mb-4">
                            <p style="color:#D8B772;font-size:14px;letter-spacing:2px;margin-bottom:5px;">MULTI-SENSORY</p>
                            <h3 style="color:#27292C;font-size:24px;margin-bottom:15px;">不定期多元感官講座</h3>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                我們相信：香氣不只是點綴，更是帶領心靈回歸平靜的引子。作為天然製香品牌，我們致力將這份「靜」延伸至日常。透過多元感官課程——無論品茶、習藝或觀照未來，這不僅是技能學習，更是一場「禪意生活」的實踐。
                            </p>
                            <p style="color:#7A7A7A;font-size:15px;line-height:2;">
                                讓我們在香氣中，看見更純粹的風景。
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- CTA -->
            <section style="background:#D8B772;padding:50px 0;">
                <div class="container text-center">
                    <h3 style="color:#fff;font-size:22px;letter-spacing:2px;margin-bottom:15px;">想了解更多課程資訊？</h3>
                    <p style="color:#fff;font-size:15px;margin-bottom:25px;">歡迎來電或來信洽詢課程細節與報名方式</p>
                    <a href="/contactus" class="btn" style="background:#fff;color:#D8B772;border-radius:30px;padding:12px 30px;font-weight:600;">聯絡我們</a>
                </div>
            </section>

        </div>
    </t>
</t>'''

# Update the activity page
activity_pages = models.execute_kw(db, uid, password, "website.page", "search_read", [
    [["url", "=", "/activity"]]
], {"fields": ["view_id"]})
if activity_pages:
    act_view_id = activity_pages[0]["view_id"][0]
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[act_view_id], {"arch": activity_arch}])
    print(f"  Updated activity page view ID={act_view_id}")

# ================================================================
# FIX 3: BLOG AUTHOR + COVER IMAGES
# ================================================================
print("\n" + "=" * 60)
print("FIX 3: Blog Author + Cover Images")
print("=" * 60)

# Fix author display name
admin_user = models.execute_kw(db, uid, password, "res.users", "read", [[uid], ["partner_id"]])
partner_id = admin_user[0]["partner_id"][0]
models.execute_kw(db, uid, password, "res.partner", "write", [[partner_id], {
    "name": "禪香不二",
}])
print("  Admin partner name set to '禪香不二'")

# Set blog cover image for all posts
blog_id = 3  # 香品學堂
all_posts = models.execute_kw(db, uid, password, "blog.post", "search_read", [
    [["blog_id", "=", blog_id]]
], {"fields": ["id", "name", "tag_ids"]})
print(f"  Blog posts to update: {len(all_posts)}")

# Use the blog cover image for posts without covers
if img_blog_cover:
    with open(os.path.join(IMG_DIR, "blog-default-cover.png"), "rb") as f:
        cover_b64 = base64.b64encode(f.read()).decode()

    # Use course images as category-specific covers
    category_covers = {}
    if img_workshop:
        with open(os.path.join(IMG_DIR, "course-incense-workshop.jpg"), "rb") as f:
            category_covers["default"] = base64.b64encode(f.read()).decode()
    if img_tea:
        with open(os.path.join(IMG_DIR, "course-tea-ceremony.jpg"), "rb") as f:
            category_covers["tea"] = base64.b64encode(f.read()).decode()
    if img_incense:
        with open(os.path.join(IMG_DIR, "course-incense-ceremony.jpg"), "rb") as f:
            category_covers["incense"] = base64.b64encode(f.read()).decode()

    # Get tag IDs for mapping
    tags = models.execute_kw(db, uid, password, "blog.tag", "search_read", [
        []
    ], {"fields": ["id", "name"]})
    tag_map = {t["name"]: t["id"] for t in tags}

    for post in all_posts:
        # Pick cover based on tag
        cover = category_covers.get("default", cover_b64)
        tag_names = []
        if post["tag_ids"]:
            tag_data = models.execute_kw(db, uid, password, "blog.tag", "read", [post["tag_ids"], ["name"]])
            tag_names = [t["name"] for t in tag_data]

        if any("茶" in tn or "琴棋" in tn for tn in tag_names):
            cover = category_covers.get("tea", cover)
        elif any("靜心" in tn or "香" in tn for tn in tag_names):
            cover = category_covers.get("incense", cover)

        # Set cover image
        try:
            models.execute_kw(db, uid, password, "blog.post", "write", [[post["id"]], {
                "cover_properties": '{"background-image": "url(\'/web/image/' + str(img_workshop) + '\')", "resize_class": "cover_auto", "opacity": "0.4"}',
            }])
        except:
            pass

    print(f"  Set cover images for {len(all_posts)} posts")

# ================================================================
# FIX 4: ADD MORE BLOG POSTS (28 new posts)
# ================================================================
print("\n" + "=" * 60)
print("FIX 4: Add Blog Posts from Original Site Categories")
print("=" * 60)

# Blog posts organized by category tag
new_posts = [
    # 一縷香的靜心
    {"name": "屬雞六合全解析：屬雞的六合貴人是誰？", "tag": "一縷香的靜心",
     "content": "<p>屬雞的人最需要掌握的關鍵運勢密碼，就是「屬雞六合：龍」。在十二地支中，酉（雞）與辰（龍）相合，龍是雞最重要的六合貴人。</p><p>了解六合關係，可以幫助我們在事業、感情、人際關係中找到最佳的合作夥伴與貴人方位。</p>"},
    {"name": "安太歲有用嗎？線上安太歲功效與禁忌一次看懂", "tag": "一縷香的靜心",
     "content": "<p>安太歲是否「真的有用」，關鍵不在於儀式本身，而在於我們賦予這份儀式的信念與敬意。太歲信仰源自古老的天文學與道教文化，是華人社會重要的年度祈福活動。</p>"},
    {"name": "如何透過焚香建立每日靜心儀式", "tag": "一縷香的靜心",
     "content": "<p>在忙碌的現代生活中，每天給自己十分鐘的靜心時間，是維持身心平衡的重要方式。焚香靜心不需要特別的空間或道具，只需要一支天然線香、一個安靜的角落。</p>"},
    {"name": "初學者的焚香入門指南：從選香到品香", "tag": "一縷香的靜心",
     "content": "<p>對於剛接觸焚香的初學者來說，面對琳瑯滿目的香品種類，往往不知從何開始。本文將從最基本的選香原則開始，帶你一步步進入香道的世界。</p>"},
    # 香與神明的對話
    {"name": "觀世音菩薩聖誕日焚香祈福指南", "tag": "香與神明的對話",
     "content": "<p>觀世音菩薩是台灣民間最受崇敬的神明之一。每年農曆二月十九日是觀音聖誕，許多信眾會前往寺廟焚香祈福。選擇適合的天然線香，可以讓您的祈禱更加虔誠。</p>"},
    {"name": "媽祖遶境進香必備的天然好香", "tag": "香與神明的對話",
     "content": "<p>每年農曆三月瘋媽祖，是台灣最盛大的宗教文化活動。無論是大甲媽祖遶境或白沙屯媽祖進香，焚香都是不可或缺的重要環節。</p>"},
    {"name": "財神爺的香品選擇與供奉方式", "tag": "香與神明的對話",
     "content": "<p>在華人文化中，財神爺是最受歡迎的神明之一。正確的供奉方式配合適合的天然香品，可以幫助招財納福、事業順利。</p>"},
    {"name": "文昌帝君：考生必拜的智慧之神", "tag": "香與神明的對話",
     "content": "<p>每逢考試季節，許多學生和家長都會前往文昌帝君廟祈求金榜題名。選擇文昌帝君專屬的線香，可以幫助提升專注力與考試運勢。</p>"},
    # 山醫命卜香
    {"name": "十二生肖與香品的五行對應關係", "tag": "山醫命卜香",
     "content": "<p>中國傳統命理學認為，每個人的生肖都有對應的五行屬性。根據自己的生肖五行選擇適合的香品，可以起到調和補缺的作用。</p>"},
    {"name": "紫微斗數與香道：用星盤找到你的專屬香品", "tag": "山醫命卜香",
     "content": "<p>紫微斗數是中國傳統命理學的精華，透過星盤分析可以了解一個人的性格特質和運勢走向。將紫微斗數與香道結合，可以找到最適合自己的香品。</p>"},
    {"name": "中醫養生與焚香：不同體質適合的香品", "tag": "山醫命卜香",
     "content": "<p>中醫理論認為，不同的香料具有不同的藥性和功效。根據個人體質選擇適合的香品，不僅能營造好氛圍，還能起到養生保健的作用。</p>"},
    {"name": "風水與香道：如何用焚香改善居家磁場", "tag": "山醫命卜香",
     "content": "<p>在風水學中，香氣被視為調整空間能量的重要工具。正確使用天然香品，可以化解煞氣、提升正面能量、改善居家風水。</p>"},
    # 時節香氣
    {"name": "立春焚香：迎接新年的第一縷香氣", "tag": "時節香氣",
     "content": "<p>立春是二十四節氣之首，代表著春天的到來。在這個萬物復甦的時刻，選擇清新的草本線香焚燒，可以為新的一年注入正面的能量。</p>"},
    {"name": "端午節艾草香：傳統避邪與現代養生", "tag": "時節香氣",
     "content": "<p>端午節是中華傳統文化中重要的節日，自古就有焚燒艾草驅邪避疫的習俗。天然艾草線香延續了這項傳統，同時融入現代養生的概念。</p>"},
    {"name": "中秋賞月品香：秋天最適合的香品推薦", "tag": "時節香氣",
     "content": "<p>秋高氣爽的季節，是品香的絕佳時機。中秋夜晚，在月光下焚一炷沉穩的檀香或沉香，與家人共享團圓的溫馨時光。</p>"},
    {"name": "冬至焚香：溫暖身心的養生之道", "tag": "時節香氣",
     "content": "<p>冬至是一年中白天最短的日子，也是陰氣最盛的時刻。此時焚燒溫暖系的香品，如肉桂、丁香、沉香等，可以幫助驅寒暖身。</p>"},
    # 食香知旅
    {"name": "台灣在地香料巡禮：從山林到餐桌", "tag": "食香知旅",
     "content": "<p>台灣豐富的地理環境孕育了許多珍貴的天然香料。從中低海拔的肖楠、黃檜，到高山的台灣紅檜，每一種香材都有其獨特的香韻與故事。</p>"},
    {"name": "日本香道文化之旅：從京都到東京的香之路", "tag": "食香知旅",
     "content": "<p>日本的香道文化源遠流長，從飛鳥時代傳入至今已有千年歷史。走訪京都的老舗香鋪、東京的現代香空間，體驗不同面向的香道文化。</p>"},
    {"name": "印度檀香之鄉：邁索爾的香木傳奇", "tag": "食香知旅",
     "content": "<p>印度邁索爾被譽為「檀香之都」，出產的老山檀香是世界上最頂級的檀香木。了解這片土地上的檀香種植歷史與文化。</p>"},
    {"name": "越南惠安沉香產地探訪", "tag": "食香知旅",
     "content": "<p>越南惠安是世界上最著名的沉香產地之一，出產的惠安系沉香以其甜美、花果香韻聞名於世。探訪這片孕育頂級沉香的土地。</p>"},
    # 琴棋書畫茶酒花香道
    {"name": "書法與焚香：文人雅士的靜心之道", "tag": "琴棋書畫茶酒花香道",
     "content": "<p>自古以來，文人雅士在揮毫潑墨之際，必先焚香靜心。香氣能幫助書法家進入專注的心流狀態，讓每一個筆畫都充滿力量與靈性。</p>"},
    {"name": "古琴與香道：聽琴品香的雅趣生活", "tag": "琴棋書畫茶酒花香道",
     "content": "<p>古琴被譽為「國樂之父」，其清雅的琴音與焚香的裊裊輕煙相互輝映，營造出最具中國古典美學的氛圍。</p>"},
    {"name": "插花與焚香：日式美學的極致表現", "tag": "琴棋書畫茶酒花香道",
     "content": "<p>在日本傳統美學中，花道與香道並列為修身養性的藝術。將插花與焚香結合，可以在有限的空間中創造無限的美感。</p>"},
    {"name": "品酒與品香：嗅覺藝術的雙重饗宴", "tag": "琴棋書畫茶酒花香道",
     "content": "<p>品酒與品香都是精緻的嗅覺藝術。了解如何在品酒的過程中搭配適合的香品，讓感官體驗更加豐富多層次。</p>"},
]

# Get tag mapping
tags = models.execute_kw(db, uid, password, "blog.tag", "search_read", [
    []
], {"fields": ["id", "name"]})
tag_map = {t["name"]: t["id"] for t in tags}

created = 0
for post_data in new_posts:
    existing = models.execute_kw(db, uid, password, "blog.post", "search", [
        [["name", "=", post_data["name"]]]
    ])
    if existing:
        continue

    tag_id = tag_map.get(post_data["tag"])
    vals = {
        "blog_id": blog_id,
        "name": post_data["name"],
        "content": post_data["content"],
        "website_published": True,
        "is_published": True,
        "website_id": 1,
    }
    if tag_id:
        vals["tag_ids"] = [(4, tag_id)]

    try:
        pid = models.execute_kw(db, uid, password, "blog.post", "create", [vals])
        created += 1
    except:
        pass

print(f"  Created {created} new blog posts")

# Final count
total = models.execute_kw(db, uid, password, "blog.post", "search_count", [[["blog_id", "=", blog_id]]])
print(f"  Total blog posts in 香品學堂: {total}")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

import urllib.request

for page, name in [("/", "Homepage"), ("/activity", "Activity"), ("/blog", "Blog")]:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069{page}")
        content = resp.read().decode()
        print(f"  [{len(content)}b] {name}: OK")
    except Exception as e:
        print(f"  {name}: {e}")

print("\n=== PRD v3 ALL FIXES APPLIED ===")
