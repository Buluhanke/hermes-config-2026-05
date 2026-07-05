---
name: web-content-pipeline
description: 网页内容提取统一管线 — fetch_url.py (Trafilatura v2 + Playwright upgrade) / defuddle (kepano Reader-Mode, 0.19.1, JS 渲染内置, 节省~45% token) / fetch_transcript.py (YouTube via youtube-transcript-api, B站 via yt-dlp) / agent-reach (8/13 渠道统一调度) / crawl4ai (复杂 JS 爬虫) 五层 fallback 链。Load when user asks "抓这个网页内容 / 读这个 YouTube 字幕 / 抓这个页面 / 解析这个 URL / 提取这篇博客 / 抓取数据 / 读 B 站视频 / B站字幕 / 看 YouTube 文案 / 网页爬虫" 任意一条。
version: 1.1.0
created: 2026-06-27
category: agent-tooling
type: capability
triggers:
  - "抓网页"
  - "读 URL 内容"
  - "提取网页"
  - "读 YouTube 字幕"
  - "读 B 站字幕"
  - "抓取数据"
  - "网页爬虫"
  - "读这篇博客"
  - "读这篇文章"
  - "解析这个页面"
  - "WeChat 文章"
  - "知乎文章"
  - "微信公众号"
metadata:
  hermes:
    tags: [web, scraping, transcript, youtube, bilibili, agent-reach, fetch_url, ponytail]
    related_skills: [ponytail-decision-ladder, proactive-execution, verification-before-reporting]
---

# Web Content Pipeline — 网页内容提取统一管线

## 🎯 这是什么

Hermes 的**网页内容提取**统一管线 —— 5 层 fallback 链，按 URL 类型自动路由到最优工具。**不写新 wrapper**，**只调度已存在的工具**（Ponytail rung 4 真值）。

## 🧰 工具栈（按 rung 排序）

### Rung 4: defuddle（Reader-Mode → npm 0.19.1，JS 渲染内置）
**位置**: `~/.local/bin/defuddle` (npm 全局) + `~/.hermes/skills/{defuddle,kepano-defuddle}/`（hub 装）
**能力**:
- kepano 出品，Node + Readability-like 算法（2026-07-03 装）
- **内置 headless JS 渲染**（puppeteer-core），不需 `--upgrade-to-js`
- 输出纯净 markdown，**实测节省 ~45% token**（22KB fetch_url vs 12KB defuddle 抓同一 URL）
- 强项：Docusaurus / VuePress / Next.js SPA / GitHub README / Medium / 简书
- 必带 `--md`，否则输出 HTML

**用法**:
```bash
defuddle parse https://example.com --md              # 基本
defuddle parse https://example.com --md -o out.md   # 落盘
defuddle parse https://example.com -p title         # 只取元数据
```

**覆盖**: 文档站 + SPA + 侧栏/导航污染严重的博客平台

**详见**: `references/defuddle-usage.md` (实测节省率 + 路由决策表 + 6 类踩坑)

### Rung 4: fetch_url.py v2（普通网页 → Trafilatura）
**位置**: `~/.hermes/scripts/fetch_url.py` (297 行, 已存在)
**能力**:
- Trafilatura 主提取（社区基准 #1）
- DiskCache 24h TTL 缓存
- Playwright 自动升级（Trafilatura 拿不到时 → JS 渲染）
- html2text 兜底
- stdlib HTMLParser 终极兜底

**用法**:
```bash
python3 ~/.hermes/scripts/fetch_url.py https://example.com
python3 ~/.hermes/scripts/fetch_url.py https://zhuanlan.zhihu.com/p/xxx --upgrade-to-js
```

**覆盖**: 普通 HTML、博客、新闻、文档站（**90% 场景**）

### Rung 4: fetch_transcript.py（视频字幕 → youtube-transcript-api + yt-dlp）
**位置**: `~/.hermes/scripts/fetch_transcript.py` (100 行, 2026-06-27 新建)
**能力**:
- YouTube 字幕提取（youtube-transcript-api）
- B 站字幕提取（yt-dlp 双 venv fallback）
- JSON / text 双格式输出
- 时间戳 + snippet 列表

**用法**:
```bash
python3 ~/.hermes/scripts/fetch_transcript.py "https://www.youtube.com/watch?v=XXX" --lang=en --json
python3 ~/.hermes/scripts/fetch_transcript.py "https://www.bilibili.com/video/BVxxx"
```

**覆盖**: YouTube 全字幕（含自动字幕）+ B 站（需 yt-dlp）

### Rung 4: agent-reach（多平台统一入口 → 8/13 渠道）
**位置**: `~/.agent-reach-venv/bin/agent-reach`
**能力**:
- ✅ GitHub 仓库/代码/Issue/PR
- ✅ YouTube 视频和字幕
- ✅ V2EX 节点/主题/回复
- ✅ RSS/Atom 订阅源
- ✅ 全网语义搜索（Exa, 免费, 无 API Key）
- ✅ 任意网页（Jina Reader fallback）
- ✅ Twitter/X 推文（twitter-cli）
- ✅ B 站视频/搜索（bili-cli）

