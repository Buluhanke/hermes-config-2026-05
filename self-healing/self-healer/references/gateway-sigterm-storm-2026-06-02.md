# Gateway SIGTERM Storm 诊断记录（2026-06-02）

## 事件时间线（June 1 15:20-16:07）

10+ 次 crash，PID 序列：53775 → 54241 → 54730 → 57094 → 57308 → 57569 → 57986 → 62566 → 64171

日志路径：`~/.hermes/logs/gateway_restart.log`

## SIGTERM 特征

```
Received SIGTERM — initiating shutdown
Shutdown context: signal=SIGTERM under_systemd=no parent_pid=21945 parent_name=? loadavg_1m=2.70 parent_cmdline='(unknown)'
```

**关键发现**：
- `parent_pid=21945` 但该进程已不存在（`ps -p 21945` 返回空）
- `parent_name=?` 说明父进程身份无法确认（可能是已退出的临时进程）
- `loadavg_1m=2.70` 触发条件：系统负载高时某机制会向 gateway 发送 SIGTERM
- 这是**外部强杀**，不是 `--replace` 接管，也不是 launchd 重启

## watchdog 行为

- 检测到 gateway DOWN 后用 `launchctl kickstart -k gui/` 拉起
- 15秒最小间隔防止频繁重启
- watchdog 能成功拉起每次 gateway，问题是出在外部 SIGTERM 源

## 两种 gateway 不稳定模式对比

| 特征 | SIGTERM storm (June 1) | launchd 服务消失 (June 2 08:54) |
|------|----------------------|--------------------------|
| 日志文件 | `gateway_restart.log` | `watchdog.log` |
| 诊断标志 | `parent_pid=21945` + `loadavg` | `Could not find service` |
| 间隔 | 60-180秒 | 15秒（kickstart） |
| 根因 | 外部 SIGTERM（机制不明） | launchd plist 注册损坏 |
| 进程状态 | 退出后被拉起 | 服务消失后被 kickstart |

## launchd I/O error 说明

当 `launchctl load` 报 `I/O error` 时，gateway 进程可能仍在运行（ps 有 PID）。这是 **launchd 服务注册损坏**，不是进程问题。

修复步骤：
```bash
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist
```

## June 2 08:54 服务消失事件

```
Could not find service "ai.hermes.gateway" in domain for user gui: 501
⚠️ Gateway DOWN — 执行kickstart...
⚠️ Gateway DOWN — 执行kickstart...
⚠️ Gateway DOWN — 执行kickstart...  (6次)
```

6次 kickstart 才拉起，说明 launchd plist 注册已损坏。unload → load 重建注册。

## 额度耗尽导致的连锁反应（June 1 深夜）

aicodee 额度耗尽后触发 403/429 错误，gateway 内部重试堆积 → 影响响应速度。
与 SIGTERM storm 是独立事件，但都导致命令慢。