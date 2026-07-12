# .env Fingerprint Sync — Test Matrix & Scoring

## Test Categories (10 tests, 10 points each = 100 total)

### A. 基礎功能 (Core Functionality) — 40 pts

| # | Test | Description | Points |
|---|------|-------------|--------|
| T1 | Baseline State | 有 OPENAI_API_KEY 時，model picker 顯示 OpenAI 群組 | 10 |
| T2 | Remove Key → Sync | 移除 OPENAI_API_KEY 後刷新，OpenAI 群組消失 | 10 |
| T3 | Add Key → Sync | 重新加入 OPENAI_API_KEY 後刷新，OpenAI 群組回來 | 10 |
| T4 | Model Call | 選擇 OpenAI model 後實際發送訊息並收到回覆 | 10 |

### B. 穩定度 (Stability) — 30 pts

| # | Test | Description | Points |
|---|------|-------------|--------|
| T5 | Round-trip 3x | 連續 3 次 add/remove cycle，每次都正確同步 | 10 |
| T6 | Rapid Toggle | 快速連續修改 .env 2 次後刷新，最終狀態正確 | 10 |
| T7 | Server Restart | Pod 重啟後 patch 仍存在，功能正常 | 10 |

### C. 邊緣條件 (Edge Cases) — 30 pts

| # | Test | Description | Points |
|---|------|-------------|--------|
| T8 | Empty .env | .env 完全清空（連 MINIMAX 也移除），model picker 不崩潰 | 10 |
| T9 | Invalid Key | 放入無效的 OPENAI_API_KEY，model picker 仍可列出（但 call 會失敗） | 10 |
| T10 | Multi-key Change | 同時新增 OPENAI + 移除 MINIMAX，model picker 正確反映 | 10 |

## Scoring

- PASS = 10/10
- PARTIAL = 5/10 (功能有效但有延遲或需多次刷新)
- FAIL = 0/10

Target: 100/100