**用法**:
```bash
source ~/.agent-reach-venv/bin/activate
agent-reach doctor                        # 体检
agent-reach transcribe URL --provider groq  # Whisper 转录（需 API key）
agent-reach format < url                  # 格式化输出
```

**覆盖**: 中文站 + 国际站 + 社交媒体（**8/13 渠道直接用**）

### Rung 6: crawl4ai（复杂 JS 爬虫 → AsyncWebCrawler）
**标准安装**: `pip install crawl4ai`（无需本地 venv 路径）

> ⚠️ **Scrapling 弃用提示（2026-07）**: D4Vinci/Scrapling（HTTP/Dynamic/Stealth三层fetch库）自2025-05起停止维护。如需反检测爬取，优先用 Crawl4AI（async、活跃维护）；如需 Scrapling 的stealth/impersonate策略做参考，skill仍可加载，但功能等同于只读存档。

**能力**:
- Python async 爬虫（v0.9.x，2026年持续活跃更新，GitHub #1 trending开源爬虫）
- JS 渲染 + BM25 内容过滤
- 结构化数据提取（LLM 驱动）
- 自托管，无需 API Key（对比 Firecrawl 的付费云服务）

**安装**:
```bash
pip install crawl4ai
crawl4ai-setup  # 自动安装 Playwright 浏览器
```

**用法**:
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

asyncio.run(main())
```

**覆盖**: SPA、React/Vue 渲染、复杂反爬场景（**其他 rung 不够时**才用）

**vs Firecrawl (2026-07-05 更新)**: Crawl4AI 优势是开源免费 + 完全自托管；Firecrawl 今年新增 **Keyless 免费层**（每月 1,000 额度，无需 API Key）和 **MCP 端点** `https://mcp.firecrawl.dev/v2/mcp`，支持 search/scrape/interact 三个接口无密钥使用（crawl/map/agent 仍需 key）。官方文档**明确提及 Hermes Agent** 作为 MCP 兼容客户端。自托管仍必须 Docker（Redis + PostgreSQL + Playwright），本机已禁 Docker 所以不可行。如需增强 JS 页面抓取或结构化提取能力，Firecrawl 的 Keyless API 可作为 web_extract/Crawl4AI 之后的第三备选。评估地址: `https://www.firecrawl.dev/agent-onboarding/SKILL.md`

**详见**: `references/crawl4ai-when-to-use.md`（已含真实使用场景，避免无脑调用）

## 🎯 路由决策表（按 URL 类型）

| URL 模式 | 第一选择 | fallback | 真失败时 |
|---|---|---|---|
| **Docusaurus / VuePress / Next.js SPA 文档** | `defuddle parse --md` | `fetch_url.py --upgrade-to-js` | crawl4ai |
| GitHub README（sidebar 污染） | `defuddle parse --md` | `fetch_url.py` | agent-reach |
| 普通网页（博客/新闻） | `fetch_url.py` | `defuddle`（备用） | crawl4ai |
| YouTube 视频 | `fetch_transcript.py` | yt-dlp 字幕（agent-reach） | agent-reach transcribe (Whisper) |
| B 站视频 | `fetch_transcript.py` | yt-dlp 字幕（agent-reach） | agent-reach |
| Twitter/X 推文 | agent-reach twitter | web_extract | fetch_url |
| GitHub 仓库/Issue/PR | agent-reach github | gh CLI | fetch_url |
| V2EX / RSS / 中文站 | agent-reach v2ex/rss | fetch_url | crawl4ai |
| 微信公众号文章 | fetch_url --upgrade-to-js | agent-reach | crawl4ai |
| 知乎专栏 / juejin | fetch_url --upgrade-to-js | agent-reach | crawl4ai |
| 小红书（需登录） | ❌ 不支持 | — | 告诉用户"需登录" |
| React/Vue SPA | fetch_url + upgrade | crawl4ai | agent-reach |

## 🚨 真缺口（不假装能做）

| URL 类型 | 状态 | 原因 |
|---|---|---|
| 小红书笔记 | ❌ 需登录 | agent-reach 也需 QR scan |
| 微信公众号（需关注） | ⚠️ 部分 | fetch_url 拿 body, 但被关注限制时拿不到 |
| 知乎登录内容 | ❌ 需登录 | agent-reach 也需 cookie |
| 需要验证码的页面 | ❌ 不支持 | 任何自动化都卡 |
| 腾讯文档（doc.weixin.qq.com） | ⚠️ 需 JS 渲染 | 纯 HTML 抓取可能缺少关键数据，需使用 `fetch_url.py --upgrade-to-js` 或浏览器工具 |
| **Next.js SPA skill hub**（agentskills.io 类） | ❌ server-side HTML 是空壳 | 100KB+ HTML 全是 `_next/static/chunks/*.js` 加载逻辑，**没有 SSR 内容**。`curl` / `web_extract` 都拿不到 skill 列表。**改走 GitHub 直查**: `web_search "<keyword> site:github.com"` 或 `https://github.com/<org>/<repo>` raw README。**判断信号**: `curl <url> \| grep -c "<keyword>"` 命中 < 5 = SPA，立即切源 |

