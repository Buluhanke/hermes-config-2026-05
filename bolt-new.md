---
name: bolt-new
description: Bolt.new — 浏览器内AI开发、SSH部署、帧捕获
version: 1.0.0
---

# Bolt.new

## When to Use
需要浏览器内完成全栈开发、快速原型构建、即时预览、或与Cursor对比选择AI IDE时使用。适合不想配置本地环境的开发者。

## Core Features
- **浏览器内开发**：无需本地配置，完全云端
- **AI对话开发**：自然语言描述需求，自动生成代码
- **帧捕获**：UI状态快照，便于调试
- **SSH部署**：自有服务器部署选项
- **全栈支持**：前端+后端+数据库
- **实时协作**：多人实时编辑

## Quick Start
```bash
# Web访问
# https://bolt.new

# 或使用StackBlitz（bolt.new底层基于此）
# https://stackblitz.com

# 创建项目后：
# 1. 描述你想要的应用
# 2. AI生成初始代码
# 3. 对话式修改
# 4. 预览或部署

# SSH部署
bolt deploy --ssh user@server.com:/var/www/app
```

## Pitfalls
- 复杂项目浏览器性能有限
- 与Cursor对比：Cursor更适合本地深度开发，Bolt更适合快速原型
- 网络依赖：离线无法使用
- 代码定制化程度有限
