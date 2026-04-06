#!/usr/bin/env python3
"""Full test of the Minimax AI integration."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Config check
print("=== AI Config ===")
configs = models.execute_kw(db, uid, password, "ai.config", "search_read", [[]],
    {"fields": ["id", "name", "type", "api_key", "model", "base_url", "temperature", "max_tokens"]})
for c in configs:
    print(f"  ID={c['id']}: {c['name']} type={c['type']} model={c['model']}")
    print(f"    api_key: {'***' + c['api_key'][-8:] if c['api_key'] else 'NOT SET'}")
    print(f"    base_url: {c['base_url'] or 'default'}")

# 2. Assistants
print("\n=== AI Assistants ===")
assistants = models.execute_kw(db, uid, password, "ai.assistant", "search_read", [[]],
    {"fields": ["id", "name"]})
for a in assistants:
    full = models.execute_kw(db, uid, password, "ai.assistant", "read", [[a["id"]]])
    d = full[0]
    print(f"  ID={d['id']}: {d['name']}")
    for k in ["config_id", "system_prompt", "active"]:
        if k in d:
            val = str(d[k])[:80]
            print(f"    {k}: {val}")

# 3. Direct API test via openai library
print("\n=== Direct Minimax API Test ===")
minimax_key = None
for c in configs:
    if c["type"] == "minimax" and c["api_key"]:
        minimax_key = c["api_key"]
        break

if minimax_key:
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=minimax_key,
            base_url="https://api.minimaxi.chat/v1",
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[
                {"role": "system", "content": "你是禪香不二的AI助手，請用繁體中文簡短回覆。"},
                {"role": "user", "content": "你好，請介紹一下禪香不二的神明系列線香"},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        print(f"  Model: {response.model}")
        print(f"  Usage: {response.usage}")
        print(f"  Reply: {reply}")
        print("\n  >>> Minimax API test PASSED! <<<")
    except Exception as e:
        print(f"  API Error: {e}")
else:
    print("  No Minimax API key found!")

# 4. Module status
print("\n=== Module Status ===")
for mod in ["ai_base_gt", "ai_minimax_connector_gt", "ai_mail_gt"]:
    m = models.execute_kw(db, uid, password, "ir.module.module", "search_read", [
        [["name", "=", mod]]
    ], {"fields": ["state", "shortdesc"]})
    if m:
        print(f"  [{m[0]['state']}] {mod}: {m[0]['shortdesc']}")

# 5. Access URLs
print("\n=== Access Points ===")
print(f"  AI Config: https://inzense-odoo.woowtech.io/web#model=ai.config&view_type=list")
print(f"  AI Assistants: https://inzense-odoo.woowtech.io/web#model=ai.assistant&view_type=list")
print(f"  Discuss (AI chat): https://inzense-odoo.woowtech.io/web#action=mail.action_discuss")
