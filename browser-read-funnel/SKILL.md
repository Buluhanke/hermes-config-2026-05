---
name: browser-read-funnel
description: "网页读取漏斗 L0extract到L1 DOM到L2截图 免截图读懂网页。Use when 读任何网页内容的统一入口决策"
triggers:
  - "读取网页内容"
  - "extract page content"
  - "shadow DOM"
  - "canvas 表格"
  - "网页读不到"
  - "页面内容提取"
  - "browser-read-funnel"
  - "操作浏览器"
  - "browser-use"
  - "browser harness"
  - "CDP browser"
l1: browser
l2: read-funnel
l3: core
---

# Browser Read Funnel — 100% 网页内容读取方案

## 零截图读懂（首选路径，2026-08-22 迭代）

**核心原则：截图是信息最差的一层（有损、慢、常失败）。看懂网页 = 拿文字/结构化数据，不是拿像素。**
行业共识（Prophet / Playwright-MCP / microsoft，2026）：accessibility tree 比截图快 2-4×、便宜 4×、文字零 OCR 误差、确定性。

### 四层（自下而上，越往上越准越快越省）
| 层 | 方法 | 截图 | 适用 |
|----|------|------|------|
| L0 | `web_extract` / `curl` → markdown | ❌ | 静态公开页(服务端渲染) |
| L1 | `Runtime.evaluate(document.body.innerText)` / AX树 | ❌ | SPA / 登录站 / 现代网页(覆盖90%) |
| L2 | `Network.getResponseBody` 抓 XHR 原始 JSON；或直接 `curl` 重放该 XHR | ❌ | 数据驱动页(表格/列表/仪表盘)，最准 |
| L3 | 官方 REST / `curl` + cookie | ❌ | 已知接口 |
| (兜底) | `computer_use` 截图 + OCR | ✅ | 仅 Canvas/WebGL 纯像素 / 空间布局 / 图片内信息 |

### L2 黄金法则（pickuma 实战，11靶8个只需1个XHR）
- 现代 SPA 数据多在 JS 消费的 XHR/fetch JSON 里。**先 DevTools Network 过滤 XHR/Fetch 找 JSON 请求**，再用 cookie 重放 `curl`，跳过浏览器直接拿干净结构。
- XHR 比 DOM 抗前端重构：DOM 读 9 个月坏 6 次(class改名)，XHR 只坏 2 次(字段改名，schema 校验会 loudly 报错)。
- 重放注意：nonce/CSRF/签名 URL/Service Worker 可能让重放不安全；只读路径优先，副作用(创建/删除/支付)路径禁止重放。
- 铁律（Skynet）：DOM 优先 → Network 观察次之 → Fetch 拦截仅在有理由时 → 重放只在校验过不变量后。

### 本机实测坑（2026-08-22 已验证，见 ZERO_SHOT_READ_MAP.md）
1. `browser_exec`(browser-use daemon) 默认连**云端**非本地 Chrome → CDP 握手 HTTP 403，不用于读本地登录态。
2. `chrome-devtools-mcp` 实际未配进 config.yaml（老文档说"已配"过时）。
3. `computer_use list_windows` 只枚举 Cua Driver+Hermes，枚举不到 Chrome/第三方 app 窗口 —— **但 `computer_use(action='capture', app='Google Chrome', mode='ax')` 能直接读前台真实 Chrome 窗口的无障碍树**（2026-08-22 实证，零调试端口、零新实例），这是登录态真实页 L1 读取的主路径。点击用 `coordinate` = native bounds ÷ 1.36（Cua Driver 0.17 不接受裸 element_index）。click 返回 `unverifiable` 多为假阴性，重抓 AX 树验证即可。
4. 用户 Chrome 常驻但窗口为 0 时，所有"读屏幕浏览器"路径无目标 → 改走 Hermes 内置 browser 后端或 `web_extract`。
5. `vision_analyze` 对有效 PNG 反复"看不到图片" → 截图链失效 1 次即降级，绝不重试。

### 前台 Chrome AX 树 L1 完整手法（详见 references/foreground-chrome-ax.md）
- 抓取：`computer_use(action='capture', app='Google Chrome', mode='ax')` → 落盘 `elements_file` JSON（600~1184 节点）。
- 点击：`coordinate = native_bounds ÷ 1.36`（Cua Driver 0.17 拒裸 element_index）；click 返回 `unverifiable` 是假阴性，重抓 AX 验证即可，勿重试。
- 解析：详情页节点上千 → `python3 scripts/parse_ax_tree.py <elements_file> --keys "规格,材质,厚度,尺寸,价格,起订" --context 6` 重建「字段→值」结构，挖 SKU 矩阵/件重尺。
- 这是登录态真实页（1688 等）零截图读取的主路径，完全绕过 9222。

### L2 现场实证（2026-08-22，Hacker News SPA）
```
curl "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=3" | python3
→ hits: 3
  - Relicensing React, Jest, Flow, and Immutable.js | 2280 pts | dwwoelfel
  - Build Your Own React | 1478 pts | pomber
  - Show HN: Performative-UI – A react component library | 1181 pts | lizhang
```
零截图、零浏览器、直接拿后端真数据。

