---
name: hermes-rhythm-gate
description: "Context-gated outbound messaging — time-of-day rhythm (work/evening/night/morning) decides whether a notification is sent, queued to a persistent JSONL file, or skipped. Includes a flush/drain pattern with fcntl flock + atomic file write, urgency caps, and ctx injection for testing. Use when you need to 'send a notification that respects quiet hours', 'queue alerts to flush at the right time', 'add a rate-cap to outbound messages', 'build a notifier that does not disturb deep night', or 'wrap telegram/feishu/discord/sms sends with a time-of-day policy'. Triggers: rhythm, time zone policy, quiet hours, notification gate, message queue, drain queue, urgency cap, critical_only, 不打扰, 节奏判断, 排队发送."
---

# Hermes Rhythm Gate

Time-of-day gated outbound messaging with a persistent JSONL queue, atomic writes, and a flush/drain loop. Built for "I want to be notified, but not at 3am."

## When to use this skill

- You have an agent that wants to push messages to telegram / feishu / discord / imessage / email / pushover / webhook
- The user works variable hours, or has explicit "do not disturb" windows
- You need a *durable* outbox — if the script crashes mid-send, the message should not be lost
- You want to test/audit the policy without writing fake clock code (use ctx injection)
- You want a cron that periodically flushes the queue when conditions become favorable

Do **not** use this for: in-session conversational replies (the model should never gate its own replies on a rhythm — that is a UX bug). Use this for *outbound* agent-initiated notifications only.

## Core architecture

```
Producer (any code path that wants to send)
    |
    v
hermes_notify(msg, level) ---> should_send_message(level)?
    |                                  |
    | yes                              | no
    v                                  v
telegram_send(msg)             queue_message(msg, level)
                                      | persistent JSONL
                                      v
                          ~/.hermes/queue/messages.jsonl
                                      |
                                      | (cron every 5 min)
                                      v
                          drain_queue(zone_check=True)
                                      |
                                      +-- sent      -> mark status=sent
                                      +-- failed    -> mark status=failed + error
                                      +-- skipped   -> keep pending, retry next tick
```

## Reference impl: ~/.hermes/scripts/hermes_notify.py

Already exists and tested. Use it as the canonical pattern. Structure:

1. `rhythm.py` — pure data: `TimeZone` enum, `RhythmContext` dataclass, `get_rhythm()`, `should_send_message(level)`
2. `hermes_notify.py` — gates send against rhythm; provides queue, drain, atomic write
3. `telegram_send()` — **placeholder**. In real hermes runtime, replace the body with `send_message(target='telegram', message=msg)`. In a standalone script, use the bot HTTP API or a CLI shim.

### Urgency levels

```
low            priority 0
medium         priority 1
high           priority 2
critical_only  priority 3   <- always passes, even at night
```

Cap per zone:
- `WORK` (9-18 weekday)      -> cap=high           (anything <= high passes)
- `EVENING` (18-22)          -> cap=medium         (no high pings after dinner)
- `NIGHT` (22-6)             -> cap=critical_only  (proactive=False except critical)
- `MORNING` (6-9)            -> cap=medium         (proactive=False; pre-work quiet)

The `critical_only` cap is special: it has priority value 99, so only critical_only entries can pass it. Use this for "system is down" / "data lost" / "security alert" type pings.

## Key techniques (re-use these patterns)

### 1. Cross-process mutex with `fcntl.flock` + `LOCK_NB`

```python
import fcntl
lock_fd = open(lock_path, "w")
try:
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    return {"note": "another drain in progress"}
# ... critical section ...
finally:
    try: fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except: pass
    lock_fd.close()
```

`LOCK_NB` is critical — without it, two cron ticks racing will serialize and the second will run stale state. With `LOCK_NB`, the second tick exits immediately with a "drain in progress" note.

### 2. Atomic JSONL rewrite with `tempfile + os.replace`

```python
fd, tmp = tempfile.mkstemp(dir=QUEUE_DIR, prefix=".queue.", suffix=".tmp")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for e in entries: f.write(json.dumps(e, ensure_ascii=False) + "\n")
    os.replace(tmp, QUEUE_FILE)
except:
    if os.path.exists(tmp): os.unlink(tmp)
    raise
```

