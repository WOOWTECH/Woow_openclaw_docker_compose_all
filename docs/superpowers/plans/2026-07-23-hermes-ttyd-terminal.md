# Hermes ttyd Terminal — Implementation Plan

> **For agentic workers:** Use this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-based terminal (ttyd) to the Hermes K8s deployment, allowing users to `kubectl exec` into the hermes-agent container from a web browser via Cloudflare Tunnel.

**Architecture:** Replicate the VK ttyd pattern — a lightweight `ubuntu:24.04` pod running ttyd on port 7681 with HTTP Basic Auth, using `kubectl exec` to attach into the hermes-agent container. Exposed via Cloudflare Tunnel at `woowtech-hermes-terminal.woowtech.io`.

**Tech Stack:** ttyd 1.7.7, kubectl, ubuntu:24.04, K8s (Deployment + Service + ConfigMap + RBAC), Cloudflare Tunnel API

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `hermes/k8s-manifests/11-terminal.yaml` | Create | ttyd Deployment + Service + ConfigMap + RBAC (all-in-one) |

No existing files need modification. The existing `hermes-agent-sa` ServiceAccount has pods/exec permission but is tied to the agent pod — the terminal needs its own SA for security isolation.

---

### Task 1: Create the terminal manifest

**Files:**
- Create: `hermes/k8s-manifests/11-terminal.yaml`

- [ ] **Step 1: Write the manifest**

