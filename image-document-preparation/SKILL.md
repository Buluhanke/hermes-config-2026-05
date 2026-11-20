---
name: image-document-preparation
description: 图片文档处理 — 裁剪、合并、排版到标准纸张。Use when 裁剪证件图片或合并到A4
version: '1.0'
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [image-processing, document, layout, pil]
    related_skills: [product-catalog-to-excel, minimax-pdf]
---

# When to Use

用户要求裁剪图片中的证件/文档区域、合并多张图片到一张标准纸张（A4/A3等）、或图片排版输出。

# Image Document Preparation

## Core Workflow

1. **Load images** — PIL Image.open()
2. **Detect card/document boundary** — Try threshold-based bbox detection first; if fails (uniform brightness), use center crop with reasonable margins
3. **Crop** — img.crop((xmin, ymin, xmax, ymax))
4. **Create canvas** — Standard paper size at 200dpi: A4 = 1654×2339, A3 = 2339×3311
5. **Scale & place** — resize each image to fit width with margin, stack vertically with spacing
6. **Save** — PNG for quality, JPEG for smaller size

## Paper Sizes (200dpi)

| Size | Pixels | Use |
|---|---|---|
| A4 | 1654×2339 | Standard document |
| A3 | 2339×3311 | Large format |

## Cropping Strategy

### Auto-detect (preferred)
```python
import numpy as np
gray = np.mean(np.array(img.convert('RGB')), axis=2)
for t in [150, 160, 170, 180, 190, 200]:
    mask = gray > t
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if rows.any() and (rows.sum() / len(rows)) < 0.9:
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        break
```

If auto-detect fails (mask covers >90% of image), the background is also light-colored and thresholding cannot distinguish card from background.

### Fallback (uniform brightness)
If auto-detect fails, use center crop with generous margins:
```python
w, h = img.size
# ID card aspect ratio ~1.585:1 (85.6mm x 54mm)
# Try center crop first, then verify with vision_analyze
crop = img.crop((int(w*0.06), int(h*0.08), int(w*0.94), int(h*0.92)))
```

After cropping, ALWAYS verify with vision_analyze that the full document is captured. If edges are cut off, adjust crop box and re-verify.

## Layout Template

```python
from PIL import Image
canvas = Image.new('RGB', (1654, 2339), 'white')
margin = 50
spacing = 50
cards = [card1, card2]
y = margin
for card in cards:
    scale = (1654 - 2*margin) / card.width
    new_w = int(card.width * scale)
    new_h = int(card.height * scale)
    scaled = card.resize((new_w, new_h), Image.LANCZOS)
    canvas.paste(scaled, (margin, y))
    y += new_h + spacing
canvas.save('/path/to/output.png', dpi=(200, 200))
```

## Key Rules

- Always verify crop captures full document (use vision_analyze to check)
- Preserve original resolution when possible
- Use PNG for documents with text, JPEG for photos
- Add margin around each image (50px at 200dpi)
- Stack vertically for multiple images on one page

## Pitfalls

- Threshold detection fails on uniform backgrounds — fallback to center crop
- Don't crop too tight — leave 5-10% margin around detected boundary
- Always maintain original aspect ratio when scaling
- PNG at 200dpi A4 is ~5MB; use JPEG if size matters
- **Light-colored fabric backgrounds** (gray/white cloth) make threshold detection fail because the entire image has light pixels — use center crop with 6% horizontal / 8% vertical margins, then verify with vision_analyze
- Always verify crop captures full document with vision_analyze before finalizing — edges may be cut off even with generous margins
