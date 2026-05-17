---
name: smol-agents
description: SmolAgents轻量Agent框架
version: 1.0.0
---

# SmolAgents — Hugging Face轻量Agent框架

## When to Use
- 需要轻量级、本地运行的Agent
- Hugging Face生态集成
- 资源受限环境

## Core Features
- **轻量设计**：最小依赖，快速启动
- **Hugging Face集成**：直接使用HF模型/数据集
- **本地运行**：无需云端，本地LLM支持
- **工具定义**：简洁的Python装饰器定义工具
- **多Agent**：支持Agent间协作

## Quick Start
```python
from smolagents import Agent, tool

@tool
def search_web(query: str) -> str:
    """搜索网页"""
    # 实现搜索逻辑
    return result

agent = Agent(
    model="meta-llama/Llama-3.2-3B-Instruct",
    tools=[search_web]
)

agent.run("帮我搜索最新的AI新闻")
```

## Pitfalls
- 本地模型性能有限
- 工具生态不如LangChain丰富
- 调试信息不完善
- 长对话上下文管理简陋
- 生产环境需要额外监控
