# screen_watcher v2 替代 peekaboo（2026-05-25）

## 背景

macOS 26.4 上 cua-driver 的 ScreenCaptureKit 实现出现 SCStreamError -3801 错误，导致 peekaboo 方案（基于 cua-driver）无法正常工作。

## 解决方案

采用 screen_watcher.py v2 — 智能防抖 + hash diffing 方案。

### 核心文件

- 进程脚本：`~/.hermes/scripts/screen_watcher.py`
- 守护脚本：`~/.hermes/scripts/screen_watcher_daemon.sh`
- 日志：`~/.hermes/logs/screen_watcher.log`
- 截图输出：`~/.hermes/screenshots/current.png`

### 关键配置

```python
MIN_CHANGE_INTERVAL = 15      # 最小触发间隔（秒）
RAPID_CHANGE_THRESHOLD = 3     # 快速变化阈值
SCREENSHOT_PATH = ~/.hermes/screenshots/current.png
```

### 工作原理

1. 每 16 秒读取当前屏幕截图
2. 计算图片 hash，与上次比较
3. 若相同且距上次触发 < 15 秒 → 抑制
4. 若快速变化（3次/15秒内）→ 警告日志但不重复触发
5. 显著变化时触发 VLM 分析

### 进程管理

- 守护通过 cronjob `screen_watcher_daemon`（每5分钟）检查进程存活
- 进程名：`HermesScreenWatcher`
- 当前状态：PID 10209，运行中

## peekaboo 废弃原因

- macOS 26.4 上 SCStreamError -3801（Stream could not be started）
- ScreenCaptureKit API 变更，cua-driver 尚未适配
- screen_watcher v2 已接管主要感知工作

## 验证命令

```bash
# 检查进程
ps aux | grep screen_watcher

# 检查日志
tail -f ~/.hermes/logs/screen_watcher.log

# 检查截图是否存在
ls -la ~/.hermes/screenshots/current.png
```
