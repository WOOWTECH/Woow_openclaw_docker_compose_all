#!/bin/bash
# .env Fingerprint Sync — Automated Test Suite
# Uses playwright-cli for frontend verification + kubectl for .env manipulation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/k8s-helpers.sh"

RESULTS_FILE="$SCRIPT_DIR/results.json"
SCORE=0
TOTAL=0
declare -A TEST_RESULTS

# ─── Helpers ───────────────────────────────────────────────────────────

log()  { echo -e "\n\033[1;36m══════ $1 ══════\033[0m"; }
pass() { echo -e "\033[1;32m  ✓ PASS: $1\033[0m"; TEST_RESULTS["$2"]="PASS"; SCORE=$((SCORE+10)); TOTAL=$((TOTAL+10)); }
fail() { echo -e "\033[1;31m  ✗ FAIL: $1\033[0m"; TEST_RESULTS["$2"]="FAIL"; TOTAL=$((TOTAL+10)); }
partial() { echo -e "\033[1;33m  ~ PARTIAL: $1\033[0m"; TEST_RESULTS["$2"]="PARTIAL"; SCORE=$((SCORE+5)); TOTAL=$((TOTAL+10)); }

# Get model groups from the model picker (returns text like "▶ MiniMax (4)")
get_model_groups() {
  # Reload the page first to trigger fresh cache check
  playwright-cli reload 2>&1 >/dev/null
  sleep 3

  # Find and click the model picker button
  local snapshot
  snapshot=$(playwright-cli --raw snapshot --depth=10 2>&1)

  # Find the model button ref
  local model_btn_ref
  model_btn_ref=$(echo "$snapshot" | grep -oP 'button "(?:Minimax|MiniMax|OpenAI|Select)[^"]*" \[ref=(\w+)\]' | head -1 | grep -oP 'ref=\K\w+')

  if [ -z "$model_btn_ref" ]; then
    echo "ERROR: Could not find model picker button"
    return 1
  fi

  # Click to open model picker
  playwright-cli click "$model_btn_ref" 2>&1 >/dev/null
  sleep 2

  # Get snapshot and extract group names
  local picker_snapshot
  picker_snapshot=$(playwright-cli --raw snapshot --depth=10 2>&1)

  # Extract lines like "▶ MiniMax (4)" or "▶ OpenAI API (10)"
  local groups
  groups=$(echo "$picker_snapshot" | grep -oP '▶\s+[^(]+\(\d+\)' | sort)

  # Close picker
  playwright-cli press Escape 2>&1 >/dev/null
  sleep 0.5

  echo "$groups"
}

# Check if groups contain a specific provider
has_group() {
  local groups="$1"
  local provider="$2"
  echo "$groups" | grep -qi "$provider"
}

# Count total groups
count_groups() {
  local groups="$1"
  echo "$groups" | grep -c "▶" 2>/dev/null || echo "0"
}

# ─── Test Execution ───────────────────────────────────────────────────

log "SETUP: Ensuring baseline state (MINIMAX + OPENAI)"
env_set_both
sleep 2

# ─── T1: Baseline State ──────────────────────────────────────────────
log "T1: Baseline State — with OPENAI_API_KEY"
groups=$(get_model_groups)
echo "  Model groups: $groups"
if has_group "$groups" "OpenAI"; then
  pass "OpenAI group visible with API key present" "T1"
else
  fail "OpenAI group NOT visible despite API key being set" "T1"
fi

# ─── T2: Remove Key → Sync ───────────────────────────────────────────
log "T2: Remove OPENAI_API_KEY → Sync"
env_set_minimax_only
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
if has_group "$groups" "OpenAI"; then
  fail "OpenAI group still visible after removing key" "T2"
else
  if has_group "$groups" "MiniMax"; then
    pass "OpenAI removed, MiniMax remains" "T2"
  else
    fail "Both groups disappeared" "T2"
  fi
fi

# ─── T3: Add Key → Sync ──────────────────────────────────────────────
log "T3: Re-add OPENAI_API_KEY → Sync"
env_set_both
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
if has_group "$groups" "OpenAI" && has_group "$groups" "MiniMax"; then
  pass "Both MiniMax and OpenAI groups visible after re-adding key" "T3"
elif has_group "$groups" "OpenAI"; then
  partial "OpenAI visible but MiniMax missing" "T3"
else
  fail "OpenAI group NOT visible after re-adding key" "T3"
fi

# ─── T4: Model Call ───────────────────────────────────────────────────
log "T4: Model Call — actually use an OpenAI model"
# First expand OpenAI group and select a model
groups_snapshot=$(playwright-cli --raw snapshot --depth=10 2>&1)
model_btn_ref=$(echo "$groups_snapshot" | grep -oP 'button "(?:Minimax|MiniMax|OpenAI|Select)[^"]*" \[ref=(\w+)\]' | head -1 | grep -oP 'ref=\K\w+')
playwright-cli click "$model_btn_ref" 2>&1 >/dev/null
sleep 1

