# Provider → env var / auth mapping (2026-07-05)

## Built-in supported providers (from config.yaml)

| Provider name | Type | Auth method | Env var / Config |
|---|---|---|---|
| openrouter | Standard | API key | `OPENROUTER_API_KEY` |
| openai-codex | Standard | OAuth | `hermes auth login openai-codex` |
| nous | Standard | **API key** (preferred) or OAuth | `hermes auth add --type api-key --api-key <key> nous` OR `hermes setup --portal` (interactive TTY) |
| zai | Standard | API key | `ZAI_API_KEY` (Z.AI / GLM — same key) |
| kimi-coding | Standard | API key | `KIMI_API_KEY` (Kimi / Moonshot) |
| kimi-coding-cn | Standard | API key | `KIMI_CN_API_KEY` (Kimi China) |
| minimax | Standard | API key | `MINIMAX_API_KEY` (MiniMax Global) |
| minimax-cn | Standard | API key | `MINIMAX_CN_API_KEY` (MiniMax China) |
| bedrock | Standard | AWS IAM | boto3 / AWS CLI credentials |
| glm | Standard | API key | `GLM_API_KEY` (智谱) |
| gemini | Standard | API key | `GEMINI_API_KEY` (Google) |

## Non-standard / custom providers

| Provider | What it is | What it needs |
|---|---|---|
| GitHub Copilot | GitHub model marketplace | Custom OpenAI-compatible endpoint + GitHub token (`GITHUB_TOKEN`) + active Copilot subscription. NOT a standard Hermes provider — needs custom_providers entry in config.yaml |
| Ollama Cloud | Hosted Ollama API (cloud, not local) | Custom provider with `base_url` + `api_key`. Distinguish from local Ollama/Docker — user may ban one but allow the other |
| 123.56.67.77:9100 | Custom proxy (MiniMax M3) | Custom provider with `provider: custom:123.56.67.77:9100`. Must have `custom_providers:` named entry with `base_url` + `key_env`. **Do NOT use `provider: openrouter`** (2026-07-05 corrected — earlier 2026-07-04 record was wrong) |
| MoA (Mixture of Agents) | **Virtual provider**, not a fallback provider | Configured in `moa:` section of config.yaml (`moa.presets`), NOT in `fallback_providers[]` |

## Fallback chain entries vs provider model counts

The fallback chain only needs **one representative model per provider** — not all models:

| Provider (total models) | Fallback chain entries | Recommended model |
|---|---|---|
| Nvidia (124) | 2 | NV Qwen 3.5 397B + NV Nemotron 3 Super 120B |
| OpenRouter (29) | 1 | OR Qwen 3 Coder:free |
| Google (11) | 1 | Gemini 2.5 Flash |
| Z.AI (10) | 1 | **Z.AI GLM-4-Flash** (only model with free quota — all others 429) |
| Ollama Cloud (40) | 1 | **gemma4:31b** (confirmed free, 200 OK on both native & OpenAI endpoints) |
| Nous Portal (29) | 1 | **stepfun/step-3.7-flash:free** (only free model out of 237; Hermes-4 series paid) |
| MoA (1) | N/A | Not a provider — configured in `moa:` section |

## Provider-specific quirks

### Z.AI / GLM
- **Same key, different provider names** — Z.AI (z.ai, international) and GLM (open.bigmodel.cn, China) share the same key format (`uuid.random_string`). A China-region key works on both `provider: zai` and `provider: glm`.
- **Free tier is glm-4-flash only** — Tested all models: glm-4-air, glm-4-plus, glm-4-0520, charglm-4, glm-4-long all return 429 "余额不足". Only glm-4-flash responds 200.
- **Base URL**: `https://open.bigmodel.cn/api/paas/v4` (China) — for Z.AI provider, use same endpoint unless using international z.ai API key.

### Ollama Cloud
- **Not local Ollama** — SaaS, zero local install. User's local Ollama/Docker ban does NOT automatically cover it. Must explicitly confirm.
- **OpenAI-compatible**: `https://ollama.com/v1/chat/completions` works with Bearer auth (OLLAMA_API_KEY).
- **Native API**: `https://ollama.com/api/generate` also works (same auth).
- **Free model confirmed**: `gemma4:31b` → 200 OK. Paid models return 403 "requires subscription".
- **Model naming**: Use `modelname:size` format (e.g. `gemma4:31b`, `qwen3.5:397b`).

### Nous Portal
- **Powered by OpenRouter** — 237 models available, but only 1 free: `stepfun/step-3.7-flash:free`
- **Inference endpoint**: `https://inference-api.nousresearch.com/v1`
- **Free model confirmed this session**: `stepfun/step-3.7-flash:free` — $0.00/1M tokens
- **Hermes-4 series all paid** — Hermes-4-70B ($0.05/$0.20 per 1M), 405B more expensive. Portal warns "not recommended for Hermes Agent."
- **Balance is $0.10** — insufficient for paid-model fallback loops.
- **OAuth token expires** — auth.json shows `"code": "invalid_grant"` → token expired.
- **`hermes auth login nous` is NOT a valid command** — only auth subcommands are: add, list, remove, reset, status, logout, spotify.

#### Recovery: API key path (preferred, 2026-07-05 discovered)

