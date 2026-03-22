# Troubleshooting / 故障排除

## Cloudflare Tunnel 502 Bad Gateway

**Symptom / 症狀:** External access returns 502, but pods are Running.

**Cause / 原因:** Ghost tunnel connections from force-deleted cloudflared pods.

**Fix / 修復:**
```bash
# Check connection count (should be 4 connections, 1 client)
CF_API_TOKEN="..." CF_ACCOUNT_ID="..." CF_TUNNEL_ID="..."
curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN" | python3 -c "
import sys,json; d=json.load(sys.stdin)['result']
clients=set(c['client_id'] for c in d.get('connections',[]));
print(f'Conns: {len(d.get(\"connections\",[]))}, Clients: {len(clients)}')"

# Clean ghost connections
curl -X DELETE "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$CF_TUNNEL_ID/connections" \
  -H "Authorization: Bearer $CF_API_TOKEN"

# Restart cloudflared
kubectl -n openclaw-tenant-1 rollout restart deployment cloudflared

# Nuclear option: create new tunnel
# See init-cloudflare.py
```

**Prevention / 預防:** `04-cloudflared.yaml` uses `strategy: Recreate` + `preStop` hook + `terminationGracePeriodSeconds: 30`.

---

## DB Pod Stuck in Pending

**Symptom:** DB pod shows Pending, FailedScheduling.

**Cause:** PersistentVolume node affinity mismatch (PV on node A, pod scheduled to node B).

**Fix:**
```bash
kubectl -n openclaw-tenant-1 delete pvc openclaw-db-pvc
kubectl -n openclaw-tenant-1 apply -f k8s-manifests/06-openclaw-core.yaml
kubectl -n openclaw-tenant-1 scale deployment openclaw-db --replicas=1
```

---

## kubectl apply Scales Down Services

**Symptom:** After `kubectl apply`, gateway and DB pods disappear.

**Cause:** Manifest had `replicas: 0` (setup wizard design).

**Fix:** Manifests now use `replicas: 1`. If you see 0 replicas:
```bash
kubectl -n openclaw-tenant-1 scale deployment openclaw-gateway --replicas=1
kubectl -n openclaw-tenant-1 scale deployment openclaw-db --replicas=1
```

---

## Gateway "event gap detected" Warning

**Symptom:** Control UI shows red "Gateway Error: event gap detected (expected seq N, got N+2)".

**Cause:** WebSocket sequence gap from tunnel reconnections. Not a real error.

**Fix:** Refresh browser page. `gateway.trustedProxies` config reduces frequency.

---

## Setup Wizard Stuck on "Switching network routes..."

**Symptom:** Progress bar stuck at step 6, but OpenClaw is actually running.

**Cause:** Cloudflare route switch takes time; auto-redirect polls every 3s.

**Fix:** Wait 30-60 seconds. If still stuck, manually visit:
```
https://your-domain/#token=your-gateway-token
```

---

## LINE Messages Not Received

**Symptom:** User sends LINE message, bot doesn't reply.

**Checklist:**
1. `chatMode` must be `"bot"` (not `"chat"`) — check LINE OA Manager
2. `allowFrom: ["*"]` must be set — run `openclaw doctor --fix`
3. Webhook URL must be reachable — click Verify in LINE Developers Console
4. Channel secret must match — check `openclaw config get channels.line`
5. Tunnel must be stable — no 502 errors

```bash
# Quick diagnosis
curl -s https://api.line.me/v2/bot/info -H "Authorization: Bearer $TOKEN"
# Must show: "chatMode":"bot"
```

---

## OpenClaw Control UI Can't Connect After Restart

**Symptom:** "device_token_mismatch" errors in logs, UI won't load.

**Fix:** Re-pair by visiting the URL with token:
```
https://your-domain/#token=your-gateway-token
```

---

## Cron Job Delivery Error

**Symptom:** Cron job status "error", message: "Delivering to LINE requires target".

**Fix:** Add delivery target:
```bash
openclaw cron edit <job-id> --to <LINE_USER_ID> --channel line
```
