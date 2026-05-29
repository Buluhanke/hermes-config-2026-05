# hermes_desktop_rpa.py osascript 超时问题（2026-06-02）

## 问题描述

`hermes_desktop_rpa.py wininfo` 调用 osascript 获取 Chrome AXUI 窗口信息，在 cron 环境下返回：

```json
{"error": "获取窗口信息失败: TIMEOUT"}
```

## 根因分析

`wininfo` 函数使用 AppleScript `System Events` 架构：
```python
script = '''
tell application "System Events"
    set chromeProc to first process whose name is "Google Chrome"
    ...
end tell
'''
out, err, code = run(["osascript", path], timeout=10)
```

**cron 环境限制**：无活跃桌面 session（no window server accessible），`osascript` 的 AXUI 堆栈无法初始化完整上下文，导致 `tell application "System Events"` 超时。

## 独立验证

```bash
# osascript 直接测试
osascript -e 'tell application "System Events" to get name of every process'
# 在 cron 环境超时 10s，在前台桌面 session 正常
```

## 与 "wininfo not in PATH" 的区别

| 问题 | 根因 | 现象 | 解决 |
|------|------|------|------|
| wininfo 不在 PATH | shell 命令未找到 | `wininfo: command not found` | 改用 `cliclick` 或 `python3 hermes_desktop_rpa.py wininfo` |
| osascript 超时 | cron 无桌面 session | `TIMEOUT`，err contains "execution paused" | 这是**环境限制**，前台 session 外无法解决 |

## 对 auto_execute 的影响

- DRY_RUN 模式：只记录不执行，`wininfo` 命令从未真正调用 → 超时不暴露
- 切换 DRY_RUN=False 时：
  - 若在前台桌面 session 运行：wininfo 正常
  - 若在 cron 环境运行：wininfo 超时导致 auto_execute 失效
- **结论**：auto_execute 的 `DRY_RUN=False` 切换**必须在有活跃桌面 session 的环境**执行，不能依赖 cron 无人值守

## 已知 path 修正（2026-06-02）

`screen_trigger_handler.py` 中引用的路径：
```python
# 旧路径（文档描述）
"~/.hermes/skills/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py"
# 新路径（实际）
"~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py"
```

实际文件存在于 `autonomous-ai-agents/hermes-rpa/scripts/`（非 `skills/` 子目录）。

## 验证方法

```bash
# 检查 hermes_desktop_rpa.py 是否存在（正确路径）
ls ~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py

# 前台测试 wininfo（需有 Chrome 在跑）
python3 ~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py wininfo
# 成功返回窗口信息；cron 环境返回 TIMEOUT
```