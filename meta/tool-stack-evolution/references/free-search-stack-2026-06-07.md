# Free Search Stack Evolution — 2026-06-07 实例

本文档是 `tool-stack-evolution` skill 中"5 步进化流程"的完整实例，
展示如何从"v1 修补"走到"v2 进化"。

## 起点：v1 fetch_url.py 修补

**触发**：`web_extract` 后端 = `searxng`，公网实例连不通 → 提取 URL 全文失败。

**v1 修补做法**（错误示范）：
- 自己写 html2text + stdlib regex 提取器
- 自己写 JSON 文件缓存
- 命名 `fetch_url.py`，落 `~/.hermes/scripts/`
- 跑起来能用，但 GitHub 页面提取出来是 nav 垃圾

## 进化：v2 走 5 步流程

### Step 1 — 盘点当下栈

| 位置 | v1 方案 | 已知短板 |
|------|---------|----------|
| 搜索主路 | anysearch | 偶尔慢 |
| URL 提取 | html2text + stdlib | GitHub 类重 JS 页面提取出 nav 垃圾 |
| 缓存 | JSON 文件 24h | 无 LRU、无原子写、并发不安全 |
| 社媒舆情 | last30days | 60s 慢但能用 |
| web_extract 后端 | searxng 公网 | **本机全连不通**（最大痛点） |

### Step 2 — 全网搜索候选

5 个 web_search 调用，分别搜：

| 搜索词 | 命中候选 |
|--------|----------|
| `best free web scraping markdown extraction tool 2026 open source` | Open-Source Web Scraping to Markdown for AI 2026 文章、awesome-web-scraping-2026、Firecrawl blog、11 best open-source web crawlers and scrapers |
| `Crawl4AI vs Jina Reader vs Firecrawl free open source 2026 benchmark` | toolhalla 三方对比、Spider blog、Slashdot comparison、crawl4ai-vs-firecrawl 2026 |
| `Jina Reader API free tier 2026 limit no key r.jina.ai` | Jina Reader 主页、serp.fast 评测、GitHub jina-ai/reader |
| `SearXNG public instance list 2026 best free metasearch engine uptime` | searx.space、searx.tiekoetter.com、hermes-agent docs |
| `DDGS duckduckgo search python library rate limit 2026 still works alternative` | duckduckgo-search PyPI、open-webui ratelimit 讨论、hermes-agent duckduckgo-search skill |
| `Brave Search API free tier 2000 requests per month AI agent` | Brave Search API 主页、AgentDeals 2026 free tier killed、implicator.ai 2/18 报道 |
| `Trafilatura python web content extraction benchmark vs BeautifulSoup readability-lxml 2026` | Trafilatura 官方 Evaluation、mdisbetter 三方对比、scrapinghub benchmark |
| `awesome self-hosted search engine list 2026 SearXNG Whoogle Yacy YaCy` | awesome-selfhosted GitHub、openalternative.co、wgall.com 2026 guide |
| `Kagi Brave Search free API alternative 2026` | openclaw/openclaw #11399（web_search providers via plugins） |
| `free in-process cache library python 2026 diskcache sqlite vs fakeredis vs cachetools` | cachetools PyPI、LibHunt cachetools-vs-johnny-cache、fakeredis GitHub |

### Step 3 — 本机实测筛选（淘汰清单）

