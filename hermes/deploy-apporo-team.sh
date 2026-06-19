#!/bin/bash
# Deploy 5 new Apporo Hermes instances in apporoalan-hermes namespace
# All share one Cloudflare tunnel and use Apporo v2 branding
set -euo pipefail

CONTEXT="woow-k3s"
NS="apporoalan-hermes"
K="kubectl --context $CONTEXT -n $NS"
NEW_API_KEY="REDACTED_MINIMAX_KEY_3"
NEW_KEY_B64=$(echo -n "$NEW_API_KEY" | base64 -w0)
API_SERVER_KEY_B64=$(echo -n "$(openssl rand -hex 32)" | base64 -w0)
IMAGE="10.43.200.138:5000/hermes-agent-custom:v0.15"
WEBUI_IMAGE="ghcr.io/nesquena/hermes-webui:latest"

# 5 team members: prefix → domain
declare -A MEMBERS=(
  [koen]="koendekyvere-hermes.woowtech.io"
  [gerard]="gerardatia-hermes.woowtech.io"
  [jose]="josemorcillo-hermes.woowtech.io"
  [richard]="richardchang-hermes.woowtech.io"
  [daniel]="danieloh-hermes.woowtech.io"
)

deploy_instance() {
  local PREFIX="$1"
  local DOMAIN="$2"
  local PG_PASS=$(openssl rand -base64 12 | tr -d '/+=' | head -c 16)
  local API_KEY=$(openssl rand -hex 32)
  local PG_PASS_B64=$(echo -n "$PG_PASS" | base64 -w0)
  local API_KEY_B64=$(echo -n "$API_KEY" | base64 -w0)

  echo "=== Deploying $PREFIX ($DOMAIN) ==="

  # 1. Secret
  cat <<EOF | $K apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ${PREFIX}-secrets
  namespace: $NS
type: Opaque
data:
  MINIMAX_API_KEY: $NEW_KEY_B64
  API_SERVER_KEY: $API_KEY_B64
  POSTGRES_PASSWORD: $PG_PASS_B64
EOF

  # 2. ConfigMap
  cat <<EOF | $K apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${PREFIX}-config
  namespace: $NS
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

  # 3. PVCs
  for PVC_NAME in "${PREFIX}-data" "${PREFIX}-postgresql-pvc" "${PREFIX}-redis-pvc"; do
    SC="local-path"
    SIZE="10Gi"
    [[ "$PVC_NAME" == *redis* ]] && SIZE="5Gi"
    [[ "$PVC_NAME" == *data* ]] && SC="longhorn" && SIZE="5Gi"
    cat <<EOF | $K apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $PVC_NAME
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: $SC
  resources:
    requests:
      storage: $SIZE
EOF
  done

  # 4. PostgreSQL
  cat <<EOF | $K apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}-postgresql
  namespace: $NS
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
        - name: POSTGRES_DB
          value: hermes
        - name: POSTGRES_USER
          value: hermes
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: POSTGRES_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        ports:
        - containerPort: 5432
        livenessProbe:
          exec:
            command: [pg_isready, -U, hermes, -d, hermes]
          initialDelaySeconds: 30
          periodSeconds: 30
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: pg-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: pg-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-postgresql-pvc
EOF

  # 5. Redis
  cat <<EOF | $K apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}-redis
  namespace: $NS
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
          requests:
            cpu: 25m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-redis-pvc
EOF

  # 6. Services
  for SVC_TYPE in agent webui postgresql redis; do
    case $SVC_TYPE in
      agent)     PORT=8642; LABEL="${PREFIX}" ;;
      webui)     PORT=8787; LABEL="${PREFIX}" ;;
      postgresql) PORT=5432; LABEL="${PREFIX}-postgresql" ;;
      redis)     PORT=6379; LABEL="${PREFIX}-redis" ;;
    esac
    # For agent/webui, the container names have specific port names
    SVC_NAME="${PREFIX}-${SVC_TYPE}-svc"
    [[ "$SVC_TYPE" == "agent" ]] && EXTRA_PORT="- port: 9119
        targetPort: 9119
        name: dashboard" || EXTRA_PORT=""
    cat <<EOF | $K apply -f -
apiVersion: v1
kind: Service
metadata:
  name: $SVC_NAME
  namespace: $NS
spec:
  selector:
    app: $LABEL
  ports:
  - port: $PORT
    targetPort: $PORT
    name: $SVC_TYPE
