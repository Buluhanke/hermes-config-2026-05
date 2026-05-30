# Fallback Chain Config — Working Reference

## Current Model Routing Architecture

```
Primary:   MiniMax-M2.7-highspeed  → v2.aicodee.com 中转 (custom provider)
Fallback 1: MiniMax-M2.7            → minimax-cn 直连
```

**Logic:** 中转额度用完 → 自动切换直连 MiniMax，两边都是 M2.7 模型。

## config.yaml model Section (exact working block)

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: custom
  base_url: https://v2.aicodee.com/v1
  api_key: sk-290...6e18
  temperature: 0.7
  top_p: 0.95
  max_tokens: 8192

providers:
  minimax-cn:
    api_key_env: MINIMAX_CN_API_KEY
    base_url_env: MINIMAX_CN_BASE_URL

fallback_providers:
  - provider: minimax-cn
    model: MiniMax-M2.7
```

## Python Script to Write the Fallback Chain

```python
import yaml

config_path = '/Users/aimac/.hermes/config.yaml'

with open(config_path) as f:
    cfg = yaml.safe_load(f)

# Clean model section
cfg['model'] = {
    'default': 'MiniMax-M2.7-highspeed',
    'provider': 'custom',
    'base_url': 'https://v2.aicodee.com/v1',
    'api_key': 'sk-290...6e18',
    'temperature': 0.7,
    'top_p': 0.95,
    'max_tokens': 8192
}

# Remove legacy fallback_model
if 'fallback_model' in cfg:
    del cfg['fallback_model']

cfg['fallback_providers'] = [
    {'provider': 'minimax-cn', 'model': 'MiniMax-M2.7'}
]

with open(config_path, 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

## Verify

```bash
hermes fallback list
```

Expected output:
```
Primary:   MiniMax-M2.7-highspeed  (via custom)

Fallback chain (1 entry):
  1. MiniMax-M2.7  (via minimax-cn)
```

## Key Discovery: v2.aicodee.com Model Names

The relay (`v2.aicodee.com`) uses its own model naming — not the official names:

| Official Name | Relay Name |
|---------------|------------|
| `MiniMax-M2.7` | `MiniMax-M2.7-highspeed` |
| `MiniMax-M2.5` | `MiniMax-M2.5-highspeed` |

Always query relay models first:
```bash
curl -s https://v2.aicodee.com/v1/models \
  -H "Authorization: Bearer $API_KEY" \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

## Notes

- Primary shows `(via custom)` because `model.provider: custom` points to the relay URL
- Fallback uses `minimax-cn` provider (reads `MINIMAX_CN_API_KEY` + `MINIMAX_CN_BASE_URL` from `.env`)
- ⚠️ `.env` `MINIMAX_CN_BASE_URL` was incorrectly set to `https://api.minimaxi.com/anthropic` — should be `https://api.minimaxi.com/v1`. User chose NOT to fix it.
- v2.aicodee.com is a hosted relay service, not self-hosted. It aggregates multiple channels but requires valid channel credentials to work.