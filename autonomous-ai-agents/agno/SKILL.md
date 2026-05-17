---
name: agno
description: Agno多模态Agent框架
version: 1.0.0
---

# Agno — 多模态AI Agent框架

## When to Use
- 需要多模态理解（文本/图像/音频）
- 复杂向量检索场景
- 生产级Agent应用

## Core Features
- **多模态支持**：文本/图像/音频统一处理
- **向量存储**：内置向量数据库集成
- **工具调用**：灵活的函数调用机制
- **记忆管理**：长期/短期记忆分离
- **团队协作**：多Agent分工

## Quick Start
```python
from agno import Agent, VectorStore

# 创建Agent
agent = Agent(
    model="gpt-4o",
    vector_store=VectorStore("chroma"),
    tools=[search, calculator]
)

# 多模态输入
agent.run("分析这张图片", images=["chart.png"])

# 向量检索增强
agent.remember("上次讨论的内容")
```

## Pitfalls
- 向量存储配置复杂
- 多模态模型调用成本高
- 工具返回格式需要严格定义
- 生产环境性能调优难度大
- 依赖版本兼容性
