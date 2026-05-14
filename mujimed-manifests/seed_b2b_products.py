#!/usr/bin/env python3
"""
Mujimed B2B Product Seeder
Seeds medical aesthetics wholesale products and categories for B2B eCommerce.

Usage:
    python3 seed_b2b_products.py [--url URL] [--db DB] [--user USER] [--password PASSWORD]

Requires: Odoo 18 with website_sale installed.
Idempotent: safe to run multiple times.
"""
import xmlrpc.client
import sys
import argparse

# ─── Configuration ──────────────────────────────────────────────
ODOO_URL = "https://mujimed-odoo.woowtech.io"
ODOO_DB = "mujimed"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


# ─── Connection ─────────────────────────────────────────────────
def connect(url, db, user, password):
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("[ERROR] Authentication failed.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    print(f"[ok] Connected as uid={uid}")
    return uid, models


def x(models, db, uid, pw, model, method, *args, **kwargs):
    return models.execute_kw(db, uid, pw, model, method, *args, **kwargs)


def find_or_create(models, db, uid, pw, model, domain, vals):
    ids = x(models, db, uid, pw, model, 'search', [domain], {'limit': 1})
    if ids:
        return ids[0]
    return x(models, db, uid, pw, model, 'create', [vals])


# ─── Category Data ──────────────────────────────────────────────
CATEGORIES = [
    "注射耗材",
    "雷射耗材",
    "體雕設備耗材",
    "保養品",
    "儀器配件",
    "診所用品",
]

# ─── Product Data ───────────────────────────────────────────────
# (name, sku, price_twd, category_name, description)
PRODUCTS = [
    # 注射耗材
    ("玻尿酸填充劑 1ml", "INJ-001", 3500, "注射耗材",
     "高品質交聯玻尿酸，適用於臉部填充，持久度 12-18 個月"),
    ("玻尿酸填充劑 2ml", "INJ-002", 6000, "注射耗材",
     "高品質交聯玻尿酸，大容量裝，適用於大範圍填充"),
    ("肉毒桿菌素 50U", "INJ-003", 4800, "注射耗材",
     "A 型肉毒桿菌素 50 單位裝，適用於除皺及瘦臉"),
    ("肉毒桿菌素 100U", "INJ-004", 8500, "注射耗材",
     "A 型肉毒桿菌素 100 單位裝，經濟包裝"),
    ("膠原蛋白增生劑 (Sculptra)", "INJ-005", 12000, "注射耗材",
     "聚左乳酸 PLLA 注射劑，刺激自體膠原蛋白增生"),

    # 雷射耗材
    ("皮秒雷射探頭 (標準)", "LAS-001", 15000, "雷射耗材",
     "皮秒雷射標準探頭，適用於除斑、嫩膚療程"),
    ("飛梭雷射探頭", "LAS-002", 12000, "雷射耗材",
     "分段式飛梭雷射探頭，適用於痘疤及毛孔治療"),
    ("淨膚雷射凝膠 500ml", "LAS-003", 800, "雷射耗材",
     "雷射術前導光凝膠，提升雷射能量傳導效率"),
    ("脈衝光導光片", "LAS-004", 8000, "雷射耗材",
     "IPL 脈衝光專用導光片，適用於多波段光療"),
    ("雷射護目鏡 (患者用)", "LAS-005", 350, "雷射耗材",
     "雷射術中患者專用防護護目鏡，可重複使用"),

    # 體雕設備耗材
    ("電波拉皮探頭 600發", "BOD-001", 25000, "體雕設備耗材",
     "電波拉皮 600 發探頭，適用於臉部及頸部緊緻療程"),
    ("電波拉皮探頭 900發", "BOD-002", 35000, "體雕設備耗材",
     "電波拉皮 900 發探頭，適用於全臉加身體療程"),
    ("音波拉提探頭 1.5mm", "BOD-003", 18000, "體雕設備耗材",
     "聚焦超音波探頭 1.5mm 深度，作用於真皮層"),
    ("音波拉提探頭 3.0mm", "BOD-004", 18000, "體雕設備耗材",
     "聚焦超音波探頭 3.0mm 深度，作用於皮下組織"),
    ("冷凍溶脂貼片 (10片裝)", "BOD-005", 5000, "體雕設備耗材",
     "冷凍減脂專用凝膠貼片，保護皮膚避免凍傷"),

    # 保養品
    ("術後修護面膜 (10片裝)", "SKN-001", 1200, "保養品",
     "醫美術後專用修護面膜，含積雪草及玻尿酸成分"),
    ("玻尿酸保濕精華液 30ml", "SKN-002", 1800, "保養品",
     "高濃度玻尿酸精華，深層保濕修護，術後日常保養"),
    ("維他命C亮白精華 30ml", "SKN-003", 2200, "保養品",
     "左旋維他命C 20% 精華液，抗氧化亮白淡斑"),
    ("術後防曬霜 SPF50 50ml", "SKN-004", 950, "保養品",
     "物理性防曬，SPF50 PA++++，術後敏感肌適用"),
    ("杏仁酸煥膚液 15% 100ml", "SKN-005", 1500, "保養品",
     "專業級杏仁酸煥膚液，溫和代謝角質，改善膚質"),

    # 儀器配件
    ("超音波導入儀探頭", "ACC-001", 6500, "儀器配件",
     "超音波導入儀替換探頭，促進精華液深層吸收"),
    ("LED 光療面罩更換燈板", "ACC-002", 4200, "儀器配件",
     "紅光 + 近紅外光 LED 燈板，促進膠原蛋白生成"),
    ("微針滾輪 0.5mm (10入)", "ACC-003", 2800, "儀器配件",
     "醫療級微針滾輪 0.5mm，適用於精華液導入"),
    ("微針滾輪 1.0mm (10入)", "ACC-004", 3200, "儀器配件",
     "醫療級微針滾輪 1.0mm，適用於痘疤及毛孔治療"),
    ("水光槍針頭 (50入)", "ACC-005", 3500, "儀器配件",
     "水光注射專用拋棄式針頭，9 針設計均勻導入"),

    # 診所用品
    ("無粉乳膠手套 (100入)", "CLI-001", 280, "診所用品",
     "醫療級無粉乳膠手套 M 號，通過 SGS 認證"),
    ("醫療用紗布 4x4 (200入)", "CLI-002", 350, "診所用品",
     "滅菌醫療紗布 4x4 吋，適用於術後傷口護理"),
    ("75% 酒精消毒液 500ml", "CLI-003", 180, "診所用品",
     "醫療級 75% 乙醇消毒液，術前皮膚消毒"),
    ("拋棄式床單 (50入)", "CLI-004", 600, "診所用品",
     "不織布拋棄式治療床單，衛生便利"),
    ("生理食鹽水 500ml (24入)", "CLI-005", 720, "診所用品",
     "0.9% 生理食鹽水，術中沖洗及術後清潔"),
]


def seed_categories(models, db, uid, pw):
    """Create internal and eCommerce categories."""
    print("\n── Seeding categories ──")
    internal_map = {}
    public_map = {}

    for cat_name in CATEGORIES:
        # Internal category (product.category)
        cat_id = find_or_create(
            models, db, uid, pw, 'product.category',
            [('name', '=', cat_name)],
            {'name': cat_name}
        )
        internal_map[cat_name] = cat_id
        print(f"  [ok] Internal: {cat_name} (id={cat_id})")

        # eCommerce category (product.public.category)
        pub_id = find_or_create(
            models, db, uid, pw, 'product.public.category',
            [('name', '=', cat_name)],
            {'name': cat_name}
        )
        public_map[cat_name] = pub_id
        print(f"  [ok] eCommerce: {cat_name} (id={pub_id})")

    return internal_map, public_map


def seed_products(models, db, uid, pw, internal_map, public_map):
    """Create B2B wholesale products."""
    print("\n── Seeding products ──")

    for name, sku, price, cat_name, desc in PRODUCTS:
        cat_id = internal_map.get(cat_name, 1)
        pub_cat_id = public_map.get(cat_name)

        vals = {
            'name': name,
            'default_code': sku,
            'type': 'consu',
            'list_price': price,
            'sale_ok': True,
            'purchase_ok': False,
            'website_published': True,
            'categ_id': cat_id,
            'description_sale': f'<p>{desc}</p>',
        }
        if pub_cat_id:
            vals['public_categ_ids'] = [(6, 0, [pub_cat_id])]

        product_id = find_or_create(
            models, db, uid, pw, 'product.template',
            [('default_code', '=', sku)],
            vals
        )
        print(f"  [ok] {sku} {name} — TWD {price:,} (id={product_id})")


def main():
    parser = argparse.ArgumentParser(description="Seed Mujimed B2B products")
    parser.add_argument('--url', default=ODOO_URL)
    parser.add_argument('--db', default=ODOO_DB)
    parser.add_argument('--user', default=ADMIN_USER)
    parser.add_argument('--password', default=ADMIN_PASS)
    args = parser.parse_args()

    uid, models = connect(args.url, args.db, args.user, args.password)
    db, pw = args.db, args.password

    internal_map, public_map = seed_categories(models, db, uid, pw)
    seed_products(models, db, uid, pw, internal_map, public_map)

    print(f"\n══════════════════════════════════════")
    print(f" Seeded: {len(CATEGORIES)} categories (internal + eCommerce)")
    print(f" Seeded: {len(PRODUCTS)} products")
    print(f"══════════════════════════════════════")


if __name__ == '__main__':
    main()
