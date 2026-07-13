#!/bin/bash
# Deploy a single Hermes instance in apporoalan-hermes namespace
# Usage: ./deploy-instance.sh <prefix> <domain>
set -euo pipefail

PREFIX="${1:?Usage: $0 <prefix> <domain>}"
DOMAIN="${2:?Usage: $0 <prefix> <domain>}"

CONTEXT="woow-k3s"
NS="apporoalan-hermes"
K="kubectl --context $CONTEXT -n $NS"
NEW_API_KEY="${MINIMAX_API_KEY:?Set MINIMAX_API_KEY env var before running}"
NEW_KEY_B64=$(echo -n "$NEW_API_KEY" | base64 -w0)
IMAGE="nousresearch/hermes-agent:latest"
WEBUI_IMAGE="ghcr.io/nesquena/hermes-webui:latest"

PG_PASS=$(openssl rand -base64 12 | tr -d '/+=' | head -c 16)
API_KEY=$(openssl rand -hex 32)
PG_PASS_B64=$(echo -n "$PG_PASS" | base64 -w0)
API_KEY_B64=$(echo -n "$API_KEY" | base64 -w0)

echo "=== Deploying $PREFIX ($DOMAIN) ==="

# Secret
cat <<EOF | $K apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ${PREFIX}-secrets
type: Opaque
data:
  MINIMAX_API_KEY: $NEW_KEY_B64
  API_SERVER_KEY: $API_KEY_B64
  POSTGRES_PASSWORD: $PG_PASS_B64
EOF

# ConfigMap
cat <<EOF | $K apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${PREFIX}-config
data:
  HERMES_BASE_URL: "https://$DOMAIN"
  HERMES_DOMAIN: "$DOMAIN"
  HERMES_AGENT_PORT: "8642"
  HERMES_WEBUI_PORT: "8787"
  POSTGRES_DB: hermes
  POSTGRES_HOST: ${PREFIX}-postgresql-svc
  POSTGRES_PORT: "5432"
  POSTGRES_USER: hermes
  REDIS_HOST: ${PREFIX}-redis-svc
  REDIS_PORT: "6379"
  WANTED_UID: "1000"
EOF

# PVCs
for SUFFIX in data postgresql-pvc redis-pvc; do
  SC="local-path"; SIZE="10Gi"
  [[ "$SUFFIX" == "redis-pvc" ]] && SIZE="5Gi"
  [[ "$SUFFIX" == "data" ]] && SC="longhorn" && SIZE="5Gi"
  $K get pvc "${PREFIX}-${SUFFIX}" &>/dev/null && echo "PVC ${PREFIX}-${SUFFIX} exists" && continue
  cat <<EOF | $K apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${PREFIX}-${SUFFIX}
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: $SC
  resources:
    requests:
      storage: $SIZE
EOF
done

# PostgreSQL
$K get deployment "${PREFIX}-postgresql" &>/dev/null && echo "PostgreSQL exists" || \
cat <<EOF | $K apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}-postgresql
  labels:
    app: ${PREFIX}-postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${PREFIX}-postgresql
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: ${PREFIX}-postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        imagePullPolicy: IfNotPresent
        env:
        - {name: POSTGRES_DB, value: hermes}
        - {name: POSTGRES_USER, value: hermes}
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: POSTGRES_PASSWORD
        - {name: PGDATA, value: /var/lib/postgresql/data/pgdata}
        ports:
        - containerPort: 5432
        livenessProbe:
          exec:
            command: [pg_isready, -U, hermes, -d, hermes]
          initialDelaySeconds: 30
          periodSeconds: 30
        resources:
          requests: {cpu: 50m, memory: 128Mi}
          limits: {cpu: 500m, memory: 512Mi}
        volumeMounts:
        - {name: pg-data, mountPath: /var/lib/postgresql/data}
      volumes:
      - name: pg-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-postgresql-pvc
EOF

# Redis
$K get deployment "${PREFIX}-redis" &>/dev/null && echo "Redis exists" || \
cat <<EOF | $K apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}-redis
  labels:
    app: ${PREFIX}-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${PREFIX}-redis
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: ${PREFIX}-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        imagePullPolicy: IfNotPresent
        command: [redis-server, --appendonly, "yes", --maxmemory, 256mb, --maxmemory-policy, allkeys-lru]
        ports:
        - containerPort: 6379
        livenessProbe:
          exec:
            command: [redis-cli, ping]
          initialDelaySeconds: 15
          periodSeconds: 30
        resources:
          requests: {cpu: 25m, memory: 64Mi}
          limits: {cpu: 200m, memory: 256Mi}
        volumeMounts:
        - {name: redis-data, mountPath: /data}
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-redis-pvc
EOF