# Click OpenAI group to expand
picker=$(playwright-cli --raw snapshot --depth=10 2>&1)
openai_group_ref=$(echo "$picker" | grep -P '▶\s+OpenAI' | grep -oP 'ref=\K\w+' | head -1)
if [ -n "$openai_group_ref" ]; then
  playwright-cli click "$openai_group_ref" 2>&1 >/dev/null
  sleep 1

  # Find and click gpt-4.1-mini or any gpt model
  expanded=$(playwright-cli --raw snapshot --depth=12 2>&1)
  gpt_ref=$(echo "$expanded" | grep -iP 'gpt.*mini' | grep -oP 'ref=\K\w+' | head -1)
  if [ -z "$gpt_ref" ]; then
    gpt_ref=$(echo "$expanded" | grep -iP 'gpt' | grep -oP 'ref=\K\w+' | head -1)
  fi

  if [ -n "$gpt_ref" ]; then
    playwright-cli click "$gpt_ref" 2>&1 >/dev/null
    sleep 1

    # Type a test message in the chat input
    chat_snapshot=$(playwright-cli --raw snapshot --depth=10 2>&1)
    chat_ref=$(echo "$chat_snapshot" | grep -P 'textbox|textarea|contenteditable' | grep -oP 'ref=\K\w+' | head -1)

    if [ -n "$chat_ref" ]; then
      playwright-cli fill "$chat_ref" 'Reply with ONLY: SYNC_TEST_OK' 2>&1 >/dev/null
      playwright-cli press Enter 2>&1 >/dev/null

      # Wait for response
      sleep 15

      response=$(playwright-cli --raw snapshot --depth=10 2>&1)
      if echo "$response" | grep -q "SYNC_TEST_OK"; then
        pass "Model responded with expected text" "T4"
      else
        partial "Message sent but response not found in snapshot" "T4"
      fi
    else
      fail "Could not find chat input" "T4"
    fi
  else
    fail "Could not find any GPT model in expanded OpenAI group" "T4"
  fi
else
  fail "Could not find OpenAI group to expand" "T4"
fi

# ─── T5: Round-trip 3x ───────────────────────────────────────────────
log "T5: Round-trip 3x (add/remove cycle)"
t5_pass=0
for i in 1 2 3; do
  echo "  Cycle $i/3: removing key..."
  env_set_minimax_only
  sleep 2
  groups=$(get_model_groups)
  if has_group "$groups" "OpenAI"; then
    echo "    FAIL: OpenAI still visible after remove (cycle $i)"
  else
    echo "    OK: OpenAI removed (cycle $i)"

    echo "  Cycle $i/3: adding key..."
    env_set_both
    sleep 2
    groups=$(get_model_groups)
    if has_group "$groups" "OpenAI"; then
      echo "    OK: OpenAI restored (cycle $i)"
      t5_pass=$((t5_pass+1))
    else
      echo "    FAIL: OpenAI not restored after add (cycle $i)"
    fi
  fi
done
if [ "$t5_pass" -eq 3 ]; then
  pass "All 3 round-trips succeeded" "T5"
elif [ "$t5_pass" -ge 2 ]; then
  partial "$t5_pass/3 round-trips succeeded" "T5"
else
  fail "Only $t5_pass/3 round-trips succeeded" "T5"
fi

# ─── T6: Rapid Toggle ────────────────────────────────────────────────
log "T6: Rapid Toggle — 2 quick changes, check final state"
env_set_minimax_only  # remove
sleep 0.5
env_set_both          # add back immediately
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
if has_group "$groups" "OpenAI" && has_group "$groups" "MiniMax"; then
  pass "Final state correct after rapid toggle" "T6"
else
  fail "Final state incorrect after rapid toggle" "T6"
fi

# ─── T7: Server Restart ──────────────────────────────────────────────
log "T7: Server Restart — verify patch survives"
# Kill the server process, let it restart
kexec bash -c 'python3 -c "import os,signal; os.kill(1, signal.SIGTERM)"' 2>/dev/null || true
echo "  Waiting for pod restart..."
sleep 20

