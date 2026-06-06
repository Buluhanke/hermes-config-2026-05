---
name: notification-rhythm-pipeline
description: |
  Use when building or extending a time-of-day-aware notification system — gating
  proactive messages by user rhythm, queueing off-zone messages to disk, and
  draining the queue via a low-overhead cron watchdog. Pattern: rhythm module
  (time→zone decision) → notify gate (should_send?) → JSONL queue (atomic write +
  fcntl lock) → drain (filtered or forced) → cron + no_agent + silent-on-empty.

  Trigger on: "节奏发送" / "时段感知" / "别在深夜打扰" / "排队发送" / "drain 队列"
  / "rhythm" / "queue_message" / "urgent cap" / "off-hours" / "rate-limit messaging".

  Don't use for: real-time critical alerts (just send), single-shot notifications
  (no queue needed), or platform-layer messaging (use send_message tool directly,
  not a script).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [notifications, rhythm, queue, cron, watchdog, rate-limiting, hermes-notify]
    related_skills: [proactive-execution, script-provider-independence, scheduled-task-audit]
---

# Notification Rhythm Pipeline

## Overview

A complete pattern for proactive messaging that respects the user's time-of-day rhythm
and never spams during off-hours. Built from the 2026-06-04 session where rhythm +
notify + drain + cron were assembled incrementally.

The pipeline has four layers:

1. **rhythm module** — `get_rhythm()` returns a `RhythmContext` (zone, proactive, cap)
2. **notify gate** — `hermes_notify(msg, level)` decides send-now vs queue
3. **drain function** — `drain_queue(zone_check=True)` flushes pending entries
4. **cron watchdog** — `*/5 * * * *` `no_agent=True` script, silent when idle

Key properties: atomic file writes, `fcntl` lock against concurrent drain, no LLM
involved in the watchdog (saves tokens, runs in <1s), empty stdout = no message to user.

## When to Use

- User says "别在深夜打扰我" / "晚上 10 点之后别发" / "工作时高优，休息时低优"
- User wants message rate limiting by time of day
- User has Telegram/Feishu/Discord channels and wants to gate proactive pings
- Need to persist notifications across Hermes sessions / gateway restarts
- Need a watchdog that runs every N minutes but stays silent most of the time

**Don't use for:**

- Single-shot critical alerts → just call `send_message` directly
- Real-time trading signals / market data → too much latency from queue
- When you have the actual `send_message` tool available in the session → just use it
- Per-user personalization (this pattern is per-environment, not per-user)

## File Map (the canonical working setup)

```
~/.hermes/scripts/
  rhythm.py              # 时区/节奏决策 (zone, proactive, cap)
  hermes_notify.py       # 通知门控 + 队列 + drain
  drain_watchdog.sh      # cron 调用, silent-on-empty
~/.hermes/queue/
  messages.jsonl         # 队列, 每行一条 JSON
  .drain.lock            # fcntl lock file
```

The cron job is `hermes-queue-drain` running `*/5 * * * *` with `no_agent=True`,
`deliver=local` (only logs, no Telegram push unless action happened).

## Architecture

### Layer 1: rhythm.py

Pure decision module. No side effects (and the `if __name__ == "__main__":` guard
around the usage example is **mandatory** — see `references/python-top-level-side-effects-20260604.md`).

```python
import datetime
from dataclasses import dataclass
from enum import Enum

class TimeZone(Enum):
    WORK = "work"        # 9-19 工作
    EVENING = "evening"  # 19-22
    NIGHT = "night"      # 22-6
    MORNING = "morning"  # 6-9

@dataclass
class RhythmContext:
    hour: int
    weekday: int
    zone: TimeZone
    is_weekend: bool
    should_proactive: bool
    urgency_cap: str

def get_rhythm() -> RhythmContext: ...
def should_send_message(level: str) -> bool: ...

if __name__ == "__main__":  # 守卫必加
    ctx = get_rhythm()
    print(...)
```

### Layer 2: hermes_notify.py

Three public functions:

- `hermes_notify(msg, level="medium")` — main entry; returns `{action: 'sent'|'queued', ...}`
- `queue_message(msg, level)` — JSONL append
- `drain_queue(zone_check=True, max_per_tick=None, ctx=None)` — flush pending

**Critical internals:**

- `importlib.import_module` + `sys.modules.setdefault("hermes_time_rhythm", rhythm)` —
  lets users write `from hermes_time_rhythm import should_send_message` even though the
  file is `rhythm.py`. (LSP will warn; runtime works. Add `# type: ignore` if needed.)
- `_write_queue` uses `tempfile.mkstemp` + `os.replace` for atomicity — half-written
  queue file on crash never replaces the good one.
- `drain_queue` uses `fcntl.flock(LOCK_EX | LOCK_NB)` — concurrent drain returns
  `{note: "another drain in progress"}` instead of blocking.
