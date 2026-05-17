# Provider & Model Discovery Guide

## Two Classes of Providers

Hermes has two fundamentally different types of model providers:

### 1. Direct API Providers (API Key)
- Configured via `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, etc. in `.env`
- Talk directly to the provider's API endpoint (e.g. `api.deepseek.com`)
- Examples: `deepseek`, `openrouter`, `minimax-cn`, `ollama`
- **Cost**: User pays provider directly (per-token or subscription)
- **Model availability**: Determined by provider's API (`/v1/models` endpoint)
- **Models**: Full provider catalog (e.g. deepseek has v4-pro, v4-flash, chat, reasoner, etc.)

### 2. OAuth / Hosted Providers (Web Auth)
- Authenticated via `hermes auth` browser OAuth flow (device code)
- Free/credits-based, included in a subscription
- Example: `nous` (Nous Portal / `portal.nousresearch.com`)
- **Cost**: Included in subscription (credits)
- **Model availability**: Static curated list in `hermes_cli/models.py` + dynamic fetch
- **Models**: Limited to what the portal offers (nous does NOT have deepseek-v4-flash, only v4-pro)

## How to Check What Models a Provider Offers

### Method 1: Check the curated model list (static)
Look in `hermes_cli/models.py` for the provider's static model list:
```python
"nous": [
    "anthropic/claude-opus-4.7",
    "deepseek/deepseek-v4-pro",  # no v4-flash for nous!
    ...
]
```

### Method 2: Dynamic API fetch
For direct API providers, call their `/v1/models` endpoint:
```bash
curl https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

### Method 3: Check credential pool status
```bash
hermes auth list        # See all providers and credential counts
hermes auth status <provider>  # Check if authenticated
hermes config           # See current model and provider
```

## Switching Provider at Runtime

Config changes do NOT affect the current session:
```bash
hermes config set model.provider nous
hermes config set model.default nous/deepseek-v4-pro
```
These only take effect on the NEXT session. To switch immediately:
```bash
hermes chat --provider nous --model nous/deepseek-v4-pro
```

To switch for ALL channels (QQ, WeChat, etc.), also update `model.default` in config.yaml and restart the gateway.

## Common Access Paths for DeepSeek Models

| Model | deepseek (direct) | nous (portal) | openrouter |
|-------|-------------------|---------------|------------|
| v4-flash | ✅ Yes | ❌ No | ✅ Yes |
| v4-pro | ✅ Yes | ✅ Yes | ✅ Yes |
