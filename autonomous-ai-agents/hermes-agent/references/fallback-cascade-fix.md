# Fallback Cascade Fix — Stop the Channel Blackout

## The Problem

When `fallback_providers` contains many OpenRouter free models, a single primary model failure triggers a cascade:

1. aicodee 403/429 → ollama (fails) → OpenRouter free model 1 → **429 rate limit**
2. → OpenRouter free model 2 → **429 rate limit**
3. → ... (cascade through all free models)
4. Gateway rapidly retrying, holding message-processing slots
5. **Messaging channel backs up → QQ/WeChat bots go completely silent**
6. Active sessions drop to 0. Bot shows "灵魂不在线，请检查主机服务部署环境"

This is what caused the repeated cascade failures you saw in May 2026.

## The Fix

**Maximum 2 fallback providers. Short chain. Then STOP.**

### Recommended config

```yaml
# config.yaml
providers:
  deepseek:
    api_key: <your-deepseek-key>
    base_url: https://api.deepseek.com/v1

fallback_providers:
  - provider: deepseek
    model: deepseek-v4-flash    # cheap, stable, paid usage
  - provider: ollama
    model: qwen2.5:latest       # local on Mac mini, never goes down
```

**Rule**: Primary → one cloud fallback → one local fallback → STOP.

Do NOT add many OpenRouter free models to the fallback chain. They share per-IP quota and cascade exhausts them all.

## DeepSeek Setup

DeepSeek is OpenAI-compatible. Use the OpenAI format endpoint:

- **Base URL**: `https://api.deepseek.com/v1` (NOT `/v1/chat/completions`)
- **Model**: `deepseek-v4-flash` (cheapest, fastest, enough for general use)
- **API key**: purchased, usage-based billing

## Why This Works

- DeepSeek is paid → no rate limit under normal use
- Ollama is local (Mac mini 192.168.0.4) → no external dependency
- Only 2 steps in the chain → fast fallback, no cascade
- Messaging channel stays clear even when model fails

## Signs of Cascade Happening

```
⚠️ Non-retryable error (HTTP 403) — trying fallback...
🔄 Primary model failed — switching to fallback: openrouter/free via openrouter
⚠️ Rate limited — switching to fallback provider...
🔄 Primary model failed — switching to fallback: inclusionai/ling-2.6-1t:free via openrouter
⚠️ Rate limited — switching to fallback provider...
[repeats rapidly]
```

If you see this pattern → simplify your `fallback_providers` immediately.
