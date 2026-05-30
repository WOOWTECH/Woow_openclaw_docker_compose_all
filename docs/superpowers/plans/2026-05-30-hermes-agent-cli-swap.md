# Hermes Agent CLI Tools Swap: Remove kubectl/psql, Add Chromium/Playwright

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the custom Hermes Agent Docker image to remove `kubectl` and `psql`, add `chromium` browser and `playwright` Python package, then rebuild and redeploy to all 4 instances on the woow-k3s remote cluster.

**Architecture:** Modify `Dockerfile.hermes-agent` to drop kubectl binary download + postgresql-client apt layer, remove google-chrome-stable (413MB), and add Playwright Python package with Chromium browser via shared `PLAYWRIGHT_BROWSERS_PATH`. Update `07-hermes-webui.yaml` to remove kubectl from init container and psql from postStart hook. Rebuild the custom image locally, push to in-cluster registry (`10.43.52.5:5000`), pull on all 4 remote nodes via `ctr`, then rolling-restart all 4 hermes-agent deployments.

**Tech Stack:** Docker, K3s, containerd, Playwright (Python), Chromium, Bash

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `hermes/Dockerfile.hermes-agent` | Remove kubectl + psql + google-chrome, add chromium + playwright |
| Modify | `hermes/k8s-manifests/07-hermes-webui.yaml` | Remove kubectl from init container, psql from postStart |
| No change | `hermes/build-image.sh` | Build script unchanged |
| No change | `hermes/k8s-manifests/06-hermes-agent.yaml` | Agent deployment manifest unchanged |

---

### Task 1: Modify Dockerfile — Remove kubectl, psql, and google-chrome

**Files:**
- Modify: `hermes/Dockerfile.hermes-agent:54` (kubectl ARG)
- Modify: `hermes/Dockerfile.hermes-agent:60-63` (kubectl RUN)
- Modify: `hermes/Dockerfile.hermes-agent:92-96` (postgresql-client RUN)
- Modify: `hermes/Dockerfile.hermes-agent:121-123` (old chrome install)

- [ ] **Step 1: Remove kubectl ARG and RUN block**

Delete `ARG KUBECTL_VERSION=v1.34.3` (line 54) and the kubectl download RUN block (lines 60-63).

- [ ] **Step 2: Remove postgresql-client layer**

Delete lines 94-96 (the postgresql-client comment + RUN block). Keep line 92-93 section comment but update it:
```dockerfile
# ── Layer 3: Google Cloud SDK ────────────────────────────────
```

- [ ] **Step 3: Remove google-chrome-stable from base image**

Add a removal step before installing Chromium — the base `nousresearch/hermes-agent` ships with `google-chrome-stable` (~413MB) which is no longer needed:
```dockerfile
RUN apt-get update && apt-get remove -y google-chrome-stable 2>/dev/null || true \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
```

---

### Task 2: Modify Dockerfile — Add Chromium and Playwright

**Files:**
- Modify: `hermes/Dockerfile.hermes-agent:116-123` (Layer 5)

- [ ] **Step 1: Update Layer 5 with proper Playwright + Chromium installation**

Replace the current Layer 5 section with:
```dockerfile
# ── Layer 5: Python & Node tools ───────────────────────────────

# Shared browser path so both root-install and USER hermes can access
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

# httpie + yt-dlp + playwright (Python)
RUN pip install --break-system-packages --no-cache-dir httpie yt-dlp playwright

# Install Chromium via Python playwright (single source of truth for browser version)
RUN python3 -m playwright install --with-deps chromium \
    && chmod -R o+rx /opt/playwright-browsers

# Playwright CLI (npm) — shares browsers via PLAYWRIGHT_BROWSERS_PATH
RUN npm install -g @playwright/cli@latest
```

Key design decisions:
- `PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers` — shared location accessible by both root (build-time) and `hermes` user (run-time)
- `python3 -m playwright install --with-deps chromium` — installs Chromium binary + all system deps (libgbm, libasound2, etc.), using Python playwright as the single source of truth for browser version
- `chmod -R o+rx` — ensures `hermes` (UID 10000) can read/execute the browser
- npm `@playwright/cli` installed separately — it will find browsers via the shared `PLAYWRIGHT_BROWSERS_PATH` env var
- Do NOT `rm -rf /root/.cache` in this layer (browsers are in `/opt/playwright-browsers`, not cache)

- [ ] **Step 2: Update Layer 6 cleanup — do not delete browser path**

Ensure the cleanup layer does not wipe `/opt/playwright-browsers`:
```dockerfile
# ── Layer 6: Cleanup & permissions ─────────────────────────────

RUN rm -rf /tmp/* /var/lib/apt/lists/* 2>/dev/null; \
    mkdir -p /home/hermes/.cache /home/hermes/.local/share \
             /home/hermes/.ssh /home/hermes/.config \
    && chown -R hermes:hermes /home/hermes
```

