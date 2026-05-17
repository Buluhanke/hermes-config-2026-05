---
name: continue
description: 开源VSCode/JetBrains插件，多模型支持，代码库问答
version: 1.0.0
category: software-development
---

# Continue.dev

## When to Use
需要IDE内嵌AI辅助编码时。VSCode或JetBrains用户首选，支持多模型切换和代码库理解。

## Core Features
- **IDE插件**：无缝集成VSCode/JetBrains
- **多模型支持**：Claude、GPT-4、Code Llama、本地Ollama
- **代码库问答**：针对整个代码库的自然语言查询
- **代码补全**：行级/函数级智能补全
- **自定义提示词**：可配置系统提示词模板

## Quick Start
```bash
# VSCode扩展市场搜索"Continue"安装

# 配置models.json
{
  "models": [
    {
      "title": "Claude",
      "provider": "anthropthropic",
      "model": "claude-3-5-sonnet"
    }
  ]
}

# 选中代码 → Ctrl+Shift+M → 开始对话
```

## Pitfalls
- JetBrains插件偶有兼容性问题
- 本地模型需要Ollama额外配置
- 代码库索引首次耗时较长
- 多模型切换响应质量差异大