# Check if pod is running
pod_status=$(kubectl --context "$CTX" -n "$NS" get pod "$POD" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
if [ "$pod_status" != "Running" ]; then
  echo "  Waiting longer for pod..."
  sleep 20
  pod_status=$(kubectl --context "$CTX" -n "$NS" get pod "$POD" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
fi

if [ "$pod_status" = "Running" ]; then
  # Check patches still applied
  patch_count=$(kexec grep -c "_get_env_file_path" /app/api/config.py 2>/dev/null || echo "0")
  if [ "$patch_count" -gt 0 ]; then
    # Reload page and check
    playwright-cli reload 2>&1 >/dev/null
    sleep 5
    groups=$(get_model_groups)
    echo "  Model groups: $groups"
    if has_group "$groups" "OpenAI" || has_group "$groups" "MiniMax"; then
      pass "Patch survived restart, models visible" "T7"
    else
      partial "Patch survived but models not loading yet" "T7"
    fi
  else
    fail "Patches not found after restart" "T7"
  fi
else
  fail "Pod not running after restart: $pod_status" "T7"
fi

# ─── T8: Empty .env ──────────────────────────────────────────────────
log "T8: Empty .env — no keys at all"
env_set_empty
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
group_count=$(count_groups "$groups")
if [ "$group_count" -eq 0 ]; then
  # No groups at all could be valid if all require API keys
  pass "No model groups with empty .env (expected behavior)" "T8"
elif ! has_group "$groups" "OpenAI"; then
  pass "No OpenAI group with empty .env, other groups may exist" "T8"
else
  fail "OpenAI group still showing with empty .env" "T8"
fi

# ─── T9: Invalid Key ─────────────────────────────────────────────────
log "T9: Invalid OPENAI_API_KEY"
env_set_invalid_openai
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
# Invalid key should still show OpenAI models (auth appears valid from .env perspective)
# but actual calls would fail - we just verify the picker doesn't crash
if [ -n "$groups" ]; then
  pass "Model picker works with invalid key (no crash)" "T9"
else
  fail "Model picker failed/empty with invalid key" "T9"
fi

# ─── T10: Multi-key Change ───────────────────────────────────────────
log "T10: Multi-key Change — OPENAI only (remove MINIMAX)"
env_set_openai_only
sleep 2
groups=$(get_model_groups)
echo "  Model groups: $groups"
if has_group "$groups" "OpenAI"; then
  if ! has_group "$groups" "MiniMax"; then
    pass "Only OpenAI group visible (MiniMax correctly removed)" "T10"
  else
    partial "OpenAI visible but MiniMax still showing" "T10"
  fi
else
  fail "OpenAI group not visible with OPENAI-only .env" "T10"
fi

# ─── Restore original state ──────────────────────────────────────────
log "CLEANUP: Restoring original .env"
env_set_both

# ─── Summary ──────────────────────────────────────────────────────────
log "TEST RESULTS SUMMARY"
echo ""
printf "  %-5s %-45s %s\n" "Test" "Description" "Result"
printf "  %-5s %-45s %s\n" "----" "--------------------------------------------" "-------"
printf "  %-5s %-45s %s\n" "T1"  "Baseline (key present → OpenAI visible)"     "${TEST_RESULTS[T1]:-N/A}"
printf "  %-5s %-45s %s\n" "T2"  "Remove key → OpenAI disappears"              "${TEST_RESULTS[T2]:-N/A}"
printf "  %-5s %-45s %s\n" "T3"  "Add key → OpenAI reappears"                  "${TEST_RESULTS[T3]:-N/A}"
printf "  %-5s %-45s %s\n" "T4"  "Model call (GPT responds)"                   "${TEST_RESULTS[T4]:-N/A}"
printf "  %-5s %-45s %s\n" "T5"  "Round-trip 3x stability"                     "${TEST_RESULTS[T5]:-N/A}"
printf "  %-5s %-45s %s\n" "T6"  "Rapid toggle final state"                    "${TEST_RESULTS[T6]:-N/A}"
printf "  %-5s %-45s %s\n" "T7"  "Server restart patch survives"               "${TEST_RESULTS[T7]:-N/A}"
printf "  %-5s %-45s %s\n" "T8"  "Empty .env (no crash)"                       "${TEST_RESULTS[T8]:-N/A}"
printf "  %-5s %-45s %s\n" "T9"  "Invalid key (no crash)"                      "${TEST_RESULTS[T9]:-N/A}"
printf "  %-5s %-45s %s\n" "T10" "Multi-key change (OPENAI only)"              "${TEST_RESULTS[T10]:-N/A}"
echo ""
echo -e "  \033[1mSCORE: $SCORE / $TOTAL\033[0m"
echo ""

if [ "$SCORE" -eq "$TOTAL" ]; then
  echo -e "  \033[1;32m★★★ PERFECT SCORE ★★★\033[0m"
elif [ "$SCORE" -ge 80 ]; then
  echo -e "  \033[1;33m★★ GOOD — minor issues to fix\033[0m"
else
  echo -e "  \033[1;31m★ NEEDS WORK — significant issues found\033[0m"
fi
