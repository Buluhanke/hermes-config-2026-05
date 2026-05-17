---
name: marvin
description: Marvin类型安全AI框架，工具调用与LLM接口
version: 1.0.0
---

# Marvin — 类型安全AI框架

## When to Use
需要类型安全Agent、严格输出格式控制时。适合Pydantic集成、复杂工具调用链、静态类型项目。相比其他框架，Marvin的Fn和Agent基于类型推导而非提示词。

## Core Features
- **Fn（Function）**: 基于类型注解的AI函数，返回值自动类型校验
- **Agent**: 有状态对话Agent，支持工具调用
- **Classifier**: 多分类器，适合意图识别
- **ImageClassifier**: 多模态图像分类
- **纯Python**: 无额外DSL，贴近Pythonic风格
- **流式输出**: 支持stream模式实时返回

## Quick Start
```bash
pip install marvin
export MARVIN_OPENAI_API_KEY="xxx"
```

```python
import marvin

# 类型化的AI函数
@marvin.fn
def classify_email(subject: str, body: str) -> str:
    """根据邮件主题和内容分类：urgent/normal/spam"""

# 直接调用
result = classify_email("紧急：服务器宕机！", "生产环境故障...")
# -> "urgent"
```

带工具的Agent：
```python
@marvin.agent
class DataAgent:
    @marvin.tool
    def search_db(self, query: str) -> list:
        """执行SQL查询"""
        return [{"id": 1, "name": "Alice"}]

    def analyze(self, question: str) -> str:
        """分析数据回答问题"""

agent = DataAgent()
result = agent.analyze("有多少用户？")
```

## Pitfalls
- 类型注解过于复杂会导致LLM解析失败
- 错误处理：LLM返回非预期格式时Fn会抛异常
- API Key必须设环境变量，不支持参数传入
- 分类器需要足量标注数据效果才好
