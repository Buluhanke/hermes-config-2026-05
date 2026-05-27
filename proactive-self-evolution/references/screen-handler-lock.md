# Screen Handler 防重复进程 — 参考

## 问题
每次 screen_watcher 检测到屏幕变化，都用 `subprocess.Popen` 启动新的 `screen_trigger_handler.py`，造成多个 handler 进程同时运行（实测出现 8 个）。

handler 内部虽有 cooldown 逻辑（60 秒同场景不重复分析），但该逻辑依赖状态文件，无法阻止并行启动的多个进程都进入分析流程。

## 根因
watcher 侧没有任何" handler 是否正在运行"的感知，纯靠 handler 内部 cooldown 是事后补救，不是事前阻止。

## 解决方案：锁文件机制

### watcher 侧 (`screen_watcher.py`)
```python
HANDLER_LOCK = os.path.expanduser("~/.hermes/screenshots/.handler_lock")

def touch_trigger():
    # 如果上次 handler 还没运行完，跳过
    if os.path.exists(HANDLER_LOCK):
        log("Handler仍在运行，跳过本次触发")
        return
    # 创建锁文件
    Path(HANDLER_LOCK).touch()
    # 启动 handler ...
```

### handler 侧 (`screen_trigger_handler.py`)
```python
if __name__ == "__main__":
    try:
        main()
    finally:
        # 运行完删除锁文件，即使崩溃也删
        LOCK = os.path.expanduser("~/.hermes/screenshots/.handler_lock")
        try:
            os.remove(LOCK)
        except:
            pass
```

### 注意
- handler 分析一张图约 8-10 秒，期间屏幕连续变化会全部被跳过而非排队
- 如需队列+单 worker 架构再改进，当前方案对大部分场景够用
- 锁文件路径需与 watcher 侧常量一致