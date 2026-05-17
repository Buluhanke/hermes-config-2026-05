---
name: linear-ai
description: Linear AI驱动Issue管理，GitHub同步与工作流自动化
version: 1.0.0
---

# Linear — AI驱动的项目管理

## When to Use
工程团队快速Issue管理、GitHub PR联动、自动化工作流。适合追求效率的软件团队。AI搜索和自动化规则是其核心优势，显著快于传统项目管理工具。

## Core Features
- **AI搜索**: 自然语言搜索Issue，无需记住标签格式
- **GitHub同步**: PR自动关联Issue，状态双向同步
- **自动化规则**: 状态变更、分配、标签的触发器
- **Cycle/Sprint**: 内置敏捷周期管理
- **完整API**: GraphQL API，支持任意集成
- ** Slack/Discord通知**: 关键事件实时推送

## Quick Start
获取API Key：Settings→API→Create API Key

```bash
pip install linear-sdk
```

```python
from linear_sdk import LinearClient

client = LinearClient(api_key="xxx")

# AI搜索（Linear特有）
issues = client/issues_search("找不到登录页面的bug")

# 列出Issue
issues = client.issues(filter={"team": {"id": "team_id"}})

# 创建Issue
issue = client.create_issue({
    "title": "修复登录bug",
    "teamId": "team_id",
    "priority": 1
})
```

GitHub集成：在Settings→Integrations→GitHub配置仓库映射

## Pitfalls
- GraphQL API需要了解query/mutation结构
- Webhook签名验证：必须校验X Linear Signature
- AI搜索依赖Linear云端，不支持私有部署
- Issue ID是哈希值，非自增整数
- 批量操作需控制速率，单请求<1KB
