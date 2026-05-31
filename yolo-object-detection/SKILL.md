---
name: yolo-object-detection
description: YOLOv8 物体检测 — M4 Mac MPS加速，支持图片检测和批量处理
triggers:
  - 图片检测
  - 物体识别
  - YOLO
  - 产品识别
  - 包装检测
---

# YOLO 物体检测

## 环境

- 运行Python: `source ~/.hermes/hermes-agent/venv/bin/activate`
- GPU加速: MPS (Apple Silicon, M4)
- 模型: ultralytics YOLOv8n (6.2MB, 最快)
- 脚本: `~/.hermes/scripts/detect.py`

## 快速使用

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
python3 ~/.hermes/scripts/detect.py <图片路径> [置信度阈值]
```

示例:
```bash
python3 ~/.hermes/scripts/detect.py ~/Downloads/product.jpg 0.3
```

## 可用模型

| 模型 | 大小 | 速度 | 精度 |
|------|------|------|------|
| yolov8n.pt (nano) | 6.2MB | 170ms | 基础 |
| yolov8s.pt (small) | 22MB | ~300ms | 较好 |
| yolov8m.pt (medium) | 52MB | ~500ms | 好 |

首次运行自动下载模型文件。

## Python代码引用

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model('image.jpg', device='mps')
for box in results[0].boxes:
    cls = model.names[int(box.cls[0])]
    conf = float(box.conf[0])
    print(f'{cls}: {conf:.1%}')
```

## 业务场景

- 产品拍照自动识别品类和数量
- 包装箱检测（结合训练自己的数据集）
- 库存盘点拍照统计
- 供应商来货照片质量检查
