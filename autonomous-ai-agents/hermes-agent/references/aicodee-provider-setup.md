# aicodee Provider Setup (2026-05-17, updated 2026-05-28)

## Overview

aicodee (v2.aicodee.com) is a custom OpenAI-compatible proxy that serves MiniMax models. It must be configured in the `custom_providers:` section of `config.yaml`.

## Current Config Structure

```yaml
custom_providers:
- api_key: YOUR_API_KEY...
  base_url: https://v2.aicodee.com/v1
  model: MiniMax-M2.7-highspeed
  name: aicodee-relay
```

**注意**：V2.aicodee.com 条目已删除（2026-05-28 用户要求）——该条目是 StepFun Step Plan 协议的独立服务，不支持 OpenAI-compatible `/v1/models` 接口，在 model picker 里显示 0 模型且占用条目，已移除。

### aicodee-relay 可用模型（2026-05-28 实测）

| Model | Endpoint Support |
|-------|-----------------|
| MiniMax-M2.1 | openai |
| MiniMax-M2.5 | openai |
| MiniMax-M2.5-highspeed | openai, anthropic |
| MiniMax-M2.7-highspeed | openai, anthropic |

The `model_catalog.providers.custom: aicodee-relay` setting enables Hermes to discover these models dynamically via `/v1/models`.

## Why custom_providers (not providers section)?

The current config uses `custom_providers:` (the preferred modern approach):

- **`custom_providers:`** — each entry has `name`, `api_key`, `base_url`, `model`
- **`model_catalog.providers.custom: aicodee-relay`** — links the model catalog to the custom provider for dynamic model discovery
- No separate `providers.aicodee` section needed

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

## ⚠️ config.yaml 是受保护文件

`~/.hermes/config.yaml` 是系统凭证文件，`patch` 工具会拒绝修改。正确做法：

```bash
# 方法1：编辑器交互修改（推荐）
hermes config edit

# 方法2：单 key 修改
hermes config set model.default MiniMax-M2.7-highspeed

# 方法3：用 Python/terminal 直接写（会触发 approval 审批）
python3 -c "open('/Users/aimac/.hermes/config.yaml').write(...)"
```

如果 approval 拒绝，用 `hermes config edit`。