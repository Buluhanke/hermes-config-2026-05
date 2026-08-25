---
name: local-image-ocr
description: "本地图片OCR pytesseract提取文字。Use when 从截图图片提取文字"
version: 1.0.0
triggers:
- Use when vision_analyze fails on local file path with 404
- Use when you need OCR on a screenshot or image saved locally
---

# Local Image OCR

> vision_analyze 对本地路径（`/path/to/file.jpg`）返回 404，成功率不稳定。本地图片文件用 pytesseract + PIL via terminal()。

## 核心命令

```bash
python3 -c "
import pytesseract
from PIL import Image
img = Image.open('/path/to/file.jpg')
print(pytesseract.image_to_string(img, lang='chi_sim+eng'))
"
```

## 常用语言参数

| 语言 | `--psm` | `lang` |
|------|---------|--------|
| 英文 | 6 | `eng` |
| 中文简體 | 6 | `chi_sim+eng` |
| 中文繁體 | 6 | `chi_tra+eng` |
| 日文 | 6 | `jpn+eng` |

`--psm 6` = Assume a uniform block of text.

## 图片预处理（提升识别率）

```python
from PIL import Image, ImageFilter

img = Image.open('/path/to/file.jpg').convert('RGB')
img_gray = img.convert('L')
img_sharp = img.filter(ImageFilter.SHARPEN)
img_gray.save('/tmp/ocr_input.png')
```

## 已知坑

- **execute_code 沙盒没有 pytesseract**：必须用 `terminal()` 执行，不能在 execute_code 里跑
- **JPEG → PNG 转换**：某些 JPEG 直接读可能出问题，先转 PNG：`img.save('/tmp/out.png', 'PNG')`
- **竖屏长图**：1292×2800 竖图，PIL + tesseract 可正常处理
- **vision_analyze 不认本地路径**：始终 404，不要反复重试，直接用 pytesseract