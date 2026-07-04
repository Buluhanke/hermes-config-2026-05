#!/bin/bash
# check-memory-budget.sh — MEMORY.md 字符预算 dry-run
# 用法: bash check-memory-budget.sh [path-to-MEMORY.md] [limit]
# 默认: ~/.hermes/MEMORY.md, 2200 字符硬限 (cron 任务约束)
# 输出: 字符数 + 超额/剩余 + 最长 5 行 (按字符数降序) — agent 据此压一行就够

set -euo pipefail

FILE="${1:-$HOME/.hermes/MEMORY.md}"
LIMIT="${2:-2200}"

if [ ! -f "$FILE" ]; then
  echo "❌ $FILE not found"
  exit 1
fi

CURRENT=$(wc -c < "$FILE" | tr -d ' ')
OVER=$((CURRENT - LIMIT))
REMAINING=$((LIMIT - CURRENT))

echo "=========================================="
echo "  MEMORY.md Budget Check"
echo "=========================================="
echo "  file:     $FILE"
echo "  current:  $CURRENT chars"
echo "  limit:    $LIMIT chars"

if [ "$OVER" -gt 0 ]; then
  echo "  status:   ❌ OVER by $OVER chars"
else
  echo "  status:   ✅ UNDER by $REMAINING chars"
fi

echo ""
echo "  longest lines (compress ONE of these to fix over-budget):"
echo "  ----------------------------------------"

# awk: 打印 line_num + char_count + 内容
awk '{ printf "  L%-3d (%4d chars)  %s\n", NR, length($0), $0 }' "$FILE" \
  | sort -t'(' -k2 -nr \
  | head -5

echo ""
echo "  tip: compress the top-1 line by $OVER chars to fit."
echo "  tip: or use 'head -c $LIMIT $FILE > /tmp/mem && mv /tmp/mem $FILE' for quick strip."
echo "=========================================="

# exit 0 = 永远 success, agent 自己判断超没超
exit 0
