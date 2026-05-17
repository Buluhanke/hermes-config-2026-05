---
name: agentkit
description: AgentKit连接AI的Agent工具包，17C工具与LangChain集成
version: 1.0.0
---

# AgentKit — Cohere的Agent工具包

## When to Use
使用Cohere Command/R/Nightmare模型构建Agent时。适合需要预置工具集、快速集成LLM到应用中的场景。17C工具开箱即用，减少重复造轮子。

## Core Features
- **17C预置工具**: 搜索、计算、代码执行、文件操作等
- **LangChain集成**: 方便对接LangChain生态
- **工具编排**: 支持工具链和依赖管理
- **多模型兼容**: 主要面向Cohere，也可扩展其他
- **Webhooks**: 异步工具回调支持

## Quick Start
```bash
pip install agentkit langchain-cohere
```

```python
from agentkit import Agent, Tool
from agentkit.tools import web_search, calculator

# 创建Agent
agent = Agent(
    model="command-r-plus",
    tools=[web_search, calculator],
    api_key="xxx"
)

# 对话
response = agent.chat("查找北京今天天气并转为华氏度")
```

自定义工具：
```python
@Tool定义自定义工具
@Tool(name="get_price", description="获取商品价格")
def get_price(product: str) -> float:
    return 99.99

agent = Agent(model="command-r", tools=[get_price])
```

## Pitfalls
- 主要针对Cohere模型，其他模型支持有限
- 17C工具中部分需要外部API（搜索等），注意配额
- LangChain集成版本兼容性需注意
- 工具描述影响LLM调用准确性，需精心编写