Instead of fixing the broken OAuth flow, use the **API key approach**:

1. Open `https://portal.nousresearch.com/orgs/<org>/api-keys` in a browser (already logged in)
2. Click **Create key** → a new key is generated
3. Register it via CLI:
   ```bash
   hermes auth add --type api-key --api-key "<the-key>" nous
   ```
   The `hermes auth add --type api-key` subcommand accepts the provider name as positional argument. The key goes in `~/.hermes/auth.json` under a `credential_pool` entry for that provider, NOT in `.env`.

4. Verify:
   ```bash
   hermes auth status nous
   # → should show "logged in" with an API key entry
   ```

5. Then add the fallback entry:
   ```bash
   sed -i '' '/^  - api_key: ${AGNES_API_KEY}/i\
     - api_key: ${NOUS_API_KEY}\
       base_url: https://inference-api.nousresearch.com/v1\
       label: Nous Portal Step 3.7 Flash (免费)\
       model: stepfun/step-3.7-flash:free\
       provider: nous\
       request_timeout_seconds: 20
   ' ~/.hermes/config.yaml
   ```

**Note**: The OAuth flow (`hermes setup --portal`) also works but requires an interactive TTY. The API key approach works fully non-interactively and doesn't expire like OAuth tokens. Prefer it for headless/Telegram-only setups.

### MiniMax M3 proxy (123.56.67.77:9100) — restoration guide

See `references/minimax-custom-provider-restoration.md` for the complete restore guide (2026-07-05 corrected version).

- This provider exists in **THREE places**:
  1. `.env` — the API key env var (e.g. `MINIMAX_M3_API_KEY`)
  2. `custom_providers[]` — the named entry with `base_url` + `key_env`
  3. `fallback_providers[]` — entry with `provider: custom:123.56.67.77:9100`
- When user says "delete and re-add", **all three must be restored**.
- **Do NOT fall back to `provider: openrouter`** — the `custom:` prefix works when `custom_providers:` is properly configured.

## Provider readiness checklist

When user asks "is X in the fallback chain?" or "add X to fallback chain":

```bash
# Step 1: Check fallback_providers[] entries
grep -A 60 'fallback_providers' ~/.hermes/config.yaml | head -60

# Step 2: Check if it's a supported provider (from config comments)
grep -E '^\s*#\s+(openrouter|openai|nous|zai|kimi|minimax|bedrock)' ~/.hermes/config.yaml

# Step 3: Check .env for required env var
grep -i '<PROVIDER_KEY>' ~/.hermes/.env

# Step 4: If OAuth provider, check auth status
hermes auth status <provider>

# Step 5: Check auth.json for detailed OAuth state
python3 -c "import json; d=json.load(open('$HOME/.hermes/auth.json')); print(json.dumps(d.get('providers',{}).get('<provider>',{}), indent=2))"
```

### Pre-configuration testing workflow

Before adding ANY provider to fallback chain, test with curl:

```bash
# 1. Key validity
curl -s -o /dev/null -w "%{http_code}" -X POST <endpoint>/v1/chat/completions \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# 2. Test multiple models for free availability
for model in "candidate1" "candidate2" "candidate3"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" ...)
  echo "$model → $code"
done

# 3. Check endpoint format: OpenAI-compatible (/v1/chat/completions) vs native
```

### Diagnostic decision tree

```
Is provider in config.yaml "Supported providers" list?
├─ YES → Does it need API key or OAuth?
│   ├─ API key → Is key in .env?
│   │   ├─ YES → curl-test first, then add to fallback_providers[]
│   │   └─ NO  → Ask user for key
│   └─ OAuth  → Is auth token valid?
│       ├─ YES → Add entry to fallback_providers[]
│       └─ NO  → Try API key path (`hermes auth add --type api-key`) — OAuth recovery unreliable
└─ NO → Is it a known non-standard provider?
    ├─ GitHub Copilot → Custom provider with base_url + token
    ├─ Ollama Cloud → Custom provider with base_url + api_key
    ├─ MoA → Don't add to fallback! It's in `moa:` section
    └─ Unknown → Need user to provide endpoint + auth details
```

## Provider deletion checklist

When user says "delete provider X" (2026-07-05 pattern):

1. **Find ALL occurrences** in config.yaml
2. **Check `fallback_providers[]`** — the active fallback entry
3. **Check `custom_providers[]`** — the custom endpoint definition (if applicable)
4. **Check `.env`** for the corresponding `X_API_KEY`
5. Remove from each location using sed
6. Verify with grep — all occurrences clean

## Ollama Cloud vs 本地 Ollama 区别

| 对比项 | 本地 Ollama | Ollama Cloud |
|---|---|---|
| 安装需求 | Docker / 本地二进制 | 无（SaaS） |
| 资源消耗 | 高（CPU/GPU/内存） | 低（仅 API 调用） |
| 用户禁令 | ❌ 已被用户明确禁止 | ⚠️ 需用户确认 |
| 配置方式 | 禁止安装 | 自定义 provider（base_url + api_key） |
| Fallback 配置 | 不适用 | `OLLAMA_API_KEY` env var, `https://ollama.com/v1` base_url, `gemma4:31b` model |
