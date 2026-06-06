# 跨平台 Handoff SOP — 2026-06-05 实测

> 来源：本会话用户问"两个机器人同步吗" → 我给他做出来的务实解法
> 适用：用户提"跨平台记忆 / 新会话能看到 / 跨机器人"等诉求时

## 1. 现状判断 (5 秒答)

| 维度 | 共享吗 | 怎么共享 |
|---|---|---|
| skills/ 根目录 | ✅ | 物理同步 |
| fact_store.db | ✅ | SQLite 单文件, FTS5 |
| MEMORY.md / USER.md | ✅ | 共享文本 |
| scripts/ | ✅ | 物理同步 |
| launchd plist | ✅ | 系统级 |
| **对话历史** | ❌ | 平台隔离, 设计如此 |
| **任务临时上下文** | ❌ | gateway 重启就丢 |

**老实跟用户说**：技能层 100% 共享, 上下文层 0% 共享。

## 2. 用户的真实诉求拆解 (避免答非所问)

用户说"两个机器人同步"时, 80% 是:

> "**我换平台问能接着干**" → 用 handoff 笔记 ✅

20% 是:

> "**我换平台用同一个 skill**" → 用 profile 配置诊断

**别混**。先问清哪个。

## 3. handoff 笔记实操 3 步

### Step 1: 创建目录 + 写当日笔记

```bash
mkdir -p ~/.hermes/daily_notes
# 写一个 4-6KB 的当日笔记, 内容包括:
#   跟用户 (哪个 platform 哪个 chat_id) 干了啥
#   修了什么 bug / 加了什么 skill / 改了什么配置
#   还有什么 P0/P1/P2 坑
#   关键命令速查 (给明天的 agent 抄)
```

**不要**:
- 写"今天心情" / "感悟" / "未来展望" (新 agent 不需要)
- 写对话原文 (memory tool 会注入上下文, 笔记是 handoff 不是 transcript)
- 写得太长 (新会话 context 会被笔记挤占, 4-6KB 是上限)

### Step 2: 改 daily_evening_summary.sh 自动 append

在 `daily_evening_summary.sh` 末尾追加 (在 `send_tg "$MSG"` 之后):

```bash
NOTES_DIR="$HERMES_HOME/daily_notes"
NOTES_FILE="$NOTES_DIR/$(date '+%Y-%m-%d').md"
mkdir -p "$NOTES_DIR"

if [ ! -f "$NOTES_FILE" ]; then
    cat > "$NOTES_FILE" <<HEADER
# 📝 每日跨平台同步笔记 — $(date '+%Y-%m-%d')

> 给明天 $(date -v+1d '+%Y-%m-%d') 起来的任何 agent 看的 handoff 笔记

## 21:00 evening_summary 自动汇总

HEADER
fi

cat >> "$NOTES_FILE" <<APPEND
### 🌙 21:00 evening_summary ($(date '+%H:%M'))

- 今日新增 fact: $TODAY_STATS
- 清理过期: $PURGED 条
- 当前总数: $TOTAL 条
- 7 天未引用: $LOW_USE 条
- 详细 report: $REPORT

---
APPEND
```

### Step 3: 写 read_daily_notes.sh 钩子脚本

```bash
#!/bin/bash
# read_daily_notes.sh — 新会话起来先读最近 3 天
set -uo pipefail
HERMES_HOME="${HOME:-/Users/aimac}/.hermes"
NOTES_DIR="$HERMES_HOME/daily_notes"
TODAY=$(date '+%Y-%m-%d')
YESTERDAY=$(date -v-1d '+%Y-%m-%d' 2>/dev/null || date -d 'yesterday' '+%Y-%m-%d')
DAY_BEFORE=$(date -v-2d '+%Y-%m-%d' 2>/dev/null || date -d '2 days ago' '+%Y-%m-%d')

for d in "$TODAY" "$YESTERDAY" "$DAY_BEFORE"; do
    f="$NOTES_DIR/$d.md"
    [ -f "$f" ] && { echo "===== $d ====="; cat "$f"; echo; }
done
```

chmod +x + 测一次。

## 4. 别做的事 (反面教材)

| 错 | 为什么错 | 改 |
|---|---|---|
| 写 `platform_inbox.md` 跨平台消息汇总 | 没人自动读它 = 死数据 | 改成 handoff 笔记 |
| 试图让两个 agent 看彼此对话 | 架构隔离, 改不了 | 老实说做不到 |
| 在 fact_store 写"用户在 X 平台问了 Y" | fact 是事实, 不是消息流 | 写有 consequence 的事 |
| 笔记 > 6KB | 挤占新会话 context | 4-6KB 上限 |

## 5. 接入 gateway 启动 hook (可选, 用户没拍板前别动)

理论:
```bash
# gateway 起来时自动 read_daily_notes.sh 注入到 system prompt
# 但这是"改启动行为", 算跨架构改动, 用户没拍板前不动
```

**目前状态 (2026-06-05)**: 钩子脚本写好 chmod +x, **没接进启动链**, 3/4 件完成度。剩下 1/4 件留给用户回来拍。

## 6. 验证清单

```bash
# 1. 笔记在
ls -la ~/.hermes/daily_notes/

# 2. 自动 append 通
bash ~/.hermes/scripts/daily_evening_summary.sh
# 期望: 末尾有 "✅ daily_notes 已更新: ..."

# 3. read_daily_notes 能读
bash ~/.hermes/scripts/read_daily_notes.sh | head -30
# 期望: 输出最近 3 天笔记拼起来

# 4. Telegram 真推了
grep "Sent to telegram" ~/.hermes/logs/daily_evening.log
# 期望: 看到 "Sent to telegram home channel"
```
