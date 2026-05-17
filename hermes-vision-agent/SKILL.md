---
name: hermes-vision-agent
description: "Phase 2 核心：视觉全域感知，看见桌面、控制一切软件。"
---

# hermes-vision-agent

**Phase 2 核心**：视觉全域感知，看见桌面、控制一切软件。

## 核心能力

```
See(截屏) -> Think(VLM分析) -> Act(拟真点击)
```

**当前可用工具（非 vision_agent 模块）：**
- 截屏：`mcp_cua_screenshot`, `peekaboo` CLI, `terminal` → `screencapture`
- 窗口枚举：`mcp_cua_list_windows`, `mcp_cua_get_window_state`
- VLM 分析：`screen_vision`（本地 smolvlm2）, `vision_analyze`（需外部模型）
- 视觉心跳：`execute_code` → 自己实现 SSIM（见 SSIM 章节）
- 通知检查：`osascript`（见通知检查章节）

**不再可用（模块未安装）：**
- ❌ `from vision_agent import vlm_click, ask_screen, find_element_by_vision`
- ❌ `from vision_agent import search_1688, add_1688_to_cart`
- ❌ `from vision_agent import wechat_send_image`
- ❌ `from vision_agent import find_and_open_app`

## smolvlm2 致命陷阱：必须用 /api/chat 接口

smolvlm2 在 `/api/chat` 接口下才能输出 click 坐标，在 `/api/generate` 接口下**永远只输出 scroll**。

**原因**：smolvlm2 是用 message-format 数据微调的，只有 chat 格式才触发 action 输出。

**错误用法（无效）**：
```bash
curl http://localhost:11434/api/generate -d '{"model":"smolvlm2","images":["$B64"],"prompt":"..."}'
# 永远只返回 scroll，不返回 click 坐标
```

**正确用法**：
```bash
curl http://localhost:11434/api/chat -d '{"model":"smolvlm2","messages":[{"role":"user","content":"...","images":["$B64"]}]}'
# 返回格式: </code>\n<code>\nclick(x=0.493, y=0.967)\n</code>
```

**坐标解析**（smolvlm2 输出混合格式，需4路径解析）：
```python
import re

def parse_smolVLM_coords(text: str):
    # 路径1: click(x,y) 裸格式
    m = re.search(r'click\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    # 路径2: <code>click(x=0.493, y=0.967)</code>
    m = re.search(r'<code>\s*click\(\s*x\s*=\s*([\d.]+)\s*,\s*y\s*=\s*([\d.]+)\s*\)\s*</code>', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    # 路径3: x= y= 格式
    m = re.search(r'x\s*=\s*([\d.]+)\s*,\s*y\s*=\s*([\d.]+)', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    # 路径4: JSON 数组
    m = re.search(r'\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]', text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None
```

**其他模型（llava、qwen2.5）继续用 `/api/generate`**，只有 smolvlm2 特殊。

---

## 纯 VLM 视觉定位准确率上限：61%

smolvlm2 屏幕定位准确率约 61%，意味着 **39% 的点击会猜错位置**。对于 1688 采购自动化，这个失败率不可接受。

**正确路线：CUA/AX-tree 做主感知（结构100%准确）+ VLM 做视觉推理**

三层感知架构：
```
smart_click("发送")
    │
    ├─ 1. 局部截图 -> Vision OCR (60-240ms)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    ├─ 2. 找不到 -> Qwen2.5-VL 视觉 (1-2s)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    └─ 3. VLM 也找不到 -> 打印警告，人工介入
```

**反馈循环**（关键！点击后必须验证）：
```python
# 点击 -> 截图 -> SSIM 对比
# SSIM > 0.98 → 失败，提取CUA元素表 -> VLM重新定位候选池 -> 重试
# SSIM < 0.92 → 成功
# 0.92-0.98 → 不确定，人工介入
```

---

## 已知局限

- `vision_agent` Python module **不存在** — 不要用 `from vision_agent import ...`。当前可用的截屏/感知工具见下方"桌面感知工具链"。
- qwen2.5vl:7b 响应约 1-2s（比 smolvlm2 快且准，6GB，M4 24GB 实测可用）
- smolvlm2 约 2-5s（1.8B 太小，准确度一般，可作备用）
- 找元素需要描述尽量具体："发送按钮" 比 "按钮" 效果好
- 文件对话框目前需要手动介入（VLM无法操作 macOS 原生文件选择器）
- mss.mss() 已废弃，新版用 mss.MSS()

---

## 桌面感知工具链

### 截屏（CUA 驱动，稳定）

```bash
# peekaboo CLI 在 cron 环境中可能失效，改用 mcp_cua_screenshot
mcp_cua_screenshot(window_id=N)  # → 返回截图路径
mcp_cua_list_windows()           # → 获取所有窗口及 window_id
mcp_cua_get_window_state(pid, window_id)  # → AX 树 + 截图
```

**典型流程（桌面巡查/值班主任）：**
1. `mcp_cua_list_windows()` — 枚举所有窗口，过滤 `is_on_screen=true`
2. 对每个 on-screen 窗口调用 `mcp_cua_screenshot(window_id)` — 获取截图
3. 用 `vision_analyze` 或 `screen_vision` 分析截图内容
4. 若只需要检查"有没有弹窗/通知"，可跳过截图，直接用 AppleScript（更快）

### 通知检查（AppleScript，无依赖）

