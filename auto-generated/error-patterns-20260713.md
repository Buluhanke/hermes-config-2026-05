---
name: auto-1783888019-error-patterns
description: 自动从 ~/.hermes/logs/agent.log 抽取的错误模式 + 修法. 由 auto_skill_from_failure.py 生成.
triggers:
  - "TimeoutError"
  - "ConnectionError"
  - "Import error"
  - "JSON parse error"
  - "Permission denied"

# 自动生成错误模式速查

**生成时间**: 2026-07-13 04:26
**扫描窗口**: 最近 24h
**发现模式**: 5 种

## 🟡 TimeoutError (出现 1920 次, 严重度 2)

**文件**: agent.log, agent.log.1, ai_collector.log, errors.log, errors.log.1

**示例**:
```
2026-07-11 20:06:53,813 WARNING gateway.platforms.qqbot.adapter: [QQBot:1903873816] WebSocket closed: code=4009 reason=Session timed out
```
```
2026-07-11 20:36:56,530 WARNING gateway.platforms.qqbot.adapter: [QQBot:1903873816] WebSocket closed: code=4009 reason=Session timed out
```

## 🟡 ConnectionError (出现 98 次, 严重度 3)

**文件**: agent.log.1, errors.log.1, self_check.log

**示例**:
```
2026-07-09 15:38:51,612 WARNING agent.model_metadata: Failed to fetch model metadata from OpenRouter: HTTPSConnectionPool(host='openrouter.ai', port=443): Max retries exceeded with url: /api/v1/models
```
```
2026-07-09 16:31:01,010 WARNING [20260709_153855_a84129] agent.conversation_loop: API call failed (attempt 1/1) error_type=APIConnectionError thread=Thread-7 (run_agent):6403059712 provider=custom bas
```

## 🟡 Import error (出现 6 次, 严重度 2)

**文件**: agent.log.1, errors.log.1

**示例**:
```
2026-07-07 09:56:04,261 WARNING [20260706_224754_b222ae0e] agent.tool_executor: Tool terminal returned error (1.68s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 4, in <m
```
```
2026-07-07 09:56:33,769 WARNING [20260706_224754_b222ae0e] agent.tool_executor: Tool terminal returned error (1.86s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 13, in <
```

## 🟢 JSON parse error (出现 4 次, 严重度 1)

**文件**: self_check.log

**示例**:
```
WARNING agent.conversation_loop: API call failed (attempt 3/5) error_type=JSONDecodeError thread=ThreadPoolExecutor-1_0:6432468992 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.com/v1
```
```
2026-06-28 13:14:29,961 WARNING [cron_ec6677e2b987_20260628_123052] agent.conversation_loop: API call failed (attempt 3/5) error_type=JSONDecodeError thread=ThreadPoolExecutor-1_0:6432468992 provider=
```

## 🟡 Permission denied (出现 3 次, 严重度 3)

**文件**: errors.log.1, self_check.log

**示例**:
```
2026-07-06 15:56:29,656 WARNING [20260706_154035_be1c32] agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <mod
```
```
WARNING agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <module>\nPermissionError: [Errno 13] Permission deni
```


## 修法 (通用)

- 1) 确认根因: 读完整 traceback, 不只看错误行
- 2) 加容错: try/except, 关键字段先 .get()
- 3) 加日志: 失败时打印完整上下文
- 4) 写 fact_store 标记已修
