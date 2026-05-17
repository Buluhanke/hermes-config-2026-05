---
name: amazon-codewhisperer
description: Amazon CodeWhisperer — 免费AI补全、Security Scan、Lambda优化
version: 1.0.0
---

# Amazon CodeWhisperer

## When to Use
AWS开发者、需要免费无限制代码补全、进行安全扫描、或优化Lambda函数时使用。与AWS生态深度集成。

## Core Features
- **免费无限**：个人使用者完全免费，无限制
- **Security Scan**：实时漏洞扫描，修复建议
- **AWS Lambda优化**：Lambda函数性能分析，冷启动优化
- **多IDE支持**：VSCode、IntelliJ、PyCharm等
- **参考追踪**：显示代码来源，避免许可证风险
- **亚马逊Q集成**：可升级至亚马逊Q专业版

## Quick Start
```bash
# VSCode: 扩展市场安装 "AWS Toolkit"
# 或 JetBrains: 安装 "AWS Toolkit"

# IDE内登录AWS Builder ID
# 启用CodeWhisperer: Cmd+Shift+P → "AWS: Connect to CodeWhisperer"

# Security Scan
# Cmd+Shift+P → "AWS: Run Security Scan"

# CLI (Amazon Q Developer)
brew install amazon-q
```

## Pitfalls
- 与AWS账号绑定，非AWS项目优势不明显
- Security Scan仅覆盖常见漏洞，非全面安全审计
- Lambda优化建议需手动验证
- 参考追踪功能偶有误报
