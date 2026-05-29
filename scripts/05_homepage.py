#!/usr/bin/env python3
"""Phase 5: Build exact homepage replica using Odoo website QWeb templates."""
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

print("=" * 60)
print("PHASE 5: Build Homepage")
print("=" * 60)

homepage_arch = f'''<t t-name="website.homepage" t-inherit="website.homepage_default" t-inherit-mode="primary">
    <xpath expr="//div[@id='wrap']" position="replace">
        <div id="wrap" class="oe_structure oe_empty">

            <!-- ============================================ -->
            <!-- SECTION 1: Hero Banner -->
            <!-- ============================================ -->
            <section class="s_cover pt0 pb0" style="min-height: 550px; position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('{img_url("hero-banner.jpg")}') center center / cover no-repeat; z-index: 0;"/>
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.35); z-index: 1;"/>
                <div class="container" style="position: relative; z-index: 2; padding: 160px 20px 140px;">
                    <div class="text-center">
                        <img src="{img_url("logo-full.png")}" alt="禪香不二" style="max-width: 180px; margin-bottom: 25px;"/>
                        <h1 style="color: #fff; font-size: 42px; font-weight: 700; letter-spacing: 6px; margin-bottom: 12px; text-shadow: 0 2px 8px rgba(0,0,0,0.3);">禪香不二</h1>
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 18px; letter-spacing: 3px; margin-bottom: 8px;">精心製作的天然線香</p>
                        <p style="color: #eee; font-size: 15px; letter-spacing: 1.5px; margin-bottom: 35px;">結合在地植物香氣，體驗台灣自然之美</p>
                        <a href="/shop" class="btn btn-primary" style="padding: 12px 40px; font-size: 15px; border-radius: 30px; letter-spacing: 2px;">立即購買</a>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 2: Brand Promise Bar -->
            <!-- ============================================ -->
            <section style="background-color: #E4916E; padding: 18px 0;">
                <div class="container">
                    <div class="row text-center">
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">天然製香 品質保證</p>
                        </div>
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">一縷清香 自在生活</p>
                        </div>
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">台灣在地 手工製作</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 3: Product Series Showcase - 沉香 -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{img_url("incense-animation.gif")}" alt="沉香系列" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Agarwood Collection</p>
                            <h2 style="font-size: 30px; margin-bottom: 20px; color: #27292C;">沉香系列</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                沉香線香系列，採用優質沉香為主要原料，涵蓋柬埔寨土沉香、泰國水沉香、加里萬丹土沉香、安汶土沉香、巴布亞土沉香、越南惠安沉香等多種珍貴產地的沉香。野生品種沉香的豐富韻味，幽遠靜謐中帶來放鬆和舒適感，適合供佛、空間芳香與淨化心靈。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 30px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 4: 檀香系列 -->
            <!-- ============================================ -->
            <section style="background-color: #f9f7f4; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 order-lg-2 mb-4">
                            <img src="{img_url("lifestyle-incense.jpg")}" alt="檀香系列" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 order-lg-1 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Sandalwood Collection</p>
                            <h2 style="font-size: 30px; margin-bottom: 20px; color: #27292C;">檀香系列</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                檀香系列，以淨化心靈為訴求，散發溫暖木質香調，深層淨化身心。嚴選正印度老山檀香、正印尼古邦老山檀香、西澳新山檀香（根部／頭部／大綜）、巴拉圭綠檀、琥珀巴西紫檀等頂級檀香。溫暖濃郁的奶香和醇厚的檸檬香，多層次的豐富變化，適合打造祥和莊嚴的修身空間。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 30px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 5: 功能系列 -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{img_url("video-sequence.gif")}" alt="功能系列" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Functional Collection</p>
                            <h2 style="font-size: 30px; margin-bottom: 20px; color: #27292C;">功能系列</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                功能系列，針對不同生活需求精心調配。財神香以西澳洲檀香根部與伊朗玫瑰招財開運；善緣香增加貴人運與事業運；除障香以十七種天然香材排除個人障礙；排寒香排除身心靈沉重能量；十方清淨以六種珍貴沉香帶來身心靈清明；壇城樂土淨化安定氣場；平安香祈求出行平安；幸運香開啟好運能量；靈感香激發創意覺醒；療心香療癒撫慰心靈；姻緣香牽引美好緣分。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 30px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 5b: 脈輪系列 -->
            <!-- ============================================ -->
            <section style="background-color: #f9f7f4; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 order-lg-2 mb-4">
                            <img src="{img_url("lifestyle-incense.jpg")}" alt="脈輪系列" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 order-lg-1 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Chakra Collection</p>
                            <h2 style="font-size: 30px; margin-bottom: 20px; color: #27292C;">脈輪系列</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                以人體七大脈輪為靈感設計的系列線香。根輪香帶來穩定與安全感；丹田輪香激發創造力；太陽輪香增強自信與個人力量；心輪香帶來愛與療癒；喉輪香促進溝通表達；眉心輪香提升直覺與洞察力；頂輪香連結高層意識與靈性覺醒。每款皆以對應的天然香材精心調配。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 30px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 5c: 台灣系列 -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-lg-6 mb-4">
                            <img src="{img_url("incense-animation.gif")}" alt="台灣系列" class="img-fluid" style="border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);"/>
                        </div>
                        <div class="col-lg-6 mb-4">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Taiwan Collection</p>
                            <h2 style="font-size: 30px; margin-bottom: 20px; color: #27292C;">台灣系列</h2>
                            <p style="color: #7A7A7A; font-size: 15px; line-height: 2;">
                                採用台灣特有的珍貴木材製作，每款皆帶有台灣的歷史痕跡。台灣肖楠香味稀少珍貴；台灣黃檜散發獨特清新木質香氣；台灣龍柏穩重而沉靜；台灣牛樟帶有獨特樟腦清香；台灣香茅清新驅蚊。結合在地植物香氣，體驗台灣自然之美。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 30px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 6: 神明系列 Banner -->
            <!-- ============================================ -->
            <section style="position: relative; min-height: 450px; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('{img_url("god-series-banner.jpg")}') center center / cover no-repeat;"/>
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.45);"/>
                <div class="container" style="position: relative; z-index: 2; padding: 100px 20px;">
                    <div class="row align-items-center">
                        <div class="col-lg-7">
                            <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Gods Collection</p>
                            <h2 style="color: #fff; font-size: 34px; margin-bottom: 20px;">神明系列</h2>
                            <p style="color: #eee; font-size: 15px; line-height: 2;">
                                點一支香，開啟你與各個神明之間的連結吧！在東方信仰文化中，香品不僅是一種香氛產品，也是人們與上天溝通的媒介。Matt老師希望透過「神明系列」線香，讓大家可以享受天然好香，也能對這些協助穩定人民心靈和生活的神明仙佛，有更進一步的認識。
                            </p>
                            <p style="color: #eee; font-size: 15px; line-height: 2;">
                                系列涵蓋觀世音菩薩、財神爺、天上聖母（媽祖）、福德正神（土地公）、關聖帝君、月老星君、藥師佛、玉皇上帝、佛祖（釋迦摩尼佛）、文昌帝君、玄天上帝、城隍爺、註生娘娘、九天玄女、中壇元帥（三太子）、閻羅王、純陽祖師（呂洞賓）、降龍羅漢（濟公）等，每款皆有獨特的香氣層次與祝福寓意。
                            </p>
                            <a href="/shop" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 12px 35px;">SHOP NOW</a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 6b: 優惠組合 Showcase -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="text-center mb-4">
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Combo Sets</p>
                        <h2 style="font-size: 30px; margin-bottom: 15px; color: #27292C;">精選優惠組合</h2>
                        <p style="color: #7A7A7A; font-size: 15px;">依據不同需求精心搭配，讓您一次擁有最適合的香品組合</p>
                    </div>
                    <div class="row">
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">神明保庇熱賣組</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">財運增益、身體安康、感情圓滿等主題組合</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽組合 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">上班創業必備組</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">職場必備、貴人好運、小人退散等主題組合</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽組合 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">脈輪療癒優惠組</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">情緒釋放、穩定能量、靈感開光、決策穩心</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽組合 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">內在穩定能量組</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">安眠舒心、專注清明、低頻退散、淨化守護</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽組合 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">迷你香系列</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">約5公分輕巧攜帶，8支/盒，各系列迷你版</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽迷你香 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; text-align: center;">
                                <h4 style="color: #27292C; font-size: 16px; margin-bottom: 8px;">拜拜用香</h4>
                                <p style="color: #7A7A7A; font-size: 13px;">古邦老山檀香、巴拉圭綠檀、柬埔寨沉香等</p>
                                <a href="/shop" style="color: #E4916E; font-weight: 600; font-size: 13px;">瀏覽拜拜香 →</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 7: Brand Promise -->
            <!-- ============================================ -->
            <section style="background-color: #E4916E; padding: 18px 0;">
                <div class="container">
                    <div class="row text-center">
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">天然製香 品質保證</p>
                        </div>
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">一縷清香 自在生活</p>
                        </div>
                        <div class="col-md-4">
                            <p style="color: #fff; font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 1.5px;">口碑不斷 真實推薦</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 8: YouTube Video -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container text-center">
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Our Story</p>
                    <h2 style="font-size: 30px; margin-bottom: 30px; color: #27292C;">品香的生活與學習</h2>
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.1);">
                                <iframe src="https://www.youtube.com/embed/IJrw-3-RfyQ" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen="allowfullscreen"/>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 9: 香品學堂 Blog Section -->
            <!-- ============================================ -->
            <section style="background-color: #f9f7f4; padding: 70px 0;">
                <div class="container text-center">
                    <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Incense Academy</p>
                    <h2 style="font-size: 30px; margin-bottom: 40px; color: #27292C;">香品學堂</h2>
                    <div class="row">
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card">
                                <h4 style="color: #27292C;">一縷香的靜心</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">透過焚香的儀式，找到內心的平靜</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card">
                                <h4 style="color: #27292C;">香與神明的對話</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">了解各種神明對應的香品選擇</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card">
                                <h4 style="color: #27292C;">山醫命卜香</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">香道與中醫、命理的深層連結</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card" style="border-bottom-color: #E4916E;">
                                <h4 style="color: #27292C;">時節香氣</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">應時節選香，順應自然的養生之道</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card" style="border-bottom-color: #E4916E;">
                                <h4 style="color: #27292C;">食香知旅</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">美食與香的結合，味覺與嗅覺的饗宴</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div class="inzense-blog-card" style="border-bottom-color: #E4916E;">
                                <h4 style="color: #27292C;">琴棋書畫茶酒花香道</h4>
                                <p style="color: #7A7A7A; font-size: 14px;">傳統雅趣與香道的完美融合</p>
                                <a href="/blog" style="color: #E4916E; font-weight: 600; font-size: 13px;">閱讀更多 →</a>
                            </div>
                        </div>
                    </div>
                    <a href="/blog" class="btn btn-primary mt-3" style="border-radius: 30px; padding: 10px 35px;">查看更多</a>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 10: Testimonials -->
            <!-- ============================================ -->
            <section style="background-color: #fff; padding: 70px 0;">
                <div class="container">
                    <div class="text-center mb-4">
                        <p style="color: #D8B772; font-family: 'Roboto Slab', serif; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px;">Testimonials</p>
                        <h2 style="font-size: 30px; margin-bottom: 30px; color: #27292C;">口碑不斷 真實推薦</h2>
                    </div>
                    <div class="row">
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「謝謝您用心製作的香，我朋友拿回家點，沒有過敏耶！她使用外面標榜多天然的產品都無法使用，竟然完好如初。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 黃小姐</p>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「香氣很純正，比我之前買的好很多。燃燒起來比其他家的耐燃，大約快2小時才燒完，紮實。香灰也比較細緻。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 郭先生</p>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「善緣香搭配方位真的很有用，我每天認識的新朋友，質都很好。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— Angely</p>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「我冥想的時候點十方清淨，雜念有比較少，而且好香真的超讚。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 陳小姐</p>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「昨天我點了壇城樂土，感覺特別可以把心靜下來。今天點了土神香，線香燒完後整個空間圍繞著靜謐的感覺。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— 高小姐</p>
                            </div>
                        </div>
                        <div class="col-lg-4 col-md-6 mb-4">
                            <div style="background: #f9f7f4; border-radius: 8px; padding: 25px; border-left: 4px solid #D8B772; height: 100%;">
                                <p style="color: #7A7A7A; font-size: 14px; line-height: 1.8; font-style: italic;">「我朋友之前買他牌的，說聞起來會頭痛，你家的用起來完全不會。他也有說你家的煙很少，很喜歡。」</p>
                                <p style="color: #E4916E; font-weight: 600; font-size: 13px; margin-bottom: 0;">— Emily</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================ -->
            <!-- SECTION 11: CTA - 身心沉靜 -->
            <!-- ============================================ -->
            <section style="position: relative; min-height: 350px; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url('{img_url("lifestyle-incense.jpg")}') center center / cover no-repeat;"/>
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(39,41,44,0.6);"/>
                <div class="container text-center" style="position: relative; z-index: 2; padding: 100px 20px;">
                    <h2 style="color: #fff; font-size: 34px; letter-spacing: 3px; margin-bottom: 15px;">身心沉靜 享受清雅之趣</h2>
                    <p style="color: #D8B772; font-family: 'Cormorant Garamond', serif; font-size: 18px; font-style: italic; letter-spacing: 2px; margin-bottom: 30px;">
                        線香不僅是一種品味香氣的行為，更是一種生活態度，一種尋找內在平靜旅程的鑰匙
                    </p>
                    <a href="/shop" class="btn" style="background: #D8B772; color: #fff; border-radius: 30px; padding: 12px 35px; font-weight: 600; letter-spacing: 1px;">探索商品</a>
                </div>
            </section>

        </div>
    </xpath>
</t>'''

# Find and update homepage view
homepage_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["key", "=", "website.homepage"]]
])

if homepage_views:
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [homepage_views, {
        "arch": homepage_arch,
    }])
    print(f"Updated homepage view IDs: {homepage_views}")
else:
    print("ERROR: Homepage view not found!")

# Verify
import urllib.request
try:
    resp = urllib.request.urlopen("http://localhost:8069/")
    print(f"Homepage HTTP status: {resp.status}")
except Exception as e:
    print(f"Homepage check: {e}")

print("Phase 5 Homepage: DONE")
