# launchd SIGTERM 与 KeepAlive 恢复指南

## 现象

Gateway 进程被 SIGTERM 优雅终止（pid=1，parent_cmdline='(unknown)'），KeepAlive 机制没有在预期时间内自动拉起，导致 Telegram/QQBot/微信全部掉线。

## 日志特征

```
WARNING gateway.run: Shutdown context: signal=SIGTERM under_systemd=yes parent_pid=1 parent_name=? loadavg_1m=3.70 parent_cmdline='(unknown)'
```

launchd 发 SIGTERM 是系统行为，Gateway 正常响应并优雅退出。

## 手动恢复

```bash
# 重新加载 LaunchAgent
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist

# 验证是否在线
tail -5 ~/.hermes/logs/gateway.log
```

## 验证清单

- [ ] `launchctl list | grep hermes` 显示 Running
- [ ] `gateway.log` 出现 "Starting Hermes Gateway..."
- [ ] "Connecting to telegram..." → "✓ telegram connected"
- [ ] "Connecting to qqbot..." → "✓ qqbot connected"
- [ ] "Connecting to weixin..." → "✓ weixin connected"
- [ ] `launchctl list | grep hermes` 显示 pid 正在运行

## 根因分析（2026-05-18）

launchd 的 KeepAlive 设置为 `SuccessfulExit=false`，意味着进程退出后应该自动重启。但在 SIGTERM 后有等待期，期间进程处于未运行状态。

loadavg 偏高（3.31-3.70）时更容易触发系统级重启。