# Services
cat <<EOF | $K apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ${PREFIX}-agent-svc
spec:
  selector:
    app: ${PREFIX}
  ports:
  - port: 8642
    targetPort: 8642
    name: gateway
  - port: 9119
    targetPort: 9119
    name: dashboard
---
apiVersion: v1
kind: Service
metadata:
  name: ${PREFIX}-webui-svc
spec:
  selector:
    app: ${PREFIX}
  ports:
  - port: 8787
    targetPort: 8787
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: ${PREFIX}-postgresql-svc
spec:
  selector:
    app: ${PREFIX}-postgresql
  ports:
  - port: 5432
    targetPort: 5432
    name: postgresql
---
apiVersion: v1
kind: Service
metadata:
  name: ${PREFIX}-redis-svc
spec:
  selector:
    app: ${PREFIX}-redis
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
EOF

echo "=== Infrastructure for $PREFIX ready ==="
echo "=== Deploying main Hermes pod... ==="

# Main Hermes combined pod deployment - write to temp file to avoid heredoc issues
TMPF=$(mktemp /tmp/hermes-deploy-XXXXX.yaml)
cat > "$TMPF" << YAMLEOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}
  namespace: ${NS}
  labels:
    app: ${PREFIX}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${PREFIX}
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: ${PREFIX}
    spec:
      serviceAccountName: hermes-agent-sa
      securityContext:
        fsGroup: 0
      containers:
      - name: hermes-agent
        image: ${IMAGE}
        imagePullPolicy: Always
        args: [gateway, run]
        env:
        - {name: HERMES_DASHBOARD, value: "1"}
        - {name: HERMES_DASHBOARD_INSECURE, value: "1"}
        - {name: HERMES_DASHBOARD_BASIC_AUTH_USERNAME, value: "admin"}
        - {name: HERMES_DASHBOARD_BASIC_AUTH_PASSWORD, value: "admin"}
        - {name: HERMES_DASHBOARD_TUI, value: "1"}
        - {name: HERMES_TUI_DIR, value: "/opt/data/ui-tui"}
        - {name: HERMES_UID, value: "1000"}
        - {name: HERMES_GID, value: "1000"}
        - {name: API_SERVER_ENABLED, value: "true"}
        - {name: API_SERVER_HOST, value: "0.0.0.0"}
        - name: API_SERVER_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: API_SERVER_KEY
        - {name: API_SERVER_CORS_ORIGINS, value: "*"}
        - {name: GATEWAY_ALLOW_ALL_USERS, value: "true"}
        - name: MINIMAX_API_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: MINIMAX_API_KEY
        - {name: PLAYWRIGHT_BROWSERS_PATH, value: /opt/data/playwright-browsers}
        - {name: PATH, value: "/opt/data/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/google-cloud-sdk/bin"}
        ports:
        - {containerPort: 8642, name: gateway}
        - {containerPort: 9119, name: dashboard}
        resources:
          requests: {cpu: 200m, memory: 1Gi}
          limits: {cpu: "2", memory: 6Gi}
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        livenessProbe:
          tcpSocket: {port: 8642}
          initialDelaySeconds: 30
          periodSeconds: 30
          failureThreshold: 5
        readinessProbe:
          tcpSocket: {port: 8642}
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 6
        lifecycle:
          postStart:
            exec:
              command: [sh, -c, "rm -f /usr/local/bin/argocd /usr/local/bin/helm /usr/bin/docker 2>/dev/null; ln -sf /opt/hermes/.venv/bin/hermes /usr/local/bin/hermes 2>/dev/null; rm -rf /opt/hermes/skills/apple /opt/hermes/skills/gaming /opt/hermes/skills/email /opt/hermes/skills/social-media /opt/hermes/skills/yuanbao /opt/hermes/skills/media/heartmula /opt/hermes/skills/media/songsee /opt/hermes/skills/media/spotify /opt/hermes/skills/media/youtube-content /opt/hermes/skills/smart-home/openhue 2>/dev/null; SITE=$(/opt/hermes/.venv/bin/python3 -c 'import site;print(site.getsitepackages()[0])' 2>/dev/null) && pip install --break-system-packages -q --target=$SITE ddgs 2>/dev/null || true"]
        volumeMounts:
        - {name: hermes-data, mountPath: /opt/data}
        - {name: playwright-shared, mountPath: /shared-pw}
        - {name: tools-shared, mountPath: /shared-tools}
      - name: hermes-webui
        image: ${WEBUI_IMAGE}
        imagePullPolicy: Always
        command: [sh, -c]
        args:
        - |
          mkdir -p /home/hermeswebui/.hermes
          echo "MINIMAX_API_KEY=\${MINIMAX_API_KEY}" > /home/hermeswebui/.hermes/.env
          chmod 644 /home/hermeswebui/.hermes/.env
          for i in \$(seq 1 90); do
            HTTP=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8642/ 2>/dev/null)
            [ "\$HTTP" = "200" ] || [ "\$HTTP" = "404" ] && break
            sleep 2
          done
          (while true; do
            NOW=\$(python3 -c "from datetime import datetime,timezone;print(datetime.now(timezone.utc).isoformat())")
            printf '{"gateway_state":"running","updated_at":"%s","pid":1,"platform":"hermes-agent","version":"0.13.0"}\n' "\$NOW" > /home/hermeswebui/.hermes/gateway_state.json 2>/dev/null
            sleep 25
          done) &
          rm -f /home/hermeswebui/.hermes/.skills_prompt_snapshot.json 2>/dev/null
          if [ -f /hermeswebui_init.bash ]; then
            sed -i 's/chmod 700 "\$itdir"/chmod 755 "\$itdir"/' /hermeswebui_init.bash 2>/dev/null
            sed -i '/cd \/app; python server.py/i test -f /home/hermeswebui/.hermes/replace_icons.sh && sh /home/hermeswebui/.hermes/replace_icons.sh 2>/dev/null || true' /hermeswebui_init.bash 2>/dev/null
            exec /hermeswebui_init.bash
          else
            echo "WebUI init script not found, sleeping..."
            sleep infinity
          fi
        env:
        - {name: HERMES_WEBUI_CHAT_BACKEND, value: gateway}
        - name: HERMES_WEBUI_GATEWAY_API_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: API_SERVER_KEY
        - name: MINIMAX_API_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: MINIMAX_API_KEY
        - {name: PLAYWRIGHT_BROWSERS_PATH, value: /opt/data/playwright-browsers}
        - {name: LD_LIBRARY_PATH, value: /opt/shared-tools/lib}
        - {name: PATH, value: "/opt/shared-tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
        - {name: HERMES_WEBUI_HOST, value: "0.0.0.0"}
        - {name: HERMES_WEBUI_PORT, value: "8787"}
        - {name: HERMES_WEBUI_STATE_DIR, value: /home/hermeswebui/.hermes/webui}
        - {name: HERMES_HOME, value: /home/hermeswebui/.hermes}
        - {name: WANTED_UID, value: "1000"}
        - {name: WANTED_GID, value: "1000"}
        - {name: GATEWAY_HEALTH_URL, value: "http://localhost:8642"}
        - {name: HERMES_WEBUI_PASSWORD, value: admin}
        tty: true
        ports:
        - {containerPort: 8787, name: http}
        resources:
          requests: {cpu: 500m, memory: 512Mi}
          limits: {cpu: "2", memory: 2Gi}
        lifecycle:
          postStart:
            exec:
              command: [sh, /home/hermeswebui/.hermes/replace_icons.sh]
        livenessProbe:
          tcpSocket: {port: 8787}
          initialDelaySeconds: 90
          periodSeconds: 30
          failureThreshold: 5
        readinessProbe:
          tcpSocket: {port: 8787}
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 12
        volumeMounts:
        - {name: hermes-data, mountPath: /home/hermeswebui/.hermes}
        - {name: playwright-shared, mountPath: /opt/playwright-browsers}
        - {name: tools-shared, mountPath: /opt/shared-tools}
      volumes:
      - name: hermes-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-data
      - name: playwright-shared
        emptyDir: {}
      - name: tools-shared
        emptyDir: {}
YAMLEOF

$K apply -f "$TMPF"
rm -f "$TMPF"
echo "=== $PREFIX ($DOMAIN) fully deployed ==="
