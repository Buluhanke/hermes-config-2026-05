---
name: griptape
description: Griptape企业级Agent框架，管道式工作流与记忆管理
version: 1.0.0
---

# Griptape — 企业级Agent框架

## When to Use
构建复杂企业级Agent、需要管道式工作流时。适合多步骤推理、长时记忆、工具调用、多Agent协作。相比轻量级框架更适合生产环境。

## Core Features
- **管道架构**: Task→Pipeline→Workflow三级组织
- **结构化工具**: @tool装饰器定义工具，类型安全
- **记忆系统**: SessionMemory、TaskMemory、LongTermMemory
- **多模型支持**: OpenAI、Anthropic、Azure OpenAI、Local
- **持久化**: SQLite/Postgres持久化工作流状态
- **日志与监控**: 内置结构化日志，完整执行追溯

## Quick Start
```bash
pip install griptape
```

```python
from griptape import Pipeline, Task
from griptape.tools import WebSearch, Calculator

pipeline = Pipeline(
    tasks=[
        Task(
            name="research",
            tool=WebSearch(),
            input="研究一下最新的AI Agent框架"
        ),
        Task(
            name="analyze",
            tool=Calculator(),
            input="分析市场规模并计算增长率"
        )
    ]
)

# 串联执行
result = pipeline.run()
```

定义工具：
```python
from griptape import tool

@tool
def get_weather(city: str) -> str:
    return f"{city}今天晴天，25度"
```

## Pitfalls
- 学习曲线较陡，Pipeline概念需要适应
- 状态持久化默认SQLite，生产换Postgres
- 工具错误不会自动重试，需手动处理
- 多Task并发时注意共享状态竞争
