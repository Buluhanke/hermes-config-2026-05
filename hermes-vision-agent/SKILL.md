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

---

## (1) 跨窗口感知方案

### 问题

多窗口环境下，目标窗口可能被遮挡、部分不可见、或在多个 Space 之间切换。纯截图只能感知当前屏幕可见区域，无法获取被遮挡窗口的完整状态。

### 感知层次

```
Level 0 — 窗口枚举（零截图开销）
  mcp_cua_list_windows() → 快速判断"1688窗口是否开着"
  用途：判断目标窗口是否存在，避免无效截屏

Level 1 — 单窗口截图
  mcp_cua_screenshot(window_id) → 获取指定窗口 PNG
  用途：已知目标窗口 ID，截取其可见内容

Level 2 — AX 树结构（全窗口信息）
  mcp_cua_get_window_state(pid, window_id)
  → 返回：window bounds、title、z_index、is_on_screen、element tree
  用途：无需截图即可知道窗口里有哪些元素、元素位置、按钮文字

Level 3 — 全屏多窗口拼接（跨屏）
  对每个 on-screen 窗口分别截图，按 bounds 拼接成全景图
  用途：多窗口同时巡查（如值班主任同时看钉钉+1688+Excel）
```

### 窗口感知决策树

```
任务：点"提交订单"按钮
  │
  ├─ 窗口是否开着？→ mcp_cua_list_windows() 过滤 title 包含"1688"
  │     └─ 没开着 → 任务失败，提示"1688窗口未打开"
  │
  ├─ 窗口可见吗？→ is_on_screen=false → 唤醒窗口或切换 Space
  │
  ├─ 窗口是否最小化？→ 在 Dock 中 → mcp_cua_get_window_state 拿到后执行 unhide
  │
  └─ 窗口可见 → 三层感知点击（OCR → VLM → SSIM）
```

### 跨窗口操作原子性

当一个任务涉及多个窗口操作时（如：从钉钉复制订单号 → 切换到 1688 填写 → 提交），必须用**窗口状态快照**保证原子性：

```python
def multi_window_task():
    # 1. 记录所有相关窗口状态
    snapshot = {}
    for name, (pid, window_id) in target_windows.items():
        state = mcp_cua_get_window_state(pid, window_id)
        snapshot[name] = {'state': state, 'z_index': state['z_index']}

    # 2. 执行多窗口操作序列
    ...

    # 3. 验证：每个窗口是否回到预期状态
    for name, expected in snapshot.items():
        current = mcp_cua_get_window_state(*target_windows[name])
        assert current['z_index'] == expected['z_index'], f"{name} 窗口顺序被打乱"
```

### Space 切换检测

macOS 多 Space 环境下，窗口可能在不同 Space：

```bash
# 判断窗口在哪个 Space
mcp_cua_get_window_state(pid, window_id)
→ space_ids: [2, 3]  # 同时属于 Space 2 和 3
→ 当前 active Space: mcp_cua_list_windows()['current_space_id']

# 窗口不在当前 Space：先切换 Space 再操作
# Mission Control API 可用时，用 mouse position 触发 Space 切换
```

---

## (2) 移动端盲区解决方案

### 问题

Hermes 运行在 macOS 桌面端，但业务流程可能涉及手机 App（微信、钉钉、移动端 H5）。纯桌面感知无法覆盖移动端盲区。

### 方案一：AirClass 镜像（推荐）

通过屏幕镜像将手机画面投射到 Mac，再用桌面感知覆盖：

```
iPhone USB 连接 → QuickTime 镜像 或 AirServer → Mac 屏幕出现手机画面窗口
→ mcp_cua_list_windows() 枚举到手机镜像窗口
→ mcp_cua_screenshot(window_id) 截取手机屏幕
→ 三层感知点击（坐标需做映射）
```

**坐标映射**：镜像窗口中手机屏幕通常不是全屏，需要计算缩放比例和偏移。

