---
name: novita
description: Novita AI GPU租赁与模型微调平台用法指南
version: 1.0.0
---

# Novita AI

## When to Use
需要租赁GPU进行推理、模型微调、OpenAI兼容API调用时使用。

## Core Features
- **GPU租赁**：提供多种规格GPU实例，按小时计费
- **模型微调**：支持Llama、Qwen等主流模型微调训练
- **OpenAI兼容API**：替换base_url即可迁移现有代码
- **图像生成**：内置FLUX.1、SDXL等图像模型API

## Quick Start
```python
from openai import OpenAI

client = OpenAI(
    api_key="NOVITA_API_KEY",
    base_url="https://api.novita.ai/v3"
)

# 文本生成
chat = client.chat.completions.create(
    model="meta-llama/llama-3.1-70b-instruct",
    messages=[{"role":"user","content":"Hello"}]
)
```

**GPU租赁**：访问控制台 → GPU Market → 选择实例 → 启动Jupyter/Terminal

## Pitfalls
- GPU实例按小时计费，不用时及时关闭
- 微调需要准备合规训练数据集
- 部分区域GPU库存可能不足