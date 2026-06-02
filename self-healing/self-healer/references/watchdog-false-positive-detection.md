# Watchdog 误检测：Gateway 运行中但被判断为 DOWN（2026-06-02）

## 问题

Watchdog 多次报告 `⚠️ Gateway DOWN — 执行kickstart...`，但 Gateway 实际在正常运行（PID 65355 从 01:56 持续运行到 10:22）。

## 根因

Watchdog 的检测逻辑使用 `pgrep -qf "hermes_cli.main gateway run"` 进行进程检测，但这个模式过于宽泛：

```bash
# watchdog 检测命令
pgrep -qf "hermes_cli.main gateway run"
```

问题：
- `pgrep -f` 匹配整个命令行，而 Gateway 进程的完整命令行可能因 launchd 包装而变化
- 当 Gateway 由 launchd 拉起时，进程名可能不精确匹配 `hermes_cli.main gateway run`
- 结果：检测不到正在运行的 Gateway → 误判为 DOWN → 执行 kickstart

## 诊断特征

从 `watchdog.log` 可以看到：
```
⚠️ Gateway DOWN — 执行kickstart...
⚠️ Gateway DOWN — 执行kickstart...  (重复6次)
⚠️ Gateway DOWN — 跳过kickstart (Gateway is already up)
```

最后一条 "Gateway is already up" 说明 watchdog 最终发现自己错了，但已经执行了多次无意义的 kickstart。

## 6月2日误检测时间线

```
01:56 - Gateway PID 65355 被 launchd 拉起（正常）
08:54 - watchdog 首次报告 "Gateway DOWN"（误检测开始）
08:54-09:55 - 连续6次 kickstart（均为误检测）
09:55 - watchdog 发现 Gateway 实际在运行，停止 kickstart
10:22 - PID 65355 正常退出（用户关闭或 Gateway 自身退出）
```

## 修复方向

改进 watchdog 的检测逻辑，使用更精确的进程匹配：
```bash
# 方法1：精确匹配进程名
pgrep -f "hermes_cli.main.*gateway.*run" | head -1

# 方法2：检查进程是否在监听端口（更可靠）
lsof -i :8222 2>/dev/null | grep LISTEN | grep -v grep

# 方法3：检查 gateway.sock 或状态文件
ls -la ~/.hermes/gateway.sock 2>/dev/null
```

## 预防

Watchdog 的检测逻辑不应仅依赖 `pgrep -qf`，而应结合：
1. 进程存在检查
2. 端口监听检查（如 8222）
3. heartbeat 文件/状态文件检查

三重检查可显著降低误检测率。