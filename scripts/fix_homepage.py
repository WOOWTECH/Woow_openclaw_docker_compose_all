#!/usr/bin/env python3
"""Fix homepage to use website.layout wrapper properly."""
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

def iu(name):
    return f"/web/image/{img[name]}" if name in img else ""

# Build homepage arch with website.layout call
arch = '<t t-name="website.homepage">\n'
arch += '  <t t-call="website.layout">\n'
arch += '    <div id="wrap" class="oe_structure oe_empty">\n'

# Hero Banner
arch += f'''
      <section style="min-height:550px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url('{iu("hero-banner.jpg")}') center/cover no-repeat;z-index:0;"/>
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.35);z-index:1;"/>
        <div class="container" style="position:relative;z-index:2;padding:160px 20px 140px;">
          <div class="text-center">
            <img src="{iu("logo-full.png")}" alt="禪香不二" style="max-width:180px;margin-bottom:25px;"/>
            <h1 style="color:#fff;font-size:42px;font-weight:700;letter-spacing:6px;margin-bottom:12px;">禪香不二</h1>
            <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:18px;letter-spacing:3px;margin-bottom:8px;">精心製作的天然線香</p>
            <p style="color:#eee;font-size:15px;letter-spacing:1.5px;margin-bottom:35px;">結合在地植物香氣，體驗台灣自然之美</p>
            <a href="/shop" class="btn btn-primary" style="padding:12px 40px;font-size:15px;border-radius:30px;letter-spacing:2px;">立即購買</a>
          </div>
        </div>
      </section>
'''

# Promise Bar
arch += '''
      <section style="background-color:#E4916E;padding:18px 0;">
        <div class="container"><div class="row text-center">
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">天然製香 品質保證</p></div>
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">一縷清香 自在生活</p></div>
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">台灣在地 手工製作</p></div>
        </div></div>
      </section>
'''

# Agarwood
arch += f'''
      <section style="background:#fff;padding:70px 0;">
        <div class="container"><div class="row align-items-center">
          <div class="col-lg-6 mb-4"><img src="{iu("incense-animation.gif")}" alt="沉香系列" class="img-fluid" style="border-radius:8px;box-shadow:0 5px 25px rgba(0,0,0,0.1);"/></div>
          <div class="col-lg-6 mb-4">
            <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Agarwood Collection</p>
            <h2 style="font-size:30px;margin-bottom:20px;color:#27292C;">沉香系列</h2>
            <p style="color:#7A7A7A;font-size:15px;line-height:2;">沉香線香系列，採用優質沉香為主要原料，產品有加里萬丹沉香、泰國沉香等。緩釋神秘古雅香氣，助於冥想與放鬆，適合室內空間提升氛圍之選。</p>
            <a href="/shop" class="btn btn-primary mt-3" style="border-radius:30px;padding:10px 30px;">SHOP NOW</a>
          </div>
        </div></div>
      </section>
'''

# Sandalwood
arch += f'''
      <section style="background:#f9f7f4;padding:70px 0;">
        <div class="container"><div class="row align-items-center">
          <div class="col-lg-6 order-lg-2 mb-4"><img src="{iu("lifestyle-incense.jpg")}" alt="檀香系列" class="img-fluid" style="border-radius:8px;box-shadow:0 5px 25px rgba(0,0,0,0.1);"/></div>
          <div class="col-lg-6 order-lg-1 mb-4">
            <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Sandalwood Collection</p>
            <h2 style="font-size:30px;margin-bottom:20px;color:#27292C;">檀香系列</h2>
            <p style="color:#7A7A7A;font-size:15px;line-height:2;">檀香系列，以淨化心靈為訴求，散發溫暖木質香調，深層淨化身心。產品包括印度老山檀香、綠檀香等，適合打造祥和莊嚴的修身空間。</p>
            <a href="/shop" class="btn btn-primary mt-3" style="border-radius:30px;padding:10px 30px;">SHOP NOW</a>
          </div>
        </div></div>
      </section>
'''

# Functional
arch += f'''
      <section style="background:#fff;padding:70px 0;">
        <div class="container"><div class="row align-items-center">
          <div class="col-lg-6 mb-4"><img src="{iu("video-sequence.gif")}" alt="功能系列" class="img-fluid" style="border-radius:8px;box-shadow:0 5px 25px rgba(0,0,0,0.1);"/></div>
          <div class="col-lg-6 mb-4">
            <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Functional Collection</p>
            <h2 style="font-size:30px;margin-bottom:20px;color:#27292C;">功能系列</h2>
            <p style="color:#7A7A7A;font-size:15px;line-height:2;">功能系列，包括財神香、善緣香與除障香，各具吸引財富、增進人緣、消除障礙等功能，以植物精華調和，適合特定需求者使用，強化意向，營造正面能量。</p>
            <a href="/shop" class="btn btn-primary mt-3" style="border-radius:30px;padding:10px 30px;">SHOP NOW</a>
          </div>
        </div></div>
      </section>
'''

