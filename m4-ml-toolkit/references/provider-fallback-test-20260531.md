# Provider Fallback Chain — 2026-06-01

## 当前配置（已验证可用）

| Provider | 模型 | 状态 | 说明 |
|----------|------|------|------|
| V2.aicodee.com (custom) | MiniMax-M2.7-highspeed | ✅ 主用 | 中转，额度充足 |
| deepseek | deepseek-v4-flash | ✅ 备用 | 直连 |
| OpenRouter | deepseek-v4-flash | ✅ 备用 | 免费额度 |

## 失效 Provider（已清理）

- **Groq** — key 失效（403）
- **Cerebras** — 账号问题（403/1009）
- **MiniMax-CN** — 额度耗尽（429），key 有效
- **Nous Portal** — 模型需付费（404）

## 历史记录

- 2026-05-21: Nous Portal + deepseek/deepseek-v4-flash (免费)
- 2026-05-30: V2.aicodee.com + MiniMax-M2.7-highspeed
- 2026-05-31: API key 全面归集，清理失效 provider
- 2026-06-01: V2.aicodee.com 重新上线（picker 消失问题已修复，添加显式 model 字段）

## .env 中实际有效的 Key

```
AICODEE_API_KEY     ✅ sk-290...6e18
DEEPSEEK_API_KEY    ✅ sk-7d7...f076
OPENROUTER_API_KEY  ✅ sk-or-...87b6
MINIMAX_CN_API_KEY  ⚠️ 额度429，key有效
GEMINI_API_KEY      ⚠️ 网络超时，配置正确
```
