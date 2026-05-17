---
name: openghost
description: 开源AI编程Agent，模拟Devin/Cursor，浏览器自动化+代码生成
version: 1.0.0
category: autonomous-ai-agents
---

# OpenGHOST

## When to Use
需要开源可自托管的AI编程助手时。与Claude Code/Devin对比，选择更透明、可定制的方案。

## Core Features
- **浏览器自动化**：Playwright驱动，自主操控浏览器完成Web任务
- **代码生成执行**：生成并执行代码，验证结果
- **多模型支持**：兼容Claude、GPT-4、Local模型
- **开源可自托管**：完全开源，支持Docker部署
- **任务分解**：将复杂需求拆解为可执行步骤

## Quick Start
```bash
# Docker部署
docker run -d -p 3000:3000 \
  -e ANTHROPIC_API_KEY=your_key \
  ghcr.io/openghost/openghost

# 或本地安装
npm install -g openghost
openghost --model claude
```

## Pitfalls
- 自托管需要足够硬件资源
- 浏览器自动化依赖稳定网络
- 多模型切换配置较复杂
- 与商业产品（Devin/Claude Code）仍有差距