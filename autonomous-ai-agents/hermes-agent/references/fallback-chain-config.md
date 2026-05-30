# Fallback Chain Config — Working Reference

## Current Model Routing Architecture

```
Primary:   deepseek/deepseek-v4-flash  → v2.aicodee.com 中转 (custom provider)
Fallback 1: MiniMax-M2.7                → minimax-cn
Fallback 2: deepseek/deepseek-v4-flash  → api.deepseek.com 直连 (deepseek provider)
```

## config.yaml model Section (exact working block)

```yaml
model:
  default: deepseek/deepseek-v4-flash
  fallback: MiniMax-M2.7
  max_tokens: 8192
  provider: custom
  temperature: 0.7
  top_p: 0.95
  base_url: https://v2.aicodee.com/v1
  api_key: sk-290...6e18
  model: deepseek/deepseek-v4-flash

providers:
  minimax-cn:
    api_key_env: MINIMAX_CN_API_KEY
    base_url_env: MINIMAX_CN_BASE_URL

fallback_providers:
  - provider: minimax-cn
    model: MiniMax-M2.7
  - provider: deepseek
    model: deepseek/deepseek-v4-flash
    base_url: https://api.deepseek.com
```

## Python Script to Write the Fallback Chain

```python
import yaml

config_path = '/Users/aimac/.hermes/config.yaml'

with open(config_path) as f:
    cfg = yaml.safe_load(f)

# Remove legacy fallback_model (replaced by fallback_providers)
if 'fallback_model' in cfg:
    del cfg['fallback_model']

cfg['fallback_providers'] = [
    {'provider': 'minimax-cn', 'model': 'MiniMax-M2.7'},
    {'provider': 'deepseek', 'model': 'deepseek/deepseek-v4-flash', 'base_url': 'https://api.deepseek.com'}
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
Primary:   deepseek/deepseek-v4-flash  (via custom)

Fallback chain (2 entries):
  1. MiniMax-M2.7  (via minimax-cn)
  2. deepseek/deepseek-v4-flash  (via deepseek)  [https://api.deepseek.com]
```

## Notes

- Primary shows `(via custom)` because `model.provider: custom` and `base_url: https://v2.aicodee.com/v1`
- Fallback 1 uses `minimax-cn` provider (reads API key from `MINIMAX_CN_API_KEY` env var)
- Fallback 2 uses `deepseek` provider with explicit `base_url: https://api.deepseek.com` to bypass the relay
- Same model name `deepseek/deepseek-v4-flash` appears twice via different providers — this is intentional (different routes, same model)
- For a distinct 兜底 model, swap Fallback 2 to `deepseek/deepseek-chat` or `deepseek-ai/DeepSeek-V3`