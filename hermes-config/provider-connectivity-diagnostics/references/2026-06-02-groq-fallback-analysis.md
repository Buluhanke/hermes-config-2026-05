# Groq API 直连测试 + Fallback Chain 分析（2026-06-02深夜）

## 发现

用户反映：MiniMax-M2.7-highspeed 额度用完后，fallback 没有触发 Groq (llama-3.3-70b-versatile)，直接报了 "💀 Final error"。

## Groq 直连测试

```python
import requests

resp = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {groq_key}'},
    json={
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': 'ping'}],
        'max_tokens': 5
    },
    timeout=15
)
# status=200 ✅
# Response: pong
```

**Groq 状态：完全可用**，llama-3.3-70b-versatile 模型存在且正常工作。

## Fallback Chain 代码分析

日志显示 MiniMax 429 后直接进入终态，没有出现任何 `🔄 Fallback activated: llama-3.3-70b-versatile via custom:Api.groq.com` 的日志。

可能原因：

1. **credential pool 锁定**：MiniMax 额度耗尽后，整个 chain 被标记为终态，不再尝试后续 provider
2. **429 触发的 fallback 路径不同**：额度耗尽（429）与服务不可用（503/403）走的可能不是同一个分支
3. **时序问题**：日志里从 MiniMax 失败到终态的时间差很短（不到1秒），说明没有等待完整的 fallback 重试窗口

## 已知有效 Provider（2026-06-02实测）

| Provider | 模型 | 状态 |
|----------|------|------|
| OpenRouter | deepseek/deepseek-v4-flash | ✅ 可用（$0.0000013/call） |
| Groq | llama-3.3-70b-versatile | ✅ 直连200 OK |
| DeepSeek直连 | deepseek-v4-flash | ❌ 401 |
| MiniMax CN | MiniMax-M2.7 | ❌ 429 额度耗尽 |
| Cerebras | zai-glm-4.7 | ❌ 401 key失效 |

## 待验证

- 在 MiniMax 429 时显式触发 Groq fallback 是否能正常工作
- credential pool 在额度耗尽后是否会跳过 Groq
- Groq 在 gateway 的 resolve_provider_client 解析 custom:Api.groq.com 是否正确

## 行动项

需要一次真实额度耗尽场景的完整日志测试，确认 fallback 触发链的具体卡点位置。