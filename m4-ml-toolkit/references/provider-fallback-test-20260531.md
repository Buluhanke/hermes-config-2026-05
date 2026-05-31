# Provider Fallback Chain Test — 2026-05-31

## 测试方法

使用 Python 脚本直接调用各提供商 API（读取 ~/.hermes/.env 获取密钥），测试 `deepseek/deepseek-v4-flash` 模型连通性。

## 结果

| # | 提供商 | URL | HTTP | 结论 |
|---|--------|-----|------|------|
| 1 | v2.aicodee.com (custom) | https://v2.aicodee.com/v1 | 403 | 额度不足 ($0.00) |
| 2 | minimax-cn | https://api.minimaxi.com/v1 | 429 | 速率超限 (2056) |
| 3 | **DeepSeek 直连** | https://api.deepseek.com | **200** | ✅ 正常, deepseek-v4-flash |
| 4 | **OpenRouter** | https://openrouter.ai/api/v1 | **200** | ✅ 正常, deepseek/deepseek-v4-flash-20260423 |
| 5 | **Nous Portal** | https://inference-api.nousresearch.com/v1 | 404 | 模型需付费充值 |

## 当前配置

2026-05-31 最终配置: OpenRouter → deepseek/deepseek-v4-flash (走用户 DeepSeek 直连渠道扣费)

## 历史记录

- 2026-05-21: Nous Portal + deepseek/deepseek-v4-flash (免费, 272次会话)
- 2026-05-30: v2.aicodee.com + MiniMax-M2.7-highspeed (额度用尽前)
- 2026-05-31: 切到 OpenRouter + deepseek/deepseek-v4-flash:free
- 2026-05-31: 改为 OpenRouter + deepseek/deepseek-v4-flash (走直连渠道)

## OAuth 令牌位置

Nous Portal: `~/.hermes/shared/nous_auth.json`
```
access_token: JWT token (自动续期)
expires_at: 2026-05-31T01:50:40+00:00 (当时)
inference_base_url: https://inference-api.nousresearch.com/v1
```
