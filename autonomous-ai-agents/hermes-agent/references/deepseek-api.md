# DeepSeek API

## 查询余额

```bash
curl -s "https://api.deepseek.com/v1/user/balance" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

返回示例：
```json
{"is_available":true,"balance_infos":[{"currency":"CNY","total_balance":"90.43","granted_balance":"0.00","topped_up_balance":"90.43"}]}
```

注意：`/v1/balance` 返回404，必须用 `/v1/user/balance`。

## 模型

| 模型 | 说明 | 价格 |
|------|------|------|
| `deepseek-v4-flash` | 最新主力模型，context 200K | $0.1/M tokens |
| `deepseek-reasoner` (R1) | 推理模型，免费额度已用完 | 同上 |
| `deepseek-chat` (V3) | 聊天模型 | 同上 |

## Fallback 配置

```yaml
fallback_providers:
- model: deepseek-v4-flash
  provider: deepseek
- model: deepseek-reasoner
  provider: deepseek
```

## 注意事项

- DeepSeek 无永久免费额度，充值余额用完即停
- 2026年5月实测：¥90充值余额，日常对话可支撑较长时间
- **瞬态 404 "model not found"**：deepseek-v4-flash 模型名在 DeepSeek API 的 `/v1/models` 端点查询是存在的，但有时会瞬态返回 HTTP 404 `model 'deepseek-v4-flash' not found`。这是 DeepSeek 服务端偶发问题，几分钟后自行恢复。如果搭配了同模型 fallback（见 SKILL.md 的 Fallback 循环陷阱），会导致无限循环失败。API 自愈后直接用 curl 测试即可恢复。
