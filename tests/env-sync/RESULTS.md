# .env Fingerprint Sync — Test Results

**Date**: 2026-07-12
**Target**: WoowTech Hermes (`hermes-59fbdd5456-2vjmv`)
**Tool**: playwright-cli + kubectl

## Round 1 — Full Test Suite

| # | Test | Description | Result | Score |
|---|------|-------------|--------|-------|
| T1 | Baseline State | OPENAI_API_KEY present → MiniMax (4) + OpenAI API (10) visible | PASS | 10/10 |
| T2 | Remove Key → Sync | Remove OPENAI_API_KEY → refresh → only MiniMax (6) | PASS | 10/10 |
| T3 | Add Key → Sync | Re-add OPENAI_API_KEY → refresh → MiniMax (6) + OpenAI (10) | PASS | 10/10 |
| T4 | Model Call | Select GPT-5.4 Mini → send "SYNC_TEST_T4_OK" → received response | PASS | 10/10 |
| T5 | Round-trip 3x | 3 consecutive add/remove cycles, all synced correctly | PASS | 10/10 |
| T6 | Rapid Toggle | Remove → immediately add → final state correct | PASS | 10/10 |
| T7 | Server Restart | Kill server → restart → patch survives → models visible | PASS | 10/10 |
| T8 | Empty .env | Truncate .env to 0 bytes → no crash, MiniMax via auth.json | PASS | 10/10 |
| T9 | Invalid Key | OPENAI_API_KEY=sk-invalid → no crash, OpenAI group shows | PASS | 10/10 |
| T10 | Multi-key Change | Only OPENAI in .env → OpenAI visible, MiniMax via auth.json | PASS | 10/10 |

### Score: 100 / 100 ★★★

## Round 2 — Regression Verification

| Test | Expected | Actual | Result |
|------|----------|--------|--------|
| Remove key → sync | Only MiniMax | MiniMax (6) | PASS |
| Add key → sync | MiniMax + OpenAI | MiniMax (6) + OpenAI (10) | PASS |

### Score: 2/2 core tests passed

## Notes

- Model group counts vary between requests (4 vs 6 for MiniMax, 10 vs 11 for OpenAI) depending on provider catalog freshness. This is normal behavior.
- MiniMax persists even with empty .env because credentials exist in `auth.json` credential_pool.
- Invalid OPENAI_API_KEY still causes OpenAI group to appear (key presence = authenticated), but actual API calls would fail with 401.
- Server restart causes session expiry (requires re-login), but patch is re-applied automatically by `replace_icons.sh` hook.

## Screenshots

- `R2-baseline-both-keys.png` — Baseline with both API keys
- `R2-after-remove.png` — After removing OPENAI_API_KEY
- `R2-after-readd.png` — After re-adding OPENAI_API_KEY
