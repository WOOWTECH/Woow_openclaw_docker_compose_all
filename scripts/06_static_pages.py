#!/usr/bin/env python3
"""Phase 6: Build all static pages - About Us, Contact, Activity, Policies, QA."""
import xmlrpc.client
import json

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

with open("/tmp/inzense-image-mapping.json") as f:
    img = json.load(f)

def img_url(name):
    return f"/web/image/{img[name]}" if name in img else ""

website_id = 1

def create_or_update_page(page_url, page_name, page_arch):
    """Create or update a website page."""
    # Search for existing page
    page_ids = models.execute_kw(db, uid, password, "website.page", "search", [
        [["url", "=", page_url], ["website_id", "=", website_id]]
    ])

    if page_ids:
        page_data = models.execute_kw(db, uid, password, "website.page", "read", [page_ids[:1], ["view_id"]])
        view_id = page_data[0]["view_id"][0]
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[view_id], {
            "arch": page_arch,
        }])
        print(f"  Updated page: {page_name} ({page_url}) view_id={view_id}")
        return page_ids[0]
    else:
        # Create new view
        view_key = f"website.inzense_{page_url.strip('/').replace('-', '_').replace('/', '_')}"
        view_id = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
            "name": page_name,
            "type": "qweb",
            "arch": page_arch,
            "key": view_key,
            "website_id": website_id,
        }])
        # Create page
        page_id = models.execute_kw(db, uid, password, "website.page", "create", [{
            "name": page_name,
            "url": page_url,
            "view_id": view_id,
            "website_id": website_id,
            "website_published": True,
            "is_published": True,
        }])
        print(f"  Created page: {page_name} ({page_url}) page_id={page_id}, view_id={view_id}")
        return page_id


print("=" * 60)
print("PHASE 6: Build Static Pages")
print("=" * 60)