```bash
# 1. 检查运行中的通讯应用（QQ/微信/钉钉/飞书）
osascript -e 'tell application "System Events" to name of every process' \
  | tr ',' '\n' | grep -iE "qq|wechat|微信|dingtalk|钉钉|feishu|旺旺"

# 2. 检查通知中心是否有内容
osascript -e '
tell application "System Events"
    try
        tell process "NotificationCenter"
            if exists (every row of list 1 of window 1) then
                return "Notifications present"
            end if
        end tell
    end try
    return "No notifications found"
end tell
'
```

### Vision 分析（需 VLM）

```bash
# 本地 Ollama（推荐 qwen2.5vl）
curl http://localhost:11434/api/chat -d '{"model":"qwen2.5vl",...}'

# Apple Vision OCR（仅文字，无坐标）
/Users/aimac/.hermes/hermes-agent/venv/bin/python -c "
import Vision, Quartz, Cocoa
# 见下方快眼 OCR 章节
"
```

**注意：** `vision_analyze` 从 `hermes_tools` 不可用。若需 VLM 分析，用 `screen_vision` 工具（本地 smolvlm2）或 `execute_code` 中调用 Ollama API。

---

## 快眼 OCR（Apple Vision，原生极速）

三层感知的第一层：文字按钮用 Vision OCR 定位，60-240ms，零 GPU 消耗，比 VLM 快 4-5 倍。

### 安装依赖

```bash
~/.hermes/hermes-agent/venv/bin/pip install pyobjc-framework-Vision pyobjc-framework-Quartz
```

### 性能基准（M4 24GB，实测）

| 操作 | 耗时 | 备注 |
|------|------|------|
| CGWindowListCreateImage 全屏截图 | 87ms | 截图不含 OCR |
| Vision OCR 全屏（Fast级别） | 233ms | 68-92个文本块 |
| Vision OCR 局部（1/6屏） | 60ms | 已知目标区域时用 region 参数，3-4x 加速 |
| SSIM 对比（1920×1080） | 5ms | 极低开销 |

### 坐标转换关键坑

Vision 返回归一化坐标，原点在**左下角**。需转换：

```python
cx = (bbox.origin.x + bbox.size.width / 2) * screen_width
cy = (1 - bbox.origin.y - bbox.size.height / 2) * screen_height
```

### 已知局限

- 终端/TUI 渲染内容识别率低（字符集不标准）
- 对 1688/微信等高对比度网页效果显著更好
- OCR 找不到时自动 fallback 到 VLM

---

## 视觉心跳（SSIM 点击验证）

三层感知的验证层：点击前后截图跑 SSIM，5ms 判断是否真正跳转。

### SSIM 阈值（实测）

| SSIM 值 | 判定 | 含义 |
|---------|------|------|
| > 0.98 | `failed` | 画面几乎无变化，点击可能失效 |
| < 0.92 | `success` | 显著跳转，页面切换成功 |
| 0.92-0.98 | `uncertain` | 轻微变化，可能是弹窗或局部刷新 |

### 区分度验证

- 完全相同图：1.000
- 随机噪声图：0.007
- 1%像素变化：0.990

### 效果

把 VLM 从"确认点击结果"苦力中解放，用像素级对比做瞬断，零 Token 消耗。

### execute_code 沙箱注意

`execute_code` 使用的 venv **没有 pyobjc 模块**。运行 Vision OCR 必须用：

```bash
/Users/aimac/.hermes/hermes-agent/venv/bin/python /tmp/your_script.py
```

正确的 import 写法（objc module 需要分离导入）：

```python
# ❌ 错误 — import 语句中不能有空格分隔的模块名链
# import Vision, Quartz, Cocoa   # 语法错误

# ✅ 正确 — 每行一个独立 import
import Vision
import Quartz
import Cocoa

img = Cocoa.NSImage(contentsOfFile="/path/to/screenshot.png")
```
```

---

## 三层感知点击架构（推荐）

```
smart_click("发送")
    │
    ├─ 1. 局部截图 -> Vision OCR (60-240ms)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    ├─ 2. 找不到 -> Qwen2.5-VL 视觉 (1-2s)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    └─ 3. VLM 也找不到 -> 打印警告，人工介入
```

分层感知原则：能用底层 API 解决的不上高级模型，日常 80% 点击走 OCR 瞬发。定位参考：`hermes-fast-ocr-ssim`

## 实现参考

详细的落地数据、代码示例、卡点记录见：
- `../hermes-vision-connect/references/ollama-models-status.md` — Ollama 模型状态实测
- `../hermes-vision-connect/SKILL.md` — vision-connect 完整实现

## 新增感知模块（2026-05-17）

### 视觉环形缓冲区 `visual_buffer.py`

位于 `hermes-humanization-core/visual_buffer.py`。后台每 2 秒截一帧，保留最近 5 帧。

```python
from visual_buffer import get_buffer
buffer = get_buffer()           # 启动后台截屏
paths = buffer.get_frame_paths()  # ['/tmp/hermes_rb/frame_0001.png', ...]
```

使用场景：操作失败时，把最近 5 帧串联发给 VLM 分析"刚才发生了什么"。

### 滑动验证码闭环 `slider_captcha.py`

位于 `hermes-humanization-core/slider_captcha.py`。

```python
from slider_captcha import auto_solve_if_present
ok = auto_solve_if_present()  # 自动检测+解题，返回False表示无验证码
```

流程：VLM 识别缺口 → 贝塞尔轨迹拖动 → 截图验证结果。
