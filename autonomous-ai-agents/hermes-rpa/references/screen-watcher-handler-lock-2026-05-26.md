# screen_watcher handler 重复 spawn 问题（2026-05-26）

## 问题现象

screen_watcher 检测到屏幕变化后，日志中看到对同一张截图（如"湖景/山脉"等风景图）被多个 handler 并行分析几十次。8 个 handler 进程同时存在。

## 根因

screen_watcher 的 `touch_trigger()` 每次屏幕变化都调用 `subprocess.Popen` 启动新 handler：

```python
def touch_trigger():
    # 每次屏幕变化都会执行这里，没有检查是否已有 handler 在运行
    subprocess.Popen(
        ["python3", "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
```

handler 内部的 cooldown 逻辑是进程级别的，无法跨进程生效。

## 解决方案

在 screen_watcher 添加锁文件机制：

1. **screen_watcher.py** — 启动前检查锁文件，存在则跳过
2. **screen_trigger_handler.py** — finally 块确保运行完删除锁文件（崩溃也删）

### screen_watcher.py 修改

```python
HANDLER_LOCK = os.path.expanduser("~/.hermes/screenshots/.handler_lock")

def touch_trigger():
    # 如果上次 handler 还没运行完，跳过
    if os.path.exists(HANDLER_LOCK):
        log("Handler仍在运行，跳过本次触发")
        return
    ts = time.time()
    with open(TRIGGER_FILE, "w") as f:
        f.write(f"{ts}")
    # 创建锁文件，handler 运行完后删除
    Path(HANDLER_LOCK).touch()
    log(f"TRIGGER FIRED at {ts}")
    try:
        subprocess.Popen(
            ["python3", "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        log(f"Handler调用失败: {e}")
        # spawn 失败也要删锁，否则永远跳过了
        try:
            os.remove(HANDLER_LOCK)
        except:
            pass
```

### screen_trigger_handler.py 修改

```python
if __name__ == "__main__":
    try:
        main()
    finally:
        # 运行完后删除锁文件，让 watcher 可以继续触发
        LOCK = os.path.expanduser("~/.hermes/screenshots/.handler_lock")
        try:
            os.remove(LOCK)
        except:
            pass
```

## 相关文件

- screen_watcher：`~/.hermes/scripts/screen_watcher.py`
- screen_trigger_handler：`~/.hermes/scripts/screen_trigger_handler.py`
- 锁文件：`~/.hermes/screenshots/.handler_lock`