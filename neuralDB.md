---
name: neuralDB
description: NeuralDB结构化知识存储，支持多模态向量检索
version: 1.0.0
---

# NeuralDB — 结构化知识存储

## When to Use
需要将结构化数据与向量检索结合时。适合知识图谱构建、事实存储与问答、多模态文档管理。传统向量库只存chunk，NeuralDB可以存实体和关系。

## Core Features
- **结构化+非结构混合**: 同时存储实体、关系和自由文本
- **多模态支持**: 文本、图像URL、表格均可存入
- **属性过滤**: 支持元数据条件过滤后再向量检索
- **实体链接**: 自动将文本中的实体关联到知识图谱
- **查询API**: REST API + Python SDK

## Quick Start
```bash
pip install neuraldb-client
```

```python
from neuraldb import NeuralDB

ndb = NeuralDB(api_key="xxx", org_id="org_xxx")

# 创建知识库
kb = ndb.create_knowledge_base("产品文档")

# 添加结构化事实
kb.add({
    "type": "fact",
    "subject": "产品A",
    "predicate": "适用于",
    "object": "中小企业",
    "embedding_text": "产品A主要面向中小企业用户"
})

# 检索
results = kb.search("哪些产品适合中小企业？", top_k=5)
```

## Pitfalls
- Schema设计要提前规划，迁移成本高
- 向量维度默认1536（OpenAI），切换模型需重建索引
- 多租户隔离：确认org_id权限划分
- 冷启动无数据时返回空，注意降级
