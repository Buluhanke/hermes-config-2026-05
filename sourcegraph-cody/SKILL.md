---
name: sourcegraph-cody
description: 代码库理解AI，悬停解释，PR摘要，多语言支持
version: 1.0.0
category: software-development
---

# Sourcegraph Cody

## When to Use
需要深度理解陌生代码库、PR review、或快速掌握遗留代码时。与Sourcegraph搜索配合效果最佳。

## Core Features
- **代码库理解**：深度分析代码结构、依赖、调用链
- **悬停解释**：鼠标悬停即可获得代码解释
- **PR摘要**：自动生成PR变更摘要
- **多语言支持**：主流编程语言全覆盖
- **企业级搜索**：结合Sourcegraph精确代码搜索

## Quick Start
```bash
# 安装Cody CLI
npm install -g @sourcegraph/cody-cli

# 认证
cody auth login

# 询问代码库
cody ask "这段代码的作用是什么？"

# 悬停功能通过VSCode扩展实现
```

## Pitfalls
- 需要Sourcegraph实例或cloud账号
- 企业私有代码库需自建Sourcegraph
- 悬停解释在大型代码库偶有延迟
- 部分语言支持仍有限