---
name: claude-artifacts
description: Claude Artifacts用法：React/Vite组件生成、save/load/open流程
version: 1.0.0
category: creative
---

# Claude Artifacts

## When to Use
需要快速生成可运行的React/Vite组件时；原型设计、代码展示、教学演示；希望生成代码可直接预览而非仅返回代码片段。

## Core Features
- **代码即预览**：生成React/Vite代码后自动渲染为可交互预览
- **多框架支持**：React、Vue、Svelte、HTML/CSS/JS
- **版本管理**：自动保存历史版本，可回溯
- **一键导出**：下载为本地文件或复制代码
- **分享链接**：生成可分享的在线预览链接

## Quick Start
1. 在Claude.ai对话中描述需求，如"用React写一个计数器组件"
2. Claude生成代码，右侧自动渲染预览
3. 点击预览区右上角"Open"在新页面查看完整应用
4. "Save"保存到你的收藏，"Copy"复制代码

## Pitfalls
- 复杂状态管理场景（如Redux）Artifact支持有限
- 生成的代码偏向原型，生产使用需重构
- 预览iframe可能有CORS限制
- 大型应用（多组件、路由）不适合用Artifact
