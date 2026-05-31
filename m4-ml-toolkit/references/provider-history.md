# 模型提供商切换历史

| 日期 | 提供商 | 模型 | 原因 | 状态 |
|------|--------|------|------|------|
| ~2026-05-21 | Nous Portal (官方) | deepseek/deepseek-v4-flash | 首次配置 | ❌ 被覆盖 |
| ~2026-05-29 | custom (v2.aicodee.com) | MiniMax-M2.7-highspeed | 切换到 aicodee | ❌ 额度不足 |
| 2026-05-31 | openrouter | deepseek/deepseek-v4-flash | 当前 | ✅ |

## Fallback 链

当前:
- Primary: openrouter / deepseek/deepseek-v4-flash
- Fallback: minimax-cn / MiniMax-M2.7 (超限中，待更新)

应更新 fallback 为 deepseek 直连或 OpenRouter 免费版。

## 可用 Key

| Key | 对应提供商 | 状态 |
|-----|----------|------|
| AICODEE_API_KEY | v2.aicodee.com | 额度不足 |
| MINIMAX_CN_API_KEY | minimax-cn | 超限 |
| DEEPSEEK_API_KEY | DeepSeek 直连 | 可用 |
| OPENROUTER_API_KEY | OpenRouter | 可用 |
| FREELLMAPI_KEY | FreeLLM聚合 | 可用 |
