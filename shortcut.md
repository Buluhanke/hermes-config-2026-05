---
name: shortcut
description: Shortcut项目管理，Sprint跟踪与API自动化
version: 1.0.0
---

# Shortcut — 项目管理（formerly Clubhouse）

## When to Use
敏捷团队项目管理、Sprint规划和进度追踪。适合软件团队的任务管理、GitHub PR关联、工作流自动化。通过API实现定时报告、状态同步等自动化。

## Core Features
- **Epic/Story/Task**: 三级层次结构
- **Sprint管理**: 创建、规划、燃尽图
- **工作流状态**: 可配置状态流转规则
- **API优先**: 完整的REST API + Webhooks
- **GitHub集成**: PR自动关联Story
- **多视图**: Board、List、Timeline

## Quick Start
获取API Token：Settings→API Tokens

```bash
# 安装CLI
npm install -g @useshortcut/shortcut-cli
```

```bash
# 创建Story
sc story create --name "实现用户登录" --epic-id 123 --workflow-state-id 500

# 搜索
sc story search "登录"

# 列表
sc story list --epic 123
```

Python API：
```python
import shortcut

client = shortcut.Client(api_key="xxx")

# 列出所有Stories
stories = client.stories.list(workflow_state_id=500)

# 创建
story = client.stories.create(
    name="实现注册功能",
    epic_id=123,
    estimate=3
)
```

## Pitfalls
- API Rate Limit：每秒10请求，注意批量操作间隔
- Webhook重试：失败最多重试72小时，需幂等处理
- 状态ID非固定：迁移环境时ID会变，用名称更稳定
- Story删除后不可恢复，Epic删除保留Stories
