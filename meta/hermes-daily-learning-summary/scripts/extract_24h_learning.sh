#!/bin/bash
# extract_24h_learning.sh
# 一键跑完 daily-learning-summary 的 Step 1-4，输出可粘到 MEMORY.md 的结构化摘要
#
# 用法:
#   bash extract_24h_learning.sh           # 默认 24h 窗口
#   bash extract_24h_learning.sh 7d        # 7 天窗口
#   bash extract_24h_learning.sh 30d       # 30 天窗口
#   bash extract_24h_learning.sh 1d 7d     # 双窗口对比
#
# 输出到 stdout，可直接 pipe 到文件或 paste 到 MEMORY.md 草稿
# Cron 集成: 在 evening_summary 之前跑，输出重定向到 /tmp，再由 Python script 解析

set -e

WINDOW="${1:-1d}"
COMPARE="${2:-}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DB="$HERMES_HOME/memory/fact_store.db"
NOTES_DIR="$HERMES_HOME/daily_notes"
LOG_AI="$HERMES_HOME/logs/ai_collector.log"
LOG_AGENT="$HERMES_HOME/logs/agent.log"

# 窗口转秒
case "$WINDOW" in
  1d|24h)   SECS=86400;   LABEL="24h" ;;
  7d|1w)    SECS=604800;   LABEL="7d"  ;;
  30d|1m)   SECS=2592000;  LABEL="30d" ;;
  *)        SECS=86400;    LABEL="24h" ;;
esac

NOW=$(date +%s)
CUTOFF=$((NOW - SECS))
DATE_TODAY=$(date '+%Y-%m-%d')
DATE_YDAY=$(date -v-1d '+%Y-%m-%d' 2>/dev/null || date -d 'yesterday' '+%Y-%m-%d')

echo "═══════════════════════════════════════════════════════════"
echo "📚 Hermes ${LABEL} 学习摘要 (cutoff: $(date -r $CUTOFF '+%Y-%m-%d %H:%M:%S'))"
echo "═══════════════════════════════════════════════════════════"
echo ""

# --- Section 1: fact_store 新增 ---
echo "### fact_store DB (id, created_local, topic, trust)"
echo '```'
if [ -f "$DB" ]; then
  sqlite3 "$DB" -separator ' | ' \
    "SELECT id, datetime(created_at,'unixepoch','localtime'), topic, trust
     FROM facts
     WHERE created_at > $CUTOFF
     ORDER BY created_at DESC;" 2>/dev/null || echo "(SQLite query failed — check timestamp type with .schema facts)"
else
  echo "(DB not found at $DB)"
fi
echo '```'
echo ""

# --- Section 2: trust 分布 ---
echo "### trust 分布"
echo '```'
if [ -f "$DB" ]; then
  sqlite3 "$DB" -separator ' | ' \
    "SELECT
       'high(>=0.8)' AS bucket, COUNT(*) AS cnt FROM facts WHERE created_at > $CUTOFF AND trust >= 0.8
     UNION ALL
     SELECT 'mid(0.5-0.8)', COUNT(*) FROM facts WHERE created_at > $CUTOFF AND trust >= 0.5 AND trust < 0.8
     UNION ALL
     SELECT 'low(<0.5)', COUNT(*) FROM facts WHERE created_at > $CUTOFF AND trust < 0.5
     UNION ALL
     SELECT 'TOTAL', COUNT(*) FROM facts WHERE created_at > $CUTOFF;" 2>/dev/null
fi
echo '```'
echo ""

# --- Section 3: daily_notes 今日/昨日 ---
echo "### daily_notes (handoff)"
echo "- 今日: $NOTES_DIR/$DATE_TODAY.md $([ -f "$NOTES_DIR/$DATE_TODAY.md" ] && echo '✅' || echo '❌ (not yet)')"
echo "- 昨日: $NOTES_DIR/$DATE_YDAY.md $([ -f "$NOTES_DIR/$DATE_YDAY.md" ] && echo '✅' || echo '❌')"
echo ""

# --- Section 4: ai_collector 自学 cron ---
echo "### ai_collector.log (最近 5 次)"
if [ -f "$LOG_AI" ]; then
  grep -E "采集开始|采集完成|新增 fact" "$LOG_AI" | tail -5
else
  echo "(log not found)"
fi
echo ""

# --- Section 5: agent.log 关键事件 ---
echo "### agent.log 关键事件 (learn|skill|update|memory|fail|error)"
if [ -f "$LOG_AGENT" ]; then
  tail -500 "$LOG_AGENT" 2>/dev/null | \
    grep -iE "learn|skill|update|memory|fail|error" | \
    tail -15
else
  echo "(log not found)"
fi
echo ""

# --- Section 6: MEMORY.md 字数 ---
MEM="$HERMES_HOME/MEMORY.md"
echo "### MEMORY.md 字数"
if [ -f "$MEM" ]; then
  echo "- 当前: $(wc -m < "$MEM") 字符 (软上限 2200, 硬上限 8000)"
  echo "- 末尾最新块: $(grep -E '^## \[' "$MEM" | tail -3 | tr '\n' ' | ')"
else
  echo "(MEMORY.md not found)"
fi
echo ""

# --- Optional: 双窗口对比 ---
if [ -n "$COMPARE" ]; then
  case "$COMPARE" in
    7d|1w)    SECS2=604800;  LABEL2="7d" ;;
    30d|1m)   SECS2=2592000; LABEL2="30d" ;;
    *)        SECS2=604800;  LABEL2="7d" ;;
  esac
  CUTOFF2=$((NOW - SECS2))
  echo "═══════════════════════════════════════════════════════════"
  echo "📊 对比窗口 ${LABEL2} (cutoff: $(date -r $CUTOFF2 '+%Y-%m-%d %H:%M:%S'))"
  echo "═══════════════════════════════════════════════════════════"
  sqlite3 "$DB" -separator ' | ' \
    "SELECT '新增', COUNT(*) FROM facts WHERE created_at > $CUTOFF2;
     SELECT 'high-trust', COUNT(*) FROM facts WHERE created_at > $CUTOFF2 AND trust >= 0.8;" 2>/dev/null
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ 摘要完成 — 可复制到 MEMORY.md 草稿"
echo "═══════════════════════════════════════════════════════════"