---
name: together-ai
description: Together AI开源模型推理平台用法指南
version: 1.0.0
---

# Together AI

## When to Use
需要调用Llama/Mixtral/Qwen等开源模型、快速部署、性价比推理时使用。

## Core Features
- **开源模型库**：Llama 3/3.1/3.2、Mixtral、Qwen 2.5、Flamingo等
- **API兼容**：OpenAI兼容API，替换endpoint即可
- **价格优势**：比OpenAI便宜约10倍
- **聊天补全**：支持文本/图像多模态

## Quick Start
```bash
# 安装
pip install together

# 代码调用
from together import Together
client = Together(api_key="YOUR_KEY")

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role":"user","content":"Explain quantum computing"}],
    max_tokens=512
)
print(response.choices[0].message.content)
```

## Pitfalls
- 部分模型有使用配额限制
- 国内访问可能不稳定，建议配置代理
- 长期大量调用建议关注成本面板