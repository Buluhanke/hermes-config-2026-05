# Crawl4AI — 最强 Shadow DOM 处理方案（2026-07-20 研究）

## 核心价值

Crawl4AI 是目前全网**唯一一个**专门解决 closed Shadow DOM 提取问题的开源工具：
- force-open closed shadow roots
- resolve slots（`<slot>` 元素内容穿透）
- 自动把 Shadow DOM 内容注入 light DOM 再抓取

对比其他工具：
- `scrapling`：支持 stealth mode，但 Shadow DOM 处理不如 Crawl4AI 彻底
- `Runtime.evaluate` 递归脚本：能读 open Shadow DOM，closed root 无解
- Firecrawl：自动处理，但闭源云端，不能自托管

## 本机安装条件（2026-07-20 实测）

| 依赖 | 状态 |
|------|------|
| Python ≥3.10 | ✅ Hermes venv 是 3.11.15 |
| Playwright | ❌ 未装，浏览器二进制需下载 |
| 磁盘 | ✅ 380 GB 可用 |
| 网络下载 Playwright | ⚠️ 待测（需访问 playwright.azureedge.net）|

## 安装步骤

```bash
# 1. 在 Hermes venv 里装核心包
~/.hermes/hermes-agent/venv/bin/pip install crawl4ai

# 2. 运行 setup（装浏览器）
crawl4ai-setup

# 3. 验证
~/.hermes/hermes-agent/venv/bin/python -c "
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url='https://example.com')
        print(result.markdown[:200])
asyncio.run(main())
"
```

## 已知限制

- **Playwright 浏览器下载**：需要访问 `playwright.azureedge.net`，本机网络可能 SSL 拦截
- **内存**：24GB Mac mini M4 够用，Crawl4AI 跑 headless chromium
- **Python 3.9 系统 Python 不够**：必须用 Hermes venv 的 Python 3.11

## 读取漏斗定位

Crawl4AI 位于漏斗的第 5 层（scrapling 之后，screenshot OCR 之前）：

```
web_extract → defuddle → CDP AX → DOM → Shadow递归
  → scrapling DynamicFetcher  ← 当前 Hermes 已有
  → Crawl4AI                  ← 待安装，最强 Shadow DOM
  → screenshot + Tesseract    ← 最终降级
```

## 与 Firecrawl 的分工

| 场景 | 方案 |
|------|------|
| 普通静态页面 | web_extract / defuddle |
| AI 站 Shadow DOM（ChatGPT、豆包等）| **Crawl4AI**（最强）或 CDP 递归脚本 |
| 企业微信 Canvas 表格 | CDP screenshot → Tesseract |
| 防反爬 / Cloudflare | Firecrawl（已配置）或 Crawl4AI stealth |
| JS 懒加载 SPA | scrapling → Crawl4AI |

## 验证状态

- [ ] Crawl4AI pip install 成功
- [ ] playwright install chromium 成功（网络测试）
- [ ] 抓取 example.com 验证 markdown 输出
- [ ] 对 AI 站 Shadow DOM 验证提取效果