**真验证 4 选 1**（按 hermes-see-act SOP）:
1. 重 fetch 看值还在不在（持久化测试）
2. 比对 metadata (title/description) vs 实际内容
3. 截图 vs DOM（看渲染完整性）
4. snippet 数量 + 平均长度（含量质量）

## 🐍 实战 fetch_transcript.py (2026-06-27 真实跑通)

```bash
# YouTube 字幕提取 - 3Blue1Brown 神经网络视频
python3 ~/.hermes/scripts/fetch_transcript.py \
  "https://www.youtube.com/watch?v=aircAruvnKk" --lang=en --json

# 结果: 286 个 snippet, 第一条 "This is a 3.", 完整字幕全文 + 时间戳
```

**真验证**: YouTube 字幕 286 片段，**与视频实际播放内容一致**（DOM `.ytp-caption-segment` 也是这段文字）。

## 🛠️ fetch_url.py 实战升级路径

```bash
# 1) 普通 HTML
python3 ~/.hermes/scripts/fetch_url.py https://example.com
# → Trafilatura 提取

# 2) Trafilatura 失败 → 升级到 Playwright
python3 ~/.hermes/scripts/fetch_url.py https://spa-site.com --upgrade-to-js
# → Playwright JS 渲染 + DOM 提取

# 3) 缓存命中
python3 ~/.hermes/scripts/fetch_url.py https://blog.com/post  # 第二次跑，秒返
# → DiskCache 24h TTL
```

## 📊 路由性能对比（实测基准）

| 工具 | 延迟 (普通页) | 延迟 (JS 重页) | 成本 |
|---|---|---|---|
| fetch_url.py (Trafilatura) | 200-500ms | — | 免费 |
| fetch_url.py (Playwright) | 3-5s | 3-5s | 免费 |
| fetch_transcript.py (YouTube) | 500ms | — | 免费 |
| agent-reach (8 渠道) | 1-3s | 1-3s | 免费 (Exa 除外) |
| crawl4ai | 5-15s | 5-15s | 免费 (LLM 提取按 token 算) |

## 🧠 路由铁律（按 Ponytail + proactive-execution）

1. **rung 4 命中 = 停**（fetch_url 已 work → 别写 wrapper）
2. **真缺口 = rung 6**（fetch_transcript 补 YouTube/B站是 rung 6 真值）
3. **汇报前必验证**（verification-before-reporting Failure 30/31/53 教训）
4. **用户描述不能照搬**（Failure 53 教训: 用户说"/moa 切换模式"其实是"/moa 单次执行"）
5. **批量装机必逐项验证**（Failure 54 教训: pip 装成功 ≠ import 成功）

## 🔗 子文件\n\n- `references/fetch-transcript-pitfalls.md` — fetch_transcript.py 实战踩坑（429/语言 fallback/yt-dlp cookie）\n- `references/agent-reach-channel-status.md` — agent-reach 8/13 渠道真实状态矩阵\n- `references/crawl4ai-when-to-use.md` — crawl4ai 真使用场景（避免无脑用）\n- `references/tencent-doc-tips.md` — 腾讯文档抓取技巧（JS 渲染、登录、验证）
- `references/defuddle-usage.md` — defuddle 0.19.1 实战配置 + 路由决策表（2026-07-03 新增）\n
## 📋 维护规则

- USER.md / fact_store #92 "2026-06-27 抓取工具链固化方案" 是本 skill 的索引
- fetch_url.py 改 v3 → patch 本 skill 的 Rung 4 段
- agent-reach 渠道变动 → 更新 8/13 渠道矩阵
- crawl4ai 升 1.0 → 更新真使用场景

## v1.0.0 变更日志 (2026-06-27)

- **新建 class-level umbrella**: 整合 fetch_url.py (Trafilatura v2) + fetch_transcript.py (YouTube/B站) + agent-reach (8/13 渠道) + crawl4ai (复杂 JS) 4 层 fallback 链
- **路由决策表**: 按 URL 类型自动路由，**不写新 wrapper**
- **真缺口矩阵**: 小红书/知乎登录/验证码类诚实标记"不支持"
- **实战基准**: 3Blue1Brown 视频拿到 286 字幕片段（fetch_transcript.py 真验证通过）
- **Ponytail 真值**: 4 个工具都是 rung 4/6，没有 rung 1/2/3 的盲点（Trafilatura/yt-dlp/youtube-transcript-api/crawl4ai 都是成熟库）
- **跟 verification-before-reporting 联动**: Failure 53/54 教训直接引用（用户描述不照搬 + 批量装机逐项验证）