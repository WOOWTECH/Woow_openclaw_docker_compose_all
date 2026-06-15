#!/usr/bin/env python3
"""
Inzense Odoo 18 — Create Internal Users
建立內部使用者，全部權限全開供測試使用。

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/61_create_internal_users.py
"""
import xmlrpc.client

# --- Connection ---
URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


def execute(model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASSWORD, model, method, *args, **kwargs)


def search(model, domain, **kwargs):
    return execute(model, "search", [domain], **kwargs)


def search_read(model, domain, fields=None, **kwargs):
    kw = {}
    if fields:
        kw["fields"] = fields
    kw.update(kwargs)
    return execute(model, "search_read", [domain], kw)


def create(model, vals):
    return execute(model, "create", [vals])


def write(model, ids, vals):
    return execute(model, "write", [ids, vals])


# ============================================================
# Phase 1: Get admin groups (full access template)
# ============================================================
print("\n=== Phase 1: 取得 admin 完整權限群組 ===")

admin_user = search_read("res.users", [["id", "=", uid]], ["groups_id"])
admin_groups = admin_user[0]["groups_id"]
print(f"  Admin 擁有 {len(admin_groups)} 個權限群組")

# ============================================================
# Phase 2: Define users
# ============================================================
# 帳號密碼一樣 (login = password)，測試用
# 注意：邱志銘 & 杜思蒨 共用 service@inzense.com.tw，
#       login 必須唯一，故分別建立不同 login

USERS = [
    {
        "name": "邱豫彥",
        "login": "fireshadow131@gmail.com",
        "email": "fireshadow131@gmail.com",
        "role": "老闆",
    },
    {
        "name": "李芸珮",
        "login": "petty@sparkledesign.com.tw",
        "email": "Petty@sparkledesign.com.tw",
        "role": "老闆娘",
    },
    {
        "name": "邱志銘",
        "login": "chiming@inzense.com.tw",
        "email": "service@inzense.com.tw",
        "role": "中和廠主管",
    },
    {
        "name": "杜思蒨",
        "login": "sichian@inzense.com.tw",
        "email": "service@inzense.com.tw",
        "role": "中和廠員工",
    },
    {
        "name": "巫詩婷",
        "login": "pr@inzense.com.tw",
        "email": "pr@inzense.com.tw",
        "role": "誠品板橋店員工",
    },
]

# ============================================================
# Phase 3: Create users with full admin groups
# ============================================================
print("\n=== Phase 2: 建立內部使用者 ===")

created = []
skipped = []

for u in USERS:
    existing = search("res.users", [["login", "=", u["login"]]])
    if existing:
        # User exists — update groups and reactivate
        write("res.users", existing, {
            "active": True,
            "groups_id": [(6, 0, admin_groups)],
            "lang": "zh_TW",
            "tz": "Asia/Taipei",
        })
        skipped.append(u)
        print(f"  [已存在] {u['name']} ({u['login']}) — 已更新權限")
        continue

    user_id = create("res.users", {
        "name": u["name"],
        "login": u["login"],
        "password": u["login"],  # 帳號密碼一樣
        "email": u["email"],
        "lang": "zh_TW",
        "tz": "Asia/Taipei",
        "groups_id": [(6, 0, admin_groups)],
    })
    created.append(u)
    print(f"  [建立成功] {u['name']} ({u['login']}) → uid={user_id} | 密碼={u['login']}")

# ============================================================
# Phase 4: Verify all users
# ============================================================
print("\n=== Phase 3: 驗證所有內部使用者 ===")

all_logins = [u["login"] for u in USERS]
active_users = search_read(
    "res.users",
    [["login", "in", all_logins], ["active", "=", True]],
    ["name", "login", "email", "lang", "tz", "groups_id"],
)

print(f"\n{'姓名':<10} {'帳號 (=密碼)':<35} {'Email':<35} {'角色':<15} {'權限數'}")
print("-" * 120)
for au in active_users:
    role = next((u["role"] for u in USERS if u["login"] == au["login"]), "")
    print(f"  {au['name']:<8} {au['login']:<35} {au['email']:<35} {role:<15} {len(au['groups_id'])} groups")

# ============================================================
# Summary
# ============================================================
print(f"\n=== 完成 ===")
print(f"  新建: {len(created)} 位")
print(f"  已存在(更新權限): {len(skipped)} 位")
print(f"\n  ⚠ 注意: 帳號=密碼，僅供測試！上線前請更換所有密碼。")
print(f"  ⚠ 注意: 邱志銘 login=chiming@inzense.com.tw / 杜思蒨 login=sichian@inzense.com.tw")
print(f"         兩人 email 都是 service@inzense.com.tw，但 login 必須各自獨立。")