| 候选 | 实测结果 | 决策 |
|------|----------|------|
| **Jina Reader** (`r.jina.ai`) | `curl -v` 显示 DNS 解析到 `157.240.2.36`（Facebook IP），10s 连接超时 | ❌ 排除 |
| **Brave Search API** | 搜索结果显示"Free tier (2,000 queries/month) eliminated" (2026/2) | ❌ 排除 |
| **SearXNG 公共实例** | 试 5 个（searx.be / search.sapti.me / searx.tiekoetter.com / priv.au / search.bus-hit.me），5/5 NOT JSON 响应 | ❌ 排除 |
| **Crawl4AI** | 依赖 Playwright，太重，本机没装 | ❌ 排除（暂缓） |
| **Readability-lxml** | 被 Trafilatura 在 scrapinghub benchmark 击败 | ❌ 排除 |
| **Trafilatura 2.0.0** | `uv pip install` 成功；用 `trafilatura.extract(html, output_format="markdown")` 实测 GitHub 页面 → 输出干净的项目描述 | ✅ **采用** |
| **DiskCache 5.6.3** | `uv pip install` 成功；benchmark 1000 写 0.063s、1000 读 0.003s、TTL 自动过期 | ✅ **采用** |
| **cachetools** | 仅 in-memory，无持久化 | ❌ 排除 |
| **fakeredis** | 测试用，不适合生产 | ❌ 排除 |
| **anysearch** | 5s 给 5 条精准结果 | ✅ 保持 |
| **last30days** | 60s 4 源真结果 | ✅ 保持 |
| **DDGS (ddgs)** | 5s 给 5 条结果 | ✅ 保持（兜底） |

### Step 4 — 决策表

| 位置 | v1 方案 | v2 方案（进化后）| 关键证据 |
|------|---------|------------------|----------|
| URL 提取 | html2text + stdlib | **Trafilatura 2.0.0** | 同一 URL 提取从"100% nav 垃圾"→"真正正文" |
| 缓存 | JSON 文件 24h | **DiskCache 5.6.3** | 1000 写 0.063s vs 1s+ |
| 搜索主路 | anysearch | 保持 | 无更强免费替代 |
| 搜索兜底 | DDGS | 保持 | 无更强免费替代 |
| 社媒舆情 | last30days | 保持 | 无更强免费替代 |
| web_extract 后端 | searxng | **弃用，改用 fetch_url 替代** | 公网实例全挂 |

### Step 5 — 替换而非叠加

`~/.hermes/scripts/fetch_url.py` **整个文件**重写为 v2：

```bash
# v1 旧版
$ du -h ~/.hermes/scripts/fetch_url.py
8.3K

# v2 新版
$ du -h ~/.hermes/scripts/fetch_url.py
8.9K  # 略大，但加了三层降级 + DiskCache

# 不是 v1 之上加 if-else
# 是 v1 整个删了，用 Trafilatura + DiskCache 写新的
```

旧 JSON 缓存目录 `~/.hermes/cache/fetch_url/` 直接 `rm -rf`，不留死代码。

## 验证（v2 落地后实测）

| 场景 | 耗时 | 结果 |
|------|------|------|
| `fetch_url.py "https://github.com/NousResearch/hermes-agent"` 首次 | ~3s | Trafilatura 输出 6299 字符真实正文 |
| `fetch_url.py "https://github.com/NousResearch/hermes-agent"` 第 2 次 | **0.159s** | DiskCache 命中 |
| `search.py "DeepSeek V4 发布"` 首次 | 4.6s | anysearch 5 条 + 写 DiskCache |
| `search.py "DeepSeek V4 发布"` 第 2 次 | **0.035s** | DiskCache 命中 |

## 关键铁律（本实例产出的）

1. **GitHub 上 star 多 ≠ 能用**——Jina Reader 看起来是 GitHub trending，实测本机连不通
2. **必须本机跑通才算候选**——`curl -v` 看真实 DNS 解析和连接超时
3. **替换而非叠加**——v1 的 html2text 代码全删，不留 fallback
4. **排除清单写下来**——Jina Reader/Brave/SearXNG/Crawl4AI/Readability-lxml 都进了"下次别重测"名单
5. **决策表公开可追溯**——5 个位置 × 5 个候选，2 个赢家，不是"我觉得"

## 相关 skill 维护记录

- `unified-search-routing` v2.0.0 → v3.0.0：fetch_url v1 → v2，search.py v3 → v3.1
- `tool-stack-evolution` v1.0.0：本文档是其首个完整实例
- `macos-computer-use` v1.0.0 → v1.1.0：补充"macOS GUI 自动化生态"小节，避免重复 Peekaboo 装
