#!/bin/bash
# daily_health_check.sh — 每日 09:00 健康检查
# v2.0 — 2026-07-17
# 重写: 基于真实 Hermes 架构 (MEMORY.md/USER.md，非 facts 表)

set -uo pipefail

HERMES_HOME="${HOME:-/Users/kk}/.hermes"
LOG="$HERMES_HOME/logs/daily_health.log"
REPORT="$HERMES_HOME/logs/daily_health_report_$(date +%Y%m%d).md"
mkdir -p "$(dirname $LOG)" "$(dirname $REPORT)"

log() { echo "$(date '+%m-%d %H:%M:%S') $1"; }

# ── 1. Gateway 健康探测 ─────────────────────────────────────
GATEWAY_OK=0
GATEWAY_PID=""
GW_LINE=$(launchctl list 2>/dev/null | grep -E "ai\.hermes\.gateway|hermes-gateway" | head -1)
if [ -n "$GW_LINE" ]; then
    GATEWAY_PID=$(echo "$GW_LINE" | awk '{print $1}')
    if [ "$GATEWAY_PID" != "-" ] && [ -n "$GATEWAY_PID" ] && [ "$GATEWAY_PID" -gt 0 ] 2>/dev/null; then
        HEALTH=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 3 http://127.0.0.1:8642/health 2>/dev/null || echo "000")
        [ "$HEALTH" = "200" ] && GATEWAY_OK=1 || log "  ⚠️ Gateway HTTP /health 返回 $HEALTH"
    fi
fi

# ── 2. 平台连接状态 ─────────────────────────────────────────
HERMES="$HERMES_HOME/hermes-agent/venv/bin/hermes"
HERMES_STATUS=$("$HERMES" status 2>/dev/null || echo "")
PLATFORMS=("Telegram" "Feishu" "Weixin" "QQBot")
PLAT_OK=() PLAT_FAIL=()
for p in "${PLATFORMS[@]}"; do
    echo "$HERMES_STATUS" | LC_ALL=C grep -qE "$p.*configured|$p.*connected" \
        && PLAT_OK+=("$p") || PLAT_FAIL+=("$p")
done

# ── 3. 记忆文件状态 ─────────────────────────────────────────
MEMORY_FILE="$HERMES_HOME/memories/MEMORY.md"
USER_FILE="$HERMES_HOME/memories/USER.md"
MEMORY_ENTRIES=$(grep -c "^§" "$MEMORY_FILE" 2>/dev/null || echo 0)
USER_ENTRIES=$(grep -c "^§" "$USER_FILE" 2>/dev/null || echo 0)
MEMORY_SIZE=$(wc -c < "$MEMORY_FILE" 2>/dev/null || echo 0)

# ── 4. 资源状态 ─────────────────────────────────────────────
DISK_PCT=$(df -g / 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
MEM_FREE_MB=$(vm_stat 2>/dev/null | awk '/Pages free/ {print int($NF)}' | tr -d '.')
MEM_FREE_MB=$((MEM_FREE_MB * 16384 / 1024 / 1024))

# ── 5. Chrome CDP ───────────────────────────────────────────
CDP_OK=0
curl -s --max-time 3 http://127.0.0.1:9222/json/version >/dev/null 2>&1 && CDP_OK=1

# ── 6. 拼报告 ───────────────────────────────────────────────
{
    echo "# 🌅 每日 09:00 健康检查 — $(date '+%Y-%m-%d %H:%M')"
    echo ""
    echo "## 1. Gateway"
    [ "$GATEWAY_OK" = "1" ] \
        && echo "✅ 运行中 (PID: $GATEWAY_PID)" \
        || { echo "❌ 未响应 — 已尝试 kickstart"; launchctl kickstart "gui/$(id -u)/ai.hermes.gateway" 2>&1 || true; }
    echo ""
    echo "## 2. 平台连接"
    echo "✅ 正常: ${PLAT_OK[*]:-无}"
    [ "${#PLAT_FAIL[@]}" -gt 0 ] && echo "❌ 异常: ${PLAT_FAIL[*]}"
    echo ""
    echo "## 3. 记忆系统"
    echo "- MEMORY.md: $MEMORY_ENTRIES 条目, ${MEMORY_SIZE} 字节"
    echo "- USER.md: $USER_ENTRIES 条目"
    echo ""
    echo "## 4. 资源"
    echo "- 磁盘: ${DISK_PCT}%"
    echo "- 空闲内存: ${MEM_FREE_MB}MB"
    echo "- Chrome CDP: $([ "$CDP_OK" = "1" ] && echo '✅ 在线' || echo '❌ 未启动')"
    echo ""
} > "$REPORT"

# ── 7. Telegram 推送 ────────────────────────────────────────
SUMMARY="🌅 早 9 点健康检查
• Gateway: $([ "$GATEWAY_OK" = "1" ] && echo "✅ PID=$GATEWAY_PID" || echo "❌ 已重启")
• 平台: ✅${#PLAT_OK[@]} ❌${#PLAT_FAIL[@]}${PLAT_FAIL[*]:+ ${PLAT_FAIL[*]}}
• 记忆: MEMORY ${MEMORY_ENTRIES}条, USER ${USER_ENTRIES}条
• 磁盘: ${DISK_PCT}%, 内存: ${MEM_FREE_MB}MB 空闲
• CDP: $([ "$CDP_OK" = "1" ] && echo "✅" || echo "❌")
• 详情: $REPORT"

log "===== 09:00 健康检查完成 ====="
log "$SUMMARY"
"$HERMES" send -t "telegram" "$SUMMARY" 2>/dev/null || log "  ⚠️ Telegram 推送失败"