# God Series Banner
arch += f'''
      <section style="position:relative;min-height:450px;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url('{iu("god-series-banner.jpg")}') center/cover no-repeat;"/>
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.45);"/>
        <div class="container" style="position:relative;z-index:2;padding:100px 20px;">
          <div class="col-lg-7">
            <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Gods Collection</p>
            <h2 style="color:#fff;font-size:34px;margin-bottom:20px;">神明系列</h2>
            <p style="color:#eee;font-size:15px;line-height:2;">點一支香，開啟你與各個神明之間的連結吧！邀請你一起點一支「神明系列」線香，感受各神明仙佛給予我們的祝福！</p>
            <a href="/shop" class="btn btn-primary mt-3" style="border-radius:30px;padding:12px 35px;">SHOP NOW</a>
          </div>
        </div>
      </section>
'''

# Promise Bar 2
arch += '''
      <section style="background-color:#E4916E;padding:18px 0;">
        <div class="container"><div class="row text-center">
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">天然製香 品質保證</p></div>
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">一縷清香 自在生活</p></div>
          <div class="col-md-4"><p style="color:#fff;font-size:15px;font-weight:600;margin:0;letter-spacing:1.5px;">口碑不斷 真實推薦</p></div>
        </div></div>
      </section>
'''

# YouTube
arch += '''
      <section style="background:#fff;padding:70px 0;">
        <div class="container text-center">
          <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Our Story</p>
          <h2 style="font-size:30px;margin-bottom:30px;color:#27292C;">品香的生活與學習</h2>
          <div class="row justify-content-center"><div class="col-lg-8">
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;box-shadow:0 5px 25px rgba(0,0,0,0.1);">
              <iframe src="https://www.youtube.com/embed/IJrw-3-RfyQ" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen="allowfullscreen"/>
            </div>
          </div></div>
        </div>
      </section>
'''

# Blog Section
arch += '''
      <section style="background:#f9f7f4;padding:70px 0;">
        <div class="container text-center">
          <p style="color:#D8B772;font-family:'Roboto Slab',serif;font-size:13px;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">Incense Academy</p>
          <h2 style="font-size:30px;margin-bottom:40px;color:#27292C;">香品學堂</h2>
          <div class="row">
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">一縷香的靜心</h4><p style="color:#7A7A7A;font-size:14px;">透過焚香的儀式，找到內心的平靜</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">香與神明的對話</h4><p style="color:#7A7A7A;font-size:14px;">了解各種神明對應的香品選擇</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">山醫命卜香</h4><p style="color:#7A7A7A;font-size:14px;">香道與中醫、命理的深層連結</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">時節香氣</h4><p style="color:#7A7A7A;font-size:14px;">應時節選香，順應自然的養生之道</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">食香知旅</h4><p style="color:#7A7A7A;font-size:14px;">美食與香的結合</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
            <div class="col-lg-4 col-md-6 mb-4"><div class="inzense-blog-card"><h4 style="color:#27292C;">琴棋書畫茶酒花香道</h4><p style="color:#7A7A7A;font-size:14px;">傳統雅趣與香道的完美融合</p><a href="/blog" style="color:#E4916E;font-weight:600;font-size:13px;">閱讀更多</a></div></div>
          </div>
          <a href="/blog" class="btn btn-primary mt-3" style="border-radius:30px;padding:10px 35px;">查看更多</a>
        </div>
      </section>
'''

# CTA
arch += f'''
      <section style="position:relative;min-height:350px;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:url('{iu("lifestyle-incense.jpg")}') center/cover no-repeat;"/>
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(39,41,44,0.6);"/>
        <div class="container text-center" style="position:relative;z-index:2;padding:100px 20px;">
          <h2 style="color:#fff;font-size:34px;letter-spacing:3px;margin-bottom:15px;">身心沉靜 享受清雅之趣</h2>
          <p style="color:#D8B772;font-family:'Cormorant Garamond',serif;font-size:18px;font-style:italic;letter-spacing:2px;margin-bottom:30px;">線香不僅是一種品味香氣的行為，更是一種生活態度</p>
          <a href="/shop" class="btn" style="background:#D8B772;color:#fff;border-radius:30px;padding:12px 35px;font-weight:600;letter-spacing:1px;">探索商品</a>
        </div>
      </section>
'''

arch += '\n    </div>\n  </t>\n</t>'

print(f"Arch length: {len(arch)} chars")

# Write the arch
models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1295], {
    "arch": arch,
}])
print("Homepage view 1295 updated successfully!")

# Verify
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()
print(f"Page size: {len(content)} bytes")
print(f"Has navbar: {'navbar' in content or 'o_main_nav' in content}")
print(f"Has footer: {'footer' in content.lower()}")
print(f"Has brand: {'禪香不二' in content}")