# ================================================================
# PAGE 1: About Us
# ================================================================
print("\n--- About Us ---")
about_arch = f'''<t t-name="website.inzense_about_us">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">

            <!-- Hero -->
            <section style="position: relative; min-height: 350px; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('{img_url("lifestyle-incense.jpg")}') center center / cover no-repeat;"/>
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(39,41,44,0.55);"/>
                <div class="container text-center" style="position: relative; z-index: 2; padding: 100px 20px;">
                    <img src="{img_url("logo-full.png")}" alt="禪香不二" style="max-width: 140px; margin-bottom: 20px;"/>
                    <h1 style="color: #fff; font-size: 38px; letter-spacing: 5px; margin-bottom: 10px;">關於 禪香不二</h1>
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 16px; letter-spacing: 2px;">結合在地植物香氣，體驗台灣自然之美</p>
                </div>
            </section>

            <!-- Brand Story -->
            <section style="background: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{img_url("incense-animation.gif")}" alt="禪香不二" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Our Story</p>
                            <h2 style="font-size: 28px; margin-bottom: 20px; color: #27292C;">品牌故事</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                禪香不二秉持著對高品質、天然原料的堅持，專注於台灣在地製作。我們的線香採用純天然木本、草本、樹脂漢方配方等香料，不添加任何化學成分或人工香精。每一款產品都是精心調配，散發怡人香氣的同時，更能平衡身心、淨化空間。
                            </p>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                從功能系列的財神香、善緣香、除障香，到以七大脈輪為靈感的脈輪系列；從連結東方信仰文化的神明系列，到採用台灣在地珍貴木材的台灣系列——每一支線香都承載著我們對天然好香的追求與對傳統文化的致敬。
                            </p>
                            <div class="inzense-quote" style="font-family: 'Cormorant Garamond', serif; font-size: 18px; font-style: italic; color: #54595F; border-left: 3px solid #D8B772; padding: 15px 25px; margin: 25px 0;">
                                「線香不僅是一種品味香氣的行為，更是一種生活態度，一種尋找內在平靜旅程的鑰匙。」
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Three Pillars -->
            <section style="background: #f9f7f4; padding: 70px 0;">
                <div class="container text-center">
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Our Commitment</p>
                    <h2 style="font-size: 28px; margin-bottom: 40px; color: #27292C;">我們的堅持</h2>
                    <div class="row">
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-cat-card" style="background: #fff; border-radius: 8px; padding: 35px 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                                <div style="width: 80px; height: 80px; background: #E4916E; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 28px; font-weight: 700;">天</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 18px; margin-bottom: 10px;">天然原料</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">堅持使用純天然木本、草本、樹脂漢方配方等原料，嚴選來自西澳、非洲、南美洲、東南亞等地的珍貴香材，不添加任何化學成分或人工香精</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-cat-card" style="background: #fff; border-radius: 8px; padding: 35px 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                                <div style="width: 80px; height: 80px; background: #D8B772; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 28px; font-weight: 700;">台</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 18px; margin-bottom: 10px;">台灣在地製作</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">從原料挑選到配方調製，每一個環節都在台灣在地完成。結合台灣珍貴的肖楠、黃檜、龍柏、牛樟等在地木材，展現台灣山林的自然之美</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-cat-card" style="background: #fff; border-radius: 8px; padding: 35px 20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">
                                <div style="width: 80px; height: 80px; background: #61CE70; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 28px; font-weight: 700;">純</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 18px; margin-bottom: 10px;">零化學添加</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">不添加任何人工香精、化學黏著劑或有害物質。採用印尼楠木黏粉作為天然黏合劑，連過敏體質的朋友也能安心使用</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Founder -->
            <section style="background: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 order-lg-2 mb-4">
                            <img src="{img_url("video-sequence.gif")}" alt="Matt老師" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 order-lg-1 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Founder</p>
                            <h2 style="font-size: 28px; margin-bottom: 20px; color: #27292C;">主理人 Matt</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                Matt老師專精於天然香的研發與製作，致力於將傳統香道文化與現代生活結合。在東方信仰文化中，香品不僅是一種香氛產品，也是人們與上天溝通的媒介。Matt老師希望透過禪香不二的線香，讓大家可以享受天然好香，也能對傳統香道文化有更進一步的認識。
                            </p>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                從原料挑選到配方調製，每一個環節都親自把關。嚴選來自西澳洲、非洲、巴拉圭、秘魯、印度、柬埔寨、越南等地的珍貴天然香材，搭配台灣在地的肖楠、黃檜、龍柏等珍貴木材，確保每一支線香都達到最高品質標準。
                            </p>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                除了製香，Matt老師也開設天然香椎手作課程、生活茶道入門、生活香道入門等課程，帶領學員親身體驗香道文化的魅力，從指尖觸碰香材的溫度中，找回對生活的掌控感。
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Business Hours -->
            <section style="background: #27292C; padding: 50px 0;">
                <div class="container text-center">
                    <h3 style="color: #D8B772; font-size: 22px; margin-bottom: 15px; letter-spacing: 2px;">營業時間</h3>
                    <p style="color: #ccc; font-size: 15px; margin-bottom: 0;">週一至週日 09:00 - 17:00</p>
                </div>
            </section>

        </div>
    </t>
</t>'''
create_or_update_page("/about-us", "關於我們", about_arch)