`os.replace` is atomic on POSIX (and Windows since 3.3). Half-written files never become the live file. The `try/except` cleans up the temp on failure so the queue dir does not accumulate `.tmp` junk.

### 3. Resilient JSONL read — skip poison rows

```python
for line in f:
    line = line.strip()
    if not line: continue
    try: out.append(json.loads(line))
    except json.JSONDecodeError: continue
```

If a crash leaves a half-written line at EOF, you skip it. Lost one row is better than the whole queue going unreadable. For higher safety, wrap each line in a length-prefixed envelope or use SQLite (out of scope for this skill).

### 4. `ctx` injection for testability

`drain_queue(ctx=...)` accepts a pre-built `RhythmContext` instead of calling `get_rhythm()`. This lets you simulate NIGHT/WORK without monkey-patching `datetime.now`. Pattern:

```python
fake_night = RhythmContext(hour=23, weekday=3, zone=TimeZone.NIGHT,
                          is_weekend=False, should_proactive=False,
                          urgency_cap="critical_only")
drain_queue(zone_check=True, ctx=fake_night)
```

### 5. `zone_check=False` as the "force flush" kill switch

The drain function takes a `zone_check` flag. When `True` (default), it respects the rhythm. When `False`, it sends every pending message regardless of zone. Use this for:
- Operator manually drains a backed-up queue
- Tests
- A "I just woke up, give me everything" user request

Always log/return the result so the user can see what was force-flushed.

### 6. `max_per_tick` for rate control

```python
drain_queue(zone_check=True, max_per_tick=10)
```

Limits how many messages go out in one cron tick. Critical when you have 500+ queued messages and do not want telegram to rate-limit you. Default `None` = unlimited.

## Wiring it up

### Standalone (script-only)

```bash
# 1. Save the script
cp references/hermes_notify.py ~/.hermes/scripts/
cp references/rhythm.py ~/.hermes/scripts/

# 2. Cron the drain (every 5 min)
crontab -e
*/5 * * * *  cd ~/.hermes && python3 -c "from scripts.hermes_notify import drain_queue; print(drain_queue())" >> ~/.hermes/queue/drain.log 2>&1
```

### In hermes runtime (the recommended path)

In hermes, the script's `telegram_send` is a placeholder. Replace its body with the platform send tool:

```python
def telegram_send(msg: str) -> bool:
    from hermes_tools import send_message
    return send_message(target="telegram", message=msg) is not None
```

Or — better — skip the script wrapper entirely in hermes runtime. The script exists for cron jobs and external triggers. When you are already in a hermes session, call `hermes_notify()` directly; the `hermes_notify_minimal` function in the reference impl is the cleanest 1:1 of the original 4-liner.

### Production checklist

- [ ] Replace `telegram_send` placeholder with real send
- [ ] Cron the drain at 5-min cadence (do not go lower, that is noise)
- [ ] Set up log rotation on `~/.hermes/queue/drain.log` (newsyslog or logrotate)
- [ ] Decide retention: when do `status=sent` rows get archived? (Default: keep 7 days, then `jq -c 'select(.ts < "2026-01-01")' messages.jsonl > archive.jsonl; rm`)
- [ ] Add a "force flush" command so the user can say "drain it now" -> `drain_queue(zone_check=False)`
- [ ] If you are using telegram: respect 30 msg/sec global, 1 msg/sec per chat. `max_per_tick=20` is safe.

## Pitfalls

1. **Do not gate conversational replies on rhythm.** The model replying to a user question is not "outbound notification" — gating that creates a "why is the agent ignoring me" UX failure. Rhythm gate is for agent-initiated push only.

2. **Do not `rm` the queue file to "clear" it.** Use `jq` filter or `mv` to an `archive.jsonl`. An empty `[]` write via `_write_queue([])` is fine and intentional, but `rm` leaves a window where concurrent drain reads a non-existent file and silently loses any in-flight append.

3. **`time.time()` race with `datetime.now()` for "tick timestamp".** Use one or the other consistently. `_should_flush_entry` and the queue `ts` field should both use `datetime.now()`.

4. **Do not use a single global lock file path across multiple queues.** If you later add a second queue (e.g., for email vs telegram), give each its own `*.lock` file. Cross-queue lock contention will silently serialize drains that should be parallel.

