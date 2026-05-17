---
name: runway
description: Runway Gen-3视频生成：运动笔刷、API价格对比、企业级功能
version: 1.0.0
---

# Runway

## When to Use
专业视频制作团队首选Runway。Gen-3在影视级质量、运动控制上领先，适合广告、电影预演、内容创作。API适合集成到自动化工作流。

## Core Features
- **Gen-3 Alpha**：当前最强模型，支持10秒视频生成，高保真运动和人像
- **运动笔刷（Motion Brush）**：在图上涂抹指定区域赋予运动，可控性强
- **导演模式（Director Mode）**：运镜控制（推拉摇移）、景深控制
- **Gen-3 API**：编程方式调用，支持视频延长（Extend）、图生视频
- **Collaborators**：团队协作功能，共享项目和素材库

## Quick Start
1. 访问 https://runwayml.com 注册
2. 选择Gen-3模型，输入提示词
3. 调整时长（3-10秒）、运镜参数
4. 生成后可继续Extend或编辑（慢动作、局部重绘）
5. API调用示例：`POST /v1/generate/video` + API Key

## Pitfalls
- 价格偏高：Plus $15/月（125积分），Pro $35/月（625积分）
- API按生成帧数计费，成本可控但累计快
- 提示词理解有时偏离预期，需多次迭代
- 某些内容被禁止（NSFW），审核严格
