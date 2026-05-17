---
name: ideogram
description: Ideogram 2.0 文字渲染与图像生成指南
version: 1.0.0
---

# Ideogram 2.0 文字渲染与图像生成

## When to Use
- **强烈推荐**：需要在图像中渲染精准文字（海报、Logo、T恤设计）
- 文字+图像一体化设计需求
- 电影海报、产品包装、社交媒体图文
- 相比DALL-E 3/Midjourney，文字渲染是核心优势

## Core Features

**文字渲染（核心优势）：**
- 在图像中嵌入可读文字，成功率远高于竞品
- 支持多种字体风格：手写、涂鸦、正式字体
- 文字可作为图像主体或装饰元素
- 最佳实践：用引号包裹关键文字

**主要指令：**
- `/ imagine` — 文字生图，核心指令
- `/ describe` — 图生文
- `/ style` — 风格预设（参考后面的Style Reference）

**Style Reference（风格参考）：**
- `Typography` — 文字为主设计
- `Design` — 平面设计风格
- `Anime` — 动漫风格
- `Comic` — 漫画风格
- `Realistic` — 写实摄影风格
- `3D` — 3D渲染风格
- `Abstract` — 抽象艺术

**Magic Prompt：**
- 开启后自动扩展/优化用户提示词
- 提升生成效果，建议保持开启

**API调用：**
- Ideogram提供API，定价基于渲染量
- 支持Python SDK调用
- 具体定价见 ideogram.ai/api

## Quick Start
1. 注册 ideogram.ai，获取API Key
2. 输入提示词，文字用引号包裹：
```
"Hello World" typography on a sunset gradient background, beautiful typography design
```
3. 选择风格参考
4. 生成并下载

## Pitfalls
- **文字渲染仍有限制**：过长文字、复杂字体可能出错
- **订阅费用**：免费额度有限，高频使用需付费
- **风格一致性**：部分风格可能与预期有偏差
- **英文优先**：非英文文字支持较弱
- **内容过滤**：版权字符/敏感词可能被拒绝
