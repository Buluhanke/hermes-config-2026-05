# Conventions — 5 个 Archetype 的代码骨架

## 1. Computed-Context

```python
"""<name>.py — <one-line purpose>"""
import datetime
from dataclasses import dataclass
from enum import Enum


class <Zone>Enum(Enum):
    A = "a"
    B = "b"


@dataclass
class <Context>:
    field: type


def get_<context>() -> <Context>:
    now = datetime.datetime.now()
    # pure logic from now()
    return <Context>(...)


if __name__ == "__main__":
    ctx = get_<context>()
    print(ctx)
```

**验证**：`python3 -c "from <name> import get_<context>; print(get_<context>())"`，无副作用。

## 2. Mutable-State

```python
"""<name>.py — <one-line purpose>"""
import json
from dataclasses import asdict, dataclass
from pathlib import Path

STATE_FILE = Path("~/.hermes/<name>.json").expanduser()


@dataclass
class <State>:
    field: type = default


def load_state() -> <State>:
    if STATE_FILE.exists():
        try:
            return <State>(**json.loads(STATE_FILE.read_text()))
        except (json.JSONDecodeError, TypeError):
            pass
    return <State>()  # default


def save_state(state: <State>) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))
    tmp.replace(STATE_FILE)  # 原子写


# --- 业务函数 ---

def update_x(value, ...) -> None:
    state = load_state()
    state.field = value
    save_state(state)


def get_<hint>() -> str:
    """生成可注入 LLM 的 context 字符串。"""
    state = load_state()
    parts = []
    if state.something:
        parts.append(...)
    return "\n".join(parts) if parts else "<fallback>"


if __name__ == "__main__":
    update_x(...)
    print(get_<hint>())
```

**验证协议**（详细见 `hermes-internalization-stack` SKILL.md §C）：
1. `python3 <name>.py` → exit 0
2. `cat <state_file>` → 持久化
3. `python3 -c "import <name>"` → 静默
4. e2e：reset → 多步 → reload → 断言

## 3. Queue (核心 arch — 见 hermes-rhythm-gate 详细)

```python
import fcntl, json, os, tempfile
from datetime import datetime
from pathlib import Path

QUEUE_DIR = Path("~/.hermes/queue")
QUEUE_FILE = QUEUE_DIR / "<name>.jsonl"


def enqueue(msg: str, level: str) -> str:
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


def drain(zone_check=True, ctx=None) -> dict:
    if ctx is None:
        ctx = get_rhythm()  # from rhythm.py
    lock = QUEUE_DIR / ".drain.lock"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    fd = open(lock, "w")
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"note": "another drain in progress"}
        # ... read entries, process, atomic write ...
        return {"sent": [], "failed": [], "skipped": [], "remaining": 0}
    finally:
        try: fcntl.flock(fd, fcntl.LOCK_UN)
        except: pass
        fd.close()
```

**关键**：fcntl flock (LOCK_NB) + tempfile+os.replace + ctx 注入 (测试) + max_per_tick (限速)

## 4. Constants-Only

```python
<NAME>_CORE = """
<your core prompt here>
"""


def build_<output>(context: str = "", hint: str = "") -> str:
    parts = [<NAME>_CORE.strip()]
    if hint:
        parts.append(f"\n【状态】\n{hint}")
    if context:
        parts.append(f"\n【任务】\n{context}")
    return "\n".join(parts)


if __name__ == "__main__":
    print(build_<output>("sample task", "sample hint")[:200], "...")
```

**验证**：调 `build_*`，assert `len(result)` 在合理范围 (400-600 chars 典型)。

## 5. Shell-Watchdog

```bash
#!/bin/bash
# silent-on-empty: empty stdout = 静默退出 (cron deliver=local 不打扰)
set -euo pipefail
VENV_PY="${HERMES_PY:-python3}"

OUT=$("$VENV_PY" - <<'PYEOF' 2>&1
import json, sys
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
# ... your drain call ...
if <nothing to report>:
    sys.exit(0)
print(json.dumps({...}))
PYEOF
)

RC=$?
[ $RC -ne 0 ] && { echo "FAILED rc=$RC"; echo "$OUT"; exit 1; }
[ -z "$OUT" ] && exit 0
echo "tick: $OUT"
```

**重要约束**：`hermes cronjob create` 的 `--script` 字段必须是 basename（不能带 `/Users/...`），相对 `~/.hermes/scripts/`。

## 跨 archetype 通用：别名 import (用户原版代码常用)

```python
import sys, importlib
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

_module = None
for _name in ("<real_name>", "hermes_<real_name>"):
    try:
        _module = importlib.import_module(_name); break
    except ImportError: continue
if _module is not None:
    sys.modules.setdefault("hermes_<real_name>", _module)
```

LSP 报 `reportMissingImports` 是误报，runtime OK。
