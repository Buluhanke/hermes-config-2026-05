#!/bin/bash
# drain_watchdog.sh — silent-on-empty cron watchdog for the rhythm-gated queue.
#
# Difference from drain_cron.sh: this version produces NO stdout when there's
# nothing to do. Pair with `hermes cronjob create ... deliver=local no_agent=True`
# so empty ticks stay invisible to the user (no telegram/feishu ping spam).
#
# Drop this into ~/.hermes/scripts/ (cron uses just the filename, relative to
# ~/.hermes/scripts/), then:
#
#   hermes cronjob create \
#     --name hermes-queue-drain \
#     --schedule "*/5 * * * *" \
#     --script drain_watchdog.sh \
#     --no-agent \
#     --deliver local
#
# On a non-empty tick it prints one line:  drain: {"sent":[...], "skipped":[...], ...}
# On a crash it prints:                    drain_watchdog FAILED rc=N
# Cron will surface only the non-empty lines to delivery.

set -euo pipefail

VENV_PY="${HERMES_PY:-python3}"

OUT=$("$VENV_PY" - <<'PYEOF' 2>&1
import json, sys
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
import hermes_notify
r = hermes_notify.drain_queue(zone_check=True)
# Silent on: nothing sent, nothing failed, queue empty
if not r["sent"] and not r["failed"] and r["remaining"] == 0:
    sys.exit(0)
print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))
PYEOF
)

RC=$?
if [ $RC -ne 0 ]; then
    echo "drain_watchdog FAILED rc=$RC"
    echo "$OUT"
    exit 1
fi
[ -z "$OUT" ] && exit 0
echo "drain: $OUT"
