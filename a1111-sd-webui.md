---
name: a1111-sd-webui
description: Automatic1111 SD WebUI 最流行开源图像生成界面
version: 1.0.0
---

# Automatic1111 SD WebUI 指南

## When to Use
- 最广泛使用的SD WebUI，社区支持最强
- 新手入门首选，文档教程最多
- 需要提示词历史和参数预设
- ControlNet爱好者

## Core Features

**Automatic1111（简称A1111）特点：**
- 最早最成熟的SD WebUI
- 社区生态最大，教程最丰富
- 扩展最多，更新最频繁

**核心功能：**

**文生图/图生图：**
- 采样器选择（DPM++、Euler、DDIM等）
- 步数、CFG Scale、Seed精确控制
- 批量生成（Batch）

**提示词历史：**
- 自动保存所有生成记录
- PNG Info功能：从已生成图片提取提示词
- 提示词模板/预设保存

**ControlNet：**
- 多预处理器（canny、depth、openpose等）
- 权重和引导终止时机控制
- 与主模型独立参数
- 多个ControlNet同时使用

**扩展（Extensions）：**
- `sd-webui-controlnet` — ControlNet主扩展
- `sd-webui-additional-networks` — LoRA/Embedding管理
- `sd-webui-reactor` — 换脸
- `a1111-sd-webui-tagcomplete` — 提示词自动补全
- `sd-webui-lora-block-weight` — LoRA强度分层控制

**Hires Fix（放大修复）：**
- 先生成低分辨率，再放大重绘
- 减少高分辨率下的伪影
- 放大算法：ESRGAN、LDSR等

## Quick Start
```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
./webui.sh  # Linux
webui-user.bat  # Windows
```
1. 浏览器打开 `http://localhost:7860`
2. 下载模型放入 `models/Stable-diffusion/`
3. 输入提示词开始生成

## Pitfalls
- **显存**：SD 1.5需4GB+，SDXL需12GB+
- **安全过滤**：内置NSFW过滤器，关闭需修改配置
- **扩展冲突**：非官方扩展可能导致不稳定
- **中文界面**：无内置中文，需安装扩展
- **更新**：git pull可能产生冲突，手动处理
