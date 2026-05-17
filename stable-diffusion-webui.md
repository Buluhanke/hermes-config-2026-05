---
name: stable-diffusion-webui
description: Stable Diffusion WebUI 本地部署与扩展指南
version: 1.0.0
---

# Stable Diffusion WebUI 本地部署

## When to Use
- 需要完全本地化运行，保护隐私
- 想要最大化的扩展生态（ControlNet、LoRA等）
- 需要Fine-tune和训练自己的模型
- 无API成本，按需无限生成

## Core Features

**本地部署要求：**
- GPU：建议8GB+ VRAM（SDXL需要12GB+）
- 系统：Windows/Linux/macOS
- 存储：10GB+用于模型文件

**安装方式：**
```bash
# 官方 AUTOMATIC1111 WebUI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
./webui.sh  # Linux/macOS
webui-user.bat  # Windows
```

**扩展生态（Extensions）：**
- **ControlNet**：姿态控制、线稿提取、深度图等
- **LoRA**：轻量模型微调，文件小（100MB左右）
- **VAE**：提升色彩和细节
- **Embedding**：负嵌入，替代负面提示词
- **Model Mixer**：模型混合

**WebUI核心功能：**
- 文生图（txt2img）
- 图生图（img2img）
- 放大（ESRGAN/Hires Fix）
- 提示词历史记录
- 参数预设保存
- ControlNet集成

**与ComfyUI对比：**

| 方面 | WebUI | ComfyUI |
|------|-------|---------|
| 上手难度 | 简单 | 复杂 |
| 灵活性 | 中等 | 极高 |
| 工作流 | 固定界面 | 节点图 |
| 批量处理 | 支持 | 支持 |
| 学习曲线 | 陡 | 更陡 |

## Quick Start
1. 安装Python 3.10+
2. 克隆仓库并运行
3. 下载基础模型（SD 1.5/SDXL/SD 3.x）
4. 放入 `models/Stable-diffusion/`
5. 启动后浏览器打开 `http://localhost:7860`

## Pitfalls
- **显存不足**：SDXL需要12GB+，否则崩溃或切换低显存模式
- **模型来源**：HuggingFace下载可能限速
- **扩展冲突**：部分扩展版本不兼容
- **更新风险**：更新后可能与旧扩展不兼容
- **macOS Metal**：GPU加速支持，但仍比Windows/Nvidia慢
