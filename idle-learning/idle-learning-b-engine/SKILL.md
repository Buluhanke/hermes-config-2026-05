---
name: idle-learning-b-engine
description: "B阶段执行层：web_search为骨干并行多源浏览→fact_store写入，不依赖特定key。"
triggers:
  - 开始自学
  - 出门学习
  - B阶段
  - idle learning
tags: [idle-learning, multi-source, web-search, fact-store]
created: 2026-08-01
---

# B阶段：多源并行浏览 → fact_store写入

## 核心原则

**不要等 key 配好再出门，外面全是实时活知识。**

B阶段是多源并行阶段。如果某个渠道失效，立即切换到其他渠道，不等不靠不解释。

## 执行流程

### Step 0：PATH前提
opencli 安装在 `~/.local/bin/opencli`，但 subprocess/PATH 默认找不到。
**必须用绝对路径** `~/.local/bin/opencli`，或先 `export PATH="$HOME/.local/bin:$PATH"`。

### Step 1：并行发起查询（同时，不要串行）

用 execute_code 并行发起查询：

```python
from hermes_tools import web_search

queries = [
    "AI LLM 2026 latest research breakthrough",
    "Hugging Face trending models 2026",
    "AI agent 2026 latest news",
]
for q in queries:
    r = web_search(query=q, limit=5)
```

### Step 2：关键文章精读

从搜索结果中选2-3篇最有价值的，用 web_extract 批量抓取全文。

### Step 3：fact_store写入

核心洞察写入 fact_store，每条一个具体事实（content具体、含关键数据）。

## 平台可用性状态（2026-08-07实测）

| 平台 | 工具 | 状态 | 备注 |
|------|------|------|------|
| web_search + web_extract | 通用搜索 | ✅ | 骨干渠道，opencli 1.8.6已升 |
| HackerNews | opencli | ✅ | show/ask可用 |
| arxiv | opencli | ⚠️ | 429限流，批量查触发 |
| GitHub | gh CLI | ✅ | 直接用 |
| Nous Portal (hy3:free) | Nous API | ❌ | 429服务端限流，免费额度耗尽 |
| Groq/Cerebras/NVIDIA NIM | API | ❌ | 国内封禁/证书错误 |
| Reddit/微博 | opencli | ❌ | 需Browser Bridge |

**npm包已升级（2026-08-07）：** opencli 1.8.6, searxng-mcp 1.1.0, repomix 1.18.0, playwright 1.62.1

## 升华

fact_store写入后：
```bash
python3 ~/.hermes/scripts/abcd_learner.py
```