## 工具栈（4 层漏斗）

| 工具 | 延迟 | 费用 | 强项 | 弱项 |
|------|------|------|------|------|
| **browser-use** | ~1s | 免费 | 主动操作：点击/填表/导航，CDP直连Chrome | 不能读页面内容 |
| **Firecrawl** | 1-3s | API额度 | 公开URL、抗反爬、零配置 | Shadow DOM不稳定 |
| **Scrapling** | 3-8s | 免费 | stealth浏览器、Cloudflare bypass | 不能处理closed Shadow DOM |
| **Crawl4AI** | 5-15s | 免费 | Shadow DOM force-open、Canvas截图+OCR | 需要浏览器二进制 |
| **截图OCR** | 10-20s | 免费 | Canvas/WebGL兜底 | OCR准确率有限 |

## 读取优先级（已验证 2026-08-17）

```
URL 输入
  ↓
browser-use（主动操作：点击/填表/导航）
  ↓
Firecrawl /scrape（快速，公开URL）
  ↓ 失败
Scrapling（stealth动态页面）
  ↓ 失败
Crawl4AI（深度，含flatten_shadow_dom）
  ↓ 仍失败
截图 → Tesseract OCR（最终降级）
```

### 0. browser-use（主动操作层）
- **用途**：不是读取工具，是**操作**工具——点击按钮/填写表单/导航页面/抓动态数据
- **安装**：`uv tool install browser-use`（已装）
- **连接Chrome**：`chrome://inspect/#remote-debugging` → 勾 Allow
- **验证**：`browser-use doctor`（显示 `chrome running`, `daemon alive`）
- **用法**：
  ```bash
  browser-use <<'PY'
  new_tab("https://example.com")
  wait_for_load()
  print(page_info())
  PY
  ```
- **读取内容**：配合 `js("document.body.innerText")` 或 `page_info()`
- **参考**：`references/browser-use-cli.md`（browser-use CLI完整指南）
- **参考**：`references/hermes-superhuman-browser.md`（GitHub Top工具调研成果）

## 使用方式

### CLI（直接用）

```bash
# 默认 auto 模式（全漏斗逐层尝试，见 read_page.py；依赖 firecrawl/Crawl4AI 等后端）
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com

# 轻量降级链（纯本地可验证：scrapling-get → scrapling-fetch → curl；2026-08-23 新增）
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_url.py https://example.com
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_url.py https://example.com --out out.md

# 强制指定工具
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com --force firecrawl
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com --force crawl4ai
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com --force scrapling

# 开启 Shadow DOM 递归展开（Crawl4AI 专用）
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com --shadow-dom

# 输出到文件
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com -o output.md

# JSON 输出（程序调用）
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com -f json
```

### Python API（Hermes 直接调用）

```python
from browser_read_funnel import read_page, ReadResult

# 方式 1：自动选择最佳工具
result: ReadResult = await read_page(
    url="https://example.com",
    prefer="auto"  # 默认，逐层尝试
)

# 方式 2：强制某个工具
result = await read_page(
    url="https://example.com",
    prefer="crawl4ai",
    flatten_shadow_dom=True,  # Crawl4AI 专用
    timeout=60,
)

print(result.success)
print(result.markdown)
print(result.via)   # "🔥 Firecrawl（云端）" 等
print(result.error)  # 失败原因
```

## 各层详解

### 1. Firecrawl（云端，第一层）

- **用途**：公开 URL 的快速读取，Hermes 内置 `web_extract` 就是这个 backend
- **API Key**：已存在于 `~/.hermes/.env`：`FIRECRAWL_API_KEY=fc-a89...`
- **适用**：普通新闻、博客、文档、GitHub 等
- **不适用**：Shadow DOM（ChatGPT、DeepSeek 等 AI 站点的对话内容）

### 2. Scrapling（本地，第二层）

- **用途**：绕过 Cloudflare 和其他反爬机制，stealth 浏览器模拟真实用户
- **安装状态**：`hermes skills install official/research/scrapling` 已装（2026-08-23）+ `scrapling install` 浏览器引擎已装；example.com 实测通过
- **CLI 实测用法**（2026-08-23 验证，非旧 Paparazzi API）：
  ```bash
  scrapling extract get 'https://example.com' out.md            # 静态 HTTP
  scrapling extract fetch 'https://spa.site' out.md --network-idle   # JS 渲染
  scrapling extract stealthy-fetch 'https://cf.site' out.html --solve-cloudflare  # 反爬
  ```
- **与 L1 前台 AX 树互补**：scrapling 抓公开/无登录页（无头），L1 读你已登录的前台 Chrome 页（零调试端口/零新实例）
- **适用**：需要登录的页面、Cloudflare 拦截页面、简单 SPA
- **不适用**：closed Shadow DOM（shadow root 为 close 状态）

### 3. Crawl4AI（本地，第三层）

