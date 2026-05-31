# Provider Test Results — 2026-05-31

## Test Script
`/tmp/test_providers.py` — Python script reading `.env` directly, testing each via `urllib.request`

## Results

| # | Provider | Model | Status | Detail |
|---|----------|-------|--------|--------|
| 1 | v2.aicodee.com | MiniMax-M2.7-highspeed | ❌ 403 | 用户额度不足, 剩余额度: $0.000000 |
| 2 | minimax-cn | MiniMax-M2.7 | ❌ 429 | usage limit exceeded (2056) |
| 3 | DeepSeek 直连 | deepseek-chat (→v4-flash) | ✅ 200 | Fast response (~0.7s) |
| 4 | OpenRouter | deepseek/deepseek-v4-flash | ✅ 200 | Model: deepseek/deepseek-v4-flash-20260423 |

## Pricing (from OpenRouter API)
- **deepseek/deepseek-v4-flash**: $0.0983/M input, $0.1966/M output
- **deepseek/deepseek-v4-flash:free**: Free (rate-limited)

## OpenRouter Providers for deepseek-v4-flash
- Baidu Qianfan (FP8, CN region)
- DeepInfra (FP4, US region)
- GMICloud (US region)

## Current Config After Session
- Primary: openrouter / deepseek/deepseek-v4-flash:free
- Fallback: minimax-cn / MiniMax-M2.7 (stale — 429)
