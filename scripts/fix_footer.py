#!/usr/bin/env python3
"""Fix footer by creating a website-specific override of the footer_custom view."""
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
logo_id = img.get("logo-header.png", "")

# Build the footer arch that replaces the default footer
footer_arch = f'''<data inherit_id="website.layout" name="Inzense Footer" active="True">
    <xpath expr="//div[@id='footer']" position="replace">
        <div id="footer" class="oe_structure oe_structure_solo" t-ignore="true" t-if="not no_footer">
            <section style="background:#27292C;padding:50px 0 20px;" data-snippet="s_text_block" data-name="Inzense Footer">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-3 col-md-6 mb-4">
                            <img src="/web/image/{logo_id}" alt="禪香不二" style="max-width:120px;margin-bottom:15px;filter:brightness(2);"/>
                            <p style="color:#999;font-size:12px;line-height:1.8;">秉持著對高品質、天然原料的堅持，專注於台灣在地製作。</p>
                            <div style="margin-top:10px;">
                                <a href="https://www.facebook.com/onlyinzense" target="_blank" style="color:#D8B772;margin-right:15px;">Facebook</a>
                                <a href="https://instagram.com/only_inzense" target="_blank" style="color:#D8B772;">Instagram</a>
                            </div>
                        </div>
                        <div class="col-lg-3 col-md-6 mb-4">
                            <h5 style="color:#D8B772;font-size:15px;font-weight:600;margin-bottom:15px;">客服資訊</h5>
                            <p style="color:#ccc;margin-bottom:6px;font-size:13px;">客服時間：週一至週五 10:00-18:00</p>
                            <p style="color:#ccc;margin-bottom:6px;font-size:13px;">客服電話：0926-926-851</p>
                            <p style="color:#ccc;margin-bottom:6px;font-size:13px;">業務/經銷：0911-675-120</p>
                            <p style="color:#ccc;margin-bottom:6px;font-size:13px;">客服信箱：service@inzense.com.tw</p>
                            <p style="color:#ccc;margin-bottom:6px;font-size:13px;">業務合作：cooperate@inzense.com.tw</p>
                            <p style="color:#ccc;margin-bottom:0;font-size:13px;">LINE@：@209hnrwf</p>
                        </div>
                        <div class="col-lg-3 col-md-6 mb-4">
                            <h5 style="color:#D8B772;font-size:15px;font-weight:600;margin-bottom:15px;">服務項目</h5>
                            <ul style="list-style:none;padding:0;">
                                <li style="margin-bottom:6px;"><a href="/contactus" style="color:#ccc;font-size:13px;">經銷通路</a></li>
                                <li style="margin-bottom:6px;"><a href="/contactus" style="color:#ccc;font-size:13px;">團購合作</a></li>
                                <li style="margin-bottom:6px;"><a href="/contactus" style="color:#ccc;font-size:13px;">配方研發</a></li>
                                <li style="margin-bottom:6px;"><a href="/contactus" style="color:#ccc;font-size:13px;">客製化代工</a></li>
                                <li style="margin-bottom:6px;"><a href="/activity" style="color:#ccc;font-size:13px;">天然香講座</a></li>
                                <li style="margin-bottom:0;"><a href="/activity" style="color:#ccc;font-size:13px;">手作課程</a></li>
                            </ul>
                        </div>
                        <div class="col-lg-3 col-md-6 mb-4">
                            <h5 style="color:#D8B772;font-size:15px;font-weight:600;margin-bottom:15px;">相關政策</h5>
                            <ul style="list-style:none;padding:0;">
                                <li style="margin-bottom:6px;"><a href="/privacy-policy" style="color:#ccc;font-size:13px;">隱私政策</a></li>
                                <li style="margin-bottom:6px;"><a href="/return-policy" style="color:#ccc;font-size:13px;">退換貨政策</a></li>
                                <li style="margin-bottom:6px;"><a href="/qa" style="color:#ccc;font-size:13px;">常見問題</a></li>
                                <li style="margin-bottom:0;"><a href="/my/orders" style="color:#ccc;font-size:13px;">訂單查詢</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </xpath>
</data>'''

# Update the existing default footer view (ID 1360) for website_id=1
# We create a website-specific copy
existing = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["key", "=", "website.footer_custom"], ["website_id", "=", 1]]
])
if existing:
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [existing, {
        "arch": footer_arch,
    }])
    print(f"Updated website-specific footer: IDs={existing}")
else:
    # Create website-specific override
    vid = models.execute_kw(db, uid, password, "ir.ui.view", "create", [{
        "name": "Inzense Footer",
        "type": "qweb",
        "arch": footer_arch,
        "key": "website.footer_custom",
        "inherit_id": 1305,  # website.layout
        "website_id": 1,
        "active": True,
        "priority": 20,  # higher priority than default (16)
    }])
    print(f"Created website-specific footer: ID={vid}")

# Verify
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/")
content = resp.read().decode()
checks = ['0926-926-851', 'service@inzense.com.tw', 'facebook.com/onlyinzense', '隱私政策', '退換貨政策']
for c in checks:
    print(f"  [{'OK' if c in content else 'MISS'}] {c}")
print("Footer fix done!")
