# Hermes PID 黑名单模式（2026-06-28 落地）

## 背景

memory_watchdog 在 DANGER/CRITICAL 时要杀进程释放内存。**绝不能杀 Hermes 自身**——杀了 watchdog 就停，用户对话也断。

## 为什么不靠 PID 名字匹配

```bash
ps -Aco pid,command | grep "hermes"
# 看起来稳，但：
# 1. 名字变一下（hermes-agent vs hermes-gateway vs gateway）就匹配漏
# 2. 扩展名、参数多了少了都影响匹配
# 3. 多进程场景下不同子进程名字不一样
```

## 黑名单文件模式

**启动 watchdog 时扫描 Hermes 相关进程，写入 `.hermes_pids` 文件**：

```python
from pathlib import Path

HERMES_PIDS_FILE = Path.home() / ".hermes" / ".hermes_pids"

def update_hermes_pids():
    """扫描 Hermes 自身进程 PID，写入黑名单文件。"""
    pids = set()

    # 1. 按进程名匹配（模糊匹配多个可能的名字）
    for name in ["hermes-agent", "hermes-gateway", "gateway"]:
        for pid, _ in find_pids_by_name(name):
            pids.add(pid)

    # 2. 按 venv python 路径匹配（gateway 跑在 venv 里）
    for pid, cmd in find_pids_by_name(".hermes/hermes-agent/venv"):
        pids.add(pid)

    # 3. 按路径包含匹配（hermes-agent 任何子进程）
    for pid, cmd in find_pids_by_name("hermes-agent"):
        pids.add(pid)

    HERMES_PIDS_FILE.write_text("\n".join(str(p) for p in pids))


def is_hermes_pid(pid: int) -> bool:
    """判断 PID 是否是 Hermes 自身。"""
    if HERMES_PIDS_FILE.exists():
        try:
            hermes = set(int(x) for x in HERMES_PIDS_FILE.read_text().split() if x.strip().isdigit())
            return pid in hermes
        except Exception:
            pass
    # 黑名单文件不存在时，宁可放过不错杀
    return False
```

## kill 前的双层保护

```python
def kill_pid(pid, name):
    """杀进程前先确认不是 Hermes。"""
    if is_hermes_pid(pid):
        log(f"  ⚠ 跳过 Hermes 自身: {name} (PID {pid})")
        return False

    # SIGTERM 先
    os.kill(pid, 15)
    time.sleep(2)

    # 没死再 SIGKILL
    try:
        os.kill(pid, 0)  # 测试是否还活着
        os.kill(pid, 9)
    except ProcessLookupError:
        pass  # 已被 SIGTERM 杀掉
```

## 黑名单更新时机

1. **watchdog 启动时** — 第一次扫描
2. **每次 DANGER/CRITICAL 触发保护动作前** — 重新扫描（防止新进程）
3. **不**在每次循环都更新 — 浪费 CPU

```python
def daemon_loop():
    update_hermes_pids()  # 启动时
    last_pids_refresh = time.time()

    while True:
        state = get_memory_state()
        if state["level"] in ("DANGER", "CRITICAL"):
            # 超过 1 小时重新扫一次黑名单
            if time.time() - last_pids_refresh > 3600:
                update_hermes_pids()
                last_pids_refresh = time.time()
            act(state)
        time.sleep(30)
```

## 额外保护：路径前缀匹配

不只是 PID 黑名单，杀任何进程前再查一次路径：

```python
def is_protected_path(pid):
    """检查进程是否运行在受保护路径。"""
    r = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                       capture_output=True, text=True)
    cmd = r.stdout.strip()
    protected_paths = [
        "/.hermes/",        # Hermes 全部家目录
        "/System/",         # 系统核心
        "/usr/libexec/",    # 系统服务
        "/private/var/",    # 系统数据
    ]
    return any(p in cmd for p in protected_paths)

def kill_pid_safe(pid, name):
    if is_hermes_pid(pid) or is_protected_path(pid):
        log(f"  ⚠ 受保护进程，跳过: {name} (PID {pid})")
        return False
    # ... 真杀
```

## 已知 Hermes PID 列表（2026-06-28 实测）

| 进程 | 描述 |
|---|---|
| `~/.hermes/hermes-agent/venv/bin/python` (PID 891) | gateway 主进程 |
| `~/.hermes/hermes-agent/venv/bin/python` (PID 879) | gateway 子进程 |
| `~/.hermes/hermes-agent/venv/bin/python3` (PID 875) | gateway 子进程 |

**注意**: watchdog 自己也是 Python 进程。watchdog 启动后必须把自己也加入黑名单（防止 watchdog 在 CRITICAL 时杀自己）。

```python
import os
HERMES_PIDS_FILE.write_text(str(os.getpid()) + "\n" + ...)
```

## 验证黑名单生效

```bash
# 列出黑名单
cat ~/.hermes/.hermes_pids

# 模拟 DANGER：手动跑一次
python3 ~/.hermes/scripts/memory_watchdog.py --once

# 看日志：每个被跳过的 PID 都该打 "⚠ 跳过 Hermes 自身"
tail -20 ~/.hermes/memory_watchdog.log
```