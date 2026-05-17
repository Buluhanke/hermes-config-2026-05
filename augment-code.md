---
name: augment-code
description: Augment Code — AI代码补全、漏洞检测与PR审查
version: 1.0.0
---

# Augment Code

## When to Use
需要在VSCode/JetBrains中获得AI代码补全、漏洞实时检测、拉取请求自动化审查时使用。适合中大型代码库的安全审计和代码质量提升。

## Core Features
- **代码补全**：行级/函数级AI补全，支持多候选推荐
- **漏洞检测**：实时扫描CVE、安全漏洞，支持OWASP Top 10
- **PR审查**：自动化PR Diff分析，评论生成，风险评估
- **VSCode集成**：官方扩展，无缝嵌入编辑器
- **多语言支持**：Python、JavaScript、TypeScript、Go、Rust等

## Quick Start
```bash
# VSCode扩展市场安装 "Augment Code"
# 或 CLI安装
npm install -g @augmentcode/cli

# 登录
augment login

# 启用漏洞检测
augment enable security-scan

# PR审查
augment pr review --repo . --pr-number 123
```

## Pitfalls
- 安全扫描需注意代码隐私政策，避免上传敏感代码
- PR审查功能需配置CI/CD集成才能自动运行
- 漏洞检测为辅助工具，需人工复核重要漏洞报告
