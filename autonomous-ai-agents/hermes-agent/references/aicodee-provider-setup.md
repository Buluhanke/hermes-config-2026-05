# aicodee Provider Setup (2026-05-17, updated 2026-05-17)

## Overview

aicodee (V2.aicodee.com) is a custom OpenAI-compatible proxy that serves MiniMax models. It must be configured in BOTH `custom_providers:` AND `providers:` sections to work correctly.

## Why Both Sections?

- **`custom_providers:`** — runtime credential pool and API calls actually use this
- **`providers:`** — required for `/model` command to recognize the provider name

Without `providers:` entry, `/model aicodee/MiniMax-M2.7-highspeed` silently fails or says "model not found."

## Working Config (4-Space Indentation, No Tabs)

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: aicodee
  base_url: https://v2.aicodee.com/v1
providers:
  aicodee:
    name: V2.aicodee.com
    base_url: https://v2.aicodee.com/v1
    api_key_env_var: AICODEE_API_KEY
    available_models:
      - MiniMax-M2.7-highspeed
      - MiniMax-M2.7
      - MiniMax-M2.5
    fallback_providers: []
    credential_pool_strategies:
      minimax-cn: fill_first
  toolsets:
    - hermes-cli
    - computer_use
```

The API key lives in `.env` as `AICODEE_API_KEY=YOUR_API_KEY...`.

## YAML Indentation Traps

⚠️ **`providers` 内部 keys 必须有 4-space 缩进**：`fallback_providers`、`credential_pool_strategies`、`toolsets` 都是 `aicodee` 的子节点，必须有 4 空格缩进。

正确：
```yaml
providers:
  aicodee:
    name: V2.aicodee.com
    available_models: [...]
    fallback_providers: []        # 4 spaces — UNDER aicodee
    credential_pool_strategies:   # 4 spaces — UNDER aicodee
      minimax-cn: fill_first
  toolsets:                      # 4 spaces — UNDER aicodee
    - hermes-cli
```

错误（2026-05-17 遇到的真实 bug）：
```yaml
providers:
  aicodee:
    ...
fallback_providers: []           # ❌ 缩进在 providers 同级
credential_pool_strategies:      # ❌ 缩进在 providers 同级
toolsets:
- hermes-cli                     # ❌ list item 缺少 4 spaces
- computer_use                   # ❌ list item 缺少 4 spaces
```

错误信息：`could not find expected ':' in "...", line 14, column 3` — 这个模糊的 YAML 解析错误实际上是因为 `fallback_providers` 被错误地缩进在 `providers` 内部（成为 `aicodee` 的子节点），导致后续的 `credential_pool_strategies` 无法正确解析。

**验证方法**：`python3 -c "import yaml; yaml.safe_load(open('/Users/aimac/.hermes/config.yaml'))"` — 无输出表示语法正确。

## Testing the Endpoint

```bash
curl -s -X POST https://v2.aicodee.com/v1/chat/completions \
  -H "Authorization: Bearer $AICODEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'
```

Expected: JSON response with `MiniMax-M2.7-highspeed` in model field.
Error `"无效的令牌"`: API key expired — get a fresh one from aicodee dashboard.

## Verification Commands

```bash
hermes config show | grep -A3 "Model"
# Should show: provider: aicodee, default: MiniMax-M2.7-highspeed

hermes config show | grep -A5 "providers"
# Should show aicodee entry
```

## Session vs Persistent Config

- `/model aicodee/MiniMax-M2.7-highspeed` → runtime switch, current session only
- Editing `config.yaml` `model.default` → persistent, takes effect on NEW sessions

Config change does NOT affect running session — must restart or use runtime `/model` for immediate effect.