# ================================================================
# PAGE 2: Contact Us
# ================================================================
print("\n--- Contact Us ---")
contact_arch = f'''<t t-name="website.inzense_contactus">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">

            <!-- Hero -->
            <section style="background: #f9f7f4; padding: 60px 0;">
                <div class="container text-center">
                    <h1 style="font-size: 34px; color: #27292C; letter-spacing: 3px; margin-bottom: 10px;">聯絡我們</h1>
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 14px; letter-spacing: 2px;">Contact Us</p>
                </div>
            </section>

            <!-- Contact Info -->
            <section style="background: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-6 mb-4">
                            <h3 style="color: #27292C; font-size: 22px; margin-bottom: 25px;">聯繫方式</h3>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">客服時間</h5>
                                <p style="color: #7A7A7A;">週一至週五 10:00 - 18:00</p>
                            </div>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">客服電話</h5>
                                <p style="color: #7A7A7A;">0926-926-851</p>
                            </div>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">業務/經銷/合作</h5>
                                <p style="color: #7A7A7A;">0911-675-120</p>
                            </div>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">客服信箱</h5>
                                <p style="color: #7A7A7A;">service@inzense.com.tw</p>
                            </div>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">業務合作信箱</h5>
                                <p style="color: #7A7A7A;">cooperate@inzense.com.tw</p>
                            </div>

                            <div style="margin-bottom: 20px;">
                                <h5 style="color: #E4916E; font-size: 15px; margin-bottom: 5px;">官方 LINE@</h5>
                                <p style="color: #7A7A7A;">@209hnrwf</p>
                            </div>
                        </div>

                        <div class="col-lg-6 mb-4">
                            <h3 style="color: #27292C; font-size: 22px; margin-bottom: 25px;">服務項目</h3>
                            <div class="row">
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">經銷通路</p>
                                    </div>
                                </div>
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">團購合作</p>
                                    </div>
                                </div>
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">配方研發</p>
                                    </div>
                                </div>
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">客製化代工</p>
                                    </div>
                                </div>
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">天然香椎手作課程</p>
                                    </div>
                                </div>
                                <div class="col-6 mb-3">
                                    <div style="background: #f9f7f4; border-radius: 8px; padding: 20px; text-align: center;">
                                        <p style="color: #27292C; font-weight: 600; margin: 0;">生活茶道／香道入門</p>
                                    </div>
                                </div>
                            </div>

                            <h3 style="color: #27292C; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">社群媒體</h3>
                            <p style="color: #7A7A7A; font-size: 14px;">
                                Facebook: <a href="https://www.facebook.com/onlyinzense" target="_blank" style="color: #E4916E;">@onlyinzense</a><br/>
                                Instagram: <a href="https://instagram.com/only_inzense" target="_blank" style="color: #E4916E;">@only_inzense</a><br/>
                                官方網站: <a href="https://www.inzense.com.tw" target="_blank" style="color: #E4916E;">www.inzense.com.tw</a>
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Locations -->
            <section style="background: #f9f7f4; padding: 70px 0;">
                <div class="container">
                    <div class="text-center mb-5">
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Our Locations</p>
                        <h2 style="font-size: 28px; color: #27292C;">門市據點</h2>
                    </div>
                    <div class="row">
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-location-card" style="background: #fff; border-radius: 8px; padding: 25px; border-left: 4px solid #E4916E;">
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 12px;">禪香不二茶香空間</h4>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 5px;">台北市北投區光明路240號2樓之8</p>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 0;">營業時間：10:00-18:00（預約制）</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-location-card" style="background: #fff; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772;">
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 12px;">慢空茶室 私人招待所</h4>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 5px;">新北市三重區集賢路138號樓上</p>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 0;">營業時間：10:00-18:00（預約制）</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div class="inzense-location-card" style="background: #fff; border-radius: 8px; padding: 25px; border-left: 4px solid #61CE70;">
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 12px;">禪香企業社 研發製香廠</h4>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 5px;">新北市中和區立德街26巷1號樓上</p>
                                <p style="color: #7A7A7A; font-size: 14px; margin-bottom: 0;">營業時間：平日 10:00-18:00（預約制）</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

        </div>
    </t>
</t>'''
create_or_update_page("/contactus", "聯絡我們", contact_arch)


