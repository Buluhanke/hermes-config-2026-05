---
name: mem0
description: Mem0个性化长期记忆层，AI应用的记忆管理
version: 1.0.0
---

# Mem0 — 个性化长期记忆层

## When to Use
需要为AI应用添加用户级记忆、跨会话个性化上下文时。适合RAG替代方案、Agent记忆管理、用户偏好持久化。向量数据库存储的是静态文档，Mem0存储的是动态的用户交互历史。

## Core Features
- **个性化记忆**: 基于用户ID的长期记忆存储与检索
- **层级记忆**: 用户→会话→消息三级记忆粒度
- **向量+语义搜索**: 混合检索，支持自然语言查询
- **记忆管理API**: 添加、搜索、删除、更新记忆
- **多后端支持**: OpenAI/Anthropic/本地模型

## Quick Start
```bash
pip install mem0ai
```

```python
from mem0 import Memory

client = Memory(api_key="xxx")

# 存储记忆
client.add("用户喜欢简洁的设计风格", user_id="alice")

# 检索记忆
results = client.search("用户的设计偏好是什么？", user_id="alice")

# 查看全部记忆
all_memories = client.get_all(user_id="alice")
```

API Key管理：通过环境变量`MEM0_API_KEY`更安全，或通过`OPENAI_API_KEY`使用OpenAI embedding。

## Pitfalls
- 免费额度有限，生产环境需配置计费
- 记忆膨胀：定期清理无关记忆，避免检索质量下降
- 隐私：不要存储敏感个人信息，Mem0服务器端存储
- 冷启动：新用户无记忆时需降级处理