5. **The `critical_only` escape hatch is a footgun.** If your producers overuse it ("everything is critical!"), the rhythm gate becomes useless. Audit `level` distribution monthly. If critical_only is > 20% of entries, retrain producers.

6. **JSONL is not a database.** No transactions, no indexing, no concurrent writers. If you need > 10k entries or multi-writer scenarios, switch to SQLite (WAL mode). The pattern still works, only the storage layer changes.

7. **Telegram `send_message` rate limit is 1/sec per chat.** A naive drain of 100 queued messages will get you 429'd. Use `max_per_tick` + `time.sleep(1.05)` between sends, or batch via `sendMediaGroup`. Not handled in the reference impl — by design, since the rate-limit policy belongs to the send adapter, not the gate.

8. **Top-level side effects in module files kill the drain silently.** Real failure case (2026-06-04): `rhythm.py` was edited to add a usage example at the bottom of the file but the print statements were placed at module level, not inside `if __name__ == "__main__":`. Result: every `import rhythm` (and transitively every `import hermes_notify`) ran the demo print + did `get_rhythm()` + called `should_send_message()`. Symptom: drain_watchdog.sh was "noisy" with two extra lines on every tick that looked like part of drain output, and side-effect `should_send_message('medium')` actually called `print` and potentially mutated state. Diagnose: when import-time side effects appear in a script, search for top-level statements below the last function def with `grep -nE '^[a-zA-Z]' file.py` and check whether they should be inside a `__main__` guard. **Fix pattern**: any demo / example / quick-test code at the bottom of a script module MUST be inside `if __name__ == "__main__":` — `import` runs the whole module body.

9. **`hermes_notify.py` style: keep `from rhythm import` aliases optional.** Real case (2026-06-04): rhythm.py was a simple leaf module, and hermes_notify.py did `import rhythm` then `sys.modules.setdefault("hermes_time_rhythm", rhythm)`. This lets callers use either name. But it means static analyzers (Pyright) flag the "hermes_time_rhythm" import as missing. False alarm in practice, but if you want a clean LSP signal, also do a `try: import hermes_time_rhythm except ImportError: pass` at module load to populate sys.modules before the static check. Not worth the complexity unless your editor is strict.

## Verification

After wiring up, verify with this exact checklist (not optional):

```bash
# 1. Imports resolve and a real-time probe works
python3 ~/.hermes/scripts/hermes_notify.py

# Expected: shows current zone, 4-level self-test, drain result, alias import OK

# 2. Queue is durable across restarts
python3 -c "import sys; sys.path.insert(0, '~/.hermes/scripts'); from hermes_notify import queue_message; queue_message('test', 'medium')"
ls -la ~/.hermes/queue/messages.jsonl   # should exist with 1 line

# 3. Drain filters by zone (use ctx injection for NIGHT)
python3 -c "
import sys; sys.path.insert(0, '~/.hermes/scripts')
from hermes_notify import drain_queue
from rhythm import RhythmContext, TimeZone
r = drain_queue(ctx=RhythmContext(23, 3, TimeZone.NIGHT, False, False, 'critical_only'))
print(r)
"
# Expected: medium entries skipped, critical_only sent (or kept pending if no critical_only queued)

# 4. Force flush works
python3 -c "import sys; sys.path.insert(0, '~/.hermes/scripts'); from hermes_notify import drain_queue; print(drain_queue(zone_check=False))"
# Expected: all pending -> sent
```

## Files in this skill

- `references/hermes_notify.py` — full reference implementation, drop-in
- `references/rhythm.py` — pure data layer (TimeZone, RhythmContext, get_rhythm, should_send_message)
- `references/queue-format.md` — JSONL schema, status state machine, retention policy
- `references/real-failure-top-level-print.md` — 2026-06-04 case: unguarded `print` in rhythm.py broke the drain
- `templates/drain_cron.sh` — copy-paste crontab entry + logrotate config (always-on logging)
- `templates/drain_watchdog_silent.sh` — silent-on-empty watchdog for `cronjob no_agent=True` delivery (no user ping on empty ticks)
- `scripts/audit_queue.py` — re-runnable: prints level distribution, oldest pending, queue size
