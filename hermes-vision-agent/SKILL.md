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

## 依赖

- `hermes-humanization-core`（必须先安装）
- smolvlm2-agentic-gui（Ollama，本地视觉模型）
- pyautogui + mss（系统控制）

## 典型用法

```python
from vision_agent import vlm_click, ask_screen, find_element_by_vision

# 1. 直接找按钮并点击（最常用）
vlm_click("加入进货单")

# 2. 问当前屏幕一个问题
answer = ask_screen("这个1688商家评分是多少？")
print(answer)

# 3. 先找坐标，确认后再点
coords = find_element_by_vision("确认付款按钮")
if coords:
    human_click(*coords)
```

## 1688 场景

```python
from vision_agent import search_1688, add_1688_to_cart

search_1688("纸箱 50*40*30")
add_1688_to_cart()
```

## 微信场景

```python
from vision_agent import wechat_send_image

# 发送图片给老板
wechat_send_image("/tmp/报价单.png", contact_name="老板")
```

## 桌面应用

```python
from vision_agent import find_and_open_app

# 打开 Safari
find_and_open_app("Safari")
```

## 已知局限

- smolvlm2 响应约30-60秒，需要耐心等待
- 找元素需要描述尽量具体："发送按钮" 比 "按钮" 效果好
- 文件对话框目前需要手动介入（VLM无法操作 macOS 原生文件选择器）

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

`execute_code` 使用的 venv 没有 pyobjc 模块。运行 Vision OCR 必须用：

```bash
/Users/aimac/.hermes/hermes-agent/venv/bin/python /tmp/your_script.py
```

或在脚本开头加 PATH 修复：

```python
import sys
venv_python = "/Users/aimac/.hermes/hermes-agent/venv/bin/python"
```

---

## 三层感知点击架构（推荐）

```
smart_click("发送")
    │
    ├─ 1. 局部截图 -> Vision OCR (60-240ms)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    ├─ 2. 找不到 -> smolvlm2 视觉 (2-5s)
    │       找到了 -> human_click + SSIM 心跳验证
    │
    └─ 3. VLM 也找不到 -> 打印警告，人工介入
```
> **注意**：smolvlm2（ahmadwaqar/smolvlm2-agentic-gui:latest）是当前主模型，qwen2.5vl:7b 因未安装在 Ollama 中已降为备选。

分层感知原则：能用底层 API 解决的不上高级模型，日常 80% 点击走 OCR 瞬发。定位参考：`hermes-fast-ocr-ssim`
