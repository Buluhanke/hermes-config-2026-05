---
name: looped
description: Looped — AI开发流程工具，context管理与Claude Code对比
version: 1.0.0
---

# Looped

## When to Use
需要AI辅助完成开发流程、context管理复杂项目、或与Claude Code对比选择时使用。适合需要AI长时间记住项目上下文的开发者。

## Core Features
- **Context管理**：长期记忆项目上下文，多文件复杂任务
- **开发流程**：需求→代码→测试→部署全流程覆盖
- **多模型支持**：Claude、GPT、Gemini等切换
- **文件索引**：自动索引项目文件，快速定位
- **任务队列**：异步任务管理
- **对话历史**：完整对话存档

## Quick Start
```bash
# 安装
npm install -g looped-cli
# 或
pip install looped

# 登录
looped login

# 初始化项目
cd my-project
looped init

# 开始对话
looped ask "重构用户认证模块"

# 管理context
looped context list
looped context load session-xxx
```

## Pitfalls
- 与Claude Code对比：Looped更注重流程管理，Claude Code更注重代码生成
- Context窗口有限，需定期清理
- 付费计划限制使用量
- 复杂项目需手动维护context质量
