---
name: bolt-deno
description: Bolt (deno版) 用法：本地部署、prompt驱动开发
version: 1.0.0
category: autonomous-ai-agents
---

# Bolt (Deno版)

## When to Use
希望本地运行prompt驱动的开发Agent时；需要Deno生态的轻量级AI编程工具；偏好TypeScript优先的开发环境。

## Core Features
- **Deno原生**：使用Deno运行时，无需Node.js
- **Prompt驱动开发**：自然语言描述需求，AI自动生成代码
- **本地部署**：完全本地运行，代码不外传
- **多文件生成**：一次prompt可生成多个相关文件
- **热重载**：代码修改后自动刷新预览

## Quick Start
1. 安装Deno后，运行`deno run -A npm:bolt-ai`或克隆bolt-deno仓库
2. 启动后访问本地端口（如 http://localhost:3000）
3. 在Web界面输入项目需求描述
4. AI生成代码，自动部署到本地预览

## Pitfalls
- Deno生态的npm兼容层偶有问题
- 生成的代码质量依赖prompt描述清晰度
- 本地GPU资源有限，大模型响应慢
- 部分AI功能需要付费API密钥
