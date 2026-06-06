# v2.4 主动循环 3-mode 完整模板（2026-06-05 落地）

> STAR-4D 框架的**完整运行实例** — 每天 3 个固定时间点：health check + 主动学习 + 整理总结 + Telegram 推送。
> 与 hourly 被动巡检**互补**，叠加成真正的 7×24 进化闭环。

## 1. 设计原理

| 维度 | hourly 巡检（v2.3） | v2.4 主动循环 |
|---|---|---|
| 频率 | 30 min | 每天 3 次固定时间 |
| 触发 | errors.log 出现错误 | 时间到就跑 |
| 行为 | 修（kill/重启/写 fact） | 检 + 学 + 整（更广维度） |
| 失败处理 | 重试 / Do 段修复 | 降级为日志，不影响整体 |
| 推送 | 不推送 | Telegram 推送（成功/失败都通知） |

**为什么需要第二层？**
- hourly 是"被动"（错误触发才动手），但**没有"健康"概念**（gateway 没死 = 没问题？）
- 主动循环 = 每天固定时间点**主动**全维度体检 + 主动学习新东西 + 整理积累
- hourly 修"刚坏的"，主动循环防"慢死的"（磁盘渐满 / 平台掉线 / 知识陈旧）

## 2. 3 个 plist 样板（2026-06-05 实测有效）

### 09:00 health — daily-health.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.daily-health</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/aimac/.hermes/scripts/daily_health_check.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/daily_health.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/daily_health_err.log</string>
</dict>
</plist>
```

### 09:30 learning — daily-learning.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.daily-learning</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/aimac/.hermes/scripts/daily_active_learning.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/daily_learning.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/daily_learning_err.log</string>
</dict>
</plist>
```

### 21:00 evening — daily-evening.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.daily-evening</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/aimac/.hermes/scripts/daily_evening_summary.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/daily_evening.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/daily_evening_err.log</string>
</dict>
</plist>
```

## 3. 3 个脚本模板（精简版）

### 3.1 daily_health_check.sh

```bash
#!/bin/bash
# 每日 09:00 健康检查 — gateway / 平台连接 / 记忆 / 磁盘 / 内存
set -uo pipefail

HERMES_HOME="${HOME:-/Users/aimac}/.hermes"
DB="$HERMES_HOME/memory_store.db"
PY="$HERMES_HOME/hermes-agent/venv/bin/python"
LOG="$HERMES_HOME/logs/daily_health.log"
REPORT="$HERMES_HOME/logs/daily_health_report_$(date +%Y%m%d).md"
mkdir -p "$(dirname $LOG)" "$(dirname $REPORT)"

log() { echo "$(date '+%m-%d %H:%M:%S') $1" >> "$LOG"; echo "$1"; }
send_tg() {
    "$HERMES_HOME/hermes-agent/venv/bin/hermes" send -t telegram "$1" 2>/dev/null \
        || log "  ⚠️ hermes send 失败"
}

# 1. Gateway 状态（list 路径，详见坑 1）
GATEWAY_OK=0
GATEWAY_PID=""
GW_LINE=$(launchctl list 2>/dev/null | grep "ai\.hermes\.gateway" | head -1)
if [ -n "$GW_LINE" ]; then
    GATEWAY_PID=$(echo "$GW_LINE" | awk '{print $1}')
    [ "$GATEWAY_PID" != "-" ] && [ -n "$GATEWAY_PID" ] && [ "$GATEWAY_PID" -gt 0 ] 2>/dev/null && GATEWAY_OK=1
fi

# 2. 各平台连接（从 hermes status 抓 configured，详见坑 3）
HERMES_STATUS=$("$HERMES_HOME/hermes-agent/venv/bin/hermes" status 2>/dev/null || echo "")
PLATFORMS=("Telegram" "Feishu" "Weixin" "QQBot")
PLAT_OK=(); PLAT_FAIL=()
for p in "${PLATFORMS[@]}"; do
    if echo "$HERMES_STATUS" | LC_ALL=C grep -qE "$p.*configured|$p.*connected"; then
        PLAT_OK+=("$p")
    else
        PLAT_FAIL+=("$p")
    fi
done