# ================================================================
# PAGE 3: Activity / Courses
# ================================================================
print("\n--- Activity ---")
activity_arch = f'''<t t-name="website.inzense_activity">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">

            <section style="position: relative; min-height: 400px; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('{img_url("lifestyle-incense.jpg")}') center center / cover no-repeat;"/>
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(39,41,44,0.6);"/>
                <div class="container text-center" style="position: relative; z-index: 2; padding: 120px 20px;">
                    <h1 style="color: #fff; font-size: 36px; letter-spacing: 4px; margin-bottom: 15px;">課程與活動</h1>
                    <p style="color: #D8B772; font-family: 'Cormorant Garamond', serif; font-size: 20px; font-style: italic; letter-spacing: 2px; margin-bottom: 8px;">一場透過呼吸找回專注的感官旅程</p>
                    <p style="color: #eee; font-size: 15px; letter-spacing: 1px;">透過穩定的溫度，喚醒沉睡在原木裡的百年靈魂</p>
                </div>
            </section>

            <section style="background: #fff; padding: 70px 0;">
                <div class="container text-center">
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Philosophy</p>
                    <h2 style="font-size: 28px; margin-bottom: 25px; color: #27292C;">課程理念</h2>
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <p style="color: #7A7A7A; font-size: 16px; line-height: 2;">
                                生活香道，是一場透過呼吸找回專注的感官旅程。將帶領您學習如何透過穩定的溫度，喚醒沉睡在原木裡的百年靈魂。當香氣穿透呼吸，您將發現，平靜其實不必遠求，就在這一呼一吸之間。
                            </p>
                            <p style="color: #7A7A7A; font-size: 16px; line-height: 2;">
                                我們相信：香氣不只是點綴，更是帶領心靈回歸平靜的引子。作為天然製香品牌，我們致力將這份「靜」延伸至日常。透過多元感官課程——無論品茶、習藝或觀照未來，這不僅是技能學習，更是一場「禪意生活」的實踐。
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section style="background: #f9f7f4; padding: 70px 0;">
                <div class="container">
                    <div class="text-center mb-5">
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Courses</p>
                        <h2 style="font-size: 28px; color: #27292C;">天然製香 禪香不二 — 課程介紹</h2>
                    </div>
                    <div class="row">
                        <div class="col-lg-6 mb-4">
                            <div style="background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.05); height: 100%;">
                                <div style="width: 60px; height: 60px; background: #E4916E; border-radius: 50%; margin-bottom: 15px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 22px;">椎</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 10px;">天然香椎手作課程</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8;">帶你親手製作屬於自己的香椎，透過焚香粉、調香、塑形的過程，感受手作的專注與沉澱，將心意緩緩注入其中。完成後以貼心盒裝成品，讓香氣陪伴你度過時序的轉換，也成為祝福的寄託。</p>
                                <ul style="color: #7A7A7A; font-size: 13px; line-height: 1.8; padding-left: 20px;">
                                    <li>教你親手製作香椎</li>
                                    <li>學習辨別天然材料</li>
                                    <li>創造屬於你的香氣</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <div style="background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.05); height: 100%;">
                                <div style="width: 60px; height: 60px; background: #D8B772; border-radius: 50%; margin-bottom: 15px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 22px;">茶</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 10px;">生活茶道入門</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8;">在繁忙的城市中心，為自己按下一段時光的暫停鍵。生活茶道，不只是泡好一杯茶，而是一場與自我靜心對話。我們將複雜的茶學化繁為簡，邀請您從認識一方茶席開始。</p>
                                <ul style="color: #7A7A7A; font-size: 13px; line-height: 1.8; padding-left: 20px;">
                                    <li>蓋碗心法：掌握告別燙手、優雅泡茶的關鍵技巧</li>
                                    <li>古樹茶辨識：學會分辨千年古樹與一般茶葉</li>
                                    <li>茶席儀式：體驗生活茶席佈置技巧</li>
                                    <li>特製古樹茶和菓子搭配品鑑</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <div style="background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.05); height: 100%;">
                                <div style="width: 60px; height: 60px; background: #61CE70; border-radius: 50%; margin-bottom: 15px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 22px;">香</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 10px;">生活香道入門</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8;">一場透過呼吸找回專注的感官旅程。帶領您學習如何透過穩定的溫度，喚醒沉睡在原木裡的百年靈魂。</p>
                                <ul style="color: #7A7A7A; font-size: 13px; line-height: 1.8; padding-left: 20px;">
                                    <li>基礎香學概論：揭開沉香與檀香的神祕面紗</li>
                                    <li>隔熱薰香原理：學習掌握火候與溫度的平衡</li>
                                    <li>深度辨香教學：對比天然野生與人工合成香材</li>
                                    <li>實作演練：親手操作香具，感受香氣變化</li>
                                </ul>
                            </div>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <div style="background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.05); height: 100%;">
                                <div style="width: 60px; height: 60px; background: #13AFF0; border-radius: 50%; margin-bottom: 15px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: #fff; font-size: 22px;">禪</span>
                                </div>
                                <h4 style="color: #27292C; font-size: 17px; margin-bottom: 10px;">不定期多元感官講座</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8;">透過多元感官課程——無論品茶、習藝或觀照未來，這不僅是技能學習，更是一場「禪意生活」的實踐。讓我們在香氣中，看見更純粹的風景。</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Testimonials -->
            <section style="background: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="text-center mb-5">
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Testimonials</p>
                        <h2 style="font-size: 28px; color: #27292C;">真實好評</h2>
                    </div>
                    <div class="row">
                        <div class="col-lg-4 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「謝謝您用心製作的香，我朋友拿回家點，沒有過敏耶！這是非常大的讚嘆～因為她使用外面標榜多天然的產品，她都無法使用，她竟然完好如初。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 黃小姐</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「香氣很純正，比我之前買的好很多。燃燒起來比其他家的耐燃，大約快2小時才燒完，紮實。香灰也比較細緻。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 郭先生</p>
                            </div>
                        </div>
                        <div class="col-lg-4 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「我冥想的時候點十方清淨，雜念有比較少，而且好香真的超讚。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 陳小姐</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Partners -->
            <section style="background: #f9f7f4; padding: 50px 0;">
                <div class="container text-center">
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Partners</p>
                    <h3 style="font-size: 22px; color: #27292C; margin-bottom: 25px;">合作夥伴</h3>
                    <p style="color: #7A7A7A; font-size: 14px;">光合生活 ｜ 台中綠園道金典里想家 ｜ 小島好日 ｜ 青玄堂清暑靜心班 ｜ 旗袍兒 ｜ 桃園土地公文化館 ｜ 鑫喜文創 ｜ 禪生活</p>
                </div>
            </section>

            <section style="background: #E4916E; padding: 50px 0;">
                <div class="container text-center">
                    <h3 style="color: #fff; font-size: 22px; margin-bottom: 15px; letter-spacing: 2px;">想了解更多課程資訊？</h3>
                    <p style="color: #fff; font-size: 15px; margin-bottom: 25px;">歡迎來電或來信洽詢課程細節與報名方式</p>
                    <a href="/contactus" class="btn" style="background: #fff; color: #E4916E; border-radius: 30px; padding: 10px 30px; font-weight: 600;">聯絡我們</a>
                </div>
            </section>

        </div>
    </t>
</t>'''
create_or_update_page("/activity", "課程與活動", activity_arch)


