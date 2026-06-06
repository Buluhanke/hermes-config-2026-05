"""Hermes 通知门控 — 节奏感知 + 队列 + drain。

架构：
    rhythm.py         时段决策（zone / proactive / cap）
    hermes_notify.py  本文件 — notify gate + JSONL queue + drain
    drain_watchdog.sh cron 调用的 silent-on-empty 脚本
    ~/.hermes/queue/  队列落盘 + 锁文件

Usage:
    from hermes_notify import hermes_notify, drain_queue
    hermes_notify("订单有 3 条", level="medium")
    drain_queue()  # flush 队列

真实集成：
    telegram_send() 当前是 print 占位。要真发, 改 _send_via_telegram() 函数。
"""
import fcntl
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# --- 让 rhythm 模块可导入, 同时支持别名 'hermes_time_rhythm' ---
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
_rhythm_module = None
for _name in ("rhythm", "hermes_time_rhythm"):
    try:
        _rhythm_module = importlib.import_module(_name)
        break
    except ImportError:
        continue
if _rhythm_module is None:
    raise ImportError(f"未找到 rhythm 模块, 请确认 {SCRIPTS_DIR}/rhythm.py 存在")

# 注册别名（用户原代码用了 'hermes_time_rhythm'）
sys.modules.setdefault("hermes_time_rhythm", _rhythm_module)

get_rhythm = _rhythm_module.get_rhythm
should_send_message = _rhythm_module.should_send_message

# --- 队列路径（可通过环境变量覆盖）---
QUEUE_DIR = Path(os.environ.get("HERMES_QUEUE_DIR", str(Path.home() / ".hermes" / "queue")))
QUEUE_FILE = QUEUE_DIR / "messages.jsonl"


# ============================================================================
# 真实发送层（占位 — 替换为真集成）
# ============================================================================
def _send_via_telegram(msg: str) -> bool:
    """占位发送器。真实集成：

    Option A: Hermes CLI
        import subprocess
        subprocess.run(["hermes", "send", "--target", "telegram", "--message", msg], check=True)

    Option B: 直接 HTTP 调用 Telegram Bot API
        import httpx
        httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                   json={"chat_id": CHAT_ID, "text": msg})

    Option C: 把队列当成"持久化日志", 用 daily digest job 统一回放
    """
    print(f"[telegram_send] {msg}")
    return True


# ============================================================================
# 队列读写（原子, 坏行容错）
# ============================================================================
def queue_message(msg: str, level: str) -> str:
    """入队, 返回 id。"""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": level,
        "msg": msg,
        "status": "pending",
    }
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["id"]


def _read_queue() -> list:
    """读队列, 坏行跳过（避免 JSONDecodeError 毒丸整个 drain）。"""
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
    """原子写：临时文件 + os.replace, 半路崩了不丢。"""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(QUEUE_DIR), prefix=".queue.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        os.replace(tmp_path, QUEUE_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ============================================================================
# 决策辅助（接受外部 ctx, 便于测试）
# ============================================================================
def _should_flush_entry(entry_level: str, ctx) -> bool:
    if not ctx.should_proactive and entry_level != "critical_only":
        return False
    priority = {"low": 0, "medium": 1, "high": 2, "critical_only": 3}
    cap_val = {"low": 0, "medium": 1, "high": 2, "critical_only": 99}
    return priority.get(entry_level, 0) <= cap_val.get(ctx.urgency_cap, 0)


# ============================================================================
# 公开 API
# ============================================================================
def hermes_notify(msg: str, level: str = "medium") -> dict:
    """主入口: 节奏允许就发, 否则入队。"""
    ctx = get_rhythm()
    if not should_send_message(level):
        qid = queue_message(msg, level)
        return {
            "action": "queued", "id": qid, "level": level,
            "zone": ctx.zone.value, "cap": ctx.urgency_cap,
        }
    ok = _send_via_telegram(msg)
    return {
        "action": "sent" if ok else "failed", "level": level,
        "zone": ctx.zone.value, "cap": ctx.urgency_cap,
    }


