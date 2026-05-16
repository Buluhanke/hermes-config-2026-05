# Gateway 重启验证 checklist

每次执行 `hermes gateway restart` 或配置变更后的重启后，**必须**按以下顺序验证，不要跳过步骤直接告诉用户"好了"。

## 验证步骤

```bash
# Step 1: 端口监听（gateway 进程是否在跑）
lsof -i :8642 2>/dev/null | grep LISTEN
# 预期：显示一行 Python 进程监听 8642

# Step 2: 健康检查（进程是否响应）
curl -s --connect-timeout 5 http://127.0.0.1:8642/health
# 预期：{"status": "ok", "platform": "hermes-agent"}

# Step 3: 平台连接状态（从日志确认全部在线）
tail -10 ~/.hermes/logs/gateway.log | grep -E "✓|Ready|Connected"
# 预期：每个平台都有 ✓ connected / Ready
```

**Step 1 通过 + Step 2 通过 → gateway 基本正常。**
**Step 3 全部 ✓ → 所有平台在线，可以告知用户。**

## 常见失败模式

### 1. Gateway crash loop
**日志特征**：
```
Exiting with code 1 (signal-initiated shutdown without restart request)
# ← 紧接着立刻出现：
Starting Hermes Gateway...
```
说明旧进程退出后新进程立刻启动，周而复始。

**诊断**：
```bash
# 查看 gateway.log 是否有 ERROR 或异常退出
grep -E "ERROR|exception|traceback|Exiting with code 1" ~/.hermes/logs/gateway.log | tail -20
```

**修复**：先 kill 残留进程，再手动启动
```bash
# 找出所有 gateway 相关进程
ps aux | grep -E "hermes.*gateway|hermes_cli.*run" | grep -v grep | awk '{print $2}'
# 全部 kill
kill <PID1> <PID2>
# 等待释放端口
sleep 3
# 手动启动
~/.hermes/hermes-agent/venv/bin/hermes gateway run
```

### 2. 进程僵死（端口监听中但不响应）
**症状**：`lsof` 显示端口监听，但 `curl health` 超时或连接被拒绝。

**诊断**：
```bash
# 看进程当前状态
ps aux | grep $(lsof -ti:8642) | grep -v grep
# 查看进程启动时间
ps -o pid,lstart,command $(lsof -ti:8642)
```

**修复**：强制重启
```bash
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
sleep 3
lsof -i :8642 2>/dev/null | grep LISTEN || echo "未启动"
```

### 3. 平台未连接（gateway 在跑但 QQ/微信断线）
**症状**：Step 1/2 通过，但 Step 3 只有部分平台 ✓。

**诊断**：
```bash
# 查看具体哪些平台未连上
tail -30 ~/.hermes/logs/gateway.log | grep -E "disconnected|failed|error|retry" | grep -v "rate limited"
```

**修复**：通常是 credential 问题（QQ 100016 / 微信 token 过期），参考 `references/qqbot-diagnostic-check.md`。

## 用户通知原则

- **不要**在验证完成前说"已重启好了"——用户那边终端还在等待连接，会感觉"失联"
- **等三项全部通过**再告知用户服务已恢复
- 如果验证发现问题，先告知用户"正在处理"，修好再说"好了"
- 重启期间用户发的消息会在 gateway 就绪后自动送达，不需要手动补发

## 背景

Gateway 重启时：
1. 旧进程收到 SIGTERM，开始 shutdown sequence（关闭 WebSocket、通知活跃会话）
2. 新进程启动，重新连接所有平台（QQ 握手、微信认证等）
3. 全程约 5-15 秒，期间用户终端显示"连接断开"是正常的

如果用户终端在 30 秒后仍然显示断线，说明 Step 1/2/3 出了问题，需要诊断。
