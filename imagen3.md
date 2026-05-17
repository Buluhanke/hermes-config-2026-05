---
name: imagen3
description: Google Imagen 3 图像生成用法指南
version: 1.0.0
---

# Google Imagen 3 图像生成

## When to Use
- 需要Google生态深度集成（Gemini、Vercel AI等）
- 高质量照片级图像生成
- Vertex AI平台用户
- 需要Deep Search研究级模式

## Core Features

**Vertex AI集成（主要使用方式）：**
```python
from vertexai.preview import generative_models
from vertexai.preview.generative_models import ImageGenerator

model = ImageGenerator.from_pretrained("imagegeneration@006")
response = model.generate_images(
    prompt="A cozy coffee shop interior with warm lighting",
    number_of_images=4,
    aspect_ratio="1:1",
    safety_filter_level="block_some",
    person_generation="allow_adult"
)
```

**核心参数：**
- `prompt` — 英文提示词
- `number_of_images` — 生成数量（1-4）
- `aspect_ratio` — `1:1` / `3:4` / `4:3` / `9:16` / `16:9`
- `safety_filter_level` — 安全过滤级别
- `person_generation` — 人物生成控制
- `negative_prompt` — 负面提示词

**Deep Search模式：**
- 研究级功能，输入提示词后自动深度搜索相关概念
- 生成更丰富、更准确的视觉内容
- 适合：需要精确视觉细节的商业项目
- 可能增加生成时间

**版权说明（重要）：**
- 生成的图像版权归用户所有
- 需遵守Google AI生成内容使用政策
- 禁止：误导性内容、版权侵权、NSFW
- 商业使用建议阅读完整服务条款
- Vertex AI有额外使用条款约束

**与Gemini集成：**
- Gemini Advanced用户可通过App访问Imagen 3
- 对话式生成，支持修改和迭代

## Quick Start
1. 拥有Google Cloud账号并启用Vertex AI API
2. 设置认证（服务账号或ADC）
3. 安装SDK：`pip install vertexai`
4. 使用Python代码调用或通过Google Cloud Console

## Pitfalls
- **区域限制**：部分地区可能无法访问
- **API成本**：Vertex AI按调用计费，需预算管理
- **人物生成**：有严格限制，误用会被阻止
- **英文优先**：非英文提示词效果较差
- **延迟**：高峰期可能有队列延迟
