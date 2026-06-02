# Fallback Chain Config — Working Reference

## Current Model Routing (2026-06-02)

```
Fallback 1: MiniMax-M2.7 via minimax-cn (直连 https://api.minimaxi.com/v1)
```

**v2.aicodee.com 中转已彻底移除 (2026-06-02)。** The relay had a 429 rate limit issue and was deleted from `.env` and all scripts (`hermes_reactor_v3.py`). Current chain uses only MiniMax direct via `minimax-cn` provider.

**Logic:** MiniMax 直连 minimaxi.com，额度用完或 429 时 fallback 到 minimax-cn 同一 endpoint（本质是同一个直连）。

## config.yaml model Section (直连 minimax-cn)

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: minimax-cn
  temperature: 0.7
  top_p: 0.95
  max_tokens: 8192

providers:
  minimax-cn:
    api_key_env: MINIMAX_CN_API_KEY
    base_url: https://api.minimaxi.com/v1

fallback_providers:
  - provider: minimax-cn
    model: MiniMax-M2.7-highspeed
```

> Note: `base_url` is hardcoded in `hermes_reactor_v3.py` as `https://api.minimaxi.com/v1` and overrides `.env` `MINIMAX_CN_BASE_URL`. The `.env` value was `https://api.minimaxi.com/anthropic` (incorrect, anthropic path) — not used by the reactor.

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



| Official Name | Relay Name |
|---------------|------------|
| `MiniMax-M2.7` | `MiniMax-M2.7-highspeed` |
| `MiniMax-M2.5` | `MiniMax-M2.5-highspeed` |

Always query relay models first:
```bash
  -H "Authorization: Bearer $API_KEY" \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

## Python Script to Write the Fallback Chain (直连 minimax-cn)

```python
import yaml

config_path = '/Users/aimac/.hermes/config.yaml'

with open(config_path) as f:
    cfg = yaml.safe_load(f)

cfg['model'] = {
    'default': 'MiniMax-M2.7-highspeed',
    'provider': 'minimax-cn',
    'temperature': 0.7,
    'top_p': 0.95,
    'max_tokens': 8192
}

# Ensure providers.minimax-cn has the correct base_url
cfg.setdefault('providers', {})
cfg['providers']['minimax-cn'] = {
    'api_key_env': 'MINIMAX_CN_API_KEY',
    'base_url': 'https://api.minimaxi.com/v1'
}

# Remove legacy fallback_model
cfg.pop('fallback_model', None)
cfg['fallback_providers'] = [
    {'provider': 'minimax-cn', 'model': 'MiniMax-M2.7-highspeed'}
]

with open(config_path, 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
```

## Notes

- **Primary uses `minimax-cn` provider** — no more `custom` + hardcoded base_url
- **v2.aicodee.com relay removed** — all scripts now point to `https://api.minimaxi.com/v1` directly
- **`.env` `MINIMAX_CN_BASE_URL`** was set to `https://api.minimaxi.com/anthropic` (wrong path, anthropic instead of v1) — not relied upon by reactor; `hermes_reactor_v3.py` hardcodes the correct URL
- ⚠️ After editing config.yaml directly, restart the gateway: `hermes gateway restart`
