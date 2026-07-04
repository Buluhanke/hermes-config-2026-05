# launchd plist 排查 + 字段陷阱（2026-07-04 落地）

## 背景

用户报 "Telegram 一直提醒发送『📚 早 9:30 学习完成』"。

`hermes cron list` 跑一遍,18 个 job 里**没有一个**是 daily-learning——`4862dc17ff7e` 是「每日 skill 采集」,03:00 跑且已 paused;剩 17 个都不是 9:30 学习任务。

真凶在 `~/Library/LaunchAgents/ai.hermes.daily-learning.plist`,调的是 `~/.hermes/scripts/daily_active_learning.sh`。

**根因教训**:
1. `hermes cron list` 只看 Hermes 内部 cron 引擎,**macOS launchd 完全独立**,plist 是另一套调度系统
2. 这个 plist 写的是 `StartInterval=1800`(每 30 分钟一次),跟脚本里 `📚 早 9:30` 的文案 / 注释 "每天 09:30" **完全对不上**——所以才会一直刷屏
3. 如果当时只信注释不去读 plist,删了 script 之后 launchd 还会每 30 分钟报 "script not found",silent error 持续

## 排查 SOP（用户报 "定时通知刷屏" / "X 任务一直跑" 0 思考照抄）

```bash
# ===== 第 1 步: 3 个调度源全部拉清单（并行, 0 思考） =====

# A. Hermes 内部 cron
hermes cron list

# B. macOS launchd（按关键词过滤）
launchctl list | grep -iE 'hermes|<关键词, 比如 daily|learning|9:30>'

# C. 系统 crontab（macOS 默认有, 但几乎不用）
crontab -l 2>/dev/null

# ===== 第 2 步: 找到嫌疑 plist 后, 立刻读实际配置 =====

# 不要信注释 / 文件名, 直接 plutil 读字段
plutil -p ~/Library/LaunchAgents/ai.hermes.daily-learning.plist

# 重点确认 4 个字段:
#   - Label:    唯一标识, 重复会互相覆盖
#   - ProgramArguments: 实际跑哪个脚本
#   - StartInterval (秒): 间隔, 1800=30分钟, 86400=1天
#   - StartCalendarInterval: 定时, 必须有 Hour + Minute
#   - RunAtLoad: true/false, 决定开机是否跑

# ===== 第 3 步: 卸载（不删文件, 先观察） =====

launchctl unload ~/Library/LaunchAgents/<name>.plist

# 验证: launchctl list | grep <name> 期望无输出

# ===== 第 4 步: 问用户是否删 plist 文件（破坏性操作） =====

# 删之前必问, 因为 plist 重建需要重写
rm ~/Library/LaunchAgents/<name>.plist

# ===== 第 5 步: 找脚本本体（可选清理, 留给用户拍板） =====

ls ~/.hermes/scripts/<script_name>.sh
# 默认不删, 报告给用户, 让用户决定
```

## plist 字段陷阱表

| 字段 | 错误 | 正确 | 现象 |
|---|---|---|---|
| `StartInterval` | 1800 (30 分钟) | 86400 (1 天) | 注释写"每天 9:30" 但实际每 30 分钟跑,刷屏 |
| `StartCalendarInterval` | 缺 `Hour`/`Minute` | `<integer>9</integer><integer>30</integer>` | 任务从未触发 |
| `Label` | 重复 (两个 plist 同 Label) | 唯一 | 后加载的覆盖前者, 行为随机 |
| `RunAtLoad` | 删了 | `<true/>` | 开机不跑, 只能等下次 tick |
| `StandardOutPath` | 写 `~/log/...` | 绝对路径 `/Users/<u>/.hermes/logs/...` | log 写不进, silent |
| `WorkingDirectory` | 没设 | 绝对路径 | 脚本里相对路径解析错, 找不到文件 |
| `EnvironmentVariables` | PATH 没设 | `<key>PATH</key><string>/usr/local/bin:/usr/bin:/bin</string>` | 脚本里 `gh`/`ddgs` 等找不到,silent |
| `KeepAlive` | 误开 | false | 进程死了自动重启, 资源被吃掉 |

## 跟 cron 的区别（避免混淆）

| 维度 | `hermes cron` (内部) | macOS `launchd` (plist) |
|---|---|---|
| 配置位置 | Hermes DB | `~/Library/LaunchAgents/*.plist` |
| 可见性 | `hermes cron list` | `launchctl list` |
| 删 job | `hermes cron remove` | `launchctl unload` + `rm plist` |
| 用户级 vs 系统级 | 仅用户级 | 也有 `/Library/LaunchDaemons/` (系统级) |
| 典型用途 | 高频自检 / 看门狗 | 长驻守护 / 开机启动 |

**铁律**: 排查"定时任务"类问题时,**两个调度源都要查**,不能只看一个。

## 反面案例

差点被 plist 注释 "每天 09:30 主动学习" 骗了——脚本里写的也是 `📚 早 9:30 学习完成`,但 plist `StartInterval=1800` 实际是 30 分钟一次。**注释不算数,字段才算**。

如果当时偷懒只看脚本和注释,删脚本不删 plist,launchd 还会每 30 分钟报 "Script not found" silent error 持续。

## 关联

- `hermes-runtime-fortress` SKILL.md 第五节（新增 launchd 排查小节）
- `references/cron-job-script-pitfalls.md`（Hermes cron 的盲区, 本文件补 launchd 的盲区 — 互补）
- `hermes-task-watchdog` skill（任务级 watchdog, 不管调度源）
