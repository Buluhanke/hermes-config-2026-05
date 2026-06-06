# 2026-06-04 — `ai.hermes.self-check` plist 挂载实操

## 背景
`~/.hermes/scripts/hermes_self_check.sh`（3034 字节，6/1 创建，权限 `-rwx--x--x`）已存在，但**没有任何 launchd 任务调度它**。导致画像里"15 分钟自检 + 30 分钟巡逻 + 连续 3 次超红线告警"全是空头支票。

诊断命令：
```bash
launchctl list | grep -i hermes    # 没有 self-check
ls ~/Library/LaunchAgents/ai.hermes.*.plist  # 没有 self-check.plist
ls ~/.hermes/logs/                  # 没有 self_check.log
```

## 实施（plist 模板）

`~/Library/LaunchAgents/ai.hermes.self-check.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.self-check</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aimac/.hermes/scripts/hermes_self_check.sh</string>
    </array>
    <!-- 每 15 分钟跑一次（900 秒）-->
    <key>StartInterval</key>
    <integer>900</integer>
    <!-- 启动后立即跑一次（避免等 15 分钟才第一次）-->
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/self_healer.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/self_healer_err.log</string>
</dict>
</plist>
```

**关键决策**：
- `StartInterval=900` 而非 `StartCalendarInterval`（calendar 只能整点/半点，15 分钟不行）
- `RunAtLoad=true` — 避免挂载后还要等 15 分钟才第一次跑
- `StandardOutPath` 必须**和脚本内的 `LOG=` 路径一致**（见下条 pitfall）

## 挂载 + 验证序列

```bash
# 1. 加载到 launchd
launchctl load -w ~/Library/LaunchAgents/ai.hermes.self-check.plist

# 2. 验证注册成功
launchctl list | grep self-check
# 期望:  <PID>  0  ai.hermes.self-check

# 3. 立即跑一次（不等 15 分钟）
launchctl kickstart "gui/$(id -u)/ai.hermes.self-check"
sleep 12

# 4. 看真实日志
tail -20 ~/.hermes/logs/self_healer.log
```

## 关键 Pitfall — 脚本日志路径 vs plist 日志路径必须对齐

**这次踩了**。脚本头有：
```bash
LOG="$HOME/.hermes/logs/self_healer.log"
exec >> "$LOG" 2>&1
```
所有 echo 都重定向到 `self_healer.log`。

但 plist 的 `StandardOutPath` 写成了 `self_check.log`。结果：
- launchd 跑出来的输出 → `self_check.log`（空，因为脚本不用它）
- 实际工作日志 → `self_healer.log`（但你按 plist 找它会以为没跑）

**症状**：`launchctl list` 显示 PID，进程正常退出，但 `self_check.log` 是空文件 → 误以为"没跑"。

**修复**：改 plist 的 `StandardOutPath` 对齐脚本的 `LOG=`，然后**重 load**（plist 修改必须 `unload` + `load` 才生效）。

**通用原则**：
- 如果脚本自己管日志，plist 的 `StandardOutPath/StandardErrorPath` 应**留空或与脚本 LOG 同步**
- 否则两份日志会让人困惑
- 验证后用 `tail` 看**脚本实际写的那个文件**，不是 plist 指向的那个

## 顺手发现 — 现有 2 个非阻塞问题

挂载后第一次自检报告的（不是新 plist 的问题）：

1. `ai.hermes.gateway-watchdog` plist **不存在**（自检脚本尝试 `launchctl load` 它时报 `Load failed: 5: Input/output error`）— 整个 watchdog 体系缺失
2. Hermes 配置里 `custom_providers` 下的 `alias` 字段不识别（2026-06-04 添加免费档时引入）— 启动报 `WARNING hermes_cli.config: providers.?: unknown config keys ignored: alias` ×2，不影响运行

**未修**（用户没要求）— 留给后续 audit session。

## 产出物

- 新 plist: `~/Library/LaunchAgents/ai.hermes.self-check.plist`（825 字节）
- 真正写入日志: `~/.hermes/logs/self_healer.log`（已有，append-only）
- 8 → 9 个 launchd 任务，纯增量
