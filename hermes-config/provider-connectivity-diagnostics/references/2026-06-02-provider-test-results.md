# Provider Test Results — 2026-06-02

## Test Script
直接用 curl 测试各 provider，无需写脚本：
```bash
source ~/.hermes/.env
curl -s --max-time 10 -X POST "<provider_url>/chat/completions" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```

## Results（2026-06-02晚实测）

| Provider | 模型 | Status | 响应 |
|----------|------|--------|------|
| MiniMax CN (api.minimaxi.com/anthropic) | MiniMax-M2.7 | ❌ 429 | usage limit exceeded (2056) — 额度耗尽 |
| DeepSeek 直连 (api.deepseek.com) | deepseek-v4-flash | ❌ 401 | Authentication Fails, api key invalid |
| Cerebras (api.cerebras.ai/v1) | llama-3.3-70b | ❌ 401 | Wrong API Key |
| Groq (api.groq.com/openai/v1) | llama-3.3-70b-versatile | ❌ 403 | Forbidden |
| **OpenRouter** (openrouter.ai/api/v1) | deepseek/deepseek-v4-flash | ✅ 200 | $0.0000013173/call |
| **OpenRouter** | google/gemma-4-31b-it:free | ✅ 200 | 免费，262K context |

## 关键发现

1. **OpenRouter + DeepSeek 是当前唯一可靠可用方案**（成本极低）
2. **MiniMax 429 不是 key 问题**：key 有效，但账户额度耗尽（2056次请求上限）
3. **DeepSeek 401 = key 本身无效**：key 整个失效，需重新获取
4. **Groq 403**：模型名格式问题，Groq 用 `llama-3.3-70b` 不是 `llama-3.3-70b-versatile`
5. **Cerebras key 整个失效**（csk-585933...格式，41位）

## OpenRouter 免费模型（2026-06-02实测）

继续有效的免费模型：
- `google/gemma-4-31b-it:free` — 262K ctx
- `nvidia/nemotron-3-super-120b-a12b:free` — 1M ctx
- `openai/gpt-oss-120b:free` — 131K ctx
- `z-ai/glm-4.5-air:free` — 131K ctx

之前可用但现在429的：
- `deepseek/deepseek-v4-flash:free` — 1M ctx，429限流
- `qwen/qwen3-coder:free` — 1M ctx，429限流
