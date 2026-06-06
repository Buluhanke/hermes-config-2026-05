---
name: mac-resource-cleanup
description: Mac mini 资源清理（内存/磁盘/进程）。触发词：内存、清理、释放、cleanup、free memory、磁盘、cache、purge、内置空间、cache、tmp、logs、AGENTS.md 红线。
---

# Mac Resource Cleanup — 资源清理 SOP

## 触发条件

- 内存 `Pages free × 16384 < 1 GB`（画像红线：< 1GB 主动清理）
- 磁盘某目录 > 1G 且是缓存/临时/日志性质
- 任何清理请求（"清一下" / "释放内存" / "cache 太多"）
- AGENTS.md 提到 "始终保留 4-6GB 可用" → 触发核对

## 清理前必走 3 步（违反任何一步 = 风险）

### 1. 核对 AGENTS.md 红线

```bash
cat ~/.hermes/AGENTS.md 2>/dev/null | grep -E "内存|可用|GB|MB"
# 或 grep "~/.hermes/AGENTS.md" 看是否有硬约束
```

**已知红线（2026-06-04）**：
- 内存：保留 4-6GB 可用
- CPU：单核不超 70%
- 超过红线先告警，再清理

### 2. 拟清理范围必须先给对账表

**永远遵循 "对账表+不扩大战果" 原则**（见 proactive-execution 规则）：
- 删什么 + 不动什么，两栏对账
- 一次只清用户明确说的目标
- 后续"还能清哪些"等用户主动问
- 不要列 11+12 行大表（用户会以为是扩大战果）

### 3. 涉及破坏性操作必须授权

| 操作类型 | 授权 |
|---|---|
| `rm -rf` 任何路径 | **必须授权** |
| `purge`（sudo） | 必须授权 + sudo 密码 |
| kill 进程 | 应用级可主动（自己管的），系统级必须授权 |
| 改系统设置 | 必授权 |
| du / df / vm_stat / ps | 主动干，不问 |
| 写清理日志到 ~/.hermes/logs | 主动干 |

## 清理目标分级（按授权需求）

### 🟢 零授权（可主动做）

1. **du / df / vm_stat 探测**（只读）
2. **清 Hermes 自带 logs 旧文件**（保留最近 3 个，删更早）
3. **清 state-snapshots 老备份**（30 天前）
4. **清 ~/.hermes/audio_cache**（TTS 临时产物）
5. **清 ~/.hermes/.env.bak.***（配置备份，保留最近 5 个）
6. **清 /tmp/hermes_* / /tmp/smoke_*.py 等临时文件**

### 🟡 一次授权后同类不需再问

- 删 ~/Library/Caches/<具体 app> 缓存（用户已授权后，同类 app 可直接删）
- 清 /Applications/.Trash
- 清用户级 browser cache（Chrome / Safari / Firefox）

### 🔴 必须重新授权

- 删 Documents / Desktop / Downloads
- 卸载 app
- 清 ~/.hermes/memory / fact_store / state.db
- 改 ~/.hermes/config.yaml
- 改 launchd 任务
- sudo 任何东西（除非用户主动给密码）

## 内存清理标准流程

```bash
# 1. 现状探测（不删）
vm_stat | head -10
# Pages free × 16384 = 可用 MB
# Pages active/wired/inactive = 已用 MB

# 2. 列出候选（按体积排序）
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -10
du -sh ~/.hermes/* 2>/dev/null | sort -rh | head -10

# 3. 给对账表（删什么 + 不动什么）

# 4. 等用户授权（用最简指令："A/B/C 选一个，或说'清'就全做"）

# 5. 执行（按对账表的 ①②③...）
rm -rf <target1> <target2> ...

# 6. 验证（vm_stat 前后对比 + 列剩多少）
vm_stat | head -10
du -sh <已清项>  # 应该是 not found
```

## 已知坑点（2026-06-04 实测）

### `sudo purge` 需要 TTY 密码

❌ 失败：`sudo: a terminal is required to read the password`
- 这是 macOS 限制，agent 走 SSH/non-TTY 时无解
- **替代方案**：让 inactive pages 自然被 OS 回收（等几分钟）或重启
- **不要**：尝试用 `echo password | sudo -S`（用户没授权泄露密码）

### Hermes state.db 不能动

`~/.hermes/state.db` 1.4G 是会话历史库，删了丢所有对话上下文。
- `state.db-wal` 是 WAL 文件，**绝不能删**
- `state-snapshots/<date>-pre-update/` 是 update 前备份，**保留**（回滚保险）
- **该目录的 1.4G 几乎全部来自 `state.db` 副本**（2026-06-04 实测：`pre-update/state.db` 单独占 1,467,244,544 字节 = 1.4G，其它 .env/auth.json/config.yaml 等加起来 < 50K）。所以 state.db 是单点大件 — 清理时别因为它大就想着"压一压"

