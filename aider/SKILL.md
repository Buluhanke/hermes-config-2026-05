---
name: aider
description: 终端AI编码工具，git diff集成，GPT Pueblo/Claude驱动
version: 1.0.0
category: software-development
---

# Aider

## When to Use
在终端中需要快速编写、修改代码时使用。适合喜欢命令行工作流的开发者，支持Git原生集成。

## Core Features
- **终端AI搭档**：直接在终端与AI对话编码
- **Git diff集成**：AI看到的每次修改都是标准diff，便于code review
- **多模型支持**：GPT-4、Claude 3.5、GPT-4 Turbo等
- **文件感知**：一次对话可跨多个文件修改
- **代码库映射**：支持大型代码库的上下文理解

## Quick Start
```bash
# 安装
pip install aider-chat

# 启动（使用Claude）
aider --model claude-3-5-sonnet

# 编辑单个文件
aider path/to/file.py

# 整个代码库
aider --chatfile=codebase.map
```

## Pitfalls
- 长对话后上下文可能丢失
- 复杂重构需要多次迭代
- API成本累积需监控
- 非GPT模型响应质量不稳定