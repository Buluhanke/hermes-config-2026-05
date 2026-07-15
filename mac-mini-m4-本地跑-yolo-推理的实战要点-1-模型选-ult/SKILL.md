---
name: mac-mini-m4-本地跑-yolo-推理的实战要点-1-模型选-ult
version: 0.1
description: |
  Mac mini M4 本地跑 YOLO 推理的实战要点：(1) 模型选 Ultralytics YOLOv8n/v11n 的 `.mlpackage` 或 Core ML 导出版本，用 `coremltools` 转好后用 Apple Neural Engine 跑，单张图片延迟能压到 10-20ms，CPU 占用几乎为零；(2) 用 MPS 后端 (`model.to('mps')`) 是 P
triggers:
  - "mac-mini-m4-本地跑-yolo-推理的实战要点-1-模型选-ult"
trigger_type: auto_crystallized
tags: ['auto_learned', 'YOLO物体检测实战技巧']
created: 2026-07-16
来源: fact_store (id=225, ret=1, trust=0.75)
---
# mac-mini-m4-本地跑-yolo-推理的实战要点-1-模型选-ult

Mac mini M4 本地跑 YOLO 推理的实战要点：(1) 模型选 Ultralytics YOLOv8n/v11n 的 `.mlpackage` 或 Core ML 导出版本，用 `coremltools` 转好后用 Apple Neural Engine 跑，单张图片延迟能压到 10-20ms，CPU 占用几乎为零；(2) 用 MPS 后端 (`model.to('mps')`) 是 PyTorch 路径里最稳的写法，不要走 CUDA 别名，遇到算子不支持时切回 CPU 即可；(3) 输入尺寸默认 640 跑实时检测，降到 320 能再快 2-3 倍但小目标漏检明显，建议 480 是性价比甜点；(4) 视频流用 `cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)` 走 AVFoundation 后端，配合 `cv2.dnn` 或 Ultralytics 的 `stream=True` 模式帧间复用模型，避免每帧重新加载；(5) 部署成服务时用 FastAPI 暴露 `/detect`，模型加载放 lifespan 里单例化，多路并发靠 asyncio 队列+单 worker 推理即可，M4 的统一内存让 batch=4 跑 1080p 完全没压力。
来源：基于本地 Ultralytics + Core ML 工具链经验（searxng 不可用，未走网络检索）。