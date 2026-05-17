---
name: openhands
description: OpenHands Docker部署与Browser-use集成
version: 1.0.0
---

# OpenHands — 开源AI Agent平台

## When to Use
- 需要Docker隔离环境的AI Agent
- 浏览器自动化任务
- Python代码执行与调试

## Core Features
- **Docker部署**：环境隔离、一键启动
- **Python执行环境**：内置Python解释器
- **Browser-use集成**：网页自动化操作
- **文件管理**：项目文件读写
- **多Agent协作**：支持子Agent分工

## Quick Start
```bash
# Docker部署
docker pull remnoteai/openhands
docker run -it remnoteai/openhands

# Python代码执行
# OpenHands内置Python解释器
# 直接编写Python代码并执行

# Browser-use示例
# 初始化浏览器
browser.open("https://example.com")
browser.click("button.submit")
browser.type("input#name", "Hello")
```

## Pitfalls
- Docker占用资源较多
- 浏览器自动化依赖网络环境
- Python环境包管理复杂
- 多Agent协作调试困难
- 长任务状态持久化问题
