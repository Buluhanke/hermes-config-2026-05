# Queue JSONL format & status state machine

## File location

Default: `~/.hermes/queue/messages.jsonl`
Override: set `HERMES_QUEUE_DIR` env var.

The directory is auto-created on first write. The file is created on first `queue_message()` call.

## Per-line schema

```json
{
  "id": "20260604150310870795",
  "ts": "2026-06-04T15:03:10",
  "level": "medium",
  "msg": "自测 medium 消息",
  "status": "pending"
}
```

Field reference:

| field   | type   | required | notes                                                  |
|---------|--------|----------|--------------------------------------------------------|
| `id`    | string | yes      | `YYYYMMDDHHMMSSffffff` (6-digit μs). Treat as opaque.  |
| `ts`    | string | yes      | ISO 8601, second precision. Insertion time.            |
| `level` | string | yes      | one of: `low`, `medium`, `high`, `critical_only`        |
| `msg`   | string | yes      | Free text. No length cap, but see Telegram 4096.       |
| `status`| string | yes      | `pending` on insert; transitions on drain              |

## Status state machine

```
              queue_message()
                    |
                    v
              +-----------+
              |  pending  | <-------------------------+
              +-----------+                           |
                    |                                 |
                    | drain_queue(zone_check=True)    |
                    |                                 |
        +-----------+------------+                    |
        |                        |                    |
   cap passes              cap blocks                |
        |                        |                    |
        v                        v                    |
   telegram_send()          (stays pending;           |
        |                    no state change) --------+
        |
   +--------+
   |  ok?   |
   +---+----+
       |
    yes/ \no
       |   |
       v   v
    sent  failed
       |   |
       v   v
    +-----------+
    | terminal  |  (not retried automatically)
    +-----------+
```

- `pending` -> `sent`: drain passed cap + telegram_send() returned True
- `pending` -> `failed`: drain passed cap + telegram_send() returned False (or raised)
- `pending` -> `pending`: drain was called but cap blocked (skipped)
- `sent` / `failed` are terminal; they remain in the file as audit history

When `status != pending`, the entry is **preserved** in the queue file (not deleted) for audit. Drain rewrites the file with both terminal and pending entries.

## Failure modes

### Partial-write at EOF

Crash mid-`queue_message()` can leave a half-line at the end. `_read_queue()` skips unparseable lines, so the rest of the queue survives. The bad line is silently lost — accepted trade-off vs. SQLite.

### Lock contention

If a second drain starts while the first is still holding the flock, the second returns immediately with `note: "another drain in progress"`. The pending queue is unchanged.

### Disk full

`_write_queue()` will raise `OSError(28)`. The original queue file is untouched (we wrote to `*.tmp` first). The exception bubbles up; the caller should log it. The current drain's status updates are lost — those entries stay `pending` in the old (un-touched) queue file.

## Retention policy

Default recommendation: archive terminal entries after 7 days, drop after 30.

```bash
# Archive sent/failed rows older than 7 days
jq -c 'select(.status == "pending" or .ts > (now - 604800 | todate))' \
   ~/.hermes/queue/messages.jsonl > ~/.hermes/queue/messages.jsonl.tmp
mv ~/.hermes/queue/messages.jsonl.tmp ~/.hermes/queue/messages.jsonl
```

Note: `jq` with `now - 604800 | todate` is GNU `jq` ≥ 1.6 with `todate` available. On macOS the bundled `jq` is fine. If you need portability, do it in Python:

```python
import json, time
from pathlib import Path
cutoff = time.time() - 7 * 86400
keep = []
for line in Path("~/.hermes/queue/messages.jsonl").expanduser().read_text().splitlines():
    if not line.strip(): continue
    e = json.loads(line)
    if e["status"] == "pending": keep.append(e); continue
    # parse ts back to epoch
    from datetime import datetime
    e_eps = datetime.fromisoformat(e["ts"]).timestamp()
    if e_eps > cutoff: keep.append(e)
# atomic rewrite
```

## Hard limits

- Telegram message body: 4096 chars. Split or truncate above that.
- Discord: 2000 chars.
- Feishu: 4000 chars text-only.
- iMessage: effectively unlimited but render degrades above ~5000.
- The queue file itself: 100MB is the safe practical limit. Above that, switch to SQLite.
