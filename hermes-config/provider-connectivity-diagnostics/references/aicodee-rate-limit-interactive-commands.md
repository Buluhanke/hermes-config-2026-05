# Provider Rate Limit Impact on Interactive Commands（2026-06-02）

## 问题

`/model`、`/new` 等命令需要较长时间（数十秒）才能出现选项。

## 根因

aicodee (V2.aicodee.com) 返回 `HTTP 429: 并发请求过多`，导致每条命令触发完整 fallback 链：

```
aicodee(MiniMax-M2.7-highspeed) → 429 → minimax-cn → OK
                                   ↓
                         (retry 3次 × 多 provider)
                                   ↓
                              总延迟 = sum(retry_timeout)
```

从 `gateway.error.log` 可见：
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) 
  error_type=RateLimitError 
  provider=custom base_url=https://v2.aicodee.com/v1 
  model=MiniMax-M2.7-highspeed 
  summary=HTTP 429: 并发请求过多，请稍后再试
```

## 诊断

```bash
# 1. 检查 aicodee 是否报 429
grep -E "429|concurrent" ~/.hermes/logs/gateway.error.log | tail -10

# 2. 检查 fallback chain 配置
grep -A10 "fallback_providers" ~/.hermes/config.yaml

# 3. 直接测试 aicodee
curl -s https://v2.aicodee.com/v1/models \
  -H "Authorization: Bearer $AICODEE_API_KEY" | head -5
```

## 处置

将 aicodee 从 fallback chain 中移除或降级：

```yaml
# config.yaml 中调整 fallback_providers 顺序
fallback_providers:
  - model: MiniMax-M2.7-highspeed
    provider: minimax-cn   # 直接走 minimax-cn，绕过 aicodee
  - model: llama-3.3-70b-versatile
    provider: custom:Api.groq.com
```

## 关键信息

aicodee 是一个 **API 中转服务**，key 格式中包含字面 `...`（如 `sk-290...6e18`）。它返回 429 表示中转额度耗尽，不是模型本身的问题。key 本身仍然有效，只需等待额度恢复或切换到直连 provider（minimax-cn）。

## 预防

- aicodee 额度有限（免费/低价中转额度），建议作为最后兜底而非首选
- 在 config.yaml 中优先使用直连 provider（minimax-cn、deepseek 直连）