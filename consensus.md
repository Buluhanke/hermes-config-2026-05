---
name: consensus
description: Consensus — AI论文搜索，Y/N/P回答与Cite Score
version: 1.0.0
---

# Consensus

## When to Use
需要进行学术论文搜索、以AI直接回答Yes/No/Probably问题、查看论文质量指标时使用。适合研究人员和学生。

## Core Features
- **AI论文搜索**：自然语言搜索学术论文
- **Y/N/P回答**：直接给出是/否/可能答案及依据
- **Cite Score**：论文引用分数，质量指标
- **多源整合**：arXiv、PubMed、Semantic Scholar等
- **摘要生成**：AI生成论文摘要
- **API访问**：开发者API接入

## Quick Start
```bash
# Web访问
# https://consensus.app

# 搜索示例
# "Does LLM hallucination improve with chain-of-thought?"
# AI返回：Yes - 78% of papers agree

# API使用
# 获取API Key: https://consensus.app/settings/api

curl "https://api.consensus.app/v1/search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"query": "LLM evaluation methods", "type": "y_n_p"}'

# Python SDK
pip install consensus-python
```

## Pitfalls
- 免费搜索有限额，API调用需付费
- Y/N/P答案基于论文统计，非绝对真理
- 论文库覆盖有盲区
- Cite Score不等于论文质量
- API文档更新较快，需查最新版本
