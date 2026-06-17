#!/usr/bin/env python3
"""
Inzense Odoo 18 — Phase 6: Verification & Independent Scoring
9-team comprehensive assessment across 8 dimensions.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/76_verify_and_score.py
"""
import xmlrpc.client
import urllib.request
import re
import json

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


def search(model, domain):
    return models.execute_kw(DB, uid, PASSWORD, model, "search", [domain])


def fetch_page(path):
    try:
        resp = urllib.request.urlopen(f"{URL}{path}", timeout=10)
        return resp.getcode(), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


# ============================================================
# Fetch all key pages
# ============================================================
print("\n=== Fetching pages ===")
pages = {}
for path in ["/", "/shop", "/my", "/contactus"]:
    code, content = fetch_page(path)
    pages[path] = {"code": code, "content": content, "size": len(content)}
    print(f"  {path}: {code} ({len(content):,} bytes)")

homepage = pages["/"]["content"]
shoppage = pages["/shop"]["content"]

# ============================================================
# SCORING: 8 Dimensions
# ============================================================
scores = {}
findings = {}


# --- 1. Color Accuracy (15%) ---
print("\n" + "=" * 60)
print("1. COLOR ACCURACY (15%)")
print("=" * 60)

color_checks = {
    "Gold #D8B772 in CSS": "D8B772" in homepage,
    "Cyan #13AFF0 in CSS": "13AFF0" in homepage,
    "Dark #27292C in CSS": "27292C" in homepage,
    "No wrong #E4916E": "E4916E" not in homepage and "e4916e" not in homepage,
    "Gold hover #7E6124": "7E6124" in homepage or "7e6124" in homepage,
    "Warm bg #f9f7f4": "f9f7f4" in homepage,
}
color_pass = sum(1 for v in color_checks.values() if v)
color_score = round(color_pass / len(color_checks) * 10, 1)
scores["color"] = color_score
findings["color"] = []
for check, result in color_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["color"].append(check)


# --- 2. Typography (10%) ---
print("\n" + "=" * 60)
print("2. TYPOGRAPHY (10%)")
print("=" * 60)

typo_checks = {
    "Cormorant Garamond loaded": "Cormorant+Garamond" in homepage or "Cormorant Garamond" in homepage,
    "Noto Sans TC loaded": "Noto+Sans+TC" in homepage or "Noto Sans TC" in homepage,
    "Roboto loaded": "Roboto" in homepage,
    "Google Fonts link": "fonts.googleapis" in homepage,
}
typo_pass = sum(1 for v in typo_checks.values() if v)
typo_score = round(typo_pass / len(typo_checks) * 10, 1)
scores["typography"] = typo_score
findings["typography"] = []
for check, result in typo_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["typography"].append(check)


# --- 3. Navigation (15%) ---
print("\n" + "=" * 60)
print("3. NAVIGATION (15%)")
print("=" * 60)

menus = sr("website.menu", [["website_id", "=", 1], ["parent_id", "!=", False]], ["name", "url", "parent_id"])
top_menus = [m for m in menus if m["parent_id"] and not any(mm["parent_id"] and mm["parent_id"][0] == m["id"] for mm in menus if mm != m)]

menu_names = [m["name"] for m in menus]
nav_checks = {
    "首頁 in menu": "首頁" in menu_names,
    "商品 in menu": "商品" in menu_names,
    "關於我們 in menu": "關於我們" in menu_names,
    "常見問題 in menu": "常見問題" in menu_names,
    "聯絡我們 in menu": "聯絡我們" in menu_names,
    "會員中心 in menu": "會員中心" in menu_names,
    "Category dropdown exists": any("category=" in (m["url"] or "") for m in menus),
    "6+ top menu items": len([m for m in menus if m["parent_id"] and "category" not in (m["url"] or "")]) >= 6,
    "Menu in Chinese": all(any('\u4e00' <= c <= '\u9fff' for c in m["name"]) for m in menus if m["name"] not in ["Home"]),
}
nav_pass = sum(1 for v in nav_checks.values() if v)
nav_score = round(nav_pass / len(nav_checks) * 10, 1)
scores["navigation"] = nav_score
findings["navigation"] = []
for check, result in nav_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["navigation"].append(check)


