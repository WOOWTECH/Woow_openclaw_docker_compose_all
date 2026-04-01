# MiniMax-M2.7 Intelligence Boundary Analysis Report

**Date**: 2026-04-01
**Model**: `minimax/MiniMax-M2.7`
**API Key**: `sk-cp-c-h9FWEhxj...` (new token, validated working)
**Platform**: OpenClaw v2026.3.31 via Nerve WebGUI
**Test Method**: Playwright automated browser tests, 19 designed / 11 completed

---

## API Key Verification

**Status: WORKING**

Model correctly identifies itself:
> 我是 **Woowtech AI Assistant**，運行在 OpenClaw 平台上。
> 型號：`minimax/MiniMax-M2.7`（預設模型）

Usage counter active: $2.52 → $2.60 during testing ($0.08 for 11 queries).

---

## Test Results (Screenshot-Verified)

| # | Test | Category | Difficulty | Result | Detail |
|---|------|----------|:----------:|:------:|--------|
| 1 | api_key_basic_chat | API驗證 | ★☆☆☆☆ | ✅ | Identifies as MiniMax-M2.7, responds in Traditional Chinese |
| 2 | simple_math | 數學推理 | ★☆☆☆☆ | ✅ | 17×23 = **391** (correct) |
| 3 | word_problem | 數學推理 | ★★☆☆☆ | ✅ | Net flow 3-1=2 tons/hr, 20/2 = **10** hours (correct) |
| 4 | logic_puzzle | 邏輯推理 | ★★★☆☆ | ✅ | Correct JSON: 混合標籤→紅球, 紅球標籤→藍球, 藍球標籤→混合 |
| 5 | compound_interest | 數學推理 | ★★★☆☆ | ✅ | 100000 × 1.05³ = **115762.50** (correct) |
| 6 | probability | 數學推理 | ★★★★☆ | ❌ | Answered **25/102** — used C(26,2) instead of C(13,2). Confused 13 hearts with 26 red cards. Correct: **1/17** |
| 7 | code_palindrome | 程式生成 | ★★☆☆☆ | ✅ | `s.lower().replace(" ",""); return s == s[::-1]` — clean, correct |
| 8 | code_two_sum | 程式生成 | ★★★☆☆ | ✅ | Hash map O(n): `seen={}`, `diff=target-n`, `if diff in seen` — correct |
| 9 | code_lru_cache | 程式生成 | ★★★★☆ | ✅ | `OrderedDict` with `move_to_end`, `popitem(last=False)` — correct O(1) |
| 10 | translation | 語言能力 | ★★☆☆☆ | ✅ | EN: "Artificial Intelligence is changing the way the world operates." JP: "人工知能は世界のあり方を変えている。" KR: "인공지능이 세계가 작동하는 방식을 변화시키고 있다." — all accurate |
| 11 | context_understanding | 語言能力 | ★★★☆☆ | ⏱️ | Timed out at 65s — model may have been processing too long or hit rate limit |

Tests 12-19 not executed (Playwright script crashed on test 12 due to UI state issue after timeout).

---

## Score Summary

| Metric | Value |
|--------|-------|
| Tests Completed | 11 / 19 |
| Passed | **9** (82%) |
| Failed | **1** (9%) — probability/combinatorics |
| Timeout | **1** (9%) — language ambiguity analysis |
| Avg Response Time | ~14s |

---

## By Difficulty Level

| Level | Tests | Pass | Rate | Assessment |
|:-----:|:-----:|:----:|:----:|------------|
| ★☆☆☆☆ L1 | 2 | 2 | 100% | **Solid** — basic chat and arithmetic |
| ★★☆☆☆ L2 | 3 | 3 | 100% | **Solid** — word problems, basic code, translation |
| ★★★☆☆ L3 | 4 | 3 | 75% | **Good** — logic puzzles, compound math, algorithm code OK; language ambiguity timed out |
| ★★★★☆ L4 | 2 | 1 | 50% | **Boundary** — LRU Cache code OK; combinatorics FAILED |
| ★★★★★ L5 | 0 | — | — | Not tested |

---

## By Category

### Math & Logic (5 tests)
| Result | Detail |
|--------|--------|
| ✅ L1 arithmetic | Perfect |
| ✅ L2 word problem | Correct reasoning chain |
| ✅ L3 logic puzzle | Excellent deductive reasoning with JSON output |
| ✅ L3 compound interest | Correct formula application |
| ❌ L4 probability | **Critical error**: confused hearts (13) with red cards (26). Thinking trace shows `C(26,2)` — a card counting mistake, not a formula error |

**Assessment**: Strong at formula application and deduction. **Weak at combinatorics** — specifically confusing subsets of a domain (hearts vs. red suits).

