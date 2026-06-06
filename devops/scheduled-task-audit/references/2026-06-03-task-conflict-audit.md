# 2026-06-03 Hermes 自进化任务冲突审计

## 背景

用户提问"查一下所有自动学习的任务有没有冲突"，触发对 Hermes
全部 scheduled-task 表面的全面审计。

## 审计对象

| 来源 | 任务数 | 类型 |
|---|---|---|
| `~/Library/LaunchAgents/ai.hermes.*.plist` | 7 | launchd |
| `crontab -l` | 0 | cron |
| `cronjob` MCP tool | 0 | 进程内调度 |
| `~/.hermes/scripts/*.{sh,py}` 自带调度注释 | 2 | 孤儿（无调度） |

## 发现

### ✅ 保留 — 3 个 self-evolution plist

| Plist | Schedule | 行为 |
|---|---|---|
| `ai.hermes.self-evolution` | `StartInterval=1800` | `self_evolution.sh hourly` — 轻量 PID/端口/磁盘巡检 |
| `ai.hermes.self-evolution-daily` | `Hour=9 Minute=0` | `self_evolution.sh daily` |
| `ai.hermes.self-evolution-weekly` | `Hour=9 Minute=0 Weekday=1` | `self_evolution.sh weekly` |

**冲突**：周一 09:00 daily + weekly 同时触发。两者调用同一脚本
不同 mode，行为有差异（daily 跑反思/压缩/技能沉淀；weekly 跑
总结/清理），无功能冲突但资源 ×2。

### ⚠️ 半残废 — `daily_learning.sh`

- 调度：❌ 无（`crontab -l` 为空；未挂 launchd）
- 实际行为：脚本顶部 log 完整，但 3 个采集步骤全为
  `log "[SKIP] ... - 待 CDP 脚本完善"`，没有真实工作
- 风险：包含 `pkill -9 -f "Chrome"` 和 `open -a "Google Chrome" --args --remote-debugging-port=9222`
  —— 若被误触发，**会杀掉用户所有 Chrome 进程并以 9222 端口重启**，
  破坏 `~/.hermes/chrome-debug` 9333 端口 CDP 会话

**判定**：🔴 DELETE 候选

### ⚠️ 注释失效 — `ai_knowledge_collector.sh`

- 调度：❌ 无（脚本注释 `# Cron: 0 3 * * * ...` 已与真实 crontab 脱节）
- 脚本本身完整：调用 6 个 AI 站点问答采集，写入 `~/.hermes/knowledge/ai_collected/`
- 注释里的 cron 路径未生效，crontab 为空
- 风险：低（无 pkill，无服务重启）

**判定**：🔧 RECONFIGURE — 挂个真正可用的 launchd 或干脆删掉注释

### ✅ 安全 — 其他 launchd plist

| Plist | Schedule | 评估 |
|---|---|---|
| `ai.hermes.chrome` | KeepAlive=false（按需） | ✅ |
| `ai.hermes.dashboard` | KeepAlive=true | ✅ |
| `ai.hermes.gateway` | KeepAlive=true | ✅ |
| `com.aimac.hermes-chrome-debug` | KeepAlive（持久） | ✅ |

## 修复建议

1. 保留 3 个 self-evolution plist（无大冲突）
2. 删除 `daily_learning.sh`（半残废 + 风险源）
3. `ai_knowledge_collector.sh` 二选一：
   - A. 挂 launchd plist（每天 03:00）
   - B. 删除 cron 注释，改写为"按需手动运行"
4. 加 1 行注释到 self_evolution.sh 顶部，提醒 daily + weekly 周一 09:00 双发

## 验证

```bash
# 删除后检查
ls ~/.hermes/scripts/daily_learning.sh 2>&1   # 应报错

# 检查 Chrome CDP 仍在 9333 监听
lsof -nP -iTCP:9333 -sTCP:LISTEN | grep -i chrome
# 应输出 chrome 进程
```

## 关键教训

- "自检"脚本不要混搭"破坏性副作用"。`daily_learning.sh` 的
  `pkill -9 -f Chrome` 是为了保证 CDP 可用，但放在一个 90% 时间
  都没真正在工作的脚本里，等于一颗随时会响的哑弹。
- 注释里的 cron schedule **必须真实存在**。时间一长注释与
  实际配置会脱节，调试时反而误导。
- 多个 launchd plist 调用同一脚本的不同 mode 是合理的，但应该
  在脚本顶部明确写出"哪些 mode 互相不冲突 / 哪些会同时跑"。

## 衍生动作

- 写入 skill `scheduled-task-audit`（新建，6 步审计方法论）
- 写入 skill `gateway-http-pool-tuning` v1.2.0（追加 post-incident
  call-site audit 表格，记录本会话的 4 处新迁移）

---

# 2026-06-03 修复执行记录

用户回答"执行"后，按建议清除了实际威胁 + 给 ai_knowledge_collector
挂上真正可用的 launchd 调度。