$([ -n "$EXTRA_PORT" ] && echo "  $EXTRA_PORT")
EOF
  done

  # 7. Main Hermes Deployment (combined agent + webui pod)
  cat <<DEPLOY | $K apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PREFIX}
  namespace: $NS
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
        image: $IMAGE
        imagePullPolicy: Never
        args: [gateway, run]
        env:
        - name: HERMES_DASHBOARD
          value: "1"
        - name: HERMES_DASHBOARD_INSECURE
          value: "1"
        - name: HERMES_UID
          value: "1000"
        - name: HERMES_GID
          value: "1000"
        - name: API_SERVER_ENABLED
          value: "true"
        - name: API_SERVER_HOST
          value: "0.0.0.0"
        - name: API_SERVER_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: API_SERVER_KEY
        - name: API_SERVER_CORS_ORIGINS
          value: "*"
        - name: GATEWAY_ALLOW_ALL_USERS
          value: "true"
        - name: MINIMAX_API_KEY
          valueFrom:
            secretKeyRef:
              name: ${PREFIX}-secrets
              key: MINIMAX_API_KEY
        - name: PLAYWRIGHT_BROWSERS_PATH
          value: /shared-pw
        - name: PATH
          value: /opt/data/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/google-cloud-sdk/bin
        ports:
        - containerPort: 8642
          name: gateway
        - containerPort: 9119
          name: dashboard
        resources:
          requests:
            cpu: 200m
            memory: 1Gi
          limits:
            cpu: "2"
            memory: 6Gi
        securityContext:
          runAsUser: 0
          runAsGroup: 0
        livenessProbe:
          tcpSocket:
            port: 8642
          initialDelaySeconds: 30
          periodSeconds: 30
          failureThreshold: 5
        readinessProbe:
          tcpSocket:
            port: 8642
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 6
        lifecycle:
          postStart:
            exec:
              command: [sh, -c, "rm -f /usr/local/bin/argocd /usr/local/bin/helm /usr/bin/docker 2>/dev/null; ln -sf /opt/hermes/.venv/bin/hermes /usr/local/bin/hermes 2>/dev/null || true"]
        volumeMounts:
        - name: hermes-data
          mountPath: /opt/data
        - name: playwright-shared
          mountPath: /shared-pw
        - name: tools-shared
          mountPath: /shared-tools
      - name: hermes-webui
        image: $WEBUI_IMAGE
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
        - name: HERMES_WEBUI_CHAT_BACKEND
          value: gateway
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
        - name: PLAYWRIGHT_BROWSERS_PATH
          value: /opt/playwright-browsers
        - name: LD_LIBRARY_PATH
          value: /opt/shared-tools/lib
        - name: PATH
          value: /opt/shared-tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
        - name: HERMES_WEBUI_HOST
          value: "0.0.0.0"
        - name: HERMES_WEBUI_PORT
          value: "8787"
        - name: HERMES_WEBUI_STATE_DIR
          value: /home/hermeswebui/.hermes/webui
        - name: HERMES_HOME
          value: /home/hermeswebui/.hermes
        - name: WANTED_UID
          value: "1000"
        - name: WANTED_GID
          value: "1000"
        - name: GATEWAY_HEALTH_URL
          value: http://localhost:8642
        - name: HERMES_WEBUI_PASSWORD
          value: admin
        tty: true
        ports:
        - containerPort: 8787
          name: http
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: "2"
            memory: 2Gi
        lifecycle:
          postStart:
            exec:
              command: [sh, /home/hermeswebui/.hermes/replace_icons.sh]
        livenessProbe:
          tcpSocket:
            port: 8787
          initialDelaySeconds: 90
          periodSeconds: 30
          failureThreshold: 5
        readinessProbe:
          tcpSocket:
            port: 8787
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 12
        volumeMounts:
        - name: hermes-data
          mountPath: /home/hermeswebui/.hermes
        - name: playwright-shared
          mountPath: /opt/playwright-browsers
        - name: tools-shared
          mountPath: /opt/shared-tools
      volumes:
      - name: hermes-data
        persistentVolumeClaim:
          claimName: ${PREFIX}-data
      - name: playwright-shared
        emptyDir: {}
      - name: tools-shared
        emptyDir: {}
DEPLOY

  echo "=== $PREFIX deployed ==="
}

# Deploy all 5
for PREFIX in "${!MEMBERS[@]}"; do
  deploy_instance "$PREFIX" "${MEMBERS[$PREFIX]}"
done

echo ""
echo "=== All 5 instances deployed ==="
echo "Waiting for PVCs to bind and pods to start..."
sleep 5
$K get pods -l 'app in (koen,gerard,jose,richard,daniel)' -o wide 2>/dev/null
$K get pvc | grep -E 'koen|gerard|jose|richard|daniel'
