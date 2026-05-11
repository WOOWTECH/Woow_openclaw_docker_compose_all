# Fresh Odoo Deploy + Taiwan Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy reservation module with all dependencies on a fresh Odoo 18 database and configure complete Taiwan localization.

**Architecture:** Sequential deployment — pull latest module code, install zh_TW language, install all modules in one batch, configure Taiwan settings via ORM, set up website menus/footer, create appointment type, verify with Playwright.

**Tech Stack:** Odoo 18, K8s (kubectl exec), XML-RPC, PostgreSQL, Playwright

---

## Pre-requisites

- Pod: `kubectl get pod -n markstudio-odoo -l app=odoo -o jsonpath='{.items[0].metadata.name}'`
- DB password: `kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d` → `I5vMv0uO8elAWlHwME/8fRFlM4H89XyK`
- Addons path: `/mnt/extra-addons/` (contains Odoo_reservation_module, woow_odoo_livechat_line, Woow_odoo_n8n_livechat, markstudio_website)
- DB: `markstudio` — fresh, only base installed

---

### Task 1: Pull latest reservation_module from GitHub

The init container cloned repos on first boot but the closing day controller fix (commit `8da4cf7`) may not be present. Git is not in the Odoo container, so use a temp alpine/git pod.

- [ ] **Step 1: Pull latest code via temp pod**

```bash
kubectl run git-pull --rm -i --restart=Never -n markstudio-odoo \
  --image=alpine/git:latest \
  --overrides='{
    "spec": {
      "containers": [{
        "name": "git-pull",
        "image": "alpine/git:latest",
        "command": ["sh", "-c", "cd /mnt/extra-addons/Odoo_reservation_module && git pull --ff-only && git log --oneline -3"],
        "volumeMounts": [{"name": "addons", "mountPath": "/mnt/extra-addons"}]
      }],
      "volumes": [{"name": "addons", "persistentVolumeClaim": {"claimName": "odoo-addons-pvc"}}]
    }
  }'
```

Expected: shows latest commits including `8da4cf7 Fix closing days`.

- [ ] **Step 2: Verify closing day fix is present**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- \
  grep -c "Check closing days" /mnt/extra-addons/Odoo_reservation_module/reservation_module/controllers/main.py
```

Expected: `1` (the closing day check exists in get_slots).

---

### Task 2: Copy markstudio_website to pod

The local module may have newer changes than what's on the PVC.

- [ ] **Step 1: Package and copy module**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project"
tar czf /tmp/markstudio_website.tar.gz markstudio_website/
ODOO_POD=$(kubectl get pod -n markstudio-odoo -l app=odoo -o jsonpath='{.items[0].metadata.name}')
kubectl cp /tmp/markstudio_website.tar.gz "markstudio-odoo/${ODOO_POD}:/tmp/markstudio_website.tar.gz" -c odoo
kubectl exec -n markstudio-odoo "${ODOO_POD}" -c odoo -- tar xzf /tmp/markstudio_website.tar.gz -C /mnt/extra-addons/
rm -f /tmp/markstudio_website.tar.gz
```

