#!/bin/bash
# daily_evening_summary.sh — 每日 21:00 记忆整理 + 总结
# v2.0 — 2026-07-17
# 重写: 基于真实 Hermes 架构 (MEMORY.md/USER.md，非 facts 表)

set -uo pipefail

HERMES_HOME="${HOME:-/Users/kk}/.hermes"
HERMES="$HERMES_HOME/hermes-agent/venv/bin/hermes"
LOG="$HERMES_HOME/logs/daily_evening.log"
REPORT="$HERMES_HOME/logs/daily_evening_$(date +%Y%m%d).md"
mkdir -p "$(dirname $LOG)" "$(dirname $REPORT)"

log() { echo "$(date '+%m-%d %H:%M:%S') $1"; }

MEMORY_FILE="$HERMES_HOME/memories/MEMORY.md"
USER_FILE="$HERMES_HOME/memories/USER.md"
MEMORY_SIZE=$(wc -c < "$MEMORY_FILE" 2>/dev/null || echo 0)
MEMORY_ENTRIES=$(grep -c "^§" "$MEMORY_FILE" 2>/dev/null || echo 0)
USER_ENTRIES=$(grep -c "^§" "$USER_FILE" 2>/dev/null || echo 0)
TODAY=$(date '+%Y-%m-%d')

# ── Obsidian 日记 ────────────────────────────────────────
OBSIDIAN_DIR="$HERMES_HOME/../Obsidian/迅龙贸易/AI进化"
SUMMARY_MD="$OBSIDIAN_DIR/${TODAY}-每日总结.md"
[ -d "$OBSIDIAN_DIR" ] && mkdir -p "$OBSIDIAN_DIR"

# ── Handoff 笔记 ─────────────────────────────────────────
NOTES_DIR="$HERMES_HOME/daily_notes"
NOTES_FILE="$NOTES_DIR/${TODAY}.md"
mkdir -p "$NOTES_DIR"
if [ ! -f "$NOTES_FILE" ]; then
    TOMORROW=$(date -v+1d '+%Y-%m-%d' 2>/dev/null || date -d 'tomorrow' '+%Y-%m-%d')
    cat > "$NOTES_FILE" <<EOF
# 📝 每日跨平台同步笔记 — $TODAY

> 给明天 $TOMORROW 起来的任何 agent 看的 handoff 笔记

## 21:00 evening_summary 自动汇总

EOF
fi

# ── 资源状态 ─────────────────────────────────────────────
DISK_PCT=$(df -g / 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
MEM_FREE_MB=$(vm_stat 2>/dev/null | awk '/Pages free/ {print int($NF)}' | tr -d '.')
MEM_FREE_MB=$((MEM_FREE_MB * 16384 / 1024 / 1024))
HERMES_STATUS=$("$HERMES" status 2>/dev/null || echo "")
PLAT_OK=($(echo "$HERMES_STATUS" | grep -cE "configured|connected" || echo 0))

# ── 写报告 ──────────────────────────────────────────────
{
    echo "# 🌙 每日 21:00 整理总结 — $(date '+%Y-%m-%d %H:%M')"
    echo ""
    echo "## 记忆状态"
    echo "- MEMORY.md: $MEMORY_ENTRIES 条目, ${MEMORY_SIZE} 字节"
    echo "- USER.md: $USER_ENTRIES 条目"
    echo ""
    echo "## 系统资源"
    echo "- 磁盘: ${DISK_PCT}%"
    echo "- 空闲内存: ${MEM_FREE_MB}MB"
    echo "- 活跃平台: ${PLAT_OK[*]:-无}"
    echo ""
} > "$REPORT"

# ── 追加 handoff ────────────────────────────────────────
cat >> "$NOTES_FILE" <<EOF
### 🌙 21:00 evening_summary ($(date '+%H:%M'))

- 记忆: MEMORY ${MEMORY_ENTRIES}条, USER ${USER_ENTRIES}条
- 资源: disk ${DISK_PCT}%, mem ${MEM_FREE_MB}MB 空闲
- 平台: ${PLAT_OK[*]:-无}
- 详细 report: $REPORT

---
EOF

# ── Obsidian 日记 ───────────────────────────────────────
if [ -d "$OBSIDIAN_DIR" ]; then
    {
        echo "# 🌙 ${TODAY} 每日总结"
        echo ""
        echo "## 记忆状态"
        echo "- MEMORY.md: $MEMORY_ENTRIES 条目"
        echo "- USER.md: $USER_ENTRIES 条目"
        echo ""
        echo "## 系统资源"
        echo "- 磁盘使用: ${DISK_PCT}%"
        echo "- 空闲内存: ${MEM_FREE_MB}MB"
    } > "$SUMMARY_MD"
fi

# ── Telegram ─────────────────────────────────────────────
MSG="🌙 晚 9 点整理完毕:
• 记忆: MEMORY ${MEMORY_ENTRIES}条, USER ${USER_ENTRIES}条
• 磁盘: ${DISK_PCT}%, 内存: ${MEM_FREE_MB}MB 空闲
• 详情: $REPORT"

log "===== 21:00 整理完成 ====="
log "$MSG"
"$HERMES" send -t "telegram" "$MSG" 2>/dev/null || log "  ⚠️ Telegram 推送失败"
log "✅ daily_notes 已更新: $NOTES_FILE"
