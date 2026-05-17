---
name: stable-video
description: Stable Video Diffusion：本地/云端部署、帧插值、视频扩散模型
version: 1.0.0
---

# Stable Video Diffusion (SVD)

## When to Use
需要在本地运行视频生成模型时选SVD。适合有GPU资源的技术团队、隐私敏感场景、或需要深度定制模型的开发者。云端适合无本地算力的用户。

## Core Features
- **SVD / SVD-XT**：Stability AI开源的视频扩散模型，支持14-25帧生成
- **本地部署**：支持ComfyUI、AUTOMATIC1111、WebUI扩展
- **帧插值（Frame Interpolation）**：使用Deforum等工具补帧使视频流畅
- **图生视频（I2V）**：上传图片生成短视频动画
- **云端部署**：Stability AI官方API、Replicate、RunPod等平台
- **自定义模型**：可微调LoRA适配特定风格

## Quick Start
### 本地部署（ComfyUI）
1. 安装ComfyUI，更新到最新版本
2. 下载SVD模型（svd.safetensors，约6GB）
3. 加载Image Only (SVD)节点，上传图片
4. 设置帧数（14/25）、FPS、CFG参数
5. 生成后用Rife或FILM补帧

### 云端API
1. 注册Replicate或Stability AI账号
2. 调用：`replicate.run("stability-ai/stable-video-diffusion:...")`
3. 传入图片URL，等待生成完成

## Pitfalls
- 本地需要8GB+显存（推荐12GB）
- 视频时长受限（最多25帧），需补帧才能变长
- 安装配置复杂，非技术用户门槛高
- 云端按秒计费，成本需控制
