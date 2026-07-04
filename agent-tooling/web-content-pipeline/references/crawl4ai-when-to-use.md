# crawl4ai 真使用场景 (避免无脑用)

## ⚠️ 第一原则

**crawl4ai 是 rung 6，不是默认。** fetch_url + agent-reach 90% 场景就够，crawl4ai 是**真缺口时的兜底**。

## ✅ 何时用 crawl4ai (2026-06-27 实测)

### 场景 1: SPA 完整 JS 渲染

```python
from crawl4ai import AsyncWebCrawler

async def t():
    async with AsyncWebCrawler() as c:
        r = await c.arun(url="https://spa-site.com")
        # r.markdown 是 JS 渲染后内容
asyncio.run(t())
```

**适用**: React/Vue/Angular SPA, fetch_url 的 Playwright 升级还不够时
**延迟**: 5-15 秒（JS 渲染 + 等待异步加载）

### 场景 2: BM25 内容过滤

```python
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=BM25ContentFilter(query="neural network")
    )
)
```

**适用**: 长页面（如博客/文档）需要 BM25 算法过滤相关段落
**触发词**: "找博客里讲 X 的部分 / 提取相关章节"

### 场景 3: LLM 驱动结构化提取

```python
from pydantic import BaseModel
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class Product(BaseModel):
    name: str
    price: float
    url: str

strategy = LLMExtractionStrategy(
    provider="openai/gpt-4o-mini",
    schema=Product.schema()
)
```

**适用**: 提取产品列表/价格/库存 → JSON schema
**注意**: **按 token 收费**，不是免费的 fallback

## ❌ 何时不用 crawl4ai

| 场景 | 应该用 | 原因 |
|---|---|---|
| 普通博客/新闻 | `fetch_url.py` | Trafilatura 5x 快 + 免费 |
| YouTube 字幕 | `fetch_transcript.py` | 专做字幕 |
| 静态文档站 | `fetch_url.py` + upgrade | Playwright 升级足够 |
| 多平台统一入口 | `agent-reach` | 8 渠道直接路由 |
| 高频抓取（>10 RPS） | scrapling stealth | crawl4ai 启动慢 |

## 🛠️ 安装

```bash
# 装到 hermes venv（agent 用）
~/.hermes/hermes-agent/venv/bin/pip install crawl4ai

# 必须装 playwright 浏览器
python3 -m playwright install --with-deps chromium
```

**当前已装**: crawl4ai 0.9.0 在 hermes venv（2026-06-27）

## 🐍 已知坑

1. **Python 3.14 vs 3.11 兼容** — 0.9.0 要 3.11，装到 3.14 venv 报 ModuleNotFoundError
2. **Playwright 浏览器必须额外装** — `python3 -m playwright install chromium`
3. **API 文档** 0.9.0 重构多次, 老 API 失效

## 📊 性能基准

| 工具 | 启动 | 普通页 | SPA | 收费 |
|---|---|---|---|---|
| fetch_url (Trafilatura) | 0ms | 200-500ms | ❌ | 免费 |
| fetch_url (Playwright 升级) | 0ms | 3-5s | 3-5s | 免费 |
| crawl4ai (basic) | 5-10s | 3-8s | 5-15s | 免费 |
| crawl4ai (LLM extract) | 5-10s | 10-30s | 15-30s | 按 token 算 |

## 触发词

"crawl4ai 什么时候用 / JS 渲染怎么办 / SPA / BM25 / 结构化提取 / LLM 提取" → 0 思考本 skill