def hermes_notify_minimal(msg: str, level: str = "medium") -> None:
    """用户原版最小实现（保留以 1:1 对齐）。"""
    if not should_send_message(level):
        queue_message(msg, level)
        return
    _send_via_telegram(msg)


def drain_queue(
    zone_check: bool = True,
    max_per_tick: int | None = None,
    ctx=None,
) -> dict:
    """flush 队列。

    Args:
        zone_check: True=按节奏过滤; False=强制全发
        max_per_tick: 单次最多发多少条
        ctx: 注入的 RhythmContext（测试用）; None=实时 get_rhythm()

    Returns:
        {sent, failed, skipped, remaining, zone, cap, note?}
    """
    if ctx is None:
        ctx = get_rhythm()

    lock_path = QUEUE_DIR / ".drain.lock"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    lock_fd = open(lock_path, "w")
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {
                "sent": [], "failed": [], "skipped": [], "remaining": -1,
                "zone": ctx.zone.value, "cap": ctx.urgency_cap,
                "note": "another drain in progress",
            }

        entries = _read_queue()
        sent, failed, skipped, remaining_entries = [], [], [], []
        sent_count = 0

        for e in entries:
            if e.get("status") != "pending":
                remaining_entries.append(e)  # 历史保留
                continue
            if max_per_tick is not None and sent_count >= max_per_tick:
                remaining_entries.append(e)
                continue
            lvl = e.get("level", "medium")
            if zone_check and not _should_flush_entry(lvl, ctx):
                skipped.append(e["id"])
                remaining_entries.append(e)
                continue
            try:
                ok = _send_via_telegram(e["msg"])
                if ok:
                    e["status"] = "sent"
                    e["sent_ts"] = datetime.now().isoformat(timespec="seconds")
                    sent.append(e["id"])
                    sent_count += 1
                else:
                    e["status"] = "failed"
                    failed.append(e["id"])
            except Exception as ex:
                e["status"] = "failed"
                e["error"] = str(ex)
                failed.append(e["id"])
            remaining_entries.append(e)

        _write_queue(remaining_entries)

        return {
            "sent": sent, "failed": failed, "skipped": skipped,
            "remaining": sum(1 for e in remaining_entries if e.get("status") == "pending"),
            "zone": ctx.zone.value, "cap": ctx.urgency_cap,
        }
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fd.close()


# ============================================================================
# 使用示例 — 必须包在 if __name__ 里, 否则 import 时触发
# 详见 proactive-execution 规则18
# ============================================================================
if __name__ == "__main__":
    ctx = get_rhythm()
    print(f"zone={ctx.zone.value}  proactive={ctx.should_proactive}  cap={ctx.urgency_cap}")

    # 1) 四档自测
    print("--- 四档自测 ---")
    for lvl in ["low", "medium", "high", "critical_only"]:
        r = hermes_notify(f"自测 {lvl}", level=lvl)
        print(f"  {lvl:14s} -> {r}")

    # 2) drain (跟随实时节奏)
    print("--- drain_queue (zone_check=True) ---")
    print(drain_queue(zone_check=True))

    # 3) 模拟深夜
    from rhythm import RhythmContext, TimeZone
    fake_night = RhythmContext(
        hour=23, weekday=3, zone=TimeZone.NIGHT, is_weekend=False,
        should_proactive=False, urgency_cap="critical_only",
    )
    queue_message("演示: 深夜 medium 排队", "medium")
    queue_message("演示: 深夜 critical 直发", "critical_only")
    print("--- drain_queue (伪造 NIGHT 节奏) ---")
    print(drain_queue(zone_check=True, ctx=fake_night))
    print("--- drain_queue (zone_check=False 强制全发) ---")
    print(drain_queue(zone_check=False, ctx=fake_night))

    # 4) 别名导入验证
    from hermes_time_rhythm import should_send_message as _ssm  # noqa: F401
    print(f"别名 OK: hermes_time_rhythm.should_send_message = {_ssm}")