# 3. 记忆完整性
FACT_COUNT=$("$PY" -c "import sqlite3; print(sqlite3.connect('$DB').execute('SELECT COUNT(*) FROM facts').fetchone()[0])" 2>/dev/null || echo "0")
FTS5_OK=$("$PY" -c "
import sqlite3
try:
    sqlite3.connect('$DB').execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='facts_fts'\").fetchone()
    print('1')
except: print('0')
" 2>/dev/null)

# 4. 资源
DISK_PCT=$(df -g / | tail -1 | awk '{print $5}' | tr -d '%')
MEM_FREE_MB=$("$PY" -c "
import subprocess
o = subprocess.check_output(['vm_stat']).decode()
f = int([l for l in o.split('\n') if 'Pages free' in l][0].split()[-1].rstrip('.'))
print(f * 16384 // 1024 // 1024)
" 2>/dev/null || echo "0")

# 拼报告 + 推送
SUMMARY="🌅 早 9 点健康检查:
• Gateway: $([ "$GATEWAY_OK" = "1" ] && echo "✅ PID=$GATEWAY_PID" || echo "❌")
• 平台: ✅${#PLAT_OK[@]} ❌${#PLAT_FAIL[@]} ${PLAT_FAIL[*]:-}
• 记忆: $FACT_COUNT facts, FTS5 $([ "$FTS5_OK" = "1" ] && echo "✅" || echo "❌")
• 磁盘: ${DISK_PCT}%, 内存: ${MEM_FREE_MB}MB 空闲"

log "===== 09:00 健康检查完成 ====="
log "$SUMMARY"
send_tg "$SUMMARY"
```

### 3.2 daily_active_learning.sh (核心)

```bash
#!/bin/bash
# 每日 09:30 主动学习 — GitHub Hermes 官方仓库 + hermesagent.org.cn
set -uo pipefail

HERMES_HOME="${HOME:-/Users/aimac}/.hermes"
DB="$HERMES_HOME/memory_store.db"
PY="$HERMES_HOME/hermes-agent/venv/bin/python"
LOG="$HERMES_HOME/logs/daily_learning.log"
LAST_SEEN_FILE="$HERMES_HOME/.cache/last_seen_github"
LAST_CN_FILE="$HERMES_HOME/.cache/last_seen_chinese"
mkdir -p "$(dirname $LOG)" "$(dirname $LAST_SEEN_FILE)"

log() { echo "$(date '+%m-%d %H:%M:%S') $1" >> "$LOG"; echo "$1"; }
send_tg() {
    "$HERMES_HOME/hermes-agent/venv/bin/hermes" send -t telegram "$1" 2>/dev/null \
        || log "  ⚠️ hermes send 失败"
}

NEW_FACTS=0
NEW_GH=0
NEW_CN=0

# === GitHub: NousResearch/hermes-agent 最近 5 commit ===
GH_JSON=$(gh api repos/NousResearch/hermes-agent/commits --jq '.[0:5] | map({sha: .sha[0:7], msg: .commit.message, date: .commit.author.date, url: .html_url})' 2>/dev/null || echo "")

if [ -n "$GH_JSON" ] && [ "$GH_JSON" != "[]" ]; then
    NEWEST_SHA=$(echo "$GH_JSON" | "$PY" -c "import json,sys; print(json.load(sys.stdin)[0]['sha'])" 2>/dev/null || echo "")
    LAST_SEEN_SHA=$(cat "$LAST_SEEN_FILE" 2>/dev/null || echo "")

    if [ -n "$NEWEST_SHA" ] && [ "$NEWEST_SHA" != "$LAST_SEEN_SHA" ]; then
        log "📦 GitHub 新 commit: $NEWEST_SHA"
        # 写前 3 条 commit 进 fact (去重靠 UNIQUE 约束)
        echo "$GH_JSON" | "$PY" -c "
import json, sys, sqlite3
data = json.load(sys.stdin)
c = sqlite3.connect('$DB')
for entry in data[:3]:
    msg = entry['msg'].split('\n')[0][:150]
    sha = entry['sha']
    try:
        c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
                  (f'Hermes GitHub ({sha}): {msg}', 'github_trending', f'hermes,github,commit,{sha}', 0.6))
        c.commit()
    except sqlite3.IntegrityError:
        pass  # 已存在
c.close()
" 2>/dev/null
        NEW_GH=$(echo "$GH_JSON" | "$PY" -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
        echo "$NEWEST_SHA" > "$LAST_SEEN_FILE"
        NEW_FACTS=$((NEW_FACTS+NEW_GH))
    fi
fi

# === hermesagent.org.cn 中文社区（按 HTML hash 判变化）===
CN_URL="https://hermesagent.org.cn"
LAST_HASH=$(cat "$LAST_CN_FILE" 2>/dev/null || echo "")

CN_HTML=$(curl -sL --max-time 15 "$CN_URL" 2>/dev/null || echo "")
if [ -n "$CN_HTML" ]; then
    CN_HASH=$(echo "$CN_HTML" | md5sum | awk '{print $1}')
    if [ "$CN_HASH" != "$LAST_HASH" ]; then
        log "🌐 中文社区有变化 (新 hash: ${CN_HASH:0:8})"
        TITLES=$(echo "$CN_HTML" | grep -oE '<h[12][^>]*>[^<]+</h[12]>' | sed -E 's/<[^>]+>//g' | head -3 | tr '\n' '|')
        if [ -n "$TITLES" ]; then
            "$PY" -c "
import sqlite3
c = sqlite3.connect('$DB')
try:
    c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
              ('中文社区更新: $TITLES', 'chinese_community', 'hermes,hermesagent.org.cn,update,$(date +%Y%m%d)', 0.5))
    c.commit()
except sqlite3.IntegrityError:
    pass
c.close()
" 2>/dev/null
            NEW_CN=1
            NEW_FACTS=$((NEW_FACTS+1))
        fi
        echo "$CN_HASH" > "$LAST_CN_FILE"
    fi
fi

# 总结推送
TOTAL=$("$PY" -c "import sqlite3; print(sqlite3.connect('$DB').execute('SELECT COUNT(*) FROM facts').fetchone()[0])" 2>/dev/null)
MSG="📚 早 9:30 学习完成:
• GitHub: $([ "$NEW_GH" -gt 0 ] && echo "+$NEW_GH 条新 commit" || echo "无新")
• 中文社区: $([ "$NEW_CN" -gt 0 ] && echo "页面更新" || echo "无变化")
• 本次新增: $NEW_FACTS 条
• 当前总数: $TOTAL"

log "===== 09:30 学习完成 ====="
log "$MSG"
send_tg "$MSG"
```

### 3.3 daily_evening_summary.sh (最简单)

```bash
#!/bin/bash
# 每日 21:00 整理 + 总结 + 推送
set -uo pipefail

HERMES_HOME="${HOME:-/Users/aimac}/.hermes"
DB="$HERMES_HOME/memory_store.db"
PY="$HERMES_HOME/hermes-agent/venv/bin/python"
LOG="$HERMES_HOME/logs/daily_evening.log"
mkdir -p "$(dirname $LOG)"

log() { echo "$(date '+%m-%d %H:%M:%S') $1" >> "$LOG"; echo "$1"; }
send_tg() {
    "$HERMES_HOME/hermes-agent/venv/bin/hermes" send -t telegram "$1" 2>/dev/null \
        || log "  ⚠️ hermes send 失败"
}

# 清理 trust<0.3 且 30 天前（与 ai_knowledge_collector 一致）
PURGED=$("$PY" -c "
import sqlite3
from datetime import datetime, timedelta
c = sqlite3.connect('$DB')
cutoff = (datetime.now() - timedelta(days=30)).isoformat()
cur = c.execute('DELETE FROM facts WHERE trust_score < 0.3 AND created_at < ?', (cutoff,))
c.commit()
print(cur.rowcount)
c.close()
" 2>/dev/null)

# 今日新增按 category 分组
TODAY_STATS=$("$PY" -c "
import sqlite3, json
from datetime import datetime, timedelta
c = sqlite3.connect('$DB')
cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
rows = c.execute('SELECT category, COUNT(*) FROM facts WHERE created_at > ? GROUP BY category', (cutoff,)).fetchall()
print(json.dumps({k: v for k, v in rows}, ensure_ascii=False))
" 2>/dev/null)

TOTAL=$("$PY" -c "import sqlite3; print(sqlite3.connect('$DB').execute('SELECT COUNT(*) FROM facts').fetchone()[0])" 2>/dev/null)

MSG="🌙 晚 9 点整理完毕:
• 今日新增: $TODAY_STATS
• 清理过期: $PURGED 条
• 当前总数: $TOTAL"

log "===== 21:00 整理完成 ====="
log "$MSG"
send_tg "$MSG"
```

## 4. 6 条 launchd 实战笔记（2026-06-05 沉淀）

### 笔记 1：plist 改时间必须 unload + load

```bash
# 改完 plist 后必须:
launchctl unload ~/Library/LaunchAgents/ai.hermes.daily-health.plist
launchctl load -w ~/Library/LaunchAgents/ai.hermes.daily-health.plist
launchctl list | grep daily-health
```

**为什么**：macOS launchd 缓存 plist 内存副本，**改文件不生效**。

### 笔记 2：每个 plist 配 StandardOutPath + StandardErrorPath

不配的话，launchd 把 stderr 写到 `~/Library/Logs/` 默认位置，**找不到**。

### 笔记 3：所有脚本必须 `set -uo pipefail`（不用 -e）

`-e` 会让任何错误退出整个脚本。`-u` 防 unbound 变量。`pipefail` 防 `cmd1 | cmd2` 失败被吞。

### 笔记 4：手测时 `bash -n` 先过 + 单独跑

```bash
bash -n ~/.hermes/scripts/daily_health_check.sh && echo OK
bash ~/.hermes/scripts/daily_health_check.sh
```

**不要直接用 launchd 验证** — launchd 报错的 context 信息极少。

### 笔记 5：hermes send CLI 走 home channel

```bash
hermes send -t telegram "msg"
# 自动发到 home channel（chat_id 7359677525）
# 不需要传 chat_id
```

要发指定 chat：用工具版 `send_message(target='telegram:chat_id:thread_id', ...)`。

### 笔记 6：失败不阻断整体

每个 step 单独 try/log，推送失败也只是降级为"仅日志记录"，不 `exit 1`。
否则一个 step 失败 → 后面全跳。

## 5. 验收清单

新增 3-mode 后，必须验证：

```bash
# 1. 3 个 plist 都在
launchctl list | grep -E "daily-health|daily-learning|daily-evening"

# 2. 手测 3 个脚本全部成功（含推送）
bash ~/.hermes/scripts/daily_health_check.sh
bash ~/.hermes/scripts/daily_active_learning.sh
bash ~/.hermes/scripts/daily_evening_summary.sh

# 3. fact 入库
sqlite3 ~/.hermes/memory_store.db "SELECT category, COUNT(*) FROM facts GROUP BY category"
# 期望: github_trending >= 3, chinese_community >= 1

# 4. 等 9:00/9:30/21:00 实际跑一次（不等则改 StartCalendarInterval 到几分钟后看效果）
```

## 6. 失败模式与恢复

| 失败 | 原因 | 恢复 |
|---|---|---|
| 推送 "hermes send 失败" | CLI 语法错 / Telegram bot 未配 | 用 `hermes send --help` 重查 |
| Gateway ❌ 已重启 | launchctl list 解析错（坑 1） | 用 `launchctl list \| grep` 路径 |
| GitHub 无新 commit | API 限流或真无新 | 看 `~/.hermes/logs/daily_learning.log` |
| fact 没写库 | UNIQUE 冲突 / python 异常 | 看 `~/.hermes/logs/daily_learning.log` 的 sqlite 错误 |

## 7. 与既有 plist 的时序

```
01:00  ai-knowledge-collector (v2 老脚本, 6站AI对话)
09:00  daily-health (v2.4 新)
09:30  daily-learning (v2.4 新) — 主动循环
09:00  self-evolution-daily (v2 老脚本) — 旧 daily
每30m  self-evolution-hourly (v2 老脚本) — 旧 hourly
21:00  daily-evening (v2.4 新) — 主动循环
周一09:00 self-evolution-weekly (v2 老脚本) — 旧 weekly
周日03:00 cleanup-logs
每30m  mem-patrol
每15m  self-check
```

**冲突点**：09:00 daily-health vs 09:00 self-evolution-daily — 同一时间，**两段都跑**。self-evolution-daily 写 fact + JSON 报告，daily-health 写健康报告 + Telegram。**不冲突**（读不同字段），但**日志时间戳会叠在一起**——可接受。
