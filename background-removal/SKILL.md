---
name: background-removal
description: 图片背景一键去除 — 本地免费，M4 Mac MPS加速
triggers:
  - 去背景
  - 抠图
  - 产品图处理
  - 背景去除
---

# 背景去除 (rembg)

## 环境
- 运行Python: `source ~/.hermes/hermes-agent/venv/bin/activate`
- 模型: u2net (176MB, ONNX, 自动缓存)
- 包: rembg 2.0.75

## 快速使用
```python
from PIL import Image
from rembg import remove

img = Image.open('input.jpg')
output = remove(img)
output.save('output.png')
```

## 性能
- 模型: u2net.onnx (176MB, ONNX Runtime)
- 首次运行: ~16s（需下载模型到 `~/.u2net/u2net.onnx`）
- 后续推理: **~2.2s/张**（M4 Mac, 640x480 输入）
- 无需 GPU 加速，ONNX Runtime 自动优化

## 使用示例

```python
from PIL import Image
from rembg import remove

# 单张处理
output = remove(Image.open('product.jpg'))
output.save('product_nobg.png')

# 批量处理
import glob
for f in glob.glob('photos/*.jpg'):
    output = remove(Image.open(f))
    output.save(f.replace('.jpg', '_nobg.png'))
```

---

> 隶属于 [`m4-ml-toolkit`](../m4-ml-toolkit/SKILL.md) — M4 Mac 本地 ML 工具箱
