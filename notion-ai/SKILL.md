---
name: notion-ai
description: Notion AI写作助手，摘要、翻译、action items提取
version: 1.0.0
category: productivity
---

# Notion AI

## When to Use
使用Notion整理笔记、写文档、做知识管理时。需要快速摘要、翻译或提取关键任务。

## Core Features
- **写作助手**：续写、润色、翻译
- **摘要生成**：一键生成文档/会议摘要
- **翻译**：多语言即时翻译
- **Action Items**：从文本提取待办事项
- **问答**：针对页面内容的自然语言问答

## Quick Start
```bash
# Notion内直接调用
# 1. 选中文本或点击"/"唤起
# 2. 输入"摘要"、"翻译"、"提取待办"
# 3. AI即时处理

# API集成
curl -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28"
```

## Pitfalls
- 需要Notion AI付费订阅
- 中文处理质量不如英文
- API调用有频率限制
- 处理长文档需分步执行