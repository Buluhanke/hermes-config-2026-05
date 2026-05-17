---
name: invokeai
description: InvokeAI 专业级图像生成界面使用指南
version: 1.0.0
---

# InvokeAI 专业图像生成

## When to Use
- 需要专业级工作流（非爱好者玩具）
- 团队协作，批量生成场景
- 需要IP-Adapter、ControlNet高级功能
- 对图像质量有严格要求

## Core Features

**安装方式：**
```bash
# pip安装
pip install invokeai
invokeai-install

# 或下载独立版本
# https://github.com/invoke-ai/InvokeAI/releases
```

**核心界面：**
- **Canvas（画布）**：节点式工作流编辑器
- **Unified Canvas**：图生图+局部重绘+外扩
- 支持无限画布外扩

**IP-Adapter：**
- 基于图像内容调整生成风格
- 类似于Midjourney的 `--image` 参数
- 支持强度控制
- 适合：角色一致性、产品照风格化

**ControlNet集成：**
- 姿态控制（OpenPose）
- 线稿控制（Canny/Scribble）
- 深度图（Depth）
- 分割（Segmentation）
- 与主模型强度可独立调节

**其他专业功能：**
- **Hotpoint（提示词加权）**：在提示词中精确控制词汇权重
- **LoRA支持**：训练和应用自定义LoRA
- **模型管理**：内置模型切换器
- **批量生成**：队列式批量处理
- **无损输出**：PNG + 元数据保存

## Quick Start
1. 安装后运行 `invokeai-webui`
2. 浏览器打开 `http://localhost:9090`
3. 选择基础模型
4. 输入提示词，调整参数
5. 生成

## Pitfalls
- **硬件要求**：与SD WebUI相近，需6GB+ VRAM
- **学习曲线**：专业功能需要学习时间
- **版本更新**：功能变化较大，更新可能带来界面变化
- **中文支持**：界面英文为主，提示词仍需英文
- **模型兼容**：不是所有SD模型都能完美兼容
