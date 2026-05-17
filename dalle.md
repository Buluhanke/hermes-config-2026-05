---
name: dalle
description: OpenAI DALL-E 3 图像生成用法指南
version: 1.0.0
---

# DALL-E 3 图像生成

## When to Use
- 需要精确文字渲染（Logo、海报文案）
- 与ChatGPT深度集成，自然语言对话式生成
- 需要API批量自动化生成
- 追求高连贯性多图生成（同一场景/角色）

## Core Features

**ChatGPT集成（网页/App）：**
- 直接用自然语言对话，GPT-4自动优化提示词
- 支持追问、修改、重生成
- 生成4张图为一组，可局部重绘
- 编辑模式：画布工具可添加/移除元素

**API调用：**
```bash
curl https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "dall-e-3",
    "prompt": "a serene Japanese garden with cherry blossoms",
    "n": 1,
    "size": "1024x1024",
    "quality": "standard"
  }'
```
- `quality`: `standard`（标准）或 `hd`（高清，2倍价格）
- `size`: `1024x1024` / `1792x1024` / `1024x1792`
- `style`: `vivid`（生动）/ `natural`（自然）
- **n只能是1**，不支持一次生成多张

**画布编辑（ChatGPT Plus）：**
- 上传图片后选择"编辑"
- 画刷工具：添加/移除区域
- 局部重绘保持整体风格一致

**4倍快速生成：**
- DALL-E 3 本身无"4x"概念
- 指GPT-4 with DALL-E 3响应更快，迭代更高效
- API端可设置 `response_format=url` 或 `b64_json`

## Quick Start
1. ChatGPT Plus用户：直接对话生成
2. API用户：获取API Key后用curl调用
3. 提示词越具体越好，DALL-E 3擅长理解复杂场景

## Pitfalls
- **API价格**：DALL-E 3较贵（$0.04-$0.12/图），做好成本控制
- **文字渲染**：DALL-E 3是文字渲染最强模型，但仍可能出错
- **NSFW过滤**：内容政策严格，避免违规提示词
- **1024x1024固定**：不同尺寸需指定size参数
- **版权**：生成图像版权归用户，但需遵守使用政策
