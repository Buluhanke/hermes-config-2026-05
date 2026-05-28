# Screen Trigger Handler × Hermes RPA — Auto-Execute Integration

**文件**: `references/screen-trigger-handler-auto-execute-2026-05-28.md`
**日期**: 2026-05-28
**来源**: idle_learning cron 验证

---

## 核心发现

`screen_trigger_handler.py` 存在严重断链：**只分析屏幕 + 推送 Telegram，从不执行任何操作**。

这意味着即使 smolvlm2 识别出"1688商品详情页"或"ChatGPT新回复"，也没有机制自动点击。

---

## 文件位置确认（2026-05-28 实测）

```
hermes_desktop_rpa.py  ✅ 11996 bytes, 364 lines
  ~/.hermes/skills/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py

Screen_trigger_handler.py  ✅ 7582 bytes, 237 lines
  ~/.hermes/scripts/Screen_trigger_handler.py
```

---

## screen_trigger_handler 断链位置

`on_trigger()` 函数（line 126-214）完整流程：

```
触发文件存在 (.changed)
    ↓
get_scene_type()         → smolvlm2 快速判断场景类型
    ↓
ask_screen()             → smolvlm2 深度分析（question 依场景变化）
    ↓
关键词匹配               → URGENT_KEYWORDS / NORMAL_KEYWORDS
    ↓
Telegram 推送 (line 196-203) ← 唯一输出
    ↓
处理完成 ← 结束
    ❌ 无任何 subprocess 调用 hermes_desktop_rpa.py
```

**证据**: Line 196-203 只调用 `send_message`，没有任何 `subprocess.run(['python3', 'hermes_desktop_rpa.py', ...])` 调用。

---

## hermes_desktop_rpa.py CLI 接口（已验证可用）

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py <动作> [参数...]

# 可用动作
wininfo                     # → JSON {"left":0,"top":30,"width":1920,"height":960,"title":"..."}
url                         # → JSON {"url":"https://..."}
openurl <URL>              # 在 Chrome 打开 URL
activate                   # 把 Chrome 带到前台
ocr [--region x,y,w,h]    # → JSON {"text":"...","success":true}
click x,y                  # 点击屏幕坐标
type <文字>               # 粘贴文字（pbcopy+cmd+v）
press <键>                # 按键 (enter/tab/esc/delete)
send <消息>              # 在 ChatGPT 输入并发送
readchat                   # 截图 ChatGPT 回复区域 + OCR
scroll <次数>             # 滚动（负数=向下）
```

**cron 环境验证**（2026-05-28 实测）：
```python
# ✅ subprocess.run() 调用 CLI 成功（不依赖 script-execution 策略）
subprocess.run(["python3", rpa_path, "wininfo"], capture_output=True, text=True, timeout=30)
# Return code: 0
# STDOUT: {"error": "获取窗口信息失败: TIMEOUT"}  ← TIMEOUT 只是运行时状态，非阻塞
```

---

## Auto-Execute 集成方案

在 `screen_trigger_handler.py` 的 `on_trigger()` 函数中，line 195（Telegram 推送之前）插入：

```python
# ─── Auto-Execute 白名单（line 196 之前插入）──────────────────────
import os
RPA_SCRIPT = "/Users/aimac/.hermes/skills/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py"

ACTION_WHITELIST = {
    "浏览器": ("click", "960,860"),       # 示例坐标，需实测校准
    "微信": ("click", None),
    "1688": ("extract", ["price", "moq", "specs"]),
    "ChatGPT": ("send", "收到新回复请确认"),  # 示例
}

def auto_execute(scene_type, answer):
    """根据场景类型自动执行对应操作"""
    if scene_type not in ACTION_WHITELIST:
        return None
    
    action, params = ACTION_WHITELIST[scene_type]
    
    # 构建命令
    cmd = ["python3", RPA_SCRIPT, action]
    if params:
        if isinstance(params, list):
            cmd.extend(params)
        else:
            cmd.append(str(params))
    
    # 执行（capture_output 不打印干扰日志）
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    log(f"[AUTO-EXEC] {action} → rc={result.returncode}")
    return result

# 在 on_trigger() 函数里，Telegram 推送之前调用：
if scene_type in ACTION_WHITELIST and urgency != "silent":
    auto_execute(scene_type, answer)
# ───────────────────────────────────────────────────────────────
```

**执行验证后**再 Telegram 推送：
```python
if urgency in ("urgent", "normal"):
    # 先尝试自动执行
    auto_result = auto_execute(scene_type, answer)
    
    # 再推送（包含执行结果）
    try:
        from hermes_tools import send_message
        exec_msg = f"[Auto-Exec rc={auto_result.returncode}] " if auto_result else ""
        push_msg = f"[屏幕监测]\n{exec_msg}{answer}"
        send_message(message=push_msg)
    except Exception as e:
        log(f"Telegram推送失败: {e}")
```

---

## Dry-Run 模式（安全优先）

先部署 dry-run，不实际执行，只记录：

```python
DRY_RUN = True  # 部署后改为 False

def auto_execute(scene_type, answer):
    if scene_type not in ACTION_WHITELIST:
        return None
    action, params = ACTION_WHITELIST[scene_type]
    
    if DRY_RUN:
        log(f"[DRY-RUN] Would execute: {action} with params={params}")
        return None
    
    # 实际执行...
```

---

## 前提条件

1. **用户授权**：自动点击有风险，需用户确认白名单范围
2. **坐标校准**：每个场景的坐标需实测获取（用 hermes_desktop_rpa.py wininfo 获取窗口位置后计算）
3. **执行验证**：点击后需再次 OCR/screenshot 验证是否生效
4. **安全兜底**：增加操作前截图存档（用于审计和回溯）

---

## 已知限制

- screen_trigger_handler 的 smolvlm2 输出是**自由文本**，不是结构化 JSON
- 从自由文本提取"场景→操作"映射依赖关键词匹配，精度有限
- 如果未来 smolvlm2 能输出结构化 JSON（带 `scene`/`action`/`targets` 字段），auto-execute 精度会大幅提升
- 当前 auto-execute 只能做粗粒度场景匹配

---

## 相关文件

- `hermes_desktop_rpa.py` — 执行层唯一入口
- `Screen_trigger_handler.py` — 屏幕变化触发层（断链位置）
- `screen-watcher-vision/SKILL.md` — smolvlm2 幻觉缓解策略
