#!/usr/bin/env bash
# evolution_startup_check.sh — Hermes启动时快速自检
# 2026-05-25新增：弥补"说了要做但没做"的执行缺口

LOG="$HOME/.hermes/logs/evolution_progress.md"
ALERT_LOG="$HOME/.hermes/logs/gateway.log"

echo "=== Hermes Evolution Startup Check ==="
date

# 1. 检查checkpoint是否存在且不过期（30分钟内更新过）
if [ -f "$LOG" ]; then
    LAST_MOD=$(stat -f %m "$LOG" 2>/dev/null || stat -c %Y "$LOG" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$((NOW - LAST_MOD))
    if [ $AGE -lt 1800 ]; then
        echo "✓ checkpoint存在且新鲜 ($((AGE/60))分钟前更新)"
    else
        echo "⚠️ checkpoint已过期 ($((AGE/60))分钟前更新)"
        echo "⚠️ 上次自主任务可能失败或中断"
    fi
else
    echo "⚠️ 无checkpoint文件 — 可能未执行过任何自主任务"
fi

# 2. 检查最近gateway日志中是否有cron执行记录（过去2小时）
echo ""
echo "=== 最近Cron执行记录 ==="
if [ -f "$ALERT_LOG" ]; then
    grep -E "cron|CRON|job|JOB|执行" "$ALERT_LOG" 2>/dev/null | tail -20
else
    echo "⚠️ gateway日志不存在"
fi

# 3. 快速健康状态
echo ""
echo "=== 进程健康 ==="
pgrep -fl hermes | head -5
pgrep -fl "n8n|ollama|chrome" | head -5

echo ""
echo "=== 自检完成 ==="