```python
def map_to_phone_coords(mirror_window_state, phone_screen_size, click_x, click_y):
    """
    mirror_window_state: mcp_cua_get_window_state 返回的 bounds
    phone_screen_size: (width, height) iPhone 分辨率如 (1170, 2532)
    click_x, click_y: 在镜像窗口截图上点击的坐标
    """
    win_w = mirror_window_state['bounds']['width']
    win_h = mirror_window_state['bounds']['height']
    win_x = mirror_window_state['bounds']['x']
    win_y = mirror_window_state['bounds']['y']

    # 计算镜像中手机画面的实际位置（通常有边框）
    scale = min(win_w / phone_screen_size[0], win_h / phone_screen_size[1])
    phone_w = phone_screen_size[0] * scale
    phone_h = phone_screen_size[1] * scale
    phone_x = win_x + (win_w - phone_w) / 2
    phone_y = win_y + (win_h - phone_h) / 2

    # 从镜像坐标映射回手机屏幕坐标
    phone_x = (click_x - phone_x) / scale
    phone_y = (click_y - phone_y) / scale
    return int(phone_x), int(phone_y)
```

### 方案二：ADB 连接（Android 设备）

Android 设备可通过 USB ADB 或无线连接，提供完整屏幕控制能力：

```bash
# 检查 ADB 是否可用
adb devices

# 截图（Android）
adb exec-out screencap -p > /tmp/phone_screen.png

# 点击（Android 坐标）
adb shell input tap 500 1200

# 滑动
adb shell input swipe 500 1200 500 600
```

**Hermes 封装**：

```python
def android_screenshot():
    import subprocess
    result = subprocess.run(
        ['adb', 'exec-out', 'screencap', '-p'],
        capture_output=True
    )
    with open('/tmp/phone_screen.png', 'wb') as f:
        f.write(result.stdout)
    return '/tmp/phone_screen.png'

def android_click(x, y):
    subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])

def android_swipe(x1, y1, x2, y2, duration_ms=300):
    subprocess.run([
        'adb', 'shell', 'input', 'swipe',
        str(x1), str(y1), str(x2), str(y2), str(duration_ms)
    ])
```

### 方案三：WebDriver/Selenium（移动端 H5）

若业务在手机浏览器 H5 页面，可用 Playwright/Selenium 的移动端模拟：

```python
from playwright.sync_api import sync_playwright

def mobile_h5_automation():
    with sync_playwright() as p:
        # iPhone 15 Pro 模拟
        iphone = p.devices['iPhone 15 Pro']
        browser = p.chromium.launch()
        context = browser.new_context(
            **iphone,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) ...'
        )
        page = context.new_page()
        page.goto('https://h5.1688.com')
        # 现在可以用 page.click() 等标准 Web 自动化操作
        # 截图路径 page.screenshot()
```

### 方案四：VNC 远程控制（备用）

对于无法用 ADB 也不方便镜像的设备，可用 VNC 方式：

```
手机安装 VNC Server → Mac VNC Viewer 连接 → 屏幕作为窗口出现在桌面
→ 同样用窗口枚举+截图+坐标映射
```

### 盲区覆盖决策表

| 场景 | 推荐方案 | 覆盖能力 |
|------|---------|---------|
| iPhone 微信聊天 | QuickTime 镜像 + 坐标映射 | 全部（截图+点击+文字识别） |
| Android 钉钉 | ADB | 全部 |
| 移动端 H5 页面 | Playwright 移动模拟 | 全部（Web 自动化） |
| 真机测试（游戏/直播） | AirPlay 镜像 | 截图+点击 |
| 手机不在身边 | 跳过，发通知提醒 | 无（通知用户处理） |

---

## (3) 语义理解 vs 像素识别的权衡

### 两种感知范式对比

| 维度 | 语义理解（VLM） | 像素识别（OCR/SSIM） |
|------|----------------|---------------------|
| **能力** | 理解画面内容、推理关系、多步骤规划 | 定位文字坐标、判断像素变化 |
| **速度** | 1-5s（LLM 推理延迟） | 5-240ms（纯计算） |
| **准确率** | ~61%（smolvlm2 坐标定位） | 接近 100%（文字匹配） |
| **抗干扰** | 弱（截图质量影响大） | 强（像素级比对） |
| **泛化能力** | 强（没见过的新界面也能理解） | 弱（需要文字/像素模板匹配） |
| **Token 消耗** | 有（$0） | 零 |

