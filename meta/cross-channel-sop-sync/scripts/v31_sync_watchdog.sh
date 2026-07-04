#!/bin/bash
# v31_sync_watchdog.sh — 每周一 09:00 跑 v3.1 跨渠道铁律同步验证
# 失败时推送 Telegram 告警，成功时静默
# 关联: skill:channel-universal-sop / SOUL.md v3.1 段落

set -e

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
LOG_FILE="$HERMES_HOME/logs/v31-sync-watchdog.log"
COMPLIANCE_SCRIPT="$HERMES_HOME/skills/meta/cross-channel-sop-sync/scripts/check_v31_compliance.sh"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

send_telegram() {
    local message="$1"
    curl -s -X POST http://127.0.0.1:9888/webhook/telegram \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"🚨 v3.1 同步告警：$message\"}" \
        >> "$LOG_FILE" 2>&1 || true
}

log "=== v3.1 跨渠道同步检查开始 ==="

if [[ ! -f "$COMPLIANCE_SCRIPT" ]]; then
    send_telegram "check_v31_compliance.sh 不存在！立即查 ~/.hermes/scripts/"
    log "❌ 验证脚本不存在"
    exit 1
fi

if bash "$COMPLIANCE_SCRIPT" >> "$LOG_FILE" 2>&1; then
    log "✅ v3.1 跨渠道铁律同步正常"
    # 成功 — 静默，不打扰用户 (watchdog pattern)
    exit 0
else
    FAIL_MSG=$(bash "$COMPLIANCE_SCRIPT" 2>&1 | grep -E '❌' | head -10 || true)
    send_telegram "v3.1 跨渠道同步失败：${FAIL_MSG:-查 $LOG_FILE}"
    log "❌ v3.1 同步失败：$FAIL_MSG"
    exit 1
fi