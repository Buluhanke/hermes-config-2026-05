# MiniMax Provider Configuration

## Endpoints

| Region | base_url | Key Prefix |
|--------|----------|------------|
| 国内直连 (China mainland) | `https://api.minimaxi.com/anthropic` | `YOUR_API_KEY-...` |
| 国际中转 (Overseas) | `https://api.minimax.io/anthropic` | `YOUR_API_KEY...` |

API mode: `anthropic_messages` — uses Anthropic-compatible message format.

## Config Pitfalls

### .env 覆盖 config.yaml

`~/.hermes/.env` 中的 `MINIMAX_CN_BASE_URL` 会 **覆盖** `config.yaml` 中的 `model.base_url`。
修 base_url 必须两处都改，否则改了 config 也不生效。

### 正确示例

```yaml
# config.yaml
model:
  default: MiniMax-M2.7
  provider: minimax-cn
  base_url: https://api.minimaxi.com/anthropic
providers:
  minimax-cn:
    api_key: YOUR_API_KEY-..._P-U
```

```bash
# .env — 必须和 config.yaml 一致
MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic
MINIMAX_CN_API_KEY=YOUR_API_KEY-..._P-U
```

### 裸 endpoint 返回 nginx 404

**错误**: `base_url: https://api.minimaxi.com` → nginx 404
**正确**: `base_url: https://api.minimaxi.com/anthropic` → 200 OK

Anthropic SDK 构造完整 URL 为 `{base_url}/v1/messages`，所以国内直连最终路径为 `https://api.minimaxi.com/anthropic/v1/messages`。

## 模型链配置（三层）

```
默认 → MiniMax-M2.7-highspeed  中转  (custom:V2.aicodee.com)
备用 → MiniMax-M2.7             直连  (minimax-cn)
压轴 → deepseek-v4-flash              (deepseek)
```

三层回落机制：默认失败 → 备用 → 压轴。每层独立配置 provider/endpoint/key。

## 验证

```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://api.minimaxi.com/anthropic/v1/messages" \
  -H "x-api-key: ${MINIMAX_CN_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
# 预期返回 200
```
