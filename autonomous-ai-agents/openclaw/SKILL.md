---
name: openclaw
description: OpenClaw开源AI编程Agent
version: 1.0.0
---

# OpenClaw — 开源AI编程Agent

## When to Use
- 需要本地运行、可自托管的AI编程Agent
- 深度定制化开发工作流
- 与Claude Code对比评估时

## Core Features
- **开源可自托管**：完整代码公开，自行部署
- **多模型支持**：Claude/GPT/本地模型
- **工具调用**：文件操作、Shell命令、Git
- **上下文管理**：智能上下文窗口管理
- **与Claude Code对比**：
  - OpenClaw：完全开源、本地优先
  - Claude Code：闭源、云端优化、商业支持

## Quick Start
```bash
# 安装
npm install -g openclaw

# 启动对话
openclaw

# 指定模型
openclaw --model claude-3-5-sonnet

# 项目模式
openclaw --project ./my-project
```

## Pitfalls
- 本地部署需要较高硬件配置
- 开源版功能可能不如商业版完善
- 自托管维护成本
- 插件生态不如主流工具丰富
