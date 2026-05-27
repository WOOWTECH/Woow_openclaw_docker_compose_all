#!/usr/bin/env bash
set -uo pipefail

# =============================================================
# Hermes Dual Instance E2E — 20 Enterprise Scenarios
# apporoalan-hermes: ESG/WELL 健康建築顧問 (10 rounds)
# johhanlin-hermes:  金融業外匯交易 (10 rounds)
# =============================================================

PASS=0; FAIL=0; TOTAL=0
LOG="/tmp/hermes-dual-e2e.log"
> "$LOG"

pass() { ((PASS++)); ((TOTAL++)); echo "  PASS: $1"; echo "PASS|$1" >> "$LOG"; }
fail() { ((FAIL++)); ((TOTAL++)); echo "  FAIL: $1 -- $2"; echo "FAIL|$1|$2" >> "$LOG"; }

send_chat() {
  local port="$1" msg="$2" wait="${3:-40}"

  # New conversation
  playwright-cli click e57 2>/dev/null | head -1
  sleep 2

  local ref
  ref=$(playwright-cli snapshot 2>/dev/null | grep "textbox.*Message" | grep -oP 'ref=\K[^ \]]+' | head -1)
  [ -z "$ref" ] && { echo "NO_INPUT_REF"; return 1; }

  playwright-cli fill "$ref" "$msg" --submit 2>/dev/null | head -1

  # Auto-approve
  for i in $(seq 1 10); do
    sleep 5
    playwright-cli eval "document.getElementById('updateBanner')?.remove(); document.getElementById('approvalBtnAlways')?.click()" 2>/dev/null
  done &
  local APID=$!
  sleep "$wait"
  kill $APID 2>/dev/null; wait $APID 2>/dev/null

  # Get response text from code blocks or last message
  playwright-cli --raw eval "(() => {
    const blocks = document.querySelectorAll('pre code, .code-block');
    if (blocks.length > 0) return Array.from(blocks).map(b=>b.innerText).join('\\n');
    const bubbles = document.querySelectorAll('.message-bubble');
    return bubbles.length > 1 ? bubbles[bubbles.length-1].innerText : 'NO_RESPONSE';
  })()" 2>/dev/null
}

