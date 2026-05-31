## subprocess.Popen Python 版本不匹配（2026-06-01 发现并修复）

### 症状
screen_watcher 日志显示大量 `"Handler仍在运行，跳过本次触发"`（483次+），但 `ps aux | grep screen_trigger` 无 handler 进程。handler_lock 文件残留（0字节空文件）。

### 诊断流程
```bash
# 1. 确认 handler lock 残留
ls -la ~/.hermes/screenshots/.handler_lock

# 2. 检查 watcher 启动方式
/bin/bash -lic 'which python3; python3 --version'
# → 通常解析到 /usr/local/bin/python3 (Python 3.14)

# 3. 检查 handler 依赖是否在系统 Python
/usr/local/bin/python3 -c "from ultralytics import YOLO"
# → ModuleNotFoundError: No module named 'ultralytics'

# 4. 确认 venv Python 可用
~/.hermes/hermes-agent/venv/bin/python3 -c "from ultralytics import YOLO; print('OK')"
# → OK
```

### 根因
screen_watcher 通过 `/bin/bash -lic set +m` 启动，`python3` 解析为系统 Python 3.14（`/usr/local/bin/python3`）。但 handler（`screen_trigger_handler.py`）依赖 `ultralytics` 只在 hermes venv（Python 3.11 at `~/.hermes/hermes-agent/venv/bin/python3`）中安装。

watcher 的 `subprocess.Popen(["python3", ...])` 使用 Python 3.14 → handler 因 `ModuleNotFoundError: ultralytics` 立即崩溃 → handler_lock 未被删除 → 所有后续 trigger 被跳过。

### 修复
```python
# screen_watcher.py line 87-90
# ❌ 旧代码（PATH 解析导致 Python 3.14）
subprocess.Popen(
    ["python3", "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

# ✅ 修复后（显式 venv 路径）
subprocess.Popen(
    ["/Users/aimac/.hermes/hermes-agent/venv/bin/python3",
     "/Users/aimac/.hermes/scripts/screen_trigger_handler.py"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
```

### 验证
修复后重启 watcher，首次 auto-trigger 即成功产生 YOLO 输出。

### 预防
任何涉及 `subprocess.Popen(["python3", ...])` 的 daemon，如果由 bash -lic 启动，`python3` 的 PATH 解析不可靠。多 Python 版本环境（venv 3.11 + 系统 3.14）下必须显式使用绝对路径。