### 大件 top 5（2026-06-04 实测）

```
1.0G  ~/Library/Caches/ms-playwright           # Playwright 浏览器二进制
673M  ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt  # Claude Desktop 更新器
218M  ~/Library/Caches/electron                 # Electron 通用
77M   ~/Library/Caches/Google                   # Chrome 缓存
72M   ~/Library/Caches/Homebrew                 # brew 下载缓存
```

**清 ms-playwright 风险**：下次需要 Playwright 时要重新下载（~400MB）
**清 claude ShipIt 风险**：下次启动 Claude Desktop 会重新下载更新

### "active 内存"清不掉

`rm -rf` 清缓存后，**Pages active 不会立即下降**。macOS 的 inactive pages 会在内存压力时自动 purge。
- 想立刻降 active：重启 / 等 OS 回收（通常几分钟）
- Pages free 立即上升 = 缓存清掉的效果
- Pages active 下降 = OS 自动回收的效果

## 用户工作流预期（2026-06-04 验证, 2026-06-05 补充）

用户说 "清理内存" → 期望流程：
1. agent 立即给现状（free / wired / active 数字）
2. 列出候选大件 top 5
3. 提对账表（删 X / 不动 Y）
4. 让用户选（A 全做 / B 只系统级 / C 你点名）
5. 拿到授权后清
6. 验证 + 对账 + 等几分钟看 active 降

**用户原话**：
- "A" / "继续" → 1 字回应 = agent 1 行执行 + 1 段对账
- "清" = 默认全做（A 方案），不重新问
- **"等会吧"** / "先这样" / "先放着" = 立刻停手 + 留状态备忘（数字 + 已做 + 未做的对账表 + 一个重启选项 R）, **不重复问"你确定吗"**, 不重复给"还能清哪些"清单. 用户会自己回 A/B/C/R.

**反模式**：
- ❌ 用户说"等会吧"后继续列"还可以清这些" → 触发"扩大战果"反感
- ❌ 把 20 行 ps 输出直接贴过去 → 触发"对账表失效"反感, 应该用 `macos-process-lifecycle` 的"进程组聚合"压到 5-6 行
- ❌ 一行连续问"你选 A 还是 B 还是 C 还是 D" → 用户拍板规则: 一次性给完整对账表 + 一个推荐选项, 不搞连续确认

## 关键背景

- Mac mini M4 24GB 统一内存
- macOS page size = **16384 字节**（非 4096），计算时 `pages × 16384`
- `~/Library/Caches` 是 user 唯一可主动清的大型缓存地
- `/Library/Caches` 和 `/private/var/folders` 需要 sudo
- `~/.hermes` 自带目录：chrome-debug 5.6G（**当前在用不能删**）、hermes-agent venv 3.9G（**不能动**）、state.db 1.4G（**不能动**）

## 日志轮转脚本的隐藏坑：`tee -a` 致双倍写入

`cleanup_hermes_logs.sh`（本 skill 配套脚本）和同目录的 `mem_patrol.sh` / `self_evolution.sh` 都是 **launchd 驱动** + 自己写 `$LOG` 文件。

**坑**：在脚本里写
```bash
log() { echo "..." | tee -a "$LOG"; }   # ← 错
```
+ plist 里
```xml
<key>StandardOutPath</key><string>/path/to/$LOG</string>
```
→ launchd 抓 stdout 也写到 `$LOG` → **每行双倍**（修前 11 行，修后 8 行）。

**修法**：
```bash
log() {
    msg="$(date '+...') $1"
    echo "$msg" >> "$LOG"   # 自己写
    echo "$msg"             # 让 launchd 再写一次 (但 launchd 的 stdout 已经会落 log)
}
```

**检测**：`tail -3 $LOG` 看每条是否双倍出现；或 `bash script.sh --dry-run` 后 `wc -l` 对比 stdout 行数。

**为啥这事归本 skill**：日志轮转的本质是"清掉过大的 log 文件"，但 log 文件因双写**翻倍膨胀** → cleanup 永远清不干净。

## 相关 skills

- `proactive-execution` — 主动执行原则 + 对账表 + 不扩大战果
- `macos-resource-debug` — 资源/性能诊断（CPU 飙高、卡顿）
- `macos-process-lifecycle` — 进程启停（清进程用）
- `hermes-model-switch` — 切模时也会触发（改 config.yaml 前可清理）

## 一键脚本

`scripts/cleanup_memory.sh`（路径 `~/.hermes/skills/devops/mac-resource-cleanup/scripts/cleanup_memory.sh`）

```bash
# 预览（不真删）
bash scripts/cleanup_memory.sh dry

# 真删（用户授权后）
bash scripts/cleanup_memory.sh
```

