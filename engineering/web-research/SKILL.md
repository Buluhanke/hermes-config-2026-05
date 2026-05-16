---
name: web-research
description: 联网研究流程 — 遇到不熟悉的领域，默认走搜索→提取→总结流程，不依赖模型记忆。
triggers:
  - "遇到不确定的事实类信息"
  - "需要了解某个领域"
  - "需要对比多个来源的信息"
  - "模型知识覆盖不了的领域"
---

## 流程（4步）

```
用户问题
  ↓
① 搜索：_search() — Bing RSS / Serper / Tavily / MiniMax（按 key 情况自动选）
  ↓
② 提取：_curl_extract() — 并发抓页面，取 <p> 段落
  ↓
③ 过滤：过滤 content < 50字的低质量结果
  ↓
④ 总结：_summarize() — 有 MiniMax key 则调用，否则返回摘录
  ↓
输出：{conclusion, sources, search_time_ms, cached}
```

**注意**：此 skill 是**函数调用**模式（`from web_research import research`），不是 agent tool 模式。
`web_search_plus` 是主 agent 内置 tool，如需在对话中搜索，**直接让我调用工具**，比走 skill 更快。

## 设计原则

- 每次最多3个来源（速度+context平衡）
- 优先来源：官方文档 > 行业站点 > 博客 > 论坛
- 结论在前，来源在后，不刷屏
- 遇到不确定的领域自动触发，不需要用户说"帮我搜"

## 快速开始

```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/engineering")
from web_research import research

result = research("Mac mini M4 外接显示器推荐")
print(result["conclusion"])
for src in result["sources"]:
    print(f"- {src['title']}: {src['url']}")
```

## 返回格式

```python
{
    "conclusion": "关键结论（2-3句话）",
    "sources": [
        {"title": "来源标题", "url": "链接", "relevance": "高/中/低"}
    ],
    "search_time_ms": 3200
}
```

## 搜索策略（免费优先，自动 fallback）

```
有 MINIMAX_API_KEY  → MiniMax 内置搜索（质量最高）
有 SERPER_API_KEY   → Serper（2500次/月免费）
有 TAVILY_API_KEY   → Tavily（1000次/月免费）
否则                → Bing RSS（完全免费，无需key）
```

**Bing RSS 方案**：`https://www.bing.com/search?q={query}&format=rss&mkt=zh-CN`
- 用 `xml.etree.ElementTree` 解析 RSS，提取 title/link/description
- 依赖 `urllib.parse` + `subprocess` 的 curl，无需任何 key
- 已知限制：description 字段内容质量不稳定，部分结果标题相关但描述弱或为空

**重要**：`web_search_plus` 是 agent 内置 tool（工具调用），不是 Python 模块，skill 内无法通过 `import` 调用。skill 层的搜索必须走上述 curl/requests 方式。**如果需要在 agent 对话中搜索，直接让我调用 `web_search_plus` 工具即可**，无需走 skill。