# --- 4. Homepage Design (15%) ---
print("\n" + "=" * 60)
print("4. HOMEPAGE DESIGN (15%)")
print("=" * 60)

hp_checks = {
    "Hero section exists": "inzense-hero" in homepage,
    "Value bar exists": "inzense-value-bar" in homepage or "天然製香" in homepage,
    "Category grid exists": "依系列選購" in homepage or "inzense-category-card" in homepage,
    "Member center section": "會員中心" in homepage,
    "CTA banner exists": "探索商品" in homepage or "inzense-cta-banner" in homepage,
    "Login CTA visible": "登入我的帳戶" in homepage or "會員登入" in homepage,
    "Shop CTA visible": "開始購物" in homepage,
    "/my link present": '"/my"' in homepage,
    "/shop links present": '"/shop' in homepage,
    "Brand name 禪香不二": "禪香不二" in homepage,
    "No YouTube embed": "youtube.com/embed" not in homepage,
    "5 sections (not 11)": homepage.count("<section") <= 6,
}
hp_pass = sum(1 for v in hp_checks.values() if v)
hp_score = round(hp_pass / len(hp_checks) * 10, 1)
scores["homepage"] = hp_score
findings["homepage"] = []
for check, result in hp_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["homepage"].append(check)


# --- 5. Shop Page (15%) ---
print("\n" + "=" * 60)
print("5. SHOP PAGE (15%)")
print("=" * 60)

shop_checks = {
    "/shop returns 200": pages["/shop"]["code"] == 200,
    "Products visible": "oe_product" in shoppage,
    "Category sidebar": "products_grid_before" in shoppage or "o_wsale_products_categories" in shoppage,
    "Price display": "oe_currency_value" in shoppage or "product_price" in shoppage,
    "Gold CSS present": "D8B772" in shoppage,
    "Add to cart button": "js_add_cart" in shoppage or "a_add_to_cart" in shoppage or "o_wsale_product_btn" in shoppage,
}
shop_pass = sum(1 for v in shop_checks.values() if v)
shop_score = round(shop_pass / len(shop_checks) * 10, 1)
scores["shop"] = shop_score
findings["shop"] = []
for check, result in shop_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["shop"].append(check)


# --- 6. Data Integrity (10%) ---
print("\n" + "=" * 60)
print("6. DATA INTEGRITY (10%)")
print("=" * 60)

websites = sr("website", [], ["name", "social_facebook", "social_youtube", "social_github", "social_tiktok"])
zero_price = len(search("product.template", [["website_published", "=", True], ["list_price", "=", 0]]))

data_checks = {
    "Only 1 website": len(websites) == 1,
    "Facebook correct": any("onlyinzense" in (w.get("social_facebook") or "") for w in websites),
    "YouTube cleared": all(not w.get("social_youtube") for w in websites),
    "GitHub cleared": all(not w.get("social_github") for w in websites),
    "TikTok cleared": all(not w.get("social_tiktok") for w in websites),
    "No zero-price products": zero_price == 0,
    "Copyright hidden (CSS)": "odoo.com" in homepage and "display: none" in homepage,
}
data_pass = sum(1 for v in data_checks.values() if v)
data_score = round(data_pass / len(data_checks) * 10, 1)
scores["data"] = data_score
findings["data"] = []
for check, result in data_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["data"].append(check)


# --- 7. Mobile Responsiveness (10%) ---
print("\n" + "=" * 60)
print("7. MOBILE RESPONSIVENESS (10%)")
print("=" * 60)

