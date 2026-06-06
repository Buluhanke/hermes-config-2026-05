#!/usr/bin/env python3
"""Audit the rhythm-gate queue: size, level distribution, oldest pending, sent/failed ratio.

Re-runnable. Safe to call from cron for a daily summary push.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Allow running standalone or from skill dir
SCRIPTS_DIR = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
QUEUE_FILE = SCRIPTS_DIR.parent / "queue" / "messages.jsonl"


def main() -> int:
    if not QUEUE_FILE.exists():
        print(f"[audit] no queue at {QUEUE_FILE}")
        return 0

    entries = []
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[audit] WARN: bad line {ln}: {e}", file=sys.stderr)

    if not entries:
        print("[audit] queue is empty")
        return 0

    total = len(entries)
    by_status = Counter(e.get("status", "unknown") for e in entries)
    by_level = Counter(e.get("level", "unknown") for e in entries)

    pending = [e for e in entries if e.get("status") == "pending"]
    pending_by_level = Counter(e.get("level", "unknown") for e in pending)

    oldest_pending = None
    if pending:
        try:
            oldest_pending = min(
                datetime.fromisoformat(e["ts"]) for e in pending if "ts" in e
            )
        except (ValueError, KeyError):
            pass

    print(f"[audit] queue file:    {QUEUE_FILE}")
    print(f"[audit] total entries: {total}")
    print(f"[audit] by status:     {dict(by_status)}")
    print(f"[audit] by level:      {dict(by_level)}")
    print(f"[audit] pending count: {len(pending)}")
    print(f"[audit] pending mix:   {dict(pending_by_level)}")
    if oldest_pending:
        age_h = (datetime.now() - oldest_pending).total_seconds() / 3600
        print(f"[audit] oldest pending: {oldest_pending.isoformat(timespec='seconds')}  ({age_h:.1f}h old)")

    # Footgun detector: critical_only should be < 20% of total
    crit = by_level.get("critical_only", 0)
    if total > 0 and crit / total > 0.20:
        print(
            f"[audit] WARN: critical_only is {crit/total*100:.0f}% of total — "
            "rhythm gate is being abused. Retrain producers."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
