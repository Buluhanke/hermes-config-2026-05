---
name: hermes-ocr
description: 统一OCR引擎层 — 自动检测可用引擎，智能降级。Vision OCR(60ms) → PaddleOCR(高精度中文) → Baidu OCR(云端) → ddddocr(验证码) → pymupdf(PDF)
tags: [OCR, Vision, PaddleOCR, BaiduOCR, ddddocr, pymupdf, PDF]
---

# Hermes OCR — 统一OCR引擎

## 能力概述

**一句话**：截图/图片进来，文字出去。自动选最快最好的引擎。

## 引擎优先级（自动降级）：**
1. `Vision OCR` — macOS原生，屏幕截图首选（**实测 1.1s/帧，不是 60ms**；首次调用需 41s 编译 Swift 二进制，后续命中缓存。详见下方"⚠️ 60ms 神话"章节）
2. `PaddleOCR` — 高精度中文，图片/文档
3. `Baidu OCR` — 云端备份
4. `ddddocr` — 验证码通杀
5. `pymupdf` — PDF文字提取（文本型PDF，非扫描件）

## ⚠️ "60ms" 神话 — 2026-06-04 实测校正

老文档/早期博客说 macOS Vision OCR 是 60ms。**端到端实测 1.1 秒**，不是 60ms：
- 60ms 大概是 Vision 框架内部 inference 时间（纯 CPU 计算部分）
- 端到端 = 1.3MB PNG 加载 + 图像预处理 + Vision 调用 + JSON 解析 ≈ 1100ms
- 首次 cold start：swiftc 编译 Swift 源码 ~41s（一次性，缓存在 `~/.hermes/scripts/.cache/vision_ocr_bin`）
- 二次及之后：~1.1s

**正确预期**：用 vision_ocr.py 跑一张 1080p 截图，正常 1-2 秒出来。如果配了 `--json` 含坐标也是 1-2 秒，**不要相信 "60ms" 这种早期 benchmark 数字**。

实测 129 行中英混排终端截图：1117ms，识别完全准确（含 Swift 关键字、中文标点）。

## 使用方式

### 方法A：execute_code 调用（推荐）

```python
from hermes_tools import terminal
import json

# 读一张图片
result = terminal('source ~/.hermes/hermes-agent/venv/bin/activate && python3 /Users/aimac/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read /tmp/test.png --json')
data = json.loads(result['output'])
print(data['text'])  # 识别的文字
print(data['engine'])  # 用的是哪个引擎
```

### 方法B：终端直接调用

```bash
# 读屏幕截图
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py screenshot --region "0,0,800,200"

# 读本地图片文件
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read /tmp/test.png

# PDF提取文字
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py pdf /tmp/doc.pdf
```

## 引擎自动检测逻辑

```python
# ocr.py 内部
engines = {}
if check_vision():       engines['vision'] = True    # macOS Vision.framework
if check_paddleocr():    engines['paddleocr'] = True  # hermes-agent venv
if check_baidu():        engines['baidu'] = True      # .env有key
if check_ddddocr():      engines['ddddocr'] = True    # Homebrew Python
if check_pymupdf():      engines['pymupdf'] = True    # 双方皆有
```

- **screenshot场景**：Vision OCR（60ms）→ PaddleOCR（1-2s）→ Baidu OCR
- **普通图片**：PaddleOCR（最准中文）→ Vision OCR（英文）→ ddddocr
- **PDF**：pymupdf直接提取（文本型）→ 转图片+Vision OCR（扫描件）
- **验证码**：ddddocr

## 安装依赖

### 引擎环境分布

| 引擎 | 位置 | Python路径 | 安装命令 |
|------|------|-----------|---------|
| Vision OCR | macOS内置 | `/opt/homebrew/bin/python3` | 无需安装 |
| PaddleOCR | hermes-agent venv | `~/.hermes/hermes-agent/venv/bin/python3` | `uv pip install paddleocr --python <path>` |
| ddddocr | Homebrew Python | `/opt/homebrew/bin/python3` | `/opt/homebrew/bin/python3 -m pip install ddddocr` |
| pymupdf | hermes-agent venv | `~/.hermes/hermes-agent/venv/bin/python3` | `uv pip install pymupdf --python <path>` |
| Baidu OCR | 云端API | .env配置 | 已配AppID 7699346 |

### 验证命令

```bash
# 一键检测全部引擎
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py detect

# 或逐个验
/opt/homebrew/bin/python3 -c "from Vision import VNRecognizeTextRequest; print('Vision: OK')"
~/.hermes/hermes-agent/venv/bin/python3 -c "from paddleocr import PaddleOCR; print('PaddleOCR: OK')"
/opt/homebrew/bin/python3 -c "import ddddocr; print('ddddocr: OK')"
~/.hermes/hermes-agent/venv/bin/python3 -c "import fitz; print(f'pymupdf: {fitz.version}')"
```

