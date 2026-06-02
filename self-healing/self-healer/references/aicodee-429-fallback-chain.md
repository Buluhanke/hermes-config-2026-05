# aicodee 429 引发命令响应慢（2026-06-02）

## 问题

`/model`、`/new` 等命令需要较长时间才能出现选项，有时长达数十秒。

## 根因

aicodee (V2.aicodee.com) 返回 `HTTP 429: 并发请求过多`，导致每条命令触发完整 fallback 链：

```
aicodee(MiniMax-M2.7-highspeed) → 429 → minimax-cn → OK
                                   ↓
                         (retry 3次 × 3 providers)
                                   ↓
                              总延迟 = sum(retry_timeout)
```

从 `gateway.error.log` 可见：
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=RateLimitError provider=custom base_url=https://v2.aicodee.com/v1 model=MiniMax-M2.7-highspeed summary=HTTP 429: 并发请求过多，请稍后再试
```

## 诊断

```bash
# 1. 检查 aicodee 是否报 429
grep -E "429|concurrent" ~/.hermes/logs/gateway.error.log | tail -10

# 2. 检查 fallback chain 配置
grep -A10 "fallback_providers" ~/.hermes/config.yaml

# 3. 直接测试 aicodee 连通性
curl -s https://v2.aicodee.com/v1/models \
  -H "Authorization: Bearer $AICOD...KEY" | head -5
```

## 处置

将 aicodee 从 fallback chain 中移除或降低优先级：

```yaml
# config.yaml 中调整
fallback_providers:
  - model: MiniMax-M2.7-highspeed
    provider: minimax-cn   # 直接用 minimax-cn
  - model: llama-3.3-70b-versatile
    provider: custom:Api.groq.com
```

## 预防

aicodee 额度有限（免费额度），建议作为最后兜底而非首选 fallback。