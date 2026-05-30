---
name: hermes-ocr
description: 统一OCR引擎层 — 自动检测可用引擎，智能降级。Vision OCR(60ms) → PaddleOCR(高精度中文) → Baidu OCR(云端) → ddddocr(验证码) → pymupdf(PDF)
tags: [OCR, Vision, PaddleOCR, BaiduOCR, ddddocr, pymupdf, PDF]
---

# Hermes OCR — 统一OCR引擎

## 能力概述

**一句话**：截图/图片进来，文字出去。自动选最快最好的引擎。

**引擎优先级（自动降级）：**
1. `Vision OCR` — 60ms，macOS原生，屏幕截图首选
2. `PaddleOCR` — 高精度中文，图片/文档
3. `Baidu OCR` — 云端备份
4. `ddddocr` — 验证码通杀
5. `pymupdf` — PDF文字提取（文本型PDF，非扫描件）

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

## 脚本位置

`scripts/ocr.py` — 主入口，支持五个子命令：

- `find <text> [--image path] [--json]` — 快速找字返回坐标
- `screenshot [--region x,y,w,h] [--json]`
- `read <image_path> [--json]`
- `pdf <pdf_path> [--json]`
- `detect` — 列出可用引擎