- **用途**：Shadow DOM 专用，`flatten_shadow_dom=True` 强制展开所有 shadow root
- **版本**：0.9.2（Hermes venv 已装）
- **安装命令**：`python3 -m pip install -U crawl4ai`
- **浏览器依赖**：`python3 -m playwright install --with-deps chromium`（setup CLI 不存在）
- **CLI 入口**：`node bin/omniroute.mjs`（OmniRoute 捆绑）；Crawl4AI 无独立 CLI，用 Python API
- **适用**：ChatGPT、DeepSeek、豆包等 AI 站点的对话内容，企业微信表格等复杂组件
- **不适用**：Canvas/WebGL 纹理文字（需降级到 OCR）
- **⚠️ OmniRoute 捆绑的 better-sqlite3 与 Node 22.23.1 ABI 不兼容**：导致 OmniRoute DB 探针循环失败，所有 API 500。独立 venv 内 `import crawl4ai` 正常，不受影响。

### 4. 截图 OCR（最终降级）

- **用途**：Canvas 渲染的表格、图表、WebGL 纹理等连 Crawl4AI 都无法提取的内容
- **依赖**：Chrome CDP（`--remote-debugging-port=9222`）+ Tesseract OCR
- **适用**：企业微信智能表格（canvas 渲染）、游戏页面、图表截图

## 降级链实现

```
read_page(url, prefer="auto")
  │
  ├─ firecrawl.scrape(url)       → 成功 → return markdown
  │
  ├─ scrapling extract fetch/stealthy-fetch  → 成功 → return markdown
  │
  ├─ crawl4ai.arun(url,
  │      flatten_shadow_dom=True,
  │      screenshot=True)
  │                              → 成功 → return markdown
  │
  └─ screenshot → Tesseract OCR
       └─ return ocr_text
```

## 已知限制

| 限制 | 原因 | 状态 |
|------|------|------|
| Cross-origin iframe | 同源策略，JS 无法穿透 | ❌ 无解 |
| 端到端加密内容 | 物理上不可解密 | ❌ 不应读 |
| CAPTCHA | 需要人机验证 | ❌ 不应绕 |
| WebGL 纹理文字 | OCR 也读不到 | ⚠️ 降级链尽头 |

## 升级能力

封装后各层可独立升级，不影响整体漏斗：

| 升级方向 | 命令 | 影响 |
|----------|------|------|
| browser-use CLI | `uv tool install browser-use --force` | 主动操作层，CDP直连Chrome |
| Firecrawl版本 | `pip install -U firecrawl-py` | 全局生效 |
| Crawl4AI版本 | `pip install -U crawl4ai` | 自动兼容 |
| Scrapling版本 | `pip install -U scrapling` | 自动兼容 |
| 加Spider API | 加 `--spider` 参数 | 只需加一个新函数 |

## 验证

```bash
# 测试 Firecrawl
python3 -c "
from firecrawl import Firecrawl
import pathlib
key = next(l for l in pathlib.Path.home().joinpath('.hermes/.env').read_text().splitlines() if l.startswith('FIRECRAWL_API_KEY=')).split('=',1)[1].strip()
fc = Firecrawl(api_key=key)
doc = fc.scrape('https://example.com', formats=['markdown'])
print('✅ Firecrawl:', doc.markdown[:100])
"

# 测试 Crawl4AI
python3 -c "
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import asyncio
async def t():
    async with AsyncWebCrawler() as c:
        r = await c.arun('https://example.com', config=CrawlerRunConfig(flatten_shadow_dom=True))
        print('✅ Crawl4AI:', r.markdown[:100])
asyncio.run(t())
"

# 快速功能测试（example.com）
python3 ~/.hermes/skills/browser-read-funnel/scripts/read_page.py https://example.com
```

## A2 后台登录页实战模板（无前台窗口时，2026-08-23 固化）
- **场景**：豆包/Gemini/1688 后台等需登录、且当前无前台 Chrome 窗口的页面。
- **步骤**：
  1. 浏览器手动打开该页 → DevTools (F12) → Network → 刷新 → 复制目标请求（XHR/Document）的 **Cookie 请求头** → 存成 `cookie.txt`（raw `k=v; k2=v2`）。
  2. 若页面数据走 XHR：`curl_xhr.py <url> --cookie cookie.txt "<jsonpath>"` 重放拿 JSON（见 `scripts/curl_xhr.py`）。
  3. 若整页渲染：`scrapling extract get/fetch <url> -H "$(cat cookie.txt|sed 's/^/Cookie: /')" out.md`（scrapling 支持 -H 透传）。
- **安全铁律**：Cookie 仅在运行时内存读取，不落盘/不进 memory/不回显到对话以外；用完即弃。`curl_xhr.py` 头注释已固化此条。
- **验证状态**：`--cookie`/`-H` 通道 2026-08-23 本地回声服务器确认 Cookie 真发出（收到 `test_session=...; login_token=***`）。真实登录页尚未实跑，等你给 URL + Cookie 文件即可验收。


## 2026 更优方案参考（全网调研 2026-08）
真实 Chrome 非无头自动化 SOTA：Quay(CDP+AX树)、Eyebrowse(MCP)、pi-browser-harness。
与本技能「前台真实 Chrome AX 树」思路一致，保留 defuddle/trafilatura 提取。