# ================================================================
# PAGE 4: Privacy Policy
# ================================================================
print("\n--- Privacy Policy ---")
privacy_arch = '''<t t-name="website.inzense_privacy">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section style="background: #f9f7f4; padding: 50px 0;">
                <div class="container text-center">
                    <h1 style="font-size: 30px; color: #27292C; letter-spacing: 2px;">隱私政策</h1>
                </div>
            </section>
            <section style="background: #fff; padding: 50px 0;">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <h3 style="color: #27292C; font-size: 20px; margin-bottom: 15px;">個人資料蒐集與使用範圍</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">當您使用本網站所提供之功能服務時，我們將視該服務功能性質，請您提供必要的個人資料，並在該特定目的範圍內處理及利用您的個人資料。</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">會員訊息及行銷活動</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">禪香不二可能會不定期以電子郵件方式，發送給您相關的商品及活動訊息。如您不願接收此類訊息，可隨時取消訂閱。</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">資料保護與第三方提供</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">本網站會嚴格保護您的個人資料安全，不會任意將您的個人資料提供給第三方，除非經過您本人同意或法律另有規定。</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">隱私權政策修訂</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">本公司保留隨時修正本隱私權政策之權利，修正後的條款將刊登於網站上，不另行個別通知。</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>'''
create_or_update_page("/privacy-policy", "隱私政策", privacy_arch)


# ================================================================
# PAGE 5: Return Policy
# ================================================================
print("\n--- Return Policy ---")
return_arch = '''<t t-name="website.inzense_return">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section style="background: #f9f7f4; padding: 50px 0;">
                <div class="container text-center">
                    <h1 style="font-size: 30px; color: #27292C; letter-spacing: 2px;">退換貨政策</h1>
                </div>
            </section>
            <section style="background: #fff; padding: 50px 0;">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <h3 style="color: #27292C; font-size: 20px; margin-bottom: 15px;">7天商品鑑賞期</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">依照消費者保護法規定，網路購物享有七天商品鑑賞期（含例假日）。</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">退換貨條件</h3>
                            <ul style="color: #7A7A7A; font-size: 14px; line-height: 2.2;">
                                <li>商品需為全新未拆封、未使用之狀態</li>
                                <li>商品外包裝及所有附件需完整保留</li>
                                <li>已拆封或使用過的商品恕不接受退換</li>
                            </ul>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">退款方式</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">退款將於收到退回商品並確認商品狀態後14個工作天內處理。</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">退貨地址</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">112 台北市北投區光明路 240 號 2 樓之 8</p>

                            <h3 style="color: #27292C; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">聯繫方式</h3>
                            <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">
                                Email: service@inzense.com.tw<br/>
                                LINE@: @209hnrwf
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>'''
create_or_update_page("/return-policy", "退換貨政策", return_arch)


