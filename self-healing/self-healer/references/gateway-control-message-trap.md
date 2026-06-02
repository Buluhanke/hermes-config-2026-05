# Gateway 控制消息陷阱（2026-06-02）

## 问题描述

用户通过 Telegram 发送以下文字后，Gateway 执行优雅关闭并广播 "Your current task will be interrupted."：
```
⚠️ Gateway shutting down — Your current task will be interrupted.
```

## 根因

这是 Gateway 内置的**控制消息机制**，定义在 `gateway/run.py`：

```python
_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "Gateway shutting down"

_CONTROL_INTERRUPT_MESSAGES = frozenset({
    "gateway shutting down",
    "gateway restarting",
    "stop requested",
    "session reset requested",
    "execution timed out",
    "sse client disconnected",
})
```

当收到的消息**小写化后**匹配这些关键词，Gateway 会触发优雅关闭流程：
1. 中断所有活跃会话
2. 广播 "Your current task will be interrupted." 给所有会话
3. 执行优雅退出

## 诊断

```bash
grep "Your current task will be interrupted" ~/.hermes/logs/gateway.log
# 会看到 inbound message 就是用户发送的这条文字

grep "Ignoring control interrupt message" ~/.hermes/logs/gateway.log
# 查看被忽略的控制消息（可能是历史遗留）
```

## 影响

- 正在处理的任务被强制中断
- 用户体验为"网关突然通知我要中断"

## 处置

**无需修复（是功能）**，但需告知用户：
> ⚠️ **不要发送** "Gateway shutting down"、"stop requested"、"reset" 等控制消息关键词，否则网关会执行关闭广播。

如误发，可忽略（关闭广播不会真的杀死进程，Gateway 会在 `KeepAlive=true` 下自动重启）。