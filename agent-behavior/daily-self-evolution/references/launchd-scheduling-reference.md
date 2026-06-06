# launchd 自进化任务管理参考

## 1. Hermes 当前 launchd 任务表（2026-06-03 audit）

| Label | 调度 | 行为 | 端口/PID 依赖 |
|---|---|---|---|
| `ai.hermes.gateway` | KeepAlive | 网关主进程 | — |
| `ai.hermes.chrome` | KeepAlive | Chrome debug 守护 | 9333 |
| `ai.hermes.dashboard` | KeepAlive | 仪表盘 | — |
| `com.aimac.hermes-chrome-debug` | RunAtLoad | Chrome debug 实例 | 9333 |
| `ai.hermes.self-evolution` | StartInterval=1800s | 轻量巡检 | — |
| `ai.hermes.self-evolution-daily` | 09:00 每天 | daily mode | — |
| `ai.hermes.self-evolution-weekly` | 周一 09:00 | weekly mode | — |
| `ai.hermes.ai-knowledge-collector` | 01:00 每天 | 6站AI问答 | Chrome 9222/9333 |

**时间避让原则**：
- 跨日任务（凌晨）放 01:00–04:00
- 9:00–10:00 是用户活跃窗口，避免长任务
- 周一 09:00 daily + weekly 跑同一脚本不同 mode，OK 不需要错开

## 2. launchd plist 模板（最小可工作）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.<name></string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aimac/.hermes/scripts/<script>.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>1</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/<name>.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/<name>_err.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**关键字段**：
- `Label` 必须唯一，格式 `ai.hermes.<name>`
- `StandardOutPath/ErrorPath` 必填，否则日志进 system log 找不到
- `RunAtLoad: false` 是日常任务默认值（避免开机即跑与守护进程争抢资源）
- `KeepAlive` 用 `true`（无 dict 形式）= 只要进程退出就重启

## 3. 修改 plist 后必须 reload

```bash
# 编辑 plist 后
plutil -lint ~/Library/LaunchAgents/ai.hermes.<name>.plist  # 语法检查

# 必须 unload + load -w 才会生效
launchctl unload ~/Library/LaunchAgents/ai.hermes.<name>.plist
launchctl load -w ~/Library/LaunchAgents/ai.hermes.<name>.plist

# 验证
launchctl list | grep <name>
plutil -extract StartCalendarInterval xml1 -o - ~/Library/LaunchAgents/ai.hermes.<name>.plist
```

**坑**：
- `unload` 后**不会自动 load**，忘记 load -w 任务会"消失"
- 改 plist 不 reload → launchd 内存里仍是旧值
- `load -w` 的 `-w` = 持久化注册到 `~/Library/LaunchAgents/`，开机自启

## 4. 半残废脚本识别清单

**判定标准**（任一即触发清理）：

| 信号 | 检测命令 | 阈值 |
|---|---|---|
| 步骤含 `SKIP`/`TODO` | `grep -c "SKIP\|TODO" script.sh` | ≥50% 步骤 |
| 含 `pkill -9 -f` | `grep -n "pkill -9" script.sh` | 配合残废才清理 |
| 注释 cron 失效 | `grep -E "^#.*[Cc]ron" script.sh` + `crontab -l` | 注释有，crontab 空 |
| 无近期日志 | `ls -lt logs/*.log | head` | >30天无新日志 |
| 进程未运行 | `launchctl list | grep <name>` | PID 字段为 0 |

**2026-06-03 清理案例**：
- `~/.hermes/scripts/daily_learning.sh`：3 个采集步骤全 SKIP + `pkill -9 -f Chrome` → **删除**
- `~/.hermes/scripts/__pycache__/daily_task.cpython-311.pyc`：老 pyc → **删除**
- `ai_knowledge_collector.sh` 注释里写 `Cron: 0 3 * * *` 但 crontab 空 → 挂到 `ai.hermes.ai-knowledge-collector.plist`

## 5. 排查命令速查

```bash
# 看所有 hermes launchd 任务
launchctl list | grep -i hermes

# 看具体 plist 的调度
plutil -extract StartCalendarInterval xml1 -o - ~/Library/LaunchAgents/ai.hermes.X.plist

# 看具体 plist 的可执行命令
plutil -extract ProgramArguments xml1 -o - ~/Library/LaunchAgents/ai.hermes.X.plist

# 跑一次 plist 调度的脚本（debug 用）
bash ~/.hermes/scripts/<script>.sh

# 看自进化脚本的所有定时痕迹
grep -E "while|interval|time\.sleep|cron" ~/.hermes/scripts/*.sh
```

## 6. 跨工具协调：launchd + cronjob + cron

| 调度器 | 配置位置 | 适合场景 |
|---|---|---|
| launchd (plist) | `~/Library/LaunchAgents/*.plist` | Hermes 主用（macOS 原生） |
| cronjob (Hermes CLI) | `~/.hermes/cron/jobs.json` | agent-driven 任务，UI 可视化 |
| crontab | `crontab -l` | macOS 上 Hermes 不依赖，仅留作兼容 |
| systemd | N/A | macOS 无此服务 |

**规则**：同一任务不要同时挂到 launchd 和 cronjob，会双重触发。Hermes 主用 launchd，cronjob 用于需要从 LLM 视角触发的场景。

## 7. 日志轮替建议

launchd 输出日志会无限增长。`~/.hermes/logs/*.log` 大于 2G 时清理：

```bash
# 清理 15 天前的日志（非破坏性）
find ~/.hermes/logs -name "*.log" -mtime +15 -delete

# 看哪个日志最大
ls -laSh ~/.hermes/logs/ | head -5
```
