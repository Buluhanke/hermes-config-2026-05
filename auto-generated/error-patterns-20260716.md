---
name: auto-1784133088-error-patterns
description: 自动从 ~/.hermes/logs/agent.log 抽取的错误模式 + 修法. 由 auto_skill_from_failure.py 生成.
triggers:
  - "TimeoutError"
  - "FileNotFoundError"
  - "ConnectionError"
  - "JSON parse error"
  - "Permission denied"

# 自动生成错误模式速查

**生成时间**: 2026-07-16 00:31
**扫描窗口**: 最近 24h
**发现模式**: 5 种

## 🟡 TimeoutError (出现 2001 次, 严重度 2)

**文件**: active_learner.log, agent.log, ai_collector.log, bootstrap-installer.log, errors.log

**示例**:
```
[05:00:08] 搜索结果: search failed: <urlopen error _ssl.c:1112: The handshake operation timed out>...
```
```
[05:00:16] AI回答: search failed: <urlopen error _ssl.c:1112: The handshake operation timed out>...
```

## 🟢 FileNotFoundError (出现 564 次, 严重度 1)

**文件**: mcp-stderr.log

**示例**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'qmd'
```
```
FileNotFoundError: [Errno 2] No such file or directory: 'qmd'
```

## 🟡 ConnectionError (出现 38 次, 严重度 3)

**文件**: self_check.log, stealth_err.log

**示例**:
```
WARNING agent.conversation_loop: API call failed (attempt 1/3) error_type=APIConnectionError thread=ThreadPoolExecutor-297_0:13053145088 provider=nv-qwen3.5-397b base_url=https://integrate.api.nvidia.
```
```
2026-06-28 10:43:04,848 WARNING [cron_ec6677e2b987_20260628_103005] agent.conversation_loop: API call failed (attempt 1/3) error_type=APIConnectionError thread=ThreadPoolExecutor-297_0:13053145088 pro
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

## 🟡 Permission denied (出现 2 次, 严重度 3)

**文件**: self_check.log

**示例**:
```
WARNING agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <module>\nPermissionError: [Errno 13] Permission deni
```
```
2026-07-06 15:56:29,656 WARNING [20260706_154035_be1c32] agent.tool_executor: Tool terminal returned error (0.96s): {"output": "Traceback (most recent call last):\n  File \"<string>\", line 2, in <mod
```


## 修法 (通用)

- 1) 确认根因: 读完整 traceback, 不只看错误行
- 2) 加容错: try/except, 关键字段先 .get()
- 3) 加日志: 失败时打印完整上下文
- 4) 写 fact_store 标记已修