### Code Generation (3 tests)
| Result | Detail |
|--------|--------|
| ✅ L2 palindrome | Clean, Pythonic, correct |
| ✅ L3 Two Sum | Correct O(n) hash map approach |
| ✅ L4 LRU Cache | OrderedDict-based, correct O(1) implementation |

**Assessment**: **Excellent** code generation. Handles classic algorithm problems well at L2-L4. Demonstrates understanding of time complexity requirements. Code is clean and idiomatic.

### Language (2 tests)
| Result | Detail |
|--------|--------|
| ✅ L2 translation | Accurate EN/JP/KR, natural phrasing |
| ⏱️ L3 ambiguity | Timeout — may struggle with open-ended analysis |

**Assessment**: Multi-language capability is strong. Open-ended linguistic analysis may be slower or less reliable.

---

## Intelligence Boundary Map

```
Capability Ceiling Estimate: Level 3.5 / 5

         L1      L2      L3      L4      L5
         │       │       │       │       │
Math     ████████████████████████████░░░░░░  (fails at L4 combinatorics)
Code     ████████████████████████████████░░  (passes L4 LRU Cache)
Logic    ████████████████████████░░░░░░░░░░  (passes L3, untested L4+)
Language ████████████████████░░░░░░░░░░░░░░  (passes L2, timeout L3)
Tools    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (not tested in this run)
```

---

## Strengths

1. **Code generation** — Strongest category. Produces clean, correct, idiomatic Python up to L4 (LRU Cache). This is commercially valuable for programming assistance use cases.
2. **Structured output** — Reliably produces JSON when asked. Good for API integration scenarios.
3. **Multi-language** — Accurate Traditional Chinese ↔ English ↔ Japanese ↔ Korean. Key for Woowtech's Asia-Pacific market.
4. **Formula application** — Correctly applies compound interest, arithmetic, and net-rate calculations.
5. **Deductive logic** — Solves the classic mislabeled boxes puzzle correctly with clear reasoning.
6. **Response speed** — Average ~14s per response is acceptable for chat UX.

## Weaknesses

1. **Combinatorics / Probability** — The hearts-vs-red-cards confusion (C(26,2) instead of C(13,2)) reveals a **domain knowledge gap** in card game combinatorics. This is a known weakness class for mid-tier models.
2. **Open-ended analysis** — Timed out on linguistic ambiguity analysis. May struggle with tasks that require exhaustive enumeration without clear stopping criteria.
3. **Untested areas** — Spatial reasoning, counterfactual thinking, adversarial trick questions, and complex multi-tool orchestration were not covered due to test script crash.

## Risk Assessment for Enterprise Use

| Use Case | Risk Level | Notes |
|----------|:----------:|-------|
| Customer service chat | LOW | Strong language + memory integration |
| Smart home control (HA) | LOW | Tool calling works well from Round 1-5 |
| Code assistance | LOW | Excellent up to L4 |
| Odoo ERP queries | LOW | Correctly generates xmlrpc scripts |
| Financial calculations | MEDIUM | Basic math OK, complex probability fails |
| Data analysis requiring statistics | HIGH | Combinatorics errors could produce wrong conclusions |
| Legal/medical reasoning | HIGH | Open-ended analysis may timeout or be incomplete |

---

## Recommendation

MiniMax-M2.7 is **adequate for the current Woowtech deployment** covering:
- Chat in Traditional Chinese / English / Japanese / Korean
- Smart home automation via HA tools
- Odoo ERP queries via exec
- Basic programming assistance
- Memory-augmented conversations

**For tasks requiring advanced mathematics (statistics, probability) or deep analytical reasoning**, consider routing to a stronger model (GPT-4o, Claude) via the multi-model config, or adding a disclaimer in SOUL.md that the agent should use `exec` with Python for calculations rather than attempting them natively.

---

## Not Yet Tested (Planned for Next Round)

| Test | Category | Difficulty | Reason Skipped |
|------|----------|:----------:|----------------|
| creative_writing | 語言能力 | ★★★☆☆ | Script crashed |
| tool_simple_chain | 工具編排 | ★★★☆☆ | Script crashed |
| tool_multi_step | 工具編排 | ★★★★☆ | Script crashed |
| tool_complex_reasoning | 工具編排 | ★★★★★ | Script crashed |
| spatial_reasoning | 高階推理 | ★★★★☆ | Script crashed |
| counterfactual | 高階推理 | ★★★★☆ | Script crashed |
| meta_reasoning | 高階推理 | ★★★★★ | Script crashed |
| adversarial_math | 高階推理 | ★★★★★ | Script crashed |

---

*Screenshots archived at `/tmp/intelligence-*.png` (12 files)*
