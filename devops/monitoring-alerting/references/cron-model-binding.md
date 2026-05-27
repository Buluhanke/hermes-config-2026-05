# Cron Job 模型绑定规则

## 核心规则

**Cron job 创建时必须显式指定 model + provider，否则运行时会失败。**

- `model=null, provider=null` → 默认用 openrouter（需要 OPENROUTER_API_KEY，config 里是空的）→ 401 失败
- `model=null, provider=custom:xxx` → 使用指定 provider
- `model=xxx, provider=null` → 使用当前默认 provider

## 可用通道

| 通道 | model 前缀 | provider | 备注 |
|------|-----------|----------|------|
| minimax-cn（默认） | MiniMax-M2.7 | custom:v2.aicodee.com | 默认可用，免费额度 |
| nous 通道 | deepseek/ | nous | 免费，需配置 |
| openrouter | 其他 | openrouter | 需要 OPENROUTER_API_KEY |

## 推荐配置

创建 cron job 时指定：

```json
{
  "model": "MiniMax-M2.7",
  "provider": "custom:v2.aicodee.com"
}
```

或使用 nous 免费通道（如果配置了）：
```json
{
  "model": "deepseek/deepseek-v4-flash",
  "provider": "nous"
}
```

## 快速检查现有 cron jobs

```bash
hermes cron list
```

检查 `model` 和 `provider` 字段是否为 `null`。

## 修复已有问题

已有 `model=null` 的 cron job，需要 update 重新指定 model 和 provider。
