---
name: val
description: Val AI — 前端开发Agent，浏览器预览与Figma导入
version: 1.0.0
---

# Val AI

## When to Use
需要AI辅助前端开发、快速将Figma设计转为代码、或需要浏览器实时预览迭代时使用。适合UI密集型项目。

## Core Features
- **前端专用**：React、Vue、Svelte等框架优化
- **浏览器预览**：代码修改即时浏览器刷新
- **Figma导入**：Figma设计稿直接转代码
- **组件识别**：自动识别设计系统组件
- **多框架输出**：React/Vue/HTML多目标
- **样式匹配**：Tailwind/CSS属性智能映射

## Quick Start
```bash
# Web访问
# https://val.ai

# 或VSCode扩展
code --install-extension val.val-vscode

# Figma导入
# 1. 在Val.ai连接Figma账号
# 2. 导入Figma文件
# 3. 选择框架输出
# 4. 下载或直接编辑

# CLI预览
val preview --port 3000
val deploy --prod
```

## Pitfalls
- Figma导入需Figma插件配合，配置稍复杂
- 自动生成代码需手动优化，非开箱即用
- 对非前端框架支持有限
- 复杂交互组件生成效果有限
