---
name: tabnine
description: TabNine — 本地模型代码补全与团队知识库
version: 1.0.0
---

# TabNine

## When to Use
需要本地运行代码补全、保护代码隐私、接入团队私有代码知识库时使用。JetBrains全家桶用户首选。

## Core Features
- **本地模型**：代码不离开本地，支持Llama、DeepSeek等本地LLM
- **代码补全**：整行/函数级补全，上下文感知
- **团队知识库**：接入私有代码库，构建团队级补全模型
- **JetBrains支持**：官方插件，支持所有JetBrains IDE
- **多语言**：支持100+编程语言
- **离线模式**：完全本地运行，无需网络

## Quick Start
```bash
# 安装JetBrains/VSCode扩展
# 或 Homebrew安装
brew install tabnine

# 登录/注册
tabnine login

# 配置本地模型
tabnine config set use_local_model true
tabnine model download llama-4

# 团队知识库配置
tabnine team connect --repo https://github.com/org/repo
```

## Pitfalls
- 本地模型需要足够GPU资源，性能依赖硬件
- 团队知识库需付费订阅
- 配置复杂，小项目用免费版足够
- 与GitHub Copilot功能重叠，选择其一即可
