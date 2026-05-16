# Hermes Agent Provider Configuration Patterns

## Two Configuration Channels

### 1. Built-in Providers (`providers` section in config.yaml)

Built-in providers are defined as `ProviderProfile` objects in `plugins/model-providers/<name>/__init__.py`. 
They have hardcoded `base_url`, `api_mode`, `auth_type`, and `env_vars`.

**Configure only the api_key** (other fields are built-in):
```yaml
providers:
  <provider-name>:
    api_key: YOUR_API_KEY...
```

Some built-in providers also accept **environment variable overrides**:
- `MINIMAX_CN_API_KEY` / `MINIMAX_CN_BASE_URL`
- `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL`
- `GEMINI_API_KEY`
- etc. (check the provider's `__init__.py` for env_vars tuple)

### 2. Custom Providers (`custom_providers` list in config.yaml)

For providers not built in, or for overriding endpoint behavior:
```yaml
custom_providers:
  - name: MyProvider
    base_url: https://api.example.com/v1
    api_key: YOUR_API_KEY...   # inline
    model: model-name  # optional default model
```

Custom providers **always use OpenAI-format** (chat_completions).

## Model Routing: fallback_providers Chain

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: custom    # primary provider name
fallback_providers:
  - minimax-cn        # try this if primary fails
  - deepseek           # try this second
```

The chain attempts providers in order. Each must be a valid provider name 
(either built-in name or custom_providers name).

## MiniMax Provider Family

| Provider Name | Endpoint | API Mode | Auth | Best For |
|---|---|---|---|---|
| `minimax` | `api.minimax.io/anthropic` | anthropic_messages | `MINIMAX_API_KEY` | International |
| `minimax-cn` | `api.minimaxi.com/anthropic` | anthropic_messages | `MINIMAX_CN_API_KEY` | China mainland |
| `minimax-oauth` | `api.minimax.io/` | OAuth flow | No key needed | Browser auth |

**Key quirk:** Base URL ending in `/anthropic` triggers `anthropic_messages` api_mode
auto-detection. To force OpenAI-format, set base_url WITHOUT the suffix 
(e.g., `https://api.minimaxi.com` → uses `/v1/chat/completions`).

`YOUR_API_KEY-` prefix = MiniMax native key (NOT aicodee).
`YOUR_API_KEY...` prefix = aicodee key.

## API Key Testing via curl

```bash
# Test OpenAI-format endpoint
curl -s https://api.minimaxi.com/v1/chat/completions \
  -H "Authorization: Bearer <key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","max_tokens":128,"messages":[{"role":"user","content":"hi"}]}'

# Test Anthropic-format endpoint
curl -s https://api.minimaxi.com/anthropic/messages \
  -H "x-api-key: <key>" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MiniMax-M2.7","max_tokens":128,"messages":[{"role":"user","content":"hi"}]}'
```

**HTTP code interpretation:**
- `401` = key not valid for this endpoint (wrong provider/port)
- `429` = key valid, rate limited (check error.message for resets_at time)
- `404` = URL/path wrong
- `200` = working

## Common Pitfalls

- `providers: {}` empty in config.yaml → no built-in providers configured. 
  The `custom_providers` list is separate.
- Fallback provider without api_key → chain breaks silently.
- Mixing aicodee keys with MiniMax native endpoints → 401.
- Changing base URL via .env can change api_mode auto-detection behavior.
- DO NOT modify `model.default` when only adding a fallback provider.
