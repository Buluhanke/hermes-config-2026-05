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

所有依赖已安装，无需额外操作。

| 引擎 | 依赖 | 安装命令 |
|------|------|---------|
| Vision OCR | macOS内置 | 无需安装 |
| PaddleOCR | paddleocr | `pip install paddleocr` |
| Baidu OCR | curl + .env | 已在.env配置 |
| ddddocr | ddddocr | `pip install ddddocr` |
| pymupdf | pymupdf | `pip install pymupdf` |

## 脚本位置

`scripts/ocr.py` — 主入口，支持四个子命令：

- `screenshot [--region x,y,w,h] [--json]`
- `read <image_path> [--json]`
- `pdf <pdf_path> [--json]`
- `detect` — 列出可用引擎
