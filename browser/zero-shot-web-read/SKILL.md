---
name: zero-shot-web-read
description: 不靠截图读懂网页的分层方法（L0-L2 优先，截图仅兜底）。
triggers:
  - "读取网页内容"
  - "extract page content"
  - "看懂网站"
  - "无截图读页面"
  - "网页读不到"
  - "页面内容提取"
  - "shadow DOM"
  - "SPA 数据提取"
  - "抓 XHR JSON"
l1: browser
l2: zero-shot-read
l3: core
---

# Zero-Shot Web Read — 不靠截图读懂网页

## 核心原则
截图是信息最差的一层（有损、慢、常失败）。看懂网页 = 拿文字/结构化数据，不是拿像素。
AX 树比截图快 2-4×、便宜 4×、文字零 OCR 误差、确定性（行业共识：Prophet / Playwright-MCP / microsoft，2026）。

## 四层（自下而上，越往上越准越快越省）
| 层 | 方法 | 截图 | 适用 |
|----|------|------|------|
| L0 | `web_extract` / `curl` → markdown | 否 | 静态公开页(服务端渲染) |
| L1 | `Runtime.evaluate(document.body.innerText)` / AX 树 | 否 | SPA / 登录站 / 现代网页(覆盖90%) |
| L2 | `Network.getResponseBody` 抓 XHR 原始 JSON；或直接 `curl` 重放该 XHR | 否 | 数据驱动页(表格/列表/仪表盘)，最准 |
| L3 | 官方 REST / `curl` + cookie | 否 | 已知接口 |
| 兜底 | `computer_use` 截图 + OCR | 是 | 仅 Canvas/WebGL 纯像素 / 空间布局 / 图片内信息 |

## L2 黄金法则（pickuma 实战，11 靶 8 个只需 1 个 XHR）
- 现代 SPA 数据多在 JS 消费的 XHR/fetch JSON 里。先 DevTools Network 过滤 XHR/Fetch 找 JSON 请求，再用 cookie 重放 `curl`，跳过浏览器直接拿干净结构。
- XHR 比 DOM 抗前端重构：DOM 读 9 个月坏 6 次(class改名)，XHR 只坏 2 次(字段改名，schema 校验会 loudly 报错)。
- 重放注意：nonce/CSRF/签名 URL/Service Worker 可能让重放不安全；只读路径优先，副作用(创建/删除/支付)路径禁止重放。
- 信任梯度（Skynet）：DOM 优先 到 Network 观察次之 到 Fetch 拦截仅在有理由时 到 重放只在校验过不变量后。

## 铁律兼容（本机用户规则）
- 禁用 `--remote-debugging-port=9222` 调试端口、禁用另起 Chrome 实例。
- 登录态优先：用用户真实登录态(需用户配合开 9222 mirror Chrome 时才走 CDP)，或走 Hermes 自己的浏览器后端，而非截用户屏幕。
- `vision_analyze` 对有效 PNG 反复"看不到图片" 到 截图链失效 1 次即降级，绝不重试。
- `browser-use` 是操作工具(点击/填表/导航)，不是读取工具；其 daemon 默认连云端非本地 Chrome 到 CDP 403，不用于读本地登录态。

## Shadow DOM / AI 站回复
- Crawl4AI `flatten_shadow_dom=True` 强制展开 closed shadow root（v0.8.5+）。
- Playwright 原生 selector 默认穿透 open shadow root；closed 需 CDP 或拦截 `attachShadow`。
- AI 站(ChatGPT/豆包)回复在 shadow 里 到 用 AX 树 / 递归 `shadowRoot` 读；Gemini 实测 AX 树可读。

## 现场实证（2026-08-22）
- L0：MDN Fetch API 页 `web_extract` 拿完整正文，零截图。
- L2：`curl "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=3"` 直拿结构化 JSON（标题/分数/作者）；GitHub/JSONPlaceholder 同法泛化通过。
- 工具线索 `mantis`(`@yrstm/mantis` 404) / `fuse-browser`(000) 在 npm 不可装 到 放弃，改用 `scripts/curl_xhr.py`。

## 用法
```bash
# L0 公开页
web_extract <url>

# L2 直连重放（脚本见 scripts/curl_xhr.py）
python3 scripts/curl_xhr.py "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=2" "hits.0.title" "hits.0.points"
```
调研浓缩见 `references/zero-shot-research-20260822.md`。
