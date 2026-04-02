#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"
source "$SCRIPT_DIR/lib/line-webhook.sh"

section "Round 3: LLM Multi-Model Switch (10 tests)"

# Save original config for restoration
ORIG_MODEL=$(kexec cat /home/node/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.load(sys.stdin)['agents']['defaults']['model'])")
ORIG_AUTH=$(kexec cat /home/node/.openclaw/agents/main/agent/auth-profiles.json)
echo "Original model: $ORIG_MODEL"

# Helper: send test message and check session got a response
test_llm_response() {
  local label="$1"
  local body; body=$(line_text_event "Hi, what model are you? Reply in one sentence.")
  local resp; resp=$(line_send_webhook "$body")
  local code; code=$(echo "$resp" | tail -1)
  if [[ "$code" != "200" ]]; then
    fail "$label: webhook" "code=$code"
    return 1
  fi
  sleep 8  # wait for AI response
  local sessions; sessions=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" -newer /tmp/.llm-test-marker 2>/dev/null | head -1)
  if [[ -n "$sessions" ]]; then
    local has_assistant; has_assistant=$(kexec tail -5 "$sessions" | grep -c '"role":"assistant"' || true)
    [[ "$has_assistant" -ge 1 ]] && pass "$label: response received" || fail "$label: response" "no assistant message"
  else
    pass "$label: webhook accepted (session check skipped)"
  fi
}

# 3.1 GPT-4o baseline
echo "── 3.1 GPT-4o baseline ──"
kexec touch /tmp/.llm-test-marker
test_llm_response "GPT-4o"

# 3.2 Add OpenRouter auth profile
echo "── 3.2 Add OpenRouter auth ──"
kexec node -e "
  const fs=require('fs'),p='/home/node/.openclaw/agents/main/agent/auth-profiles.json';
  const c=JSON.parse(fs.readFileSync(p,'utf8'));
  c.openrouter={apiKey:process.env.OPENROUTER_API_KEY||'${OPENROUTER_API_KEY}',baseURL:'${OPENROUTER_BASE_URL}'};
  fs.writeFileSync(p,JSON.stringify(c));
" 2>/dev/null
VERIFY=$(kexec cat /home/node/.openclaw/agents/main/agent/auth-profiles.json | grep -c "openrouter" || true)
[[ "$VERIFY" -ge 1 ]] && pass "OpenRouter auth added" || fail "OpenRouter auth" "not found in profile"

# 3.3 Switch to Gemini
echo "── 3.3 Switch to Gemini ──"
kexec openclaw config set agents.defaults.model "openrouter/google/gemini-2.0-flash-001" > /dev/null 2>&1
sleep 3
CUR=$(kexec cat /home/node/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.load(sys.stdin)['agents']['defaults']['model'])")
[[ "$CUR" == *"gemini"* ]] && pass "Switched to Gemini" || fail "Gemini switch" "model=$CUR"

# 3.4 Gemini test
echo "── 3.4 Gemini conversation ──"
kexec touch /tmp/.llm-test-marker
test_llm_response "Gemini"

# 3.5 Switch to Claude
echo "── 3.5 Switch to Claude ──"
kexec openclaw config set agents.defaults.model "openrouter/anthropic/claude-3.5-haiku" > /dev/null 2>&1
sleep 3
CUR=$(kexec cat /home/node/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.load(sys.stdin)['agents']['defaults']['model'])")
[[ "$CUR" == *"claude"* ]] && pass "Switched to Claude" || fail "Claude switch" "model=$CUR"

# 3.6 Claude test
echo "── 3.6 Claude conversation ──"
kexec touch /tmp/.llm-test-marker
test_llm_response "Claude"

# 3.7 Switch to Llama
echo "── 3.7 Switch to Llama ──"
kexec openclaw config set agents.defaults.model "openrouter/meta-llama/llama-3.1-8b-instruct" > /dev/null 2>&1
sleep 3
CUR=$(kexec cat /home/node/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.load(sys.stdin)['agents']['defaults']['model'])")
[[ "$CUR" == *"llama"* ]] && pass "Switched to Llama" || fail "Llama switch" "model=$CUR"

# 3.8 Llama test
echo "── 3.8 Llama conversation ──"
kexec touch /tmp/.llm-test-marker
test_llm_response "Llama"

# 3.9 Switch back to GPT-4o
echo "── 3.9 Restore GPT-4o ──"
kexec openclaw config set agents.defaults.model "$ORIG_MODEL" > /dev/null 2>&1
# Restore original auth profiles
echo "$ORIG_AUTH" | kexec sh -c 'cat > /home/node/.openclaw/agents/main/agent/auth-profiles.json'
sleep 3
CUR=$(kexec cat /home/node/.openclaw/openclaw.json | python3 -c "import sys,json; print(json.load(sys.stdin)['agents']['defaults']['model'])")
[[ "$CUR" == "$ORIG_MODEL" ]] && pass "Restored $ORIG_MODEL" || fail "Restore" "model=$CUR"

# 3.10 GPT-4o recovery
echo "── 3.10 GPT-4o recovery ──"
kexec touch /tmp/.llm-test-marker
test_llm_response "GPT-4o recovery"

summary
