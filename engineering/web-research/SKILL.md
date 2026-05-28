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

**重要**：`web_search_plus` 是 agent 内置 tool（工具调用），不是 Python 模块，skill 层无法通过 `import` 调用。**如果需要在 agent 对话中搜索，直接让我调用 `web_search_plus` 工具即可**，无需走 skill。

## 页面内容提取（免费方案，按优先级）

当需要获取某个URL的页面内容时，按以下顺序尝试：

```
① web_extract()  — 免费，需抓取5个以内页面
   注意：firecrawl托管的页面可能收费，失败返回 "Payment Required"
   失败时直接跳到方案②，不浪费时间

② browser_navigate() + browser_console JS提取  — 推荐方案
   无需任何API key，绕过Firecrawl限制
   长页面用JS分段提取，比snapshot可靠

③ browser_navigate() snapshot  — 后备方案
   适合短页面，8000字符以内
   超过8000字符会被截断，snapshot实质不完整

④ mcp_chrome_chrome_navigate()  — MCP chrome工具
   需确保mcp-chrome-stdio进程运行中
```

**browser_navigate + JS提取（推荐，Firecrawl不可用时首选项）：**

```
browser_navigate(url="https://example.com/long-article")

# 方案A：提取文章主体内容（最常用）
browser_console(
  expression='document.querySelector("article").innerText.slice(0, 5000)'
)
# ↓
browser_console(
  expression='document.querySelector("article").innerText.slice(5000, 10000)'
)

# 方案B：提取整个页面文本
browser_console(
  expression='document.body.innerText.slice(0, 50000)'
)

# 方案C：提取特定区域
browser_console(
  expression='document.querySelector(".content").innerText'
)
```

**为什么优先用 JS 提取而非 scroll + snapshot：**
- browser_snapshot 有硬 8000 字符截断，且对长页面返回的内容可能在滚动后仍然被截断（内容重复，出现 "N more lines truncated" 且滚动后 snapshot 返回相同内容）
- browser_console 返回完整 JS 执行结果，不截断
- JS 提取只占用一次 tool call，scroll+snapshot 需要多次且可能白费

**已知限制：**
- article/body 选择器不是所有页面都适用（一些页面用 div.content、main、#root）
- 单次 browser_console 返回上限约 50KB，极长页面需分片
- mcp_chrome_stdio需要进程运行中，否则报"Failed to connect to MCP server"
- 某些页面有反爬（stealth_warning提示），内容可能受限
