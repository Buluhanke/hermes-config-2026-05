#!/usr/bin/env bash
# Cron entry for the rhythm-gated drain.
# Drop this into your crontab with `crontab -e`:
#
#   */5 * * * *  /Users/aimac/.hermes/skills/productivity/hermes-rhythm-gate/templates/drain_cron.sh
#
# Or copy the line from this file's CRON_LINE variable.

set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export LANG="${LANG:-en_US.UTF-8}"

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SCRIPTS_DIR="$HERMES_HOME/scripts"
LOG_DIR="$HERMES_HOME/queue"
LOG_FILE="$LOG_DIR/drain.log"

mkdir -p "$LOG_DIR"

# Rotate log if > 5MB
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv "$LOG_FILE" "$LOG_FILE.$(date +%Y%m%d%H%M%S).old"
    : > "$LOG_FILE"
fi

cd "$HERMES_HOME" || exit 1

python3 - <<'PY' >> "$LOG_FILE" 2>&1
import sys
sys.path.insert(0, "$HERMES_HOME/scripts")
from hermes_notify import drain_queue
import json
r = drain_queue(zone_check=True, max_per_tick=20)
print(json.dumps({"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"), **r}))
PY
