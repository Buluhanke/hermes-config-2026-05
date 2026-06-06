#!/bin/bash
# 30 分钟空闲自动 kill 模板
# 用法: ./idle_kill.sh <pattern> [idle_minutes]
# 例: ./idle_kill.sh 'ollama' 30
#     ./idle_kill.sh 'Chrome.*debug' 30

set -e

PATTERN="${1:?usage: $0 <pattern> [idle_minutes]}"
IDLE_MIN="${2:-30}"

# 1) 检查前台
visible_pids=$(osascript -e 'tell application "System Events" to get unix id of every process whose visible is true' 2>/dev/null | tr ',' ' ')
if ps aux | grep -E "$PATTERN" | grep -v grep | awk '{print $2}' | tr '\n' ' ' | grep -qE "$(echo $visible_pids | tr ' ' '|')"; then
  echo "  ⚠️  匹配进程在前台，不杀"
  exit 1
fi

# 2) 找匹配进程
pids=$(ps aux | grep -E "$PATTERN" | grep -v grep | awk '{print $2}' | xargs)
if [ -z "$pids" ]; then
  echo "  ℹ️  没有匹配的进程"
  exit 0
fi

# 3) 检查 etime（启动时间）
for pid in $pids; do
  etime=$(ps -p $pid -o etime= 2>/dev/null | xargs)
  echo "  PID $pid 启动: $etime"
done

# 4) 调度 at 任务
cmd="kill_pids=\$(ps aux | grep -E '$PATTERN' | grep -v grep | awk '{print \$2}' | xargs); [ -n \"\$kill_pids\" ] && kill -9 \$kill_pids 2>/dev/null; echo \"[idle_kill] killed PIDs=\$kill_pids at \$(date)\" >> /tmp/hermes_kills/idle_kill.log"
echo "$cmd" | at now + "$IDLE_MIN" minutes 2>/dev/null \
  && echo "  ✅ 已调度 $IDLE_MIN 分钟后 kill" \
  || echo "  ❌ at 调度失败（系统没启用 atrun）"

# 5) 记录
mkdir -p /tmp/hermes_kills
echo "[$(date)] pattern=$PATTERN idle=${IDLE_MIN}min pids=$pids" >> /tmp/hermes_kills/idle_kill.log
