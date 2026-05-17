---
name: openrouter-models
description: OpenRouter模型排名与推荐用法指南
version: 1.0.0
---

# OpenRouter Models

## When to Use
需要比较和选择大语言模型、寻找免费模型、或了解模型速度排名时使用。

## Core Features
- **模型排名**：实时更新的速度/性价比排行榜
- **免费模型列表**：列出所有可用免费模型（如GPT-4o-mini free、部分开源模型）
- **路由原理**：智能路由到最优提供商，支持统一API调用
- **多提供商**：聚合OpenAI、Anthropic、Google、Cohere等

## Quick Start
1. 访问 openrouter.ai/models 查看排名
2. 按速度或价格排序筛选
3. 获取API Key
4. 通过统一endpoint调用：

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role":"user","content":"hi"}]}'
```

## Pitfalls
- 免费模型随时可能被限流或下架
- 路由质量依赖提供商稳定性
- 部分模型在特定地区不可用