- [ ] **Step 2: Verify files**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- ls /mnt/extra-addons/markstudio_website/views/
```

Expected: `homepage_templates.xml  news_templates.xml`

---

### Task 3: Install zh_TW language

- [ ] **Step 1: Load Traditional Chinese**

```bash
PGPASS=$(kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- odoo -d markstudio \
  --load-language=zh_TW \
  --stop-after-init --no-http \
  --db_host=odoo-db-svc --db_port=5432 --db_user=odoo --db_password="$PGPASS"
```

Expected last line: `Stopping gracefully`

---

### Task 4: Install all modules in one batch

Single `-i` command installs all modules and their dependencies. Order doesn't matter — Odoo resolves the dependency graph.

**DO NOT install:** point_of_sale, hr_expense, hr, stock, account (user explicitly removed these before the DB reset).

- [ ] **Step 1: Install modules**

```bash
PGPASS=$(kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- odoo -d markstudio \
  -i website,im_livechat,reservation_module,woow_odoo_livechat_line,im_livechat_n8n,markstudio_website \
  --stop-after-init --without-demo=all --no-http \
  --db_host=odoo-db-svc --db_port=5432 --db_user=odoo --db_password="$PGPASS"
```

Expected: `X modules loaded in Y.YYs` then `Stopping gracefully`. If `_post_init_hook` crashes on `booking_type`, the GitHub fix (commit `8da4cf7`) wasn't pulled — go back to Task 1.

- [ ] **Step 2: Restart Odoo to load all modules**

```bash
kubectl rollout restart deployment/odoo -n markstudio-odoo
kubectl wait --for=condition=Ready pod -l app=odoo -n markstudio-odoo --timeout=120s
```

- [ ] **Step 3: Verify health**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- \
  curl -s http://localhost:8069/web/health
```

Expected: `{"status": "pass"}`

---

### Task 5: Taiwan localization + admin setup (all via single ORM script)

One Python script does everything: rename admin, set language, timezone, company, currency, website language.

- [ ] **Step 1: Run localization script**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- python3 -c "
import xmlrpc.client

url = 'http://localhost:8069'
db = 'markstudio'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Rename admin to 馬克
models.execute_kw(db, uid, 'admin', 'res.users', 'write', [[uid], {'name': '馬克', 'lang': 'zh_TW', 'tz': 'Asia/Taipei'}])
print('[1/5] Admin: 馬克 / zh_TW / Asia/Taipei')

# 2. Company
tw = models.execute_kw(db, uid, 'admin', 'res.country', 'search', [[['code', '=', 'TW']]])
models.execute_kw(db, uid, 'admin', 'res.company', 'write', [[1], {'name': '馬克健身', 'country_id': tw[0]}])
print(f'[2/5] Company: 馬克健身, Taiwan (id={tw[0]})')

# 3. Currency TWD
twd = models.execute_kw(db, uid, 'admin', 'res.currency', 'search_read',
    [[['name', '=', 'TWD'], ['active', 'in', [True, False]]]],
    {'fields': ['id', 'active'], 'context': {'active_test': False}})
if twd:
    if not twd[0]['active']:
        models.execute_kw(db, uid, 'admin', 'res.currency', 'write', [[twd[0]['id']], {'active': True}])
    models.execute_kw(db, uid, 'admin', 'res.company', 'write', [[1], {'currency_id': twd[0]['id']}])
    print(f'[3/5] Currency: TWD (id={twd[0][\"id\"]})')
else:
    print('[3/5] WARN: TWD not found')

# 4. Website default lang
lang = models.execute_kw(db, uid, 'admin', 'res.lang', 'search', [[['code', '=', 'zh_TW']]])
if lang:
    models.execute_kw(db, uid, 'admin', 'website', 'write', [[1], {'default_lang_id': lang[0]}])
    print(f'[4/5] Website lang: zh_TW (id={lang[0]})')

# 5. Verify
co = models.execute_kw(db, uid, 'admin', 'res.company', 'read', [1], {'fields': ['name', 'country_id', 'currency_id']})
print(f'[5/5] Verified: {co[0][\"name\"]} / {co[0][\"country_id\"]} / {co[0][\"currency_id\"]}')
"
```

Expected: 5 lines of confirmation ending with `馬克健身 / [..., 'Taiwan'] / [..., 'TWD']`

---

### Task 6: Website menus + header cleanup (single ORM script)

- [ ] **Step 1: Configure menus and remove CTA**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- python3 -c "
import xmlrpc.client

url = 'http://localhost:8069'
db = 'markstudio'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Delete default menus (except root)
old = models.execute_kw(db, uid, 'admin', 'website.menu', 'search',
    [[['website_id', '=', 1], ['url', '!=', '/default-main-menu']]])
if old:
    models.execute_kw(db, uid, 'admin', 'website.menu', 'unlink', [old])
    print(f'Deleted {len(old)} old menus')

# 2. Get root menu
root = models.execute_kw(db, uid, 'admin', 'website.menu', 'search',
    [[['website_id', '=', 1], ['url', '=', '/default-main-menu']]])
root_id = root[0] if root else 4

# 3. Create new menus
for name, url, seq in [('服務介紹', '/#services', 10), ('最新消息', '/#news', 20), ('立即預約', '/appointment', 30)]:
    mid = models.execute_kw(db, uid, 'admin', 'website.menu', 'create', [{
        'name': name, 'url': url, 'parent_id': root_id, 'sequence': seq, 'website_id': 1}])
    print(f'Created: {name} -> {url} (id={mid})')

# 4. Deactivate Contact Us CTA button
cta_ids = models.execute_kw(db, uid, 'admin', 'ir.ui.view', 'search',
    [[['key', '=', 'website.header_call_to_action']]])
if cta_ids:
    models.execute_kw(db, uid, 'admin', 'ir.ui.view', 'write', [cta_ids, {'active': False}])
    print(f'Deactivated CTA button (id={cta_ids[0]})')

# 5. Deactivate phone text element
txt_ids = models.execute_kw(db, uid, 'admin', 'ir.ui.view', 'search',
    [[['key', '=', 'website.header_text_element']]])
if txt_ids:
    models.execute_kw(db, uid, 'admin', 'ir.ui.view', 'write', [txt_ids, {'active': False}])
    print(f'Deactivated phone text (id={txt_ids[0]})')
"
```

---

### Task 7: Footer customization

Replace default Odoo English footer with Chinese branded content via direct DB update on `website.footer_custom`.

- [ ] **Step 1: Update footer via Python/psycopg2**

```bash
PGPASS=$(kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- python3 -c "
import psycopg2, json

conn = psycopg2.connect(host='odoo-db-svc', port=5432, user='odoo', password='$PGPASS', dbname='markstudio')
cur = conn.cursor()

footer_html = '''<data inherit_id=\"website.layout\" name=\"Default\" active=\"True\">
    <xpath expr=\"//div[@id='footer']\" position=\"replace\">
        <div id=\"footer\" class=\"oe_structure oe_structure_solo\" t-ignore=\"true\" t-if=\"not no_footer\">
            <section style=\"background-color: #0d1117; padding: 48px 0 24px;\">
                <div class=\"container\">
                    <div class=\"row\">
                        <div class=\"col-lg-4 col-md-6 mb-4\">
                            <h5 style=\"color:#fff; font-weight:700; margin-bottom:16px;\">快速連結</h5>
                            <ul style=\"list-style:none; padding:0;\">
                                <li style=\"margin-bottom:8px;\"><a href=\"/\" style=\"color:#999; text-decoration:none;\">主頁介紹</a></li>
                                <li style=\"margin-bottom:8px;\"><a href=\"/appointment\" style=\"color:#999; text-decoration:none;\">預約服務</a></li>
                                <li style=\"margin-bottom:8px;\"><a href=\"/#news\" style=\"color:#999; text-decoration:none;\">最新消息</a></li>
                            </ul>
                        </div>
                        <div class=\"col-lg-4 col-md-6 mb-4\">
                            <h5 style=\"color:#fff; font-weight:700; margin-bottom:16px;\">關於馬克健身</h5>
                            <p style=\"color:#999; font-size:14px; line-height:1.8;\">馬克健身致力於提供專業的按摩與伸展服務，透過獨創的核心平衡伸展術，幫助您從根源解決身體的煩惱，享受健康舒適的生活。</p>
                        </div>
                        <div class=\"col-lg-4 col-md-6 mb-4\">
                            <h5 style=\"color:#fff; font-weight:700; margin-bottom:16px;\">聯繫我們</h5>
                            <p style=\"color:#999; font-size:14px; margin-bottom:6px;\"><i class=\"fa fa-phone\" style=\"margin-right:8px;\"/> <a href=\"tel:0900000000\" style=\"color:#999; text-decoration:none;\">0900-000-000</a></p>
                            <p style=\"color:#999; font-size:14px; margin-bottom:12px;\"><i class=\"fa fa-envelope\" style=\"margin-right:8px;\"/> <a href=\"mailto:info@markstudio.com.tw\" style=\"color:#999; text-decoration:none;\">info@markstudio.com.tw</a></p>
                            <a href=\"#\" style=\"color:#999; margin-right:12px;\"><i class=\"fa fa-facebook fa-lg\"/></a>
                            <a href=\"#\" style=\"color:#999; margin-right:12px;\"><i class=\"fa fa-instagram fa-lg\"/></a>
                            <a href=\"#\" style=\"color:#999;\"><i class=\"fa fa-youtube-play fa-lg\"/></a>
                        </div>
                    </div>
                    <div style=\"border-top:1px solid #333; padding-top:16px; margin-top:16px; display:flex; justify-content:space-between; flex-wrap:wrap;\">
                        <span style=\"color:#666; font-size:12px;\">&#169; 2026 馬克健身 Mark Studio &#8212; Powered by WoowTech</span>
                        <span style=\"font-size:12px;\"><a href=\"#\" style=\"color:#666; text-decoration:none; margin-right:16px;\">隱私政策</a><a href=\"#\" style=\"color:#666; text-decoration:none;\">服務條款</a></span>
                    </div>
                </div>
            </section>
        </div>
    </xpath>
</data>'''

arch = json.dumps({'en_US': footer_html})
cur.execute('UPDATE ir_ui_view SET arch_db = %s WHERE key = %s', (arch, 'website.footer_custom'))
print(f'Footer updated: {cur.rowcount} row(s)')
conn.commit()
conn.close()
"
```

Expected: `Footer updated: 1 row(s)`

---

### Task 8: Create appointment type + weekly availability

- [ ] **Step 1: Create appointment and availability via ORM**

```bash
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- python3 -c "
import xmlrpc.client

url = 'http://localhost:8069'
db = 'markstudio'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Create appointment type
apt_id = models.execute_kw(db, uid, 'admin', 'appointment.type', 'create', [{
    'name': '專業按摩伸展',
    'slot_duration': 1.0,
    'timezone': 'Asia/Taipei',
    'is_published': True,
    'assign_staff': True,
    'allow_customer_choose_staff': False,
    'staff_user_ids': [[6, 0, [uid]]],
}])
print(f'Appointment type created: id={apt_id}')

# 2. Create weekly availability Mon-Sun 9:00-21:00
days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
for day in range(7):
    models.execute_kw(db, uid, 'admin', 'appointment.availability', 'create', [{
        'appointment_type_id': apt_id,
        'dayofweek': str(day),
        'hour_from': 9.0,
        'hour_to': 21.0,
        'user_id': uid,
    }])
    print(f'  {days[day]} 09:00-21:00')

print('Done: 7 days of availability created')
"
```

Expected: appointment type id=1 and 7 availability records.

---

### Task 9: Restart Odoo and clear caches

- [ ] **Step 1: Clear asset cache and restart**

```bash
kubectl exec -n markstudio-odoo deploy/odoo-db -- psql -U odoo -d markstudio \
  -c "DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR url LIKE '%/web/assets%';"
kubectl rollout restart deployment/odoo -n markstudio-odoo
kubectl wait --for=condition=Ready pod -l app=odoo -n markstudio-odoo --timeout=120s
```

---

### Task 10: Verify with Playwright

- [ ] **Step 1: Start port-forward and open browser**

```bash
kill $(lsof -ti :18069) 2>/dev/null
kubectl port-forward -n markstudio-odoo svc/odoo-web-svc 18069:8069 &
sleep 3
playwright-cli open http://localhost:18069/
```

- [ ] **Step 2: Verify homepage loads with all sections**

```bash
playwright-cli resize 1280 720
playwright-cli screenshot --filename=verify-home.png
```

Check: hero image, nav shows 服務介紹/最新消息/立即預約(gold), footer in Chinese.

- [ ] **Step 3: Verify all 9 section IDs present**

```bash
playwright-cli eval "['hero','stats','services','technique','experience','booking','news','faq','contact'].every(id => !!document.getElementById(id))"
```

Expected: `true`

- [ ] **Step 4: Verify smooth scroll**

```bash
playwright-cli click "getByRole('menuitem', { name: '服務介紹' })"
# wait 2s
playwright-cli eval "Math.round(document.documentElement.scrollTop)"
```

Expected: value > 500 (scrolled down).

- [ ] **Step 5: Verify appointment page**

```bash
playwright-cli goto http://localhost:18069/appointment/1
playwright-cli screenshot --filename=verify-apt.png
```

Check: shows "專業按摩伸展" with "Select Date & Time" button.

- [ ] **Step 6: Login and verify zh_TW backend**

```bash
playwright-cli goto http://localhost:18069/web/login
playwright-cli fill "getByRole('textbox', { name: 'Email' })" "admin"
playwright-cli fill "getByRole('textbox', { name: 'Password' })" "admin" --submit
playwright-cli screenshot --filename=verify-backend.png
```

Check: interface in Traditional Chinese, company name "馬克健身" in top-right.

- [ ] **Step 7: Verify removed modules not in sidebar**

```bash
playwright-cli click "getByTitle('首頁功能表')"
playwright-cli snapshot --depth=3
```

Check: NO POS營業點, 開支, 發票, 庫存, 員工. Only: 討論, 日曆, 預約管理, 網站, 線上客服, 應用程式, 設定.

- [ ] **Step 8: Clean up**

```bash
playwright-cli close
kill $(lsof -ti :18069) 2>/dev/null
rm -f verify-*.png
```
