---
name: zeroscope
description: Zeroscope V2：开源视频模型、本地运行、ComfyUI集成
version: 1.0.0
---

# Zeroscope V2

## When to Use
完全免费、开源、本地运行首选Zeroscope V2。适合开发者和技术爱好者深度定制，无商业使用限制，可离线运行保护隐私。

## Core Features
- **Zeroscope V2**：Wan-AI开源的文生视频模型，576x320分辨率
- **无水印无限制**：完全免费，可商用（需遵循开源协议）
- **ComfyUI原生支持**：节点化工作流，可视化编辑
- **本地运行**：支持消费级GPU（8GB+显存）
- **多种模型变体**：Zeroscope V2、Zeroscope V2 XL等
- **可定制**：LoRA微调、提示词工程、后期处理

## Quick Start
### ComfyUI
1. 安装ComfyUI，更新到最新版本
2. 从Civitai/HuggingFace下载Zeroscope V2模型
3. 添加Text2Video节点，输入提示词
4. 可串联AnimateDiff增加运镜动画
5. 用Rife补帧后放大分辨率

### Python脚本
```python
from diffusers import DiffusionPipeline
pipe = DiffusionPipeline.from_pretrained("cerspense/zeroscope_v2_576w")
pipe.enable_model_cpu_offload()
video = pipe("astronaut riding a horse").frames
```

## Pitfalls
- 分辨率较低（576x320），需后期放大
- 运动质量不如商业模型
- 需要下载大模型文件（5-10GB）
- 提示词理解能力有限，需优化措辞