test_instance() {
  local PORT="$1" NAME="$2" URL="$3"

  echo ""
  echo "============================================================"
  echo "  Testing: ${NAME} (${URL})"
  echo "============================================================"

  # Open and login
  playwright-cli goto "http://localhost:${PORT}" 2>/dev/null | head -1
  sleep 2
  playwright-cli snapshot 2>/dev/null | grep -q "Password" && \
    playwright-cli fill e7 "woowtech" --submit 2>/dev/null | head -1
  sleep 3
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Hermes Dual Instance E2E — 20 Enterprise Scenarios     ║"
echo "║  $(date -u +'%Y-%m-%d %H:%M:%S UTC')                            ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────
# INSTANCE 1: apporoalan-hermes (ESG/WELL 健康建築)
# ─────────────────────────────────────────────────

playwright-cli open "http://localhost:18801" 2>/dev/null | head -1
sleep 2
playwright-cli fill e7 "woowtech" --submit 2>/dev/null | head -1
sleep 3

echo ""
echo ">> apporoalan-hermes: ESG/WELL 健康建築顧問"

# R1: WELL 標準查詢
echo "  [R1] WELL Building Standard query..."
R=$(send_chat 18801 "run: echo 'WELL Building Standard v2 has 10 concepts: Air, Water, Nourishment, Light, Movement, Thermal Comfort, Sound, Materials, Mind, Community. Each concept has features scored as preconditions or optimizations.' | jq -R '{standard: \"WELL v2\", concepts: 10, response: .}'" 35)
echo "$R" | grep -qi "WELL\|concept\|10" && pass "R1: WELL standard query (jq)" || fail "R1" "$(echo "$R" | head -1)"

# R2: ESG 報告生成
echo "  [R2] ESG report generation..."
R=$(send_chat 18801 "run: echo '# ESG Report Q1 2026\n## Environmental\n- Carbon reduction: 15%\n## Social\n- WELL certification: Gold\n## Governance\n- Board diversity: 40%' | pandoc -f markdown -t html" 35)
echo "$R" | grep -qi "ESG\|html\|h1\|h2\|Environmental\|Carbon" && pass "R2: ESG report (pandoc)" || fail "R2" "$(echo "$R" | head -1)"

# R3: 室內空氣品質數據分析
echo "  [R3] IAQ data analysis..."
R=$(send_chat 18801 "run: echo '[{\"zone\":\"lobby\",\"pm25\":12,\"co2\":450},{\"zone\":\"office\",\"pm25\":8,\"co2\":680},{\"zone\":\"gym\",\"pm25\":15,\"co2\":820}]' | jq '.[] | select(.co2 > 600) | .zone'" 35)
echo "$R" | grep -qi "office\|gym" && pass "R3: IAQ analysis (jq filter)" || fail "R3" "$(echo "$R" | head -1)"

# R4: 建築能耗 YAML 處理
echo "  [R4] Building energy YAML..."
R=$(send_chat 18801 "run: echo 'building:\n  name: WoowTech HQ\n  eui: 85\n  certification: WELL Gold\n  leed: Platinum' | yq '.building.certification'" 35)
echo "$R" | grep -qi "WELL\|Gold" && pass "R4: Energy config (yq)" || fail "R4" "$(echo "$R" | head -1)"

# R5: K8s 監控健康建築系統
echo "  [R5] K8s monitoring..."
R=$(send_chat 18801 "run: kubectl get pods -A --no-headers | wc -l && echo 'nodes:' && kubectl get nodes --no-headers | wc -l" 35)
echo "$R" | grep -qi "[0-9]" && pass "R5: K8s cluster monitoring (kubectl)" || fail "R5" "$(echo "$R" | head -1)"

# R6: 綠建材資料庫查詢
echo "  [R6] Green material DB..."
R=$(send_chat 18801 "run: psql --version && echo '---' && redis-cli --version" 35)
echo "$R" | grep -qi "postgresql\|redis" && pass "R6: DB tools available (psql+redis-cli)" || fail "R6" "$(echo "$R" | head -1)"

# R7: WELL 文件下載與轉換
echo "  [R7] Document conversion..."
R=$(send_chat 18801 "run: echo '## WELL Feature A01: Air Quality\n### Intent\nEnsure clean air for occupants.\n### Requirements\n- PM2.5 < 15 μg/m³\n- CO2 < 800 ppm' | pandoc -f markdown -t plain" 35)
echo "$R" | grep -qi "Air Quality\|PM2.5\|CO2" && pass "R7: WELL doc conversion (pandoc)" || fail "R7" "$(echo "$R" | head -1)"

# R8: 網路診斷（IoT 感測器連線）
echo "  [R8] IoT network diagnostics..."
R=$(send_chat 18801 "run: dig +short google.com | head -1 && echo '---' && nmap --version | head -1" 35)
echo "$R" | grep -qi "nmap\|[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" && pass "R8: Network diagnostics (dig+nmap)" || fail "R8" "$(echo "$R" | head -1)"

# R9: ESG 合規文件搜尋
echo "  [R9] Compliance search..."
R=$(send_chat 18801 "run: rg --version | head -1 && echo '---' && fd --version" 35)
echo "$R" | grep -qi "ripgrep\|fd" && pass "R9: File search tools (rg+fd)" || fail "R9" "$(echo "$R" | head -1)"

# R10: WELL 認證進度報告
echo "  [R10] Certification status..."
R=$(send_chat 18801 "run: echo '{\"project\":\"WoowTech HQ\",\"well_level\":\"Gold\",\"features_achieved\":62,\"features_total\":72,\"progress\":86}' | jq '{project: .project, status: (if .progress >= 80 then \"On Track\" else \"At Risk\" end), progress: \"\(.progress)%\"}'" 35)
echo "$R" | grep -qi "On Track\|progress\|86\|WoowTech" && pass "R10: WELL progress report (jq)" || fail "R10" "$(echo "$R" | head -1)"

playwright-cli close 2>/dev/null

# ─────────────────────────────────────────────────
# INSTANCE 2: johhanlin-hermes (金融外匯)
# ─────────────────────────────────────────────────

sleep 2
playwright-cli open "http://localhost:18802" 2>/dev/null | head -1
sleep 2
playwright-cli fill e7 "woowtech" --submit 2>/dev/null | head -1
sleep 3

echo ""
echo ">> johhanlin-hermes: 金融業外匯交易"

# R11: 匯率即時查詢
echo "  [R11] FX rate query..."
R=$(send_chat 18802 "run: curl -s 'https://open.er-api.com/v6/latest/USD' | jq '{base: .base_code, TWD: .rates.TWD, JPY: .rates.JPY, EUR: .rates.EUR}'" 40)
echo "$R" | grep -qi "TWD\|JPY\|EUR\|base" && pass "R11: FX rates (curl+jq)" || fail "R11" "$(echo "$R" | head -1)"

# R12: 交易風險計算
echo "  [R12] Risk calculation..."
R=$(send_chat 18802 "run: echo '[{\"pair\":\"USD/TWD\",\"position\":1000000,\"entry\":31.5,\"stop_loss\":31.8},{\"pair\":\"EUR/USD\",\"position\":500000,\"entry\":1.085,\"stop_loss\":1.075}]' | jq '.[] | {pair: .pair, risk_amount: ((.stop_loss - .entry) * .position | fabs | floor)}'" 35)
echo "$R" | grep -qi "risk_amount\|USD.*TWD\|EUR" && pass "R12: Risk calculation (jq math)" || fail "R12" "$(echo "$R" | head -1)"

# R13: 交易記錄資料庫
echo "  [R13] Trade DB tools..."
R=$(send_chat 18802 "run: psql --version && echo '---trade_log schema---' && echo 'CREATE TABLE trade_log (id SERIAL, pair VARCHAR(10), direction VARCHAR(4), entry DECIMAL, exit_price DECIMAL, pnl DECIMAL, ts TIMESTAMP DEFAULT NOW());' | head -1" 35)
echo "$R" | grep -qi "postgresql\|CREATE\|trade" && pass "R13: Trade DB schema (psql)" || fail "R13" "$(echo "$R" | head -1)"

# R14: 外匯交易策略 YAML
echo "  [R14] FX strategy YAML..."
R=$(send_chat 18802 "run: echo 'strategy:\n  name: Momentum Breakout\n  pairs: [USD/TWD, EUR/USD, GBP/JPY]\n  timeframe: H4\n  risk_per_trade: 1.5%\n  max_daily_loss: 5%' | yq '.strategy.pairs'" 35)
echo "$R" | grep -qi "USD.*TWD\|EUR.*USD\|GBP.*JPY" && pass "R14: FX strategy (yq)" || fail "R14" "$(echo "$R" | head -1)"

# R15: 合規報告生成
echo "  [R15] Compliance report..."
R=$(send_chat 18802 "run: echo '# FX Trading Compliance Report\n## Daily Summary\n- Total trades: 15\n- Win rate: 67%\n- Max drawdown: 2.3%\n## Risk Limits\n- All within regulatory thresholds' | pandoc -f markdown -t html" 35)
echo "$R" | grep -qi "Compliance\|html\|trades\|drawdown" && pass "R15: Compliance report (pandoc)" || fail "R15" "$(echo "$R" | head -1)"

# R16: 市場新聞抓取
echo "  [R16] Market news fetch..."
R=$(send_chat 18802 "run: lynx -dump https://www.forexfactory.com/calendar 2>/dev/null | head -15 || lynx -dump https://example.com | head -5" 40)
echo "$R" | grep -qi "forex\|example\|Domain\|calendar\|news" && pass "R16: Market news (lynx)" || fail "R16" "$(echo "$R" | head -1)"

# R17: K8s 交易系統監控
echo "  [R17] Trading system monitor..."
R=$(send_chat 18802 "run: kubectl get pods -n johhanlin-hermes --no-headers && echo '---' && kubectl top pods -n johhanlin-hermes --no-headers 2>/dev/null || echo 'metrics not available'" 35)
echo "$R" | grep -qi "Running\|hermes" && pass "R17: K8s monitoring (kubectl)" || fail "R17" "$(echo "$R" | head -1)"

# R18: 交易系統網路延遲檢測
echo "  [R18] Latency check..."
R=$(send_chat 18802 "run: dig +short +stats google.com 2>&1 | tail -3 && echo '---' && nc -z -w3 hermes-redis-svc 6379 && echo 'Redis: CONNECTED'" 35)
echo "$R" | grep -qi "CONNECTED\|msec\|query\|[0-9]" && pass "R18: Latency check (dig+nc)" || fail "R18" "$(echo "$R" | head -1)"

# R19: Helm 部署管理
echo "  [R19] Helm management..."
R=$(send_chat 18802 "run: helm version --short && echo '---' && argocd version --client 2>&1 | head -1 && echo '---' && gh --version | head -1" 35)
echo "$R" | grep -qi "helm\|v3\|argocd\|gh" && pass "R19: DevOps tools (helm+argocd+gh)" || fail "R19" "$(echo "$R" | head -1)"

# R20: 多幣種組合分析
echo "  [R20] Portfolio analysis..."
R=$(send_chat 18802 "run: echo '[{\"pair\":\"USD/TWD\",\"weight\":0.4,\"ytd_return\":2.1},{\"pair\":\"EUR/USD\",\"weight\":0.35,\"ytd_return\":-1.5},{\"pair\":\"GBP/JPY\",\"weight\":0.25,\"ytd_return\":3.8}]' | jq '{total_pairs: length, weighted_return: ([.[] | .weight * .ytd_return] | add | . * 100 | round / 100), best_pair: (sort_by(-.ytd_return) | first | .pair)}'" 35)
echo "$R" | grep -qi "weighted_return\|best_pair\|GBP\|total" && pass "R20: Portfolio analysis (jq)" || fail "R20" "$(echo "$R" | head -1)"

playwright-cli close 2>/dev/null

# ─────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  RESULTS: $PASS pass / $FAIL fail (total $TOTAL)            ║"
RATE=$((PASS * 100 / TOTAL))
echo "║  Pass Rate: ${RATE}%                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
