# Telegram Platform Troubleshooting

## 连接池耗尽（Pool Timeout）— 2026-06-03

### 错误特征
```
telegram.error.TimedOut: Pool timeout: All connections in the connection pool are occupied.
Request was *not* sent to Telegram. Consider adjusting the connection pool size or the pool timeout.
```

### 发生条件
- Telegram bot 长时间运行（18+ 小时）
- 消息发送频率高或响应体较大
- httpx 连接池所有连接被占满，无法释放

### 诊断步骤
```bash
# 1. 查看 gateway 日志中的 pool timeout 错误密度
grep -n "Pool timeout" ~/.hermes/logs/gateway.log | wc -l

# 2. 查看错误首次出现时间
grep -n "Pool timeout" ~/.hermes/logs/gateway.log | head -3

# 3. 查看 gateway 进程运行时间
ps -p <pid> -o %cpu,%mem,rss,etime,state

# 4. 查看最后活跃时间（日志尾端）
tail -5 ~/.hermes/logs/gateway.log
```

### 修复方案：重启 Gateway

Gateway 进程卡死但主进程还在，重启即可恢复：

```bash
# 查找 gateway 进程 PID
ps aux | grep "hermes_cli.main gateway" | grep -v grep

# 重启 gateway（后台运行，自动 fork）
pkill -f "hermes_cli.main gateway"
sleep 3
nohup ~/.hermes/hermes-agent/venv/bin/hermes gateway run --replace &
```

### 预防方案
- Telegram 连接池大小可在 platform config 中调（如果有的话）
- 高频消息 bot 建议每日自动重启 gateway cron
- 监控 `gateway.log` 中 `Pool timeout` 出现频率，超过 10 次/小时则告警

### ⚠️ 重启后"Another gateway instance"陷阱（2026-06-03 新增）

如果 `pkill` 杀得不彻底，旧进程还没完全退出就启动新进程，会看到：
```
ERROR gateway.run: Another gateway instance (PID 2931) started during our startup. Exiting to avoid double-running.
```

**处理**：
```bash
# 1. 彻底杀掉所有 gateway 进程（杀两次确保干净）
pkill -f "hermes_cli.main gateway"
sleep 2
pkill -f "hermes_cli.main gateway"   # 第二次杀残留

# 2. 清理 pid 文件（如果存在）
rm -f ~/.hermes/*.pid ~/.hermes/gateway.pid 2>/dev/null

# 3. 等待旧进程完全退出再启动
sleep 3

# 4. 启动新 gateway
nohup ~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace > ~/.hermes/logs/gateway_restart.log 2>&1 &

# 5. 验证
sleep 6
ps aux | grep "hermes_cli.main gateway" | grep -v grep
```

**判断哪个是旧进程**：看 `ELAPSED` 列，运行时间最长的那个是旧进程。
**判断新进程是否成功**：日志出现 `✓ telegram connected` 且无 `Another gateway instance` 错误。

### 相关日志路径
```
~/.hermes/logs/gateway.log      # 主日志
~/.hermes/logs/gateway.error.log # 错误专日志
~/.hermes/logs/agent.log        # Agent 任务日志
```

---

## 其他已知 Telegram 失败模式

### edit message 超时
```
ERROR gateway.platforms.telegram: [Telegram] Failed to edit Telegram message NNNNN: Pool timeout...
```
消息编辑失败不影响后续消息，但会导致 Telegram 端编辑功能失效。

### 重试机制
Telegram platform adapter 内置 3 次重试（1s → 2s → 4s），每次重试间隔翻倍。
Pool timeout 发生在重试过程中说明连接长期被占用，重启是唯一有效解。

---

## 验证修复
重启后观察：
```bash
# 确认进程新启动（etime 重置）
ps aux | grep "hermes_cli.main gateway" | grep -v grep

# 确认日志正常
tail -10 ~/.hermes/logs/gateway.log
```
正常情况：日志持续写入，无 Pool timeout。