## 实际动作

| 操作 | 命令 | 结果 |
|---|---|---|
| 删除半残废脚本 | `rm ~/.hermes/scripts/daily_learning.sh` | ✅ 删除 |
| 清理过时 pyc | `rm ~/.hermes/scripts/__pycache__/daily_task.cpython-311.pyc` | ✅ |
| 新建 plist | `~/Library/LaunchAgents/ai.hermes.ai-knowledge-collector.plist` | Hour=3, Minute=0 |
| 加载 plist | `launchctl load -w ...plist` | PID 已注册 |

## 用户随后改时间

"最早的任务是几点" → "改为每天01点"

修改步骤（**关键路径**）：

```bash
# 1. plutil 改 Hour 3 → 1
# 2. 必须 reload 才生效（仅改文件 launchd 内存不刷新）
launchctl unload ~/Library/LaunchAgents/ai.hermes.ai-knowledge-collector.plist
launchctl load -w ~/Library/LaunchAgents/ai.hermes.ai-knowledge-collector.plist
# 3. 验证
plutil -extract StartCalendarInterval xml1 -o - ~/Library/LaunchAgents/ai.hermes.ai-knowledge-collector.plist
launchctl list | grep ai-knowledge-collector
```

`unload` 不会自动 `load`；必须显式 `load -w`（`-w` = 持久化注册到
LaunchAgents 目录，开机自启）。改完用户不 reload 任务会"消失"。

## 最终时间表

| 任务 | 时间 | 备注 |
|---|---|---|
| `ai-knowledge-collector` | **01:00** 每天 | 6站AI问答 |
| `self-evolution` | 每30min | 巡检 |
| `self-evolution-daily` | 09:00 每天 | 深度学习 |
| `self-evolution-weekly` | 周一 09:00 | 周报 |

---

# 2026-06-03 学习系统重写（闭环重建）

用户说"学习的方向和路径明确吗" → 我坦白说不闭环 → 用户答"修复"。

**问题诊断**：v1 三脚本断链 — `daily_evolution.sh` log 字符串无产出；
`ai_knowledge_collector.sh` 写文件但 FTS5 不查；`self_evolution.sh`
模式匹配 + log +1 但行为不变。

**重写后**（已实测跑通）：

| 脚本 | 旧 → 新 |
|---|---|
| `self_evolution.sh` (293行) | grep模式 + log字符串 → **grep模式 + 自动修复 + 写fact到FTS5 + 生成可被daily消费的笔记** |
| `ai_knowledge_collector.sh` (96行) | 写了没人读 → **写完入FTS5, 下次MemoryManager.prefetch_all()自动检索** |
| `daily_evolution.sh` | 重复且断链 → **删除（并入self_evolution.sh daily）** |

**实测闭环**：

```
$ ~/.hermes/scripts/self_evolution.sh hourly
... 工具错误 15 次/小时 → 新 fact=1, 磁盘=40%

$ sqlite3 ~/.hermes/memory_store.db \
    "SELECT content FROM facts WHERE category='error_pattern'"
小时工具错误聚集: 15 次 — 需要 daily 分析分布   ← 已入库

$ ~/.hermes/scripts/self_evolution.sh daily
✅ 每日笔记: ~/Obsidian/.../2026-06-03-每日学习.md (fact=1, 修复=0)
```

**关键 bug**（已修）：`set -uo pipefail` + `if [ "$DISK" -gt 80 ]` 在
第一次跑时 `$DISK` 未定义 → `unbound variable` 错误退出。修复用
`${DISK:-0}` 默认值。

**周报文件名坑**：用 `date +%Y-W%W`（Monday-based）做文件名，标题用
`%V`（ISO），导致 `2026-W22.md` 文件里写着"2026-W23"标题，文件名与
标题脱节。统一为 `%V`。

## 闭环验证清单

跑通后必须验证：

```bash
# 1. fact 真进库
sqlite3 ~/.hermes/memory_store.db \
  "SELECT category, COUNT(*) FROM facts GROUP BY category"
# 应有 error_pattern / infrastructure 等类别

# 2. FTS5 自动索引（schema 自带 trigger）
sqlite3 ~/.hermes/memory_store.db \
  "SELECT content FROM facts_fts WHERE facts_fts MATCH 'tools'"
# 应能命中

# 3. Obsidian 笔记生成
ls -lt ~/Obsidian/迅龙贸易/AI进化/2026-06-03-每日学习.md
# 应有当天笔记，含 4 个量化数字

# 4. 清理后 fact 总数稳定
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts"
# v1 留 34 条，hourly 跑完 +1，daily 拉取不增加，weekly 拉取不增加
```

## 旧脚本备份位置

`~/.hermes/scripts/_old/{self_evolution.sh,daily_evolution.sh,ai_knowledge_collector.sh}.bak`

7天后无问题可删。
