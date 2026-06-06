---
name: hermes-internalization-stack
description: |
  Hermes 内部人化/状态基础设施栈 — ~/.hermes/scripts/ 下的小型 Python 模块,
  把"人化"的几个支柱(节奏 / 关系 / 人格 / 盲区 / 通知队列)变成可 import 的代码。
  Use when: 在 ~/.hermes/scripts/ 下新建或修改小型持久化模块、需要把 rhythm/relationship/
  persona/blind_spots 组合成一个 system prompt 上下文、需要把 hermes_notify 队列接到
  telegram/feishu/discord 任一平台、需要给 hermes 增加一个"记忆/认知/上下文"型小工具。
  Don't use for: 改 hermes 源码(用 hermes-internal-architecture-patterns)、
  写 cron 任务(用 hermes-rhythm-gate 或 proactive-execution)、
  商业数据持久化(用 hermes-memory-hpc)。
---

# Hermes Internalization Stack

User memory 的"13 条核心能力体系"在 `hermes-evolution-context` 里有元描述。这个 skill 描述**这些能力的物质化层**——`~/.hermes/scripts/` 下的小型 Python 模块。每个模块都很小(<300 行)，遵循同一组约定。

## The stack (current modules)

| 模块 | 类型 | 状态文件 | 角色 | 在 13 条能力里的位置 |
|------|------|----------|------|---------------------|
| `rhythm.py` | computed | — | 时段/节奏判断 | #12 主动执行(时段门控) |
| `hermes_notify.py` | queue | `~/.hermes/queue/messages.jsonl` | 通知门控 + 队列 + drain | #12 主动执行 + #11 自我修复 |
| `drain_watchdog.sh` | shell | — | cron 调用 drain_queue | #11 自我修复(资源巡逻) |
| `relationship.py` | state | `~/.hermes/relationship.json` | mood/followup/sensitive | #3 记忆系统(关系层) |
| `persona.py` | constants | — | 人格核心 + system prompt 构造器 | #1 浏览器控制(人设一致性) + #5 屏幕识别 |
| `blind_spots.py` | state | `~/.hermes/blind_spots.json` | 知识盲区 + 置信度 | #9 自我学习进化 |

**截至 2026-06-04** — 后续每加一个新模块，请更新本表 + `references/module-catalog.md`。

## Module archetypes (pick one when adding a new module)

### 1. Computed-Context (无持久化)
- 入口：纯函数 + `dataclass` 返回
- 文件：无
- 验证：直接调函数，断言边界
- 例子：`rhythm.py` — `get_rhythm() -> RhythmContext`

### 2. Mutable-State (有 JSON 持久化)
- 入口：`@dataclass State` + `load_state(default) -> State` + `save_state(state)`
- 文件：`~/.hermes/<name>.json`
- 操作函数：`update_x()` / `add_y()` / `mark_done()` 等动词
- 验证：reset → 操作 → reload → 断言
- 例子：`relationship.py`、`blind_spots.py`

### 3. Queue (有 JSONL 持久化 + drain)
- 入口：`enqueue(msg, level) -> id` + `drain(...) -> {sent,failed,skipped,remaining}`
- 文件：`~/.hermes/queue/<name>.jsonl`
- 关键设计：fcntl flock + tempfile+os.replace 原子写
- 例子：`hermes_notify.py` (见 `hermes-rhythm-gate` skill 详细)

### 4. Constants-Only (只读常量 + builder)
- 入口：模块级字符串常量 + `build_*(...)` 函数
- 文件：无
- 例子：`persona.py` — `PERSONA_CORE` + `build_system_prompt(task, hint)`

### 5. Shell-Watchdog (cron 包装)
- 入口：bash 脚本
- 关键模式：silent-on-empty stdout + exit 0
- 文件：无
- 例子：`drain_watchdog.sh`

## 强制约定 (apply to ALL new modules)