- `_should_flush_entry(level, ctx)` accepts external `ctx` → easy to test night/weekend
  scenarios by injecting a fake `RhythmContext` without monkey-patching `datetime`.

### Layer 3: drain_watchdog.sh

```bash
#!/bin/bash
set -euo pipefail
VENV_PY="${HERMES_PY:-python3}"

OUT=$("$VENV_PY" - <<'PYEOF'
import json, sys
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
import hermes_notify
r = hermes_notify.drain_queue(zone_check=True)
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
```

Key design: `no_agent=True` cron + `deliver=local` + empty-stdout = silent.
`drain_queue()` returns dict → JSON-serialize → print → cron captures stdout.
If `drain_queue` itself crashes (rare; fcntl lock + atomic write protect against
most paths), shell wrapper surfaces the error to cron logs (still silent to user).

### Layer 4: cron job

Created via `cronjob` tool:

```python
cronjob(
    action="create",
    name="hermes-queue-drain",
    no_agent=True,
    schedule="*/5 * * * *",
    script="drain_watchdog.sh",  # relative to ~/.hermes/scripts/
)
```

**`no_agent=True` is critical** — it skips the LLM agent loop entirely. Without it,
every 5 min you'd spin up an LLM call to "decide what to do", wasting tokens and
adding 3-10s latency. The script's stdout is delivered verbatim, and empty stdout =
no message (the watchdog pattern).

`deliver=local` (not "origin") keeps it out of the user's Telegram/CLI when idle.

## Common Pitfalls

1. **Top-level code in `rhythm.py` / `hermes_notify.py`** — `print` or function calls
   outside `if __name__ == "__main__":` will fire on every import. **Always wrap the
   "使用示例" section.** See `proactive-execution` rule 18 and the references/ file.

2. **Cron script must use relative path** — `cronjob` rejects absolute paths.
   Place scripts in `~/.hermes/scripts/`, reference by filename only.

3. **`no_agent=False` (default) burns tokens** — every 5 min you'd wake the LLM to
   read the prompt, see "drain queue", and reply. Use `no_agent=True` for any pure
   shell/Python watchdog.

4. **`telegram_send` placeholder in hermes_notify.py** — the script can't reach
   hermes' platform layer (no `send_message` tool in subprocess). The current
   implementation is `print(msg)` and works for cron testing. For real delivery,
   either:
   - (a) Replace `telegram_send` body with `subprocess.run(['hermes', 'send', ...])`
     if a CLI exists, OR
   - (b) Run a separate cron (no_agent=False) that calls `drain_queue` and then
     `send_message` tool — but that defeats the "lightweight watchdog" goal.
   - (c) Accept the queue as a *persistent record* and have a daily digest job
     summarize and resend the day's pending messages.

5. **Concurrent drain** — if `drain_watchdog.sh` fires while another drain is
   running (rare with 5-min schedule, but possible on slow machines), the second
   one returns `{note: "another drain in progress"}` and exits 0 silently. Good.
   Don't remove the lock thinking "5 min is enough spacing" — clock skew / manual
   triggers can race.

6. **Queue grows unbounded** — every entry is appended forever. Add a compression
   step (e.g. archive `sent`/`failed` older than 7 days to `messages.archive.jsonl`).
   Not critical until ~10k entries; 1k/day = 1 year before it hurts.

7. **LSP false-positive on `from hermes_time_rhythm import ...`** — the alias is
   registered at runtime via `sys.modules.setdefault`, so static analysis can't
   see it. Add `# type: ignore` or use the direct `from rhythm import ...` in
   new code. The runtime works.

8. **Top-level side effects masquerade as "main block triggered on import"** —
   classic 5+ round debugging trap. Symptom: `import X` outputs "使用示例" lines.
   First instinct: "Python's `if __name__` is broken / pyc cache is stale /
   sys.path is wrong". All wrong. The truth is always: the file has a top-level
   `print(...)` (or other call) **outside** the `if __name__ == "__main__":` guard.
   Python is behaving correctly — top-level code runs on import by design.
   **Fix**: wrap examples in `if __name__ == "__main__":` (rule 18 of
   `proactive-execution`). Verify by running a one-liner: `python3 -c "import X"
   2>&1 | head -5` — any unexpected output = top-level leak.

9. **`hermes-cli/mcp` 路径必须**用 `~/.hermes/scripts/` 下文件名的相对路径**
   (not absolute). The `cronjob` tool rejects absolute paths with a clear error,
   but the workaround is to use the filename and place the script in
   `~/.hermes/scripts/`. Don't fight it; place the file there.

## Verification Checklist

