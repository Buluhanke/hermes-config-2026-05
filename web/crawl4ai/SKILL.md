---
name: crawl4ai
description: Crawl4AI — GitHub 73.6K⭐开源网页爬虫，网页→干净Markdown，专为大模型优化。触发：需要抓取网页并转为干净格式/RAG数据准备/结构化提取/大模型友好爬虫。
triggers:
  - 爬取网页转为markdown
  - RAG数据准备
  - 网页去噪清洗
  - 结构化数据提取
  - llm友好爬虫
  - crawl4ai
  - 网页转markdown
version: 1.0.0
---

## 安装

```bash
pip install -U crawl4ai
crawl4ai-setup
crawl4ai-doctor
# 如遇浏览器问题
python -m playwright install --with-deps chromium
```

## 核心用法

### Python API（推荐）

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)          # 干净Markdown
        print(result.html)              # 原始HTML
        print(result.metadata)          # 元数据
```

### CLI

```bash
# 基础爬取
crwl https://example.com -o markdown

# 深度爬取（最多10页）
crwl https://docs.example.com --deep-crawl bfs --max-pages 10

# LLM提取（指定问题）
crwl https://example.com/products -q "Extract all product prices"
```

### LLM结构化提取

```python
result = await crawler.arun(
    url="https://example.com",
    prompt="Extract all product names and prices",
    schema={"type": "object", "properties": {...}}
)
```

## 与现有工具的关系

| 工具 | 适合场景 | vs Crawl4AI |
|------|----------|-------------|
| `web_extract` | 简单页面+PDF | 无JS渲染，快速 |
| `browser_navigate` | 需交互的页面 | 返回DOM树，非Markdown |
| **Crawl4AI** | 干净Markdown+RAG | 去噪+结构化+大模型友好 |

## 注意事项

- **必须用terminal运行**，execute_code沙盒无浏览器支持
- Docker版本有但用户Docker禁令有效，不使用Docker安装
- 首次安装需要跑`crawl4ai-setup`初始化Playwright浏览器
- 支持CSS选择器/XPath快速提取，适合重复性子页面抓取
- 认证网站支持cookie/session持久化

## 验证安装

```bash
python3 -c "from crawl4ai import AsyncWebCrawler; print('crawl4ai OK')"
crwl --help
```