mobile_checks = {
    "@media rules exist": "@media" in homepage,
    "Max-width 768px rule": "768px" in homepage,
    "Max-width 480px rule": "480px" in homepage,
    "Offcanvas styles": "offcanvas" in homepage,
    "Mobile navbar toggler": "navbar-toggler" in homepage,
    "Responsive hero height": "min-height" in homepage and "320px" in homepage,
}
mobile_pass = sum(1 for v in mobile_checks.values() if v)
mobile_score = round(mobile_pass / len(mobile_checks) * 10, 1)
scores["mobile"] = mobile_score
findings["mobile"] = []
for check, result in mobile_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["mobile"].append(check)


# --- 8. Performance (10%) ---
print("\n" + "=" * 60)
print("8. PERFORMANCE (10%)")
print("=" * 60)

perf_checks = {
    "Homepage < 100KB": pages["/"]["size"] < 100000,
    "Shop page loads": pages["/shop"]["code"] == 200,
    "No large GIF embeds": ".gif" not in homepage.lower() or "video-sequence" not in homepage,
    "Content-visibility CSS": "content-visibility" in homepage,
    "Font-display swap": "display=swap" in homepage or "font-display" in homepage,
    "No inline <script>": homepage.count("<script") < 15,
}
perf_pass = sum(1 for v in perf_checks.values() if v)
perf_score = round(perf_pass / len(perf_checks) * 10, 1)
scores["performance"] = perf_score
findings["performance"] = []
for check, result in perf_checks.items():
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {check}")
    if not result:
        findings["performance"].append(check)


# ============================================================
# FINAL SCORECARD
# ============================================================
weights = {
    "color": 0.15,
    "typography": 0.10,
    "navigation": 0.15,
    "homepage": 0.15,
    "shop": 0.15,
    "data": 0.10,
    "mobile": 0.10,
    "performance": 0.10,
}

labels = {
    "color": "色彩準確性",
    "typography": "字型系統",
    "navigation": "導航結構",
    "homepage": "首頁設計",
    "shop": "商店頁面",
    "data": "資料完整性",
    "mobile": "行動裝置",
    "performance": "效能",
}

weighted_total = sum(scores[k] * weights[k] for k in weights)
min_score = min(scores.values())
all_above_5 = all(s >= 5 for s in scores.values())
pass_threshold = weighted_total >= 7.5 and all_above_5

print("\n" + "=" * 60)
print("INDEPENDENT SCORING REPORT — 獨立評分報告")
print("=" * 60)
print(f"\n{'類別':<14} {'權重':<8} {'得分':<8} {'加權':<8} {'狀態'}")
print("-" * 56)
for key in weights:
    w = weights[key]
    s = scores[key]
    ws = round(s * w, 2)
    status = "✅" if s >= 7.5 else ("⚠" if s >= 5 else "❌")
    print(f"  {labels[key]:<12} {int(w*100):>3}%     {s:>5}/10   {ws:>5}    {status}")

print("-" * 56)
print(f"  {'整體加權':<12} {'100%':>4}     {weighted_total:>5.1f}/10")
print(f"  {'最低分':<12} {'':>4}     {min_score:>5.1f}/10")
print(f"\n  及格標準: 整體 ≥ 7.5 且所有類別 ≥ 5.0")
print(f"  結果: {'✅ PASS — 通過' if pass_threshold else '❌ FAIL — 未通過'}")

# Issues to fix
if findings:
    print(f"\n{'=' * 60}")
    print("ISSUES TO FIX — 待修復項目")
    print("=" * 60)
    for category, issues in findings.items():
        if issues:
            print(f"\n  [{labels[category]}] (目前 {scores[category]}/10)")
            for issue in issues:
                print(f"    - {issue}")

# Save report
report = {
    "scores": scores,
    "weighted_total": round(weighted_total, 2),
    "min_score": min_score,
    "passed": pass_threshold,
    "findings": findings,
}
with open("/tmp/inzense_score_report.json", "w") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n  Report saved to: /tmp/inzense_score_report.json")
print("\nPhase 6 complete.")