### A. `if __name__ == "__main__":` 守卫
**踩过的坑 (2026-06-04)**：在 `rhythm.py` 末尾加 demo 没包进守卫，import 触发副作用。
- 任何 demo / quick test / 注释里的"运行"代码 → 必须守卫
- 见 `hermes-rhythm-gate` pitfall #8 和 `references/real-failure-top-level-print.md`

### B. 别名 import (兼容性)
User 原版示例常用 `hermes_<name>` 别名（如 `from hermes_relationship import get_greeting_context`）。模块顶加：

```python
import sys
from pathlib import Path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
_module = None
for _name in ("<name>", "hermes_<name>"):
    try:
        _module = importlib.import_module(_name); break
    except ImportError: continue
if _module is not None:
    sys.modules.setdefault("hermes_<name>", _module)
```

LSP 会报 `reportMissingImports`，runtime OK，**可忽略**。

### C. 验证协议 (落地必跑)
1. `python3 <module>.py` → exit 0
2. `cat <state_file>` → 持久化正确
3. `python3 -c "import <module>; print('clean')"` → **不**打印 demo
4. e2e：reset → 多步操作 → reload → 断言
5. 跑完后告诉 user 测试是否污染了真实 state file(让他们决定是否回滚)

### D. 不主动改用户原版
User 用"复制"模式时，原版就是 given 表面。**没要求就不加**加固 (lock/atomic/清理/多 user)——除非 user 明确说"加固"。见 `hermes-evolution-context` 新增的"用户代码落地工作流"段。

## 何时建 `hermes_init.py` (facade)

当 ≥3 个模块被同时 import 时，建顶层 facade：

```python
# ~/.hermes/scripts/hermes_init.py
from rhythm import get_rhythm, should_send_message
from hermes_relationship import get_greeting_context
from persona import build_system_prompt
from blind_spots import should_verify_before_answer, record_blind_spot, mark_verified
from hermes_notify import hermes_notify, drain_queue, queue_message
```

**触发条件**：开始组合多个模块构造 LLM 调用上下文（典型 = `build_system_prompt(task, get_greeting_context(), blind_spots.get_blind_spots_summary())`）。在 cron 或 simple 调用场景下**不需要** facade。

## Pitfalls (stack-wide)

1. **Top-level side effects** — 详见 A
2. **rm/format 需授权** — 测试 reset 也算破坏性操作。Test pollution 需 user 决定回滚，不要自作主张
3. **LSP 误报** — 详见 B
4. **状态文件互相污染** — 多个 module 共享 `~/.hermes/` 目录，e2e 时注意文件命名不要撞
5. **多 user_id** — 暂未实现。当前默认 `"default"`。需要时改 relationship.py 即可，参考 `MEMORY_FILE` 已有结构

## Files in this skill

- `references/module-catalog.md` — 当前所有模块的索引（路径/类型/角色/数据流）
- `references/conventions.md` — 上面 5 个 archetype 的代码骨架
- `templates/state-module.py` — Mutable-State archetype 模板
- `templates/queue-module.py` — Queue archetype 模板
- `templates/cron-watchdog.sh` — silent-on-empty watchdog 模板
- `scripts/verify_all_modules.sh` — 一次性跑所有模块 `__main__` 块

## Related skills

- `hermes-rhythm-gate` — `hermes_notify.py` + `drain_watchdog.sh` 背后的详细原理
- `hermes-evolution-context` — "13 条核心能力体系"元描述 + 用户代码落地工作流
- `hermes-humanization-core` — Phase 1+2（动作拟真 / 视觉感知）；本 stack 是它的物质化
- `hermes-memory-hpc` — 商业数据归 user，技术数据归 hermes；本 stack 的 relationship.py / blind_spots.py **不是**商业数据，是 hermes 内部"自我认知"
- `proactive-execution` — "推荐清单=执行令"在本 stack 上的体现是每个新模块落地后给 user 提 2-3 个加固方向