- [ ] `python3 -c "import hermes_notify; print('clean')"` — no top-level side effects
- [ ] `python3 hermes_notify.py` — runs main, prints all 4 level results
- [ ] `~/.hermes/scripts/drain_watchdog.sh` — runs, rc=0, stdout empty when queue empty
- [ ] Queue with 1 entry → drain fires, returns `{sent: [...], remaining: 0}`
- [ ] Queue with 1 critical_only during work zone → stays `skipped`, `remaining: 1`
- [ ] `cronjob action=list` — shows `hermes-queue-drain`, schedule `*/5 * * * *`
- [ ] `cronjob action=log job_id=<id>` after 5 min — shows last run output
- [ ] `~/.hermes/queue/messages.jsonl` — JSONL, valid JSON per line
- [ ] `~/.hermes/queue/.drain.lock` — exists, 0 bytes (lock file)

## Tuning Knobs

| Knob | Where | Default | When to change |
|---|---|---|---|
| `zone` boundaries | `rhythm.py` `get_rhythm()` | 9-18 work, 18-22 evening, 22-6 night | User works night shift, or 12h timezone diff |
| `cap` per zone | `rhythm.py` | work=high, evening=medium, night=critical_only | User wants fewer pings during work, or more in evening |
| Drain frequency | cron `schedule` | `*/5` | Too many wake-ups → `*/15`; too laggy → `*/2` |
| `max_per_tick` | `drain_queue` arg | None | Add `max_per_tick=20` if first drain after long idle floods |
| Queue retention | manual / future script | forever | Archive `sent`/`failed` >7d, or >30d |

## Migration Path to Real Telegram Delivery

When you want real Telegram delivery (not the print placeholder), pick one:

**Option A: Hermes CLI bridge** (best when CLI has `hermes send`):
```python
# In hermes_notify.telegram_send():
import subprocess
subprocess.run(["hermes", "send", "--target", "telegram", "--message", msg], check=True)
```

**Option B: No-agent drain + agent resender** (split cron in two):
- Cron 1 (no_agent=True, */5): writes `{pending_ids}` to a flag file, exits silent
- Cron 2 (no_agent=False, */5 with offset): reads flag, calls `send_message` tool per id

**Option C: Same-cron agent mode** (simplest but expensive):
- Single cron (no_agent=False, */5): full LLM call reads queue, calls `send_message`
- Burns ~3-5k tokens per tick. Acceptable if you don't care about cost; avoid otherwise.

**Option D: Adapter-level inject in `telegram.py::send`** (recommended for deep integration):
- ⚠️ This requires editing hermes-agent internal code (`gateway/platforms/telegram.py`)
- Add ~5 lines at top of `send()` method to call `should_send_message(urgency)`
- Pull `urgency` from `metadata` (default "medium"); if blocked, return early with `{filtered: "rhythm", delivered: false}`
- **Constraint**: hermes-agent process ≠ `~/.hermes/scripts/` Python. The alias
  `hermes_time_rhythm` only works on the script side. From inside the adapter
  you need either (a) re-import via `sys.path` injection, (b) a wrapper module
  inside hermes-agent's own package, or (c) call a CLI subprocess.
- **Always start in dry-run mode** (log + return) for at least 1 week before
  enabling real drops. Otherwise a 23:00 stuck alert can lose a real message.

**Recommended**: A for scripts; D for deep integration (after dry-run week).

### 关键架构警示（2026-06-04 调研发现）

`DeliveryRouter.deliver()` 路径**实际不存在于 runtime**——`run.py` 构造了 `self.delivery_router`
但从不调 `.deliver()`。真实的 telegram 出站都直接 `await adapter.send(chat_id, content, metadata=...)`。
这意味着：

- **不要**在 `DeliveryRouter.deliver` 加门控（死路径，加了也拦不到）
- **不要**在 `_deliver_to_platform` 加判断（cron output 路径，不影响 runtime push）
- **要**改就改 `telegram.py::send`（唯一 runtime chokepoint）

详见 `hermes-internal-architecture-patterns` § 7 "Telegram 推送的真实路径"。

## Real Files (Reference Implementation, 2026-06-04)

The current working setup lives at:

- `/Users/aimac/.hermes/scripts/rhythm.py` — 56 lines, guarded main
- `/Users/aimac/.hermes/scripts/hermes_notify.py` — 285 lines, drain_queue + lock + atomic
- `/Users/aimac/.hermes/scripts/drain_watchdog.sh` — 25 lines, silent-on-empty
- `~/.hermes/queue/messages.jsonl` — populated by tests, drain in cron
- Cron job `b2ad855429b2` (hermes-queue-drain) — every 5 min, no_agent=True

Copy these files as starting point. The `templates/` directory of this skill has
clean, well-commented versions meant for reproduction.

## Related

- `proactive-execution` rule 18 — Python `if __name__` guard discipline
- `proactive-execution` rule 19 — "还有其他任务" intent recognition
- `script-provider-independence` — don't hardcode providers in cron scripts
- `scheduled-task-audit` — audit pattern for cron jobs you can't remember creating
- `references/python-top-level-side-effects-20260604.md` — full debug transcript
  of the `rhythm.py` import-side-effect incident
