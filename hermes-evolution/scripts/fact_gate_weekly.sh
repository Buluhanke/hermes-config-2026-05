#!/bin/bash
# 每周事实库门控审计（no_agent cron 用；纯脚本，不调用任何模型）
# 只标记归档候选，绝不删除、绝不改 content；幂等。
set -euo pipefail
GATE="$HOME/.hermes/scripts/fact_gate.py"
[ -f "$GATE" ] || { echo "FACT_GATE_MISSING: $GATE"; exit 1; }
python3 - "$GATE" <<'PY'
import json, subprocess, sys
gate = sys.argv[1]
r = subprocess.run(["python3", gate, "audit", "--apply", "--json"],
                   capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print("FACT_GATE_ERROR:", r.stderr[:200]); raise SystemExit(1)
d = json.loads(r.stdout)
b = d["bands"]
print(
    f"FACT_GATE weekly: total={d['total']} keep={b['KEEP']} watch={b['WATCH']} "
    f"archive_candidates={b['ARCHIVE_CANDIDATE']} newly_marked={d['marked_this_run']} "
    f"report={d['generated_at'][:10]}"
)
PY