### ⚠️ 恢复指南

PaddleOCR和pymupdf装在hermes-agent venv里，如果清理/重建venv会丢失。恢复命令：

```bash
# PaddleOCR（~300MB依赖，需等几分钟）
uv pip install paddleocr --python ~/.hermes/hermes-agent/venv/bin/python3

# pymupdf
uv pip install pymupdf --python ~/.hermes/hermes-agent/venv/bin/python3
```

**注意**：系统pip受PEP 668保护，不能用普通`pip install`。一律用 `uv pip install --system` 或 `uv pip install --python <venv_path>`。Vision OCR只能走Homebrew Python（有pyobjc）。

## 补充工具层（2026-06 实测新增）

以下工具与 Hermes OCR 引擎互补，按需调用：

| 工具 | 场景 | 内存 | 安装 |
|------|------|------|------|
| **uitag** | 文字+图标双检测，YOLO加持 90.8% 准确率 | 低 | `pip install "uitag[yolo]"` |
| **EasyScreenOCR** | 日常快捷键截图，菜单栏常驻 | 低 | App Store / 官网 |
| **DeepSeek-OCR** | 复杂文档/表格/公式，MPS 加速 | 高 | 本地 Web 服务 |

```bash
# uitag 示例（文字+图标双识别）
uitag screenshot.png --yolo -o ./output

# DeepSeek-OCR 启动
git clone https://github.com/xiumaoprompt/DeepSeek-OCR_macOS.git
cd DeepSeek-OCR_macOS && python setup.py
python -m macos_workflow.app
# 访问 http://127.0.0.1:7860
```

## 快速找字（屏幕坐标）

新增 `find` 子命令，毫秒级定位文字 + 返回屏幕坐标：

```bash
# 找"发送"按钮坐标
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py find "发送"

# 输出示例
[Fast OCR] 找到 '发送' 含 '发送', 耗时: 473ms, 坐标: (1385, 70)
{"text": "发送", "x": 1385, "y": 70, "ms": 473.0}
```

**核心用法**：找字 → 拿坐标 → pyautogui/human_click 模拟真人点击。

**内部逻辑**：
1. `screencapture -x` 截全屏（绕过Chrome GPU合成层黑屏问题）
2. Vision VNRecognizeTextRequest, recognitionLevel=1(Fast), 中文优先
3. 坐标转换：Vision归一化左下角原点 → Mac屏幕像素左上角原点

**注意**：CGWindowListCreateImage 会被Chrome GPU合成层黑屏，必须用 `screencapture -x`。

## macOS Vision OCR 桥（2026-06-04 新增）

`scripts/ocr.py` 用 Homebrew Python（pyobjc）调 Vision，**仅 macOS 可用**。新增了一个**纯 Swift 子进程版**作为零依赖替代：

**位置**：`~/.hermes/skills/vision/scripts/vision_ocr.py`

**核心优势**：
- **0 依赖**（不依赖 pyobjc、不依赖 Homebrew Python、不依赖 PaddleOCR）
- **纯 Swift + Vision.framework + AppKit**，适合任何 macOS
- **首次调用 41s**（swiftc 编译），之后命中 `~/.hermes/scripts/.cache/vision_ocr_bin` 缓存，**单帧 ~1.1s**
- **支持中英混排**（recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]）
- **可选输出坐标**（`--json` 返回 text + confidence + box[4]）

**用法**：
```bash
python3 ~/.hermes/skills/vision/scripts/vision_ocr.py <image>          # 纯文本输出
python3 ~/.hermes/skills/vision/scripts/vision_ocr.py <image> --bench  # +耗时到 stderr
python3 ~/.hermes/skills/vision/scripts/vision_ocr.py <image> --json   # 完整 JSON
python3 ~/.hermes/skills/vision/scripts/vision_ocr.py --screen          # 截全屏再 OCR
```

**何时用它 vs scripts/ocr.py**：
- 想 0 依赖、要绝对稳：vision_ocr.py
- 需要 pymupdf/PaddleOCR/ddddocr/坐标找字：scripts/ocr.py
- 两者**不冲突**，可并存

## 脚本位置

`scripts/ocr.py` — 主入口，支持五个子命令：

- `find <text> [--image path] [--json]` — 快速找字返回坐标
- `screenshot [--region x,y,w,h] [--json]`
- `read <image_path> [--json]`
- `pdf <pdf_path> [--json]`
- `detect` — 列出可用引擎
