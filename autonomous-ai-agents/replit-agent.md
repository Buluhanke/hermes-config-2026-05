---
name: replit-agent
description: Replit Agent用法：nix环境、claim流程
version: 1.0.0
category: autonomous-ai-agents
---

# Replit Agent

## When to Use
在Replit平台快速构建应用时；需要nix环境隔离的可复现构建；想体验对话式编程但希望在Replit生态内。

## Core Features
- **nix环境**：每项目独立的可复现依赖环境
- **Agent对话流**：自然语言驱动的代码生成
- **一键部署**：内置Hosting，代码完成后可直接上线
- **协作编辑**：支持多人实时协作
- **Claim流程**：Agent创建项目后需手动claim到你的账户
- **模板支持**：从空白或模板开始

## Quick Start
1. 登录replit.com，点击"Create Repl"
2. 选择"Agent"模式，输入需求描述
3. Agent自动创建项目、编写代码、运行测试
4. 完成后点击"Claim"将项目所有权转移到你的账户

## Pitfalls
- Replit免费版计算时间有限
- nix配置复杂，依赖冲突排查困难
- 国内访问延迟高
- Agent生成的代码可能包含Replit特定配置
