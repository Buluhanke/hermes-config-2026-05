"""<name>.py — <one-line purpose> (Mutable-State archetype template)

Copy this file to ~/.hermes/scripts/<name>.py and fill in the <> sections.
Then add the state file path to references/module-catalog.md.

Conventions enforced (see hermes-internalization-stack SKILL.md §A-D):
  A. `if __name__ == "__main__":` guard
  B. Alias import (real_name / hermes_<real_name>)
  C. Verify with: exec -> cat state_file -> import silent -> e2e reset
  D. Don't add hardening (lock/atomic/cleanup) unless user asks
"""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# --- 别名 import (convention B) ---
import sys
import importlib
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# --- 状态文件 (convention C) ---
STATE_FILE = Path("~/.hermes/<name>.json").expanduser()


# --- State dataclass ---
@dataclass
class <State>:
    """<one-line state description>"""
    field_a: str = ""
    field_b: list = field(default_factory=list)
    field_c: int = 0


# --- Persistence (load/save) ---
def load_state() -> <State>:
    if STATE_FILE.exists():
        try:
            return <State>(**json.loads(STATE_FILE.read_text()))
        except (json.JSONDecodeError, TypeError):
            pass  # 坏文件回退到 default
    return <State>()


def save_state(state: <State>) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 原子写 (简单版——user 没要求 lock/atomic 时用这个)
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))
    tmp.replace(STATE_FILE)


# --- 业务函数 (verb-named) ---

def update_<x>(value: ..., ...) -> None:
    """<one-line purpose>"""
    state = load_state()
    state.field_a = value
    save_state(state)


def get_<hint>() -> str:
    """生成可注入 LLM 的 context 字符串。"""
    state = load_state()
    parts = []
    if state.field_a:
        parts.append(f"<context about field_a: {state.field_a}>")
    if state.field_b:
        parts.append(f"<context about field_b: {', '.join(state.field_b[:3])}>")
    return "\n".join(parts) if parts else "<fallback when no state>"


# --- demo (convention A: 必须守卫) ---
if __name__ == "__main__":
    update_<x>("sample_value")
    print(get_<hint>())