# ================================================================
# PAGE 6: QA
# ================================================================
print("\n--- QA Page ---")
qa_arch = '''<t t-name="website.inzense_qa">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <section style="background: #f9f7f4; padding: 50px 0;">
                <div class="container text-center">
                    <h1 style="font-size: 30px; color: #27292C; letter-spacing: 2px;">常見問題</h1>
                    <p style="color: #D8B772; font-family: \'Roboto Slab\', serif; font-size: 14px;">QA &#x554F;&#x984C;&#x56DE;&#x8986;</p>
                </div>
            </section>
            <section style="background: #fff; padding: 50px 0;">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-lg-8">

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 品牌介紹？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">禪香不二由主理人Matt專精於天然香的研發與製作，堅持使用純天然原料，台灣在地製作。我們的線香採用純天然木本、草本、樹脂漢方配方等香料，不添加任何化學成分或人工香精。線香不僅是一種品味香氣的行為，更是一種生活態度，一種尋找內在平靜旅程的鑰匙。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 如何訂購？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">您可以透過官網直接訂購，也可以透過蝦皮、MOMO購物網等電商平台選購。如需批發或團購，歡迎來電或來信洽詢。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 付款方式有哪些？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">線上刷卡、銀行轉帳、超商付款。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 寄送方式？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">超商店到店寄送、宅配到府。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 到貨時間？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">一般一週內寄出；若無現貨約需14-21天製作。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 產品有哪些系列？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">我們提供豐富的產品線，包括：<br/>
                                ● <b>線香</b>：功能系列（財神香、善緣香、除障香、排寒香等）、神明系列（觀世音菩薩、財神爺、天上聖母等15款）、脈輪系列（七大脈輪對應香品）、五行系列（金木水火土）、台灣系列（肖楠、黃檜、龍柏等台灣特有木材）、外國系列（秘魯聖木、白色鼠尾草等）、檀香系列、沉香系列、特色系列<br/>
                                ● <b>迷你香</b>：各系列的迷你版本，約5公分，8支/盒<br/>
                                ● <b>拜拜用香</b>：古邦老山檀香、巴拉圭綠檀、柬埔寨沉香等<br/>
                                ● <b>優惠組合</b>：神明保庇熱賣組、上班創業必備組、脈輪療癒優惠組等主題組合</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 線香的成分是什麼？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">所有原料皆為純天然木本、草本、樹脂漢方配方，搭配印尼楠木黏粉作為天然黏合劑，絕無香精、化學成分或劣質材料。原料來源涵蓋西澳洲檀香、非洲降真檀、巴拉圭綠檀、秘魯聖木、柬埔寨沉香、越南惠安沉香、印度老山檀香、台灣黃檜、台灣肖楠等數十種珍貴天然香材。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 線香的尺寸規格？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">長管線香約17-18.5公分，直徑約1.8-2.5mm，燃燒時間約40-50分鐘（無風室內環境）。每管約20-34支，重量約10-12g。迷你香長約5公分，每盒8支，重約0.3g。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 線香如何保存？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">請存放於常溫、乾燥、陰涼處即可。點燃時請遠離兒童與寵物，建議在通風良好的室內使用。</p>
                            </div>

                            <div style="border-bottom: 1px solid #eee; padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 過敏體質可以使用嗎？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">我們的線香全部採用純天然原料，不含任何化學添加物。許多對市面上其他品牌過敏的客人，使用禪香不二的產品都沒有過敏反應。不過每個人體質不同，建議先少量試用。</p>
                            </div>

                            <div style="padding: 25px 0;">
                                <h4 style="color: #E4916E; font-size: 16px; margin-bottom: 10px;">Q: 有提供課程嗎？</h4>
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 2;">有的！我們提供天然香椎手作課程、生活茶道入門、生活香道入門，以及不定期的多元感官講座。歡迎至課程與活動頁面了解更多，或來電預約。</p>
                            </div>

                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>'''
create_or_update_page("/qa", "常見問題", qa_arch)


# Verify all pages
print("\n=== Verifying pages ===")
import urllib.request
pages = ["/", "/about-us", "/contactus", "/activity", "/privacy-policy", "/return-policy", "/qa"]
for page_url in pages:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069{page_url}")
        print(f"  [{resp.status}] {page_url}")
    except Exception as e:
        print(f"  [FAIL] {page_url}: {e}")

print("\nPhase 6: DONE")
