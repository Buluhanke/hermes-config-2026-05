---
name: groq
description: Groq API极速LLM推理平台用法指南
version: 1.0.0
---

# Groq

## When to Use
需要极低延迟的LLM推理、实时对话应用、免费Tier尝鲜时使用。

## Core Features
- **LPU推理引擎**：自研LPU芯片，Token生成速度业界领先
- **速度优势**：可达1000+ tokens/秒，远超普通GPU云
- **免费Tier**：每分钟20次请求，免费无成本体验
- **模型列表**：Llama 3/3.1、Mixtral-8x7B、Gemma-7B等

## Quick Start
```python
from groq import Groq
client = Groq(api_key="GRSK_REDACTED")

chat = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role":"user","content":"Write a haiku about AI"}],
    temperature=0.7
)
print(chat.choices[0].message.content)
```

## Pitfalls
- 免费Tier限速严格，高并发会触发限流
- 仅支持推理，无模型训练/微调功能
- 部分地区IP可能访问受限