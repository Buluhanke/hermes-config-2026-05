---
name: "Vision — Image Processing, Resize, Convert & Watermark"
description: "Resize, crop, convert, watermark, OCR, QR code, chart extraction, 1688 product images. Powered by ImageMagick + native tools."
version: "4.0.0"
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
tags: ["vision", "image-processing", "resize", "crop", "convert", "optimize", "exif", "watermark", "ocr", "qr-code", "chart", "1688", "图像处理"]
related_skills:
  - baidu-ocr
---

# vision

Image processing toolkit powered by ImageMagick + native tools.

## Quick Start / 快速开始

- "Resize photo.jpg to 800px width"
- "Recognize text in screenshot.png" / 识别截图文字
- "Parse QR code from qr.png" / 解析二维码
- "Extract chart data from chart.jpg" / 提取图表数据
- "Process 1688 product image" / 处理1688商品图

## Commands

### resize
```bash
bash scripts/script.sh resize --input photo.jpg --width 800
bash scripts/script.sh resize --input photo.jpg --percent 50
```

### convert
```bash
bash scripts/script.sh convert --input photo.png --to webp
bash scripts/script.sh convert --input photo.jpg --to png
```

### optimize
```bash
bash scripts/script.sh optimize --input photo.jpg --quality 80
```

### watermark
```bash
bash scripts/script.sh watermark --input photo.jpg --text "© 2025" --position southeast
```

### ocr — 截图文字识别
```bash
bash scripts/script.sh ocr --input screenshot.png
bash scripts/script.sh ocr --input screenshot.png --engine baidu    # 百度OCR（需配置API密钥）
bash scripts/script.sh ocr --input screenshot.png --engine native    # 系统原生OCR（macOS Vision框架）
bash scripts/script.sh ocr --input screenshot.png --json            # JSON结构化输出
```

### qrcode — 二维码解析
```bash
bash scripts/script.sh qrcode --input qr.png           # 解析二维码内容
bash scripts/script.sh qrcode --input qr.png --json   # JSON输出
bash scripts/script.sh barcode --input barcode.png     # 解析条形码
```

### chart — 图表数据提取
```bash
bash scripts/script.sh chart --input chart.png              # 提取图表数据（自动检测类型）
bash scripts/script.sh chart --input chart.png --type bar   # 指定为柱状图
bash scripts/script.sh chart --input chart.png --type line # 指定为折线图
bash scripts/script.sh chart --input chart.png --type pie   # 指定为饼图
bash scripts/script.sh chart --input chart.png --json       # JSON结构化输出
```

### 1688 — 1688商品图处理
```bash
bash scripts/script.sh 1688 --input product.jpg                    # 标准化处理（白底+去文字）
bash scripts/script.sh 1688 --input product.jpg --whitelist text  # 仅去文字
bash scripts/script.sh 1688 --input product.jpg --background white # 指定背景色
```

## Requirements
- bash 4+
- ImageMagick (convert, identify, magick)
- zbar (for QR/barcode) — `brew install zbar`
- Python 3 with Pillow for chart extraction
- 百度OCR: BAIDU_API_KEY in ~/.hermes/.env (可选)
- macOS原生OCR: 系统自带，无需额外安装