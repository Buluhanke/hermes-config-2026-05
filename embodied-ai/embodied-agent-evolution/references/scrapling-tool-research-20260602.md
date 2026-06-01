# Scrapling 工具研究记录（2026-06-02）

## 基本信息

- **GitHub**: `D4Vinci/Scrapling`
- **Stars**: 56.8k（真实，1446次提交，2天前更新）
- **许可证**: 官方赞助商列表含商业代理（ColdProxy/HyperSolutions/BirdProxies等）
- **官网**: `scrapling.readthedocs.io`

## 安装

```bash
~/.hermes/hermes-agent/venv/bin/pip3 install "scrapling[all]"
```

完整依赖链：
- 基础：`scrapling`（lxml/cssselect/orjson/tld/w3lib）
- 隐身抓取：`curl_cffi`（浏览器指纹模拟）
- 浏览器引擎：`patchright`（Playwright分支）
- 浏览器指纹：`browserforge`（HeaderGenerator/Browser）
- MCP支持：官方提供MCP服务器

## 核心功能

### 1. 自适应解析（Adaptive Parsing）
```python
fetcher = StealthyFetcher()
p = fetcher.fetch('https://example.com', headless=True, network_idle=True)
items = p.css('.product', adaptive=True)  # 网站结构变也能找到
```
**价值**：1688页面结构频繁变化，CSS选择器容易失效，`adaptive=True`自动重定位元素。

### 2. 隐身抓取（StealthyFetcher）
```python
StealthyFetcher.adaptive = True
p = StealthyFetcher.fetch(url, headless=True, network_idle=True)
```
**价值**：内置绕过Cloudflare Turnstile等反爬，开箱即用。

### 3. 爬虫框架
```python
from scrapling.spiders import Spider, Response
class MySpider(Spider):
    name = "demo"
    start_urls = ["https://example.com/"]
    async def parse(self, response: Response):
        for item in response.css('.product'):
            yield {"title": item.css('h2::text').get()}
MySpider().start()
```

### 4. MCP服务器
- 官方提供：`scrapling.readthedocs.io/en/latest/ai/mcp-server.html`
- 可被AI Agent调用

## 1688实测（2026-06-02）

```python
from scrapling.fetchers import StealthyFetcher
fetcher = StealthyFetcher()
p = fetcher.fetch('https://s.1688.com/joffer/offer_search.htm?keywords=%B0%D7%B4%B5', headless=True, network_idle=True)
# ✅ 成功获取（301→302→200重定向处理正常）
# ✅ 页面标题：批发_供应_阿里巴巴
```

**注意**：1688有阿里自研滑块验证码（nc-1-n1z），Scrapling的Turnstile绕过对此无效。

## 与现有Hermes工具对比

| 工具 | 反爬能力 | 自适应解析 | 适用场景 |
|------|---------|-----------|---------|
| Playwright CDP | 有限 | ❌ | 登录态/复杂交互 |
| Scrapling | Cloudflare/Turnstile原生 | ✅ | 大规模数据采集 |
| DrissionPage | 一般 | ❌ | 备选 |

## 内存占用

`scrapling[all]` 会装入 playwright(1.59GB) + patchright + browserforge，对M4 Mac mini 24GB有压力。

**结论**：作为1688批量采集的进阶备用方案（当CDP被反爬拦截时）。日常1688任务继续用CDP+DOM方案。
