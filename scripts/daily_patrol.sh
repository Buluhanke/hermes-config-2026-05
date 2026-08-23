#!/bin/bash
# Hermes Daily Patrol — 健康检查脚本
# 每日 09:00 cron 跑，检查所有关键服务
DATE=$(date +%Y%m%d_%H%M)
LOG_DIR="$HOME/.hermes/logs/patrol"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/patrol_$DATE.txt"

echo "=== Hermes Daily Patrol $(date) ===" > "$LOG"
echo "" >> "$LOG"

# 1. Gateway
if pgrep -f "hermes-gateway" > /dev/null 2>&1 || pgrep -f "hermes_cli.main gateway" > /dev/null 2>&1; then
    echo "Gateway: RUNNING" >> "$LOG"
else
    echo "Gateway: STOPPED — restarting..." >> "$LOG"
    bash "$HOME/.hermes/scripts/restart_gateway.sh" >> "$LOG" 2>&1
fi

# 2. Chrome CDP
if curl -s --max-time 3 http://localhost:9222/json/version >> "$LOG" 2>&1; then
    echo "CDP: OK" >> "$LOG"
else
    echo "CDP: DOWN" >> "$LOG"
fi

# 3. OmniRoute
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:20128/api/monitoring/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "OmniRoute: OK" >> "$LOG"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "OmniRoute: OK (database empty — needs onboarding)" >> "$LOG"
else
    echo "OmniRoute: HTTP $HTTP_CODE — may need restart" >> "$LOG"
fi

# 4. Memory
echo "" >> "$LOG"
echo "Memory:" >> "$LOG"
vm_stat 2>/dev/null | grep "Pages free" | head -1 >> "$LOG"

# 5. Disk
echo "" >> "$LOG"
echo "Disk /:" >> "$LOG"
df -h / 2>/dev/null | tail -1 | awk '{print "Used: "$5" ("$3" / "$2")"}' >> "$LOG"

echo "" >> "$LOG"
echo "Done at $(date)" >> "$LOG"

# 如果有 STOPPED/DOWN 等关键词，追加到日志方便排查
if grep -q "STOPPED\|DOWN" "$LOG" 2>/dev/null; then
    echo "=== ANNOTATION: Issues found — review above ===" >> "$LOG"
fi

cat "$LOG"