脚本封装了：vm_stat 前后对比、6 类缓存清理、Herems 日志/snapshots/audio_cache 清理、/tmp 临时文件清理。**只清理零授权范围（🟢 级），破坏性操作（🔴 级）不在脚本里**。

## 30 分钟空闲回收（与 `macos-process-lifecycle` 配合）

**用户偏好**（2026-06-04 拍板）：30 分钟无调用的吃资源服务自动杀，需要时按需拉起。

**实现位置**（不在本 skill 维护）：
- 模板脚本：`~/.hermes/skills/devops/macos-process-lifecycle/scripts/idle_kill.sh`
- 实战部署：cron job `2f527c06f06d`（用户自定义版 `~/.hermes/scripts/idle_killer.sh`）
- 监控名单 + 杀法 + 拉起法：见 `macos-process-lifecycle` SKILL.md
- **⚠️ cua-driver 特殊**：99% CPU 是空转，cputime delta 判断空闲会误判，详见 macos-process-lifecycle 的 cua-driver-idle-pattern.md

**什么时候触发**：
- 用户说"半小时不用就杀掉" / "按需启动" → 引用本节
- 内存/资源压力到 80% 红线 → 优先看本节"白名单/监控名单"，而不是 `rm -rf`
- 任何"杀 cua-driver/ToDesk" 类请求 → 必须先查 `mcp_cua_driver_*` 是否正在跑

## 自动定时监控（cron / launchd 触发）

**适用场景**：用户说"每 30 分钟检查一次内存/CPU"、"内存到 80% 自动清"、"CPU 高了自动释放缓存并写日志"——把清理从"用户触发"升级为"定时主动执行"。

**资源监控脚本模板**：`templates/resource_monitor.sh`（参数化：阈值/日志路径/清理项全用环境变量覆盖，部署时直接 `cp` 改路径就行）

**vm_stat 字段兼容**：解析内存百分比时要用兼容新旧 macOS 字段的写法——`Pages wired` 在新版（macOS 13+）变成 `Pages wired down`，`Pages occupied by compressor` 在新版可能消失。**直接套用 `references/macos-vmstat-fields.md` 里的 awk 模板**，别自己写。常见的"解析后内存 = 0% / 监控永远不告警"就是踩这个坑。

**触发方式**（按推荐度）：

| 方式 | 优点 | 缺点 | 何时用 |
|---|---|---|---|
| **cron** | 简单，一行配置 | PATH 极简（要显式 `/bin/bash` + 展开 `$HOME`）、无 retry | 用户明确说"cron"或简单定时 |
| **launchd plist** | 失败重试、stdout 落日志、可 watch_patterns | plist XML 较啰嗦 | 想监控任务健康度、要告警 |
| **Hermes cronjob (`no_agent=True`)** | 跟其他 Hermes 任务统一管理、走 skill 加载 | 要显式 no_agent 才能直接跑 shell | 已有 Hermes 任务在用 |

**cron 最小配置**（2026-06-05 实测可用）：
```bash
# 资源监控 — 每 30 分钟，stdout 单独落一份排查用
*/30 * * * * /bin/bash $HOME/.hermes/scripts/resource_monitor.sh >> $HOME/.hermes/logs/resource-monitor-cron.log 2>&1
```

**关键坑**：
- 阈值要写成**常量**（`THRESHOLD_MEM=80`）而不是环境变量——因为 macOS `cron` 不会保留 shell 启动时的环境。脚本里用 `THRESHOLD_MEM="${THRESHOLD_MEM:-80}"` 兜底。
- **`set -u` + awk 空匹配 = 崩**（vm_stat 字段缺失时）。**用 `set -o pipefail` 替代**。
- 清理动作只做**🟢 零授权范围**（Hermes 自己的 logs/audio_cache/tmp/sync），不要碰 🟡🔴（用户授权过才清 ~/Library/Caches、Documents 等）。这跟本 skill 的"破坏性操作原则"一致。
- `cron` 没有 `$PATH` 设置 → 必须用绝对路径（`/bin/bash` 而不是 `bash`）和 `$HOME` 完整路径。

**部署后必须验证**（3 步）：

1. 手动跑一次 `bash resource_monitor.sh`，看 `tail -10 $LOG` 数字合理（不是 0%）
2. 临时把阈值改低（如 `sed -i '' 's/THRESHOLD_MEM=80/THRESHOLD_MEM=40/'`）跑一次，确认清理逻辑触发、`RESULT` 行有清理前后对比 → **改回原阈值**
3. 用 `crontab -l` 确认任务已注册；想立刻看效果可以等下一次 tick 或手动 `bash` 一次

**关联文件**：
- 脚本模板：`templates/resource_monitor.sh`
- 字段兼容参考：`references/macos-vmstat-fields.md`
- 现有 `resource_monitor.sh`（实战版）：`~/.hermes/scripts/resource_monitor.sh`
