---
name: pydantic-ai
description: PydanticAI类型安全Agent框架
version: 1.0.0
---

# PydanticAI — 类型安全Agent框架

## When to Use
- 需要严格类型安全的AI应用
- OpenAI兼容接口迁移
- 结构化输出验证

## Core Features
- **类型安全**：Pydantic模型定义输入输出
- **OpenAI兼容**：API兼容，可切换模型
- **结构化输出**：强制输出符合Schema
- **验证机制**：自动校验LLM输出
- **依赖注入**：灵活的依赖管理

## Quick Start
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

class Response(BaseModel):
    title: str
    score: float
    summary: str

agent = Agent(
    model="openai:gpt-4o",
    result_type=Response
)

result = agent.run("推荐一部科幻电影")
# result 自动为 Response 类型
```

## Pitfalls
- Pydantic模型设计复杂
- 部分模型不支持结构化输出
- 验证失败需要重试逻辑
- 性能开销比纯文本稍高
- 调试类型错误较困难
