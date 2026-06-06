# 2026-06-05 daily plist 三件套上线 — 实战 transcript

## 用户原始需求
1. 09:00 健康检查 cron: gateway + 平台 + 记忆 + 磁盘内存 + Telegram
2. 09:30 主动学习 cron: GitHub 官方仓库 + hermesagent.org.cn + 写 fact + 摘要推送
3. 21:00 整理 cron: 整理今日记忆 + 清理过期 + 写今日总结 + 推送

## 复用 vs 重写
- 复用 `~/.hermes/scripts/hermes_self_check.sh`（15min 已在跑）做参考
- 复用 `~/.hermes/scripts/ai_knowledge_collector.sh`（2:00 已在跑）做参考
- **没重写老脚本**（避免破坏现有 15min 自检的依赖）
- 新建 3 个独立脚本 + 3 个独立 plist:
  - `daily_health_check.sh` → `ai.hermes.daily-health.plist` (Hour=9, Minute=0)
  - `daily_active_learning.sh` → `ai.hermes.daily-learning.plist` (Hour=9, Minute=30)
  - `daily_evening_summary.sh` → `ai.hermes.daily-evening.plist` (Hour=21, Minute=0)

## 踩的 6 个新坑

### 坑 1: `launchctl list <label>` 走 print 路径
**症状**: self_check.sh 和新写的 daily_health_check.sh 都用
```bash
launchctl list "$LABEL" | grep -qE "^[0-9]"
```
判断 Gateway 是否在。**永远失败** — `launchctl list <label>` 走 print
路径返回 plist 块, 不走 list 路径。
**修法**:
```bash
LINE=$(launchctl list 2>/dev/null | grep -E "^[0-9-]+\s+[0-9-]+\s+$LABEL$")
```

### 坑 2: launchd Status 列是退出码不是状态
**症状**: `launchctl list` 显示 `-9  ai.hermes.gateway` — 以为 Gateway 死了
**真相**: `-9` = 上次退出的 exit code, 不是当前状态。Gateway 进程其实在
(PID 79290, 8642 /health 返回 200, 0.6ms)
**修法**: launchd 状态 + 进程探测 + HTTP 探测**三道防线**

### 坑 3: `hermes send` flag 形状
**症状**: 写 `--target "telegram" --message "..."` 全部静默失败
**真相**: hermes send 用 `-t <target> <message-positional>`, 跟 send_message tool 不一样
**修法**:
```bash
hermes send -t "telegram" "message"
```
**验证**: 成功会打印 `Sent to telegram home channel (chat_id: 7359677525)`

### 坑 4: 平台配置在 `hermes status` 不在 `hermes platforms list`
**症状**: 写 `hermes platforms list` 判平台状态, 命令不存在 (error: invalid choice)
**真相**: 子命令列表里只有 `status` / `chat` / `gateway` / ..., 没 `platforms`
**修法**:
```bash
HERMES_STATUS=$("$HERMES_HOME/hermes-agent/venv/bin/hermes" status 2>/dev/null)
echo "$HERMES_STATUS" | LC_ALL=C grep -qE "Telegram.*configured"
```

### 坑 5: `LC_ALL=C` 处理 ✓ U+2713
**症状**: macOS bash 默认 locale 下, grep 对 ✓ 字符处理不一致, 静默失败
**修法**: `LC_ALL=C grep -qE "Telegram.*configured"` — 不依赖 UTF-8 locale

### 坑 6: `exec >> "$LOG"` 跟 plist StandardOutPath 冲突
**症状**: `hermes_self_check.sh` line 7 `exec >> "$LOG" 2>&1` 把 stdout 全吞到
self_healer.log, plist 的 StandardOutPath=self_check.log 永远 0 字节 — 误判"自检没跑"
**修法**: 删 exec, 让 plist 的 StandardOutPath 赢
**验证**: 19:28:23 self_check.log 5617 字节, ✅ Gateway PID 79290 — 修对了

## 4 个 plist 改动汇总

| Plist | 改前 | 改后 | 触发原因 |
|---|---|---|---|
| ai.hermes.daily-health | (无) | 新建 09:00 | 用户要求 09:00 健康检查 |
| ai.hermes.daily-learning | (无) | 新建 09:30 | 用户要求 09:30 主动学习 |
| ai.hermes.daily-evening | (无) | 新建 21:00 | 用户要求 21:00 整理总结 |
| ai.hermes.self-check | StartInterval=900 + StandardOutPath=self_healer.log | StartCalendarInterval(0/15/30/45) + StandardOutPath=self_check.log | 修 exec 吞 stdout |

## 验证清单

```bash
# 1. 3 个新 plist loaded
launchctl list | grep -E "daily-health|daily-learning|daily-evening"
# 期望: 3 行

# 2. 3 个新脚本可执行 + 语法 OK
for f in daily_health_check daily_evening_summary daily_active_learning; do
    bash -n ~/.hermes/scripts/$f.sh && echo "✅ $f"
done

# 3. 手动跑一次完整链路
bash ~/.hermes/scripts/daily_health_check.sh 2>&1 | tail -10
# 期望: Sent to telegram home channel

# 4. 看 self_check 拆日志
ls -la ~/.hermes/logs/self_check.log
# 期望: size > 0, 19:28 之后

# 5. fact_store 实际增长
sqlite3 ~/.hermes/memory_store.db "SELECT count(*) FROM facts"
# 期望: 9 (清完) → 15+ (09:30 + 21:00 之后)
```

## 学到的: 3 个新 pitfall 候选

这 6 个坑里有 3 个值得加进 SKILL.md pitfalls 段 (已加):
1. `launchctl list <label>` 走 print 路径 (cross-cutting)
2. launchd Status 列是退出码 (任何 launchd 探测脚本)
3. `exec >>` 跟 StandardOutPath 冲突 (self-check 类脚本)

剩余 3 个 (hermes send flag / hermes status 平台 / LC_ALL=C ✓) 算 hermes CLI
特有, 跟 launchd 无关, 应该塞进 hermes-agent skill 或类似 umbrella。
