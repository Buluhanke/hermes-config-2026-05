---
name: community-learning
version: 0.1
description: "社区真实知识转fact_store+skill HN Reddit V2EX。Use when 从技术社区挖实践经验入库"
trigger_type: idle_learning
tags: [idle-learning, community, clawhub, skill-acquisition]
created: 2026-07-25
---

# Community Learning

## 核心理念

自我学习 = ABCD 流水线 + **F 社区获取**。不跑 F 步骤不算完成学习。

## F 步骤

```bash
# 1. 搜索 clawhub（最大社区市场，90K+ skills）
hermes skills search "<主题>" --source clawhub --limit 5 --json

# 2. 搜索 github
hermes skills search "<主题>" --source github --limit 5 --json

# 3. 预览有价值 skill
hermes skills inspect <identifier>

# 4. 直接安装（必须加 --yes）
hermes skills install <identifier> --yes

# 5. 知识内容写入 fact_store
sqlite3 ~/.hermes/memory_store.db "INSERT INTO facts ... category='community-insight', trust_score=0.75 ..."
```

## 社区来源

| 来源 | 命令 | 说明 |
|------|------|------|
| clawhub | `--source clawhub` | 最大，90K+ skills |
| github | `--source github` | GitHub 直接装 |
| huggingface | `--source huggingface` | HF 官方 |

## 坑

- `--yes` 必须加，否则卡住
- caution verdict 被安全扫描拦截可用 `--force`（不推荐）
- browse --source community 输出为空，用 `search` 代替
- nvidia-cuda 因 caution verdict 被拦（2026-07-25 实测）
