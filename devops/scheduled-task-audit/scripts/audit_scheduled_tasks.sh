#!/bin/bash
# Hermes scheduled-task 一行审计
# 用法: bash audit_scheduled_tasks.sh
# 输出: launchd plists 表 + 孤儿脚本 + 破坏性副作用清单

set -e

echo "=== 1. launchd plists ==="
for f in ~/Library/LaunchAgents/ai.hermes.*.plist; do
  [ -f "$f" ] || continue
  echo "--- $(basename "$f") ---"
  plutil -p "$f" | grep -E "StartCalendarInterval|StartInterval|KeepAlive|Label|StartTime"
done

echo ""
echo "=== 2. crontab ==="
if crontab -l 2>/dev/null | grep -v "^#" | grep -q .; then
  crontab -l 2>/dev/null
else
  echo "(empty)"
fi

echo ""
echo "=== 3. 脚本中提到的 cron 调度 (可能已脱节) ==="
grep -rnE "^[# ]*Cron:|@hourly|@daily|@weekly|crontab" ~/.hermes/scripts/*.{sh,py} 2>/dev/null | head -20

echo ""
echo "=== 4. 半残废脚本 (含 TODO/SKIP/FIXME) ==="
for f in ~/.hermes/scripts/*.{sh,py}; do
  [ -f "$f" ] || continue
  cnt=$(grep -cE "TODO|SKIP|FIXME|XXX|HACK" "$f" 2>/dev/null || echo 0)
  [ "$cnt" -gt 0 ] && echo "$cnt  $(basename "$f")"
done

echo ""
echo "=== 5. 破坏性副作用 (pkill/killall/rm -rf/launchctl) ==="
for f in ~/.hermes/scripts/*.{sh,py}; do
  [ -f "$f" ] || continue
  hits=$(grep -nE "pkill|kill -9|killall|rm -rf|launchctl (unload|bootout)" "$f" 2>/dev/null)
  if [ -n "$hits" ]; then
    echo "--- $(basename "$f") ---"
    echo "$hits"
  fi
done

echo ""
echo "=== 6. Chrome 端口冲突检查 ==="
echo "实际监听端口:"
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -i chrome | awk '{print $9}' | sort -u
echo ""
echo "脚本中硬编码的端口:"
grep -rnE "remote-debugging-port|--port=|9222|9333" ~/.hermes/scripts/*.{sh,py} 2>/dev/null | head -10

echo ""
echo "=== 审计完成 ==="
