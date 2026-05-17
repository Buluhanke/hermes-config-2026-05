---
name: openart
description: OpenArt.ai AI图像生成平台用法指南
version: 1.0.0
---

# OpenArt.ai

## When to Use
需要快速生成AI图像、研究不同SD模型效果、探索风格标签时使用。

## Core Features
- **多模型支持**：SD1.5、SDXL、Flux.1 Schnell/Pro/Dev
- **DISTANCE比例系统**：0–10控制提示词影响力，0=忽略提示，10=严格遵循
- **风格标签**：数百种预置风格（Cinematic、Anime、Photorealistic等）
- **免费额度**：每日积分制，新用户约100积分

## Quick Start
1. 访问 openart.ai 注册账号
2. 选择模型（建议SDXL新手入门）
3. 输入提示词，调整DISTANCE值（默认5）
4. 选择风格标签或留空
5. 点击Generate

**示例提示词**：`portrait of a woman, golden hour lighting, DISTANCE:7`

## Pitfalls
- Flux模型消耗积分更多，优先用SDXL节省额度
- DISTANCE值过高（>8）会导致过度饱和/构图僵硬
- 免费积分每日重置，过期不累积