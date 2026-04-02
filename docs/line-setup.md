# LINE x OpenClaw Setup Guide / LINE 整合指南

## LINE Developers Console 設定

1. **建立 Messaging API Channel**
   - 到 https://developers.line.biz/console/
   - 建立 Provider → 建立 Messaging API Channel

2. **取得 credentials**
   - **Channel Access Token**: 點 "Issue" 取得 long-lived token
   - **Channel Secret**: 在 Basic settings 頁面複製

3. **設定 Webhook**
   - Webhook URL: `https://your-domain/line/webhook`
   - **Use webhook**: 開啟
   - 點 **Verify** 確認回傳 200

4. **LINE Official Account Manager 回應設定**（最關鍵！）
   - 到 https://manager.line.biz/
   - **「聊天」: 關閉** ← chatMode 必須是 "bot"，否則 LINE 不發送 webhook
   - **Webhook**: 開啟
   - **自動回應訊息**: 關閉

## 驗證 chatMode

```bash
curl -s https://api.line.me/v2/bot/info \
  -H "Authorization: Bearer YOUR_TOKEN"
# 必須顯示 "chatMode":"bot"
# 如果是 "chat"，LINE 不會發送 webhook event
```

## OpenClaw GUI 設定 (Channels → LINE)

| 欄位 | 值 |
|------|-----|
| Channel Access Token | LINE long-lived token |
| Channel Secret | LINE channel secret |
| Dm Policy | `open` |
| Group Policy | `open` |
| Enabled | 開啟 |
| Allow From | `*` |
| Webhook URL | `https://your-domain/line/webhook` |

## K8s Secret 設定

```bash
kubectl -n openclaw-tenant-1 patch secret openclaw-secrets --type='merge' \
  -p '{"stringData":{"LINE_CHANNEL_TOKEN":"your-token","LINE_CHANNEL_SECRET":"your-secret"}}'
```

## 常見問題

| 問題 | 原因 | 解決 |
|------|------|------|
| LINE 不發送 webhook | chatMode="chat" | 關閉 LINE OA Manager 的「聊天」功能 |
| 訊息被靜默丟棄 | allowFrom 未設定 | 執行 `openclaw doctor --fix` |
| Pod 重啟後 LINE 斷線 | 啟動腳本未注入 token | 確認 env var 在 K8s Secret 中 |
| Webhook verify 成功但訊息不到 | Tunnel 502 ghost 連線 | 清除 tunnel connections 並重啟 cloudflared |