### 决策框架

```
任务特征 → 选择感知策略

"这张图里有什么？"（问答）
  → VLM 语义理解（唯一选择）

"点搜索按钮"（已知文字）
  → Vision OCR（60ms，精确）

"检查页面是否跳转到商品详情"（状态变化）
  → SSIM（5ms，精确）

"点击红色的那个叉号"（视觉特征描述）
  → VLM 视觉理解（唯一选择）

"滑块拖动到最右边"（连续值操作）
  → VLM 识别缺口位置 + 贝塞尔轨迹执行

"点那个看起来像购物车的图标"（图标语义）
  → VLM 视觉理解（图标没有文字，OCR 无法定位）
```

### 混合策略：VLM 定位 + 像素验证

VLM 的 61% 准确率意味着近 40% 失败。**混合策略**可以把成功率拉到接近 100%：

```python
def hybrid_locate(target_desc, screenshot_path):
    """
    1. VLM 提出候选坐标
    2. 像素识别在候选坐标周围验证文字/图标是否存在
    3. 只有验证通过才执行点击
    """
    candidate = vlm_locate(target_desc, screenshot_path)  # VLM 返回候选 (x, y)

    if candidate is None:
        return None  # VLM 完全没找到

    # 在候选点周围局部截图
    cx, cy = candidate
    region = (cx - 100, cy - 50, 200, 100)  # 截取候选点周围区域
    local_path = screenshot_region(screenshot_path, region)

    # 用 OCR 验证周围是否有目标文字
    ocr_results = fast_ocr_scan(local_path)  # 返回 [(text, x, y), ...]

    for text, ox, oy in ocr_results:
        if target_desc in text:
            # 验证通过，返回校正后坐标（取 OCR 实际文字位置，而非 VLM 候选点）
            return (cx + ox, cy + oy)

    # VLM 候选周围没有目标文字，说明 VLM 猜错了
    # 回退到全局 OCR 扫描（慢但准）
    full_ocr = fast_ocr(target_desc, screenshot_path)
    return full_ocr
```

### 语义理解失败恢复

当 VLM 彻底失败（说"找不到"），不要直接放弃：

```python
FAILURE_RECOVERY = {
    "vlm_not_found": [
        "尝试同义词描述：'发送' → ['发送', '发送按钮', 'Submit', 'Send']",
        "尝试更宽泛描述：'红色的叉' → '关闭按钮'",
        "截图缩小发送给 VLM（减少干扰背景）",
        "用环形缓冲区历史帧分析（目标可能被部分遮挡）",
    ],
    "vlm_wrong_target": [
        "提取 AX 元素列表，让 VLM 从结构化列表中选择而非凭空猜测",
        "缩小候选范围（VLM 在小区域内判断更准）",
        "改用 OCR 精确匹配（如果目标是文字按钮）",
    ]
}
```

### 性能-准确率权衡表

| 策略 | 耗时 | 准确率 | 适用场景 |
|------|------|--------|---------|
| OCR 精确匹配 | 60-240ms | ~100% | 文字按钮、有明确标签 |
| SSIM 精确比对 | 5ms | ~100% | 状态变化检测、验证 |
| VLM 裸用 | 1-5s | ~61% | 图标、无标签按钮、内容理解 |
| CUA AX-tree | 50-100ms | 结构 100%，位置 100% | 原生 macOS 应用 |
| 混合（OCR+SSIM+VLM） | 300ms-3s | 95%+ | 复杂场景、关键操作 |

**原则**：
- **能用结构化 API（AX-tree）解决的问题，不用 VLM**
- **能用文字匹配解决的问题，不用视觉推理**
- **VLM 是最后兜底，不是第一选择**

