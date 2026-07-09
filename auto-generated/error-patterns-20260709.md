---
name: auto-1783549134-error-patterns
description: 自动从 ~/.hermes/logs/agent.log 抽取的错误模式 + 修法. 由 auto_skill_from_failure.py 生成.
triggers:
  - "TimeoutError"
  - "ConnectionError"
  - "JSON parse error"
  - "Import error"
  - "Permission denied"
  - "CDP attach failed"

# 自动生成错误模式速查

**生成时间**: 2026-07-09 06:18
**扫描窗口**: 最近 24h
**发现模式**: 6 种

## 🟡 TimeoutError (出现 2002 次, 严重度 2)

**文件**: agent.log, ai_collector.log, errors.log, gateway.error.log, gateway.log

**示例**:
```
2026-07-06 17:46:20,284 WARNING gateway.platforms.qqbot.adapter: [QQBot:1903873816] WebSocket closed: code=4009 reason=Session timed out
```
```
2026-07-06 18:16:22,904 WARNING gateway.platforms.qqbot.adapter: [QQBot:1903873816] WebSocket closed: code=4009 reason=Session timed out
```

## 🟡 ConnectionError (出现 214 次, 严重度 3)

**文件**: gateway.error.log, self_check.log, stealth_err.log

**示例**:
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=APIConnectionError thread=ThreadPoolExecutor-297_0:13053145088 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.
```
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=APIConnectionError thread=ThreadPoolExecutor-297_0:13053145088 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.
```

## 🟢 JSON parse error (出现 13 次, 严重度 1)

**文件**: gateway.error.log, self_check.log

**示例**:
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=JSONDecodeError thread=bg-review:13170929664 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.com/v1/ model=qwen
```
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=JSONDecodeError thread=ThreadPoolExecutor-279_0:13137276928 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.com
```

## 🟡 Import error (出现 9 次, 严重度 2)

**文件**: agent.log, errors.log, gateway.error.log

**示例**:
```
2026-07-07 09:56:04,261 WARNING [20260706_224754_b222ae0e] agent.tool_executor: Tool terminal returned error (1.68s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 4, in <m
```
```
2026-07-07 09:56:33,769 WARNING [20260706_224754_b222ae0e] agent.tool_executor: Tool terminal returned error (1.86s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 13, in <
```

## 🟡 Permission denied (出现 4 次, 严重度 3)

**文件**: errors.log, gateway.error.log, self_check.log

**示例**:
```
2026-07-06 15:56:29,656 WARNING [20260706_154035_be1c32] agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <mod
```
```
WARNING agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <module>\nPermissionError: [Errno 13] Permission deni
```

## 🔴 CDP attach failed (出现 3 次, 严重度 4)

**文件**: errors.log, gateway.error.log

**示例**:
```
2026-07-05 21:40:08,852 WARNING [20260705_212116_c3bff8] agent.tool_executor: Tool browser_cdp returned error (0.28s): {"error": "Target.attachToTarget failed: {'code': -32602, 'message': 'No target w
```
```
WARNING agent.tool_executor: Tool browser_cdp returned error (0.05s): {"error": "Target.attachToTarget failed: {'code': -32602, 'message': 'No target with given id found'}", "method": "Runtime.evaluat
```


## 修法 (通用)

- 1) 确认根因: 读完整 traceback, 不只看错误行
- 2) 加容错: try/except, 关键字段先 .get()
- 3) 加日志: 失败时打印完整上下文
- 4) 写 fact_store 标记已修
