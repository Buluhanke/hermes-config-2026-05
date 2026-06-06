#!/bin/bash
# drain_watchdog.sh — cron 每 N 分钟调用, 把 hermes_notify 队列里可发的消息 flush 出去
# 用法: 由 hermes cronjob(no_agent=True) 调用, 路径: ~/.hermes/scripts/drain_watchdog.sh
# 规则: empty stdout = 静默; 非空 = 简短汇报
#
# 配合 cron:
#   cronjob(action="create", name="hermes-queue-drain",
#           no_agent=True, schedule="*/5 * * * *", script="drain_watchdog.sh")

set -euo pipefail

VENV_PY="${HERMES_PY:-python3}"

OUT=$("$VENV_PY" - <<'PYEOF'
import json, sys
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
import hermes_notify
r = hermes_notify.drain_queue(zone_check=True)
# 静默条件: 没动作 + 队列空
if not r["sent"] and not r["failed"] and r["remaining"] == 0:
    sys.exit(0)
print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))
PYEOF
)

RC=$?

# zone_check=True 永远有返回; drain 自身不应崩。若崩则报警
if [ $RC -ne 0 ]; then
    echo "drain_watchdog FAILED rc=$RC"
    echo "$OUT"
    exit 1
fi

# 空输出 = 静默（这是关键, 让用户感觉不到 cron 存在）
[ -z "$OUT" ] && exit 0

echo "drain: $OUT"
