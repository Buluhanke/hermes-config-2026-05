"""<name>_queue.py — 带节奏门控的队列 (Queue archetype template)

Copy to ~/.hermes/scripts/<name>_queue.py. Pair with `hermes-rhythm-gate` skill
for the full drain_queue reference impl.

Key invariants:
  - enqueue is append-only, no read-modify-write
  - drain holds fcntl flock (LOCK_EX | LOCK_NB) for the whole read-modify-write
  - drain writes atomically via tempfile + os.replace
  - ctx injection lets tests simulate any zone without monkey-patching time
  - max_per_tick caps the blast radius if the queue ever floods
"""
import fcntl
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

QUEUE_DIR = Path("~/.hermes/queue")
QUEUE_FILE = QUEUE_DIR / "<name>.jsonl"


def enqueue(msg: str, level: str) -> str:
    """Append a new entry. Returns the entry id (timestamp + microseconds)."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": level,  # "low" | "medium" | "high" | "critical_only"
        "msg": msg,
        "status": "pending",
    }
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["id"]


def _read_queue() -> list:
    """Read all entries, skipping any malformed lines (poison-row defense)."""
    if not QUEUE_FILE.exists():
        return []
    out = []
    with QUEUE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _write_queue(entries: list) -> None:
    """Atomic write — temp file + os.replace."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(QUEUE_DIR), prefix=".queue.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        os.replace(tmp, QUEUE_FILE)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def drain(zone_check: bool = True, max_per_tick=None, ctx=None) -> dict:
    """Process pending entries. Returns counts.

    Args:
        zone_check: if True, skip entries that don't pass current rhythm ctx.
                    If False, force-send everything (operator "drain now" mode).
        max_per_tick: cap the number of sends in this tick (None=unlimited).
        ctx: RhythmContext-like object (must have .should_proactive and
             .urgency_cap). None=call get_rhythm() at drain time.
    """
    if ctx is None:
        from rhythm import get_rhythm  # import lazy to avoid cycle
        ctx = get_rhythm()

    lock = QUEUE_DIR / ".drain.lock"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    fd = open(lock, "w")
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"sent": [], "failed": [], "skipped": [],
                    "remaining": -1, "note": "another drain in progress"}

        entries = _read_queue()
        sent, failed, skipped, remaining = [], [], [], []
        sent_count = 0

        for e in entries:
            if e.get("status") != "pending":
                remaining.append(e)  # 历史保留
                continue
            if max_per_tick is not None and sent_count >= max_per_tick:
                remaining.append(e)
                continue
            lvl = e.get("level", "medium")
            if zone_check and not _passes_rhythm(lvl, ctx):
                skipped.append(e["id"])
                remaining.append(e)
                continue
            try:
                ok = <send_fn>(e["msg"])  # your send impl
                if ok:
                    e["status"] = "sent"
                    e["sent_ts"] = datetime.now().isoformat(timespec="seconds")
                    sent.append(e["id"]); sent_count += 1
                else:
                    e["status"] = "failed"
                    failed.append(e["id"])
            except Exception as ex:
                e["status"] = "failed"
                e["error"] = str(ex)
                failed.append(e["id"])
            remaining.append(e)

        _write_queue(remaining)
        return {
            "sent": sent, "failed": failed, "skipped": skipped,
            "remaining": sum(1 for e in remaining if e.get("status") == "pending"),
        }
    finally:
        try: fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception: pass
        fd.close()


def _passes_rhythm(level: str, ctx) -> bool:
    if not ctx.should_proactive and level != "critical_only":
        return False
    priority = {"low": 0, "medium": 1, "high": 2, "critical_only": 3}
    cap_val = {"low": 0, "medium": 1, "high": 2, "critical_only": 99}
    return priority.get(level, 0) <= cap_val.get(ctx.urgency_cap, 0)


def <send_fn>(msg: str) -> bool:
    """PLACEHOLDER. In real hermes runtime, replace with:
        from hermes_tools import send_message
        return send_message(target="telegram", message=msg) is not None
    For tests, replace with a counter or assertion helper.
    """
    print(f"[send] {msg}")
    return True


# --- demo (convention A: 必须守卫) ---
if __name__ == "__main__":
    enqueue("hello world", "medium")
    print(drain(zone_check=False))  # 强制发，验证 enqueue -> drain 通路