The manifest contains 6 resources (matching VK's `11-terminal.yaml` pattern):

```yaml
# 1. ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hermes-terminal-sa
  namespace: hermes
---
# 2. Role (minimum: pods/get,list + pods/exec)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: hermes-terminal-role
  namespace: hermes
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create", "get"]
---
# 3. RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: hermes-terminal-rb
  namespace: hermes
subjects:
  - kind: ServiceAccount
    name: hermes-terminal-sa
    namespace: hermes
roleRef:
  kind: Role
  name: hermes-terminal-role
  apiGroup: rbac.authorization.k8s.io
---
# 4. ConfigMap (connect.sh + startup.sh)
apiVersion: v1
kind: ConfigMap
metadata:
  name: hermes-terminal-scripts
  namespace: hermes
data:
  connect.sh: |
    #!/bin/sh
    NAMESPACE="hermes"
    LABEL="app=hermes"
    CONTAINER="hermes-agent"
    while true; do
      POD=$(kubectl get pod -l "$LABEL" -n "$NAMESPACE" \
        --field-selector=status.phase=Running \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
      if [ -n "$POD" ]; then
        echo "Connecting to $POD ($CONTAINER)..."
        kubectl exec -it "$POD" -n "$NAMESPACE" -c "$CONTAINER" -- /bin/bash
        echo ""
        echo "Session ended. Reconnecting in 2s..."
        sleep 2
      else
        echo "Waiting for hermes-agent pod..."
        sleep 5
      fi
    done
  startup.sh: |
    #!/bin/bash
    if [ ! -f /usr/local/bin/ttyd ]; then
      apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
      curl -sLo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64
      chmod +x /usr/local/bin/ttyd
      curl -sLo /usr/local/bin/kubectl "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
      chmod +x /usr/local/bin/kubectl
    fi
    echo "Starting ttyd on :7681..."
    exec ttyd -p 7681 -c "admin:${TUI_PASSWORD}" -W /scripts/connect.sh
---
# 5. Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hermes-terminal
  namespace: hermes
  labels:
    app: hermes-terminal
    app.kubernetes.io/component: terminal
    app.kubernetes.io/part-of: hermes
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: hermes-terminal
  template:
    metadata:
      labels:
        app: hermes-terminal
    spec:
      serviceAccountName: hermes-terminal-sa
      containers:
        - name: ttyd
          image: ubuntu:24.04
          command: ["bash", "/scripts/startup.sh"]
          ports:
            - containerPort: 7681
              name: ttyd
          env:
            - name: TUI_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: hermes-secrets
                  key: WEBUI_PASSWORD
                  optional: true
          volumeMounts:
            - name: scripts
              mountPath: /scripts
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
          readinessProbe:
            tcpSocket:
              port: 7681
            initialDelaySeconds: 30
            periodSeconds: 10
          livenessProbe:
            tcpSocket:
              port: 7681
            initialDelaySeconds: 60
            periodSeconds: 30
      volumes:
        - name: scripts
          configMap:
            name: hermes-terminal-scripts
            defaultMode: 0755
---
# 6. Service
apiVersion: v1
kind: Service
metadata:
  name: hermes-terminal-svc
  namespace: hermes
  labels:
    app: hermes-terminal
    app.kubernetes.io/part-of: hermes
spec:
  selector:
    app: hermes-terminal
  ports:
    - name: ttyd
      protocol: TCP
      port: 7681
      targetPort: 7681
  type: ClusterIP
```

- [ ] **Step 2: Commit the manifest**

```bash
cd "/var/tmp/vibe-kanban/worktrees/c38b-k3s-kubernetes-h/k3s project"
git add hermes/k8s-manifests/11-terminal.yaml
git commit -m "feat: add ttyd browser terminal for hermes-agent"
```

---

### Task 2: Deploy to K8s

- [ ] **Step 1: Apply the manifest**

```bash
kubectl --context woow-k3s apply -f hermes/k8s-manifests/11-terminal.yaml
```

- [ ] **Step 2: Wait for pod readiness**

```bash
kubectl --context woow-k3s -n hermes wait --for=condition=Ready pod -l app=hermes-terminal --timeout=120s
```

Expected: `pod/hermes-terminal-xxx condition met`

- [ ] **Step 3: Verify ttyd is listening**

```bash
kubectl --context woow-k3s -n hermes exec deploy/hermes-terminal -- curl -s -o /dev/null -w "%{http_code}" http://localhost:7681/
```

Expected: `401` (HTTP Basic Auth required)

---

### Task 3: Add Cloudflare Tunnel route

- [ ] **Step 1: Get current tunnel config**

```bash
CF_TOKEN=$(kubectl --context woow-k3s -n hermes get secret cf-secrets -o jsonpath='{.data.CF_API_TOKEN}' | base64 -d)
TUNNEL_ID="a7ca50e6-b808-4e20-8f0b-4136c8c03fb2"
ACCOUNT_ID="9c27f623ee596e0b67be56263bcb1974"

curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
  -H "Authorization: Bearer ${CF_TOKEN}" | python3 -m json.tool
```

- [ ] **Step 2: Add terminal hostname to tunnel ingress**

```bash
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
  -H "Authorization: Bearer ${CF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"config":{"ingress":[
    {"hostname":"woowtech-dashboard.woowtech.io","service":"http://hermes-agent-svc:9119"},
    {"hostname":"woowtech-hermes.woowtech.io","service":"http://hermes-webui-svc:8787"},
    {"hostname":"woowtech-hermes-terminal.woowtech.io","service":"http://hermes-terminal-svc:7681"},
    {"service":"http_status:404"}
  ]}}'
```

- [ ] **Step 3: Add DNS record** (if not auto-created by tunnel)

```bash
# Get zone ID for woowtech.io
ZONE_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=woowtech.io" \
  -H "Authorization: Bearer ${CF_TOKEN}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result'][0]['id'])")

# Create CNAME record
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "Authorization: Bearer ${CF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"CNAME\",\"name\":\"woowtech-hermes-terminal\",\"content\":\"${TUNNEL_ID}.cfargotunnel.com\",\"proxied\":true}"
```

- [ ] **Step 4: Restart cloudflared to pick up new route**

```bash
kubectl --context woow-k3s -n hermes rollout restart deploy/cloudflared
```

---

### Task 4: Verify E2E

- [ ] **Step 1: Test external access**

```bash
curl -s -u admin:PASSWORD -o /dev/null -w "%{http_code}" https://woowtech-hermes-terminal.woowtech.io/
```

Expected: `200`

- [ ] **Step 2: Browser test via Playwright**

Navigate to `https://woowtech-hermes-terminal.woowtech.io/`, enter credentials, verify terminal loads and shows hermes-agent bash shell.

- [ ] **Step 3: Verify kubectl exec works inside terminal**

In the browser terminal, verify:
- `hermes --version` works
- `hermes mcp list` works
- `kubectl get pods -n hermes` works
- Tools: `jq`, `yq`, `gh`, `cloudflared` are available

---

### Task 5: Push to GitHub

- [ ] **Step 1: Push manifest to OpenClaw repo**

```bash
git push origin vk/c38b-k3s-kubernetes-h
```

- [ ] **Step 2: Copy to Hermes repo**

```bash
cd /tmp && git clone https://github.com/WOOWTECH/Woow_hermes_agent_docker_compose_all.git hermes-terminal-commit
cp "/var/tmp/vibe-kanban/worktrees/c38b-k3s-kubernetes-h/k3s project/hermes/k8s-manifests/11-terminal.yaml" hermes-terminal-commit/deploy/k3s/manifests/
cd hermes-terminal-commit && git add . && git commit -m "feat: add ttyd browser terminal manifest" && git push
```