(Remove `/root/.cache` from the rm list — it's harmless and avoids accidentally nuking any pip caches needed.)

---

### Task 3: Update WebUI Manifest — Remove kubectl and psql

**Files:**
- Modify: `hermes/k8s-manifests/07-hermes-webui.yaml:69-70` (kubectl in install-tools)
- Modify: `hermes/k8s-manifests/07-hermes-webui.yaml:131` (postgresql-client in postStart)

- [ ] **Step 1: Remove kubectl from install-tools initContainer**

Delete these 2 lines from install-tools args:
```yaml
# DELETE:
  KUBECTL_V=v1.34.3
  curl -fsSL "https://dl.k8s.io/release/${KUBECTL_V}/bin/linux/amd64/kubectl" -o /opt/tools/kubectl
```

- [ ] **Step 2: Remove postgresql-client from postStart hook**

Change:
```yaml
jq fd-find rsync postgresql-client redis-tools \
```
To:
```yaml
jq fd-find rsync redis-tools \
```

- [ ] **Step 3: Commit all changes**

```bash
git add hermes/Dockerfile.hermes-agent hermes/k8s-manifests/07-hermes-webui.yaml
git commit -m "feat: swap kubectl/psql for chromium/playwright in Hermes Agent image"
```

---

### Task 4: Build Custom Image Locally

- [ ] **Step 1: Build the updated Docker image**

```bash
cd "/var/tmp/vibe-kanban/worktrees/c38b-k3s-kubernetes-h/k3s project/hermes"
./build-image.sh
```

Expected: Build succeeds (~10-15 min due to Chromium download + deps)

- [ ] **Step 2: Verify the image**

```bash
docker run --rm hermes-agent-custom:latest sh -c '
  python3 -c "import playwright; print(\"playwright python:\", playwright.__version__)";
  npx playwright --version;
  python3 -m playwright install --dry-run 2>&1 | grep chromium || echo "chromium installed";
  which kubectl && echo "FAIL: kubectl still present" || echo "OK: kubectl removed";
  which psql && echo "FAIL: psql still present" || echo "OK: psql removed";
  which google-chrome && echo "FAIL: chrome still present" || echo "OK: chrome removed";
  ls /opt/playwright-browsers/ 2>/dev/null && echo "OK: browser path exists"
'
```

Expected: playwright works, chromium in `/opt/playwright-browsers`, kubectl/psql/chrome absent.

---

### Task 5: Push Image to Remote In-Cluster Registry

- [ ] **Step 1: Tag and push to remote registry**

```bash
docker tag docker.io/woowtech/hermes-agent-custom:latest 10.43.52.5:5000/hermes-agent-custom:latest
docker push 10.43.52.5:5000/hermes-agent-custom:latest
```

Note: `10.43.52.5:5000` is the woow-k3s in-cluster registry (distinct from `10.43.80.213:5000` on the local cluster). Requires VPN connectivity.

- [ ] **Step 2: Pull image on all 4 remote nodes via ctr**

```bash
for NODE_IP in 192.168.10.21 192.168.10.22 192.168.10.23 192.168.10.24; do
  ssh $NODE_IP "sudo ctr -n k8s.io images pull --plain-http 10.43.52.5:5000/hermes-agent-custom:latest" &
done
wait
```

---

### Task 6: Rolling Restart All 4 Hermes Agent Deployments

- [ ] **Step 1: Restart agent deployments across all 4 namespaces**

```bash
for NS in hermes apporoalan-hermes johhanlin-hermes alanlin-hermes; do
  kubectl --context=woow-k3s -n $NS rollout restart deploy/hermes-agent
done
```

- [ ] **Step 2: Wait for rollout completion**

```bash
for NS in hermes apporoalan-hermes johhanlin-hermes alanlin-hermes; do
  kubectl --context=woow-k3s -n $NS rollout status deploy/hermes-agent --timeout=120s
done
```

---

### Task 7: Verify CLI Tools on All 4 Instances

- [ ] **Step 1: Verify removal + installation on each namespace**

```bash
for NS in hermes apporoalan-hermes johhanlin-hermes alanlin-hermes; do
  echo "=== $NS ==="
  kubectl --context=woow-k3s -n $NS exec deploy/hermes-agent -- sh -c '
    python3 -c "import playwright; print(\"playwright:\", playwright.__version__)";
    echo "playwright cli: $(npx playwright --version 2>/dev/null)";
    ls /opt/playwright-browsers/chromium-* 2>/dev/null && echo "OK: chromium installed" || echo "FAIL: chromium missing";
    which kubectl && echo "FAIL: kubectl present" || echo "OK: kubectl removed";
    which psql && echo "FAIL: psql present" || echo "OK: psql removed"
  '
  echo ""
done
```

- [ ] **Step 2: Functional browser launch test on ALL namespaces**

```bash
for NS in hermes apporoalan-hermes johhanlin-hermes alanlin-hermes; do
  echo "=== $NS ==="
  kubectl --context=woow-k3s -n $NS exec deploy/hermes-agent -- \
    python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = browser.new_page()
    page.goto('https://example.com')
    print('Title:', page.title())
    browser.close()
print('OK: Playwright + Chromium functional')
"
  echo ""
done
```

Expected per namespace:
- `playwright: x.x.x` — OK
- `chromium installed` — OK
- `kubectl removed` — OK
- `psql removed` — OK
- `Title: Example Domain` — OK
- `OK: Playwright + Chromium functional` — OK

---

## Summary of Changes

| Before | After |
|--------|-------|
| kubectl v1.34.3 (58MB binary) | Removed |
| postgresql-client (psql) | Removed |
| google-chrome-stable 148 (~413MB) | Removed |
| @playwright/cli (npm only, no Python) | @playwright/cli (npm) + playwright (Python) |
| No chromium binary | Chromium via Playwright in `/opt/playwright-browsers` |

**Net effect:** ~471MB freed (kubectl 58MB + chrome 413MB + psql ~5MB), ~300MB added (Chromium + Playwright deps) = **~170MB net reduction**.
