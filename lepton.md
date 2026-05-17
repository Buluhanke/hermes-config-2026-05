---
name: lepton
description: Lepton AI搜索增强与Phidata集成用法指南
version: 1.0.0
---

# Lepton AI

## When to Use
需要搜索增强的AI应用、与Phidata框架集成、自定义工具调用时使用。

## Core Features
- **搜索增强**：内置Web Search集成，提升LLM实时信息获取
- **Phidata集成**：支持Phidata Agent Framework
- **自定义工具**：灵活定义函数工具供LLM调用
- **低价高效**：按Token计费，成本可控

## Quick Start
```python
# 基本搜索调用
from leptonai import Photon

# 搜索增强示例
payload = {
    "query": "今天比特币价格",
    "search": True,  # 启用搜索增强
    "model": "llama-3.1-70b"
}

# Phidata集成
# 参考文档：https://www.phidata.com/providers/lepton
```

## Pitfalls
- 搜索增强会增加响应延迟
- 自定义工具需正确编写schema
- 国内访问建议配置代理