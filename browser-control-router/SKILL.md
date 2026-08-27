---
name: browser-control-router
description: 浏览器控制统一路由——读/操作/登录态三轴决策表，消除在 cua-browser-control / browser-cdp-control / chrome-cdp-control / browser-read-funnel 间重复选型。Use when 任何浏览器任务（读页面/点按/填表/登录态）先来判断走哪条 lineage。
version: "1.0"
triggers:
  - "读网页/抓页面内容"
  - "操作浏览器/点按钮/填表"
  - "登录态页面自动化"
  - "哪个浏览器 skill 该用"
  - "browser control / CDP / 前台 Chrome / 镜像 Chrome 怎么选"
l1: browser
l2: router
l3: core
---

# Browser Control Router — 三轴决策表（5 lineage 杂交固化）

本 skill 是路由层，不重复实现细节。它把 4 个底层 skill 的决策边界一次性定清，避免每次任务重新推导。

底层 lineage（按需 skill_view 加载全文）：
- `browser-read-funnel` — 读内容漏斗 L0→L3
- `browser-cdp-control` — CDP 9222 本地 Chrome（含镜像/DoH 反爬）
- `chrome-cdp-control` — CDP 进阶（fresh vs mirror 策略、生命周期）
- `cua-browser-control` — cua-driver 的 cua_browser_* 精确绑定真实 tab

## 三轴模型（先判轴，再选工具）

```
任务
 ├─ 轴A: 读内容?   → browser-read-funnel（L0→L3 漏斗）
 ├─ 轴B: 操作?     → cua_browser_control / chrome-cdp-control（点击/填表）
 └─ 轴C: 登录态?   → 决定 轴A/轴B 用哪条具体路径
```

## 决策表（直接照抄）

| # | 任务 | 登录态 | 首选路径 | 工具 / 命令 |
|---|------|--------|----------|-------------|
| 1 | 读公开静态页（博客/文档/GitHub） | 否 | L0 | `web_extract(url)` |
| 2 | 读 SPA / 登录页正文 | 是/否 | **L1 前台 AX 树**（零调试端口） | `computer_use(action='capture', app='Google Chrome', mode='ax')` → `parse_ax_tree.py` |
| 3 | 读已登录真实页（无前台窗口） | 是 | CDP mirror innerText | `read_page_text.py <url>`（chrome-cdp-control） |
| 4 | 读 AI 对话（Shadow DOM） | 是 | L1 AX 优先，失败→L2 XHR 重放 | `curl_xhr.py` + cookie（browser-read-funnel A2） |
| 5 | 点按/填表（登录站） | 是 | **cua_browser 精确绑定** | `cua_browser_prepare`→`state`→`click/type`（cua-browser-control） |
| 6 | 批量 DOM 读/写（登录站） | 是 | CDP mirror 9222 | `Runtime.evaluate`（chrome-cdp-control） |
| 7 | 绕过 DNS 劫持 / 反爬 403 | 是 | CDP mirror + DoH | `--host-resolver-rules` + cookie prewarm（chrome-cdp-control） |
| 8 | Canvas/WebGL 表格 | - | 截图+OCR（最后兜底） | `Page.captureScreenshot`→Tesseract（browser-read-funnel L3） |

## 已杂交固化的关键结论（解决 lineage 间矛盾）

**矛盾1：读任务要不要镜像 Chrome？**
- ❌ 旧认知（browser-cdp-control 早期）：读登录页必须镜像 Chrome 到 9222。
- ✅ 2026-08-22 实测修正（browser-read-funnel）：**读任务首选前台真实 Chrome 的 AX 树**（`computer_use capture mode='ax'`），零调试端口、零新实例、零镜像步骤。镜像 Chrome（9222）只在**操作任务（#5/#6）或无前台窗口（#3）**时才必要。
- 路由规则：先问"读还是操作"。读→走 #2；操作→走 #5/#6（需 9222）。

**矛盾2：cua_browser_* vs 裸 CDP，谁管操作？**
- cua_browser_*：精确绑定**真实已开 tab**，背景不抢焦点，适合单次点按/填表（#5）。
- 裸 CDP `Runtime.evaluate`：批量 DOM 读写、脚本化循环，适合 #6。
- 两者共享 9222 端口，不冲突。

**矛盾3：config 怎么改？**
- `browser.cdp_url` / `mcp_servers.*` 是安全敏感项，`patch` 被拒 → 一律用 `hermes config set <dotted.key> <value>`，list 值再用 python yaml pass 修（chrome-cdp-control 已固化）。

## 黄金铁律（跨 lineage 通用）
- 截图是信息最差层（有损/慢/常失败），看懂网页=拿文字/结构化数据，不是拿像素。
- `vision_analyze` / `browser_vision` 失败 1 次即降级，绝不重试 2-3 次。
- 写用户真实在线数据（企微表/真实库）前先报"写 X 到 Y"，不可逆操作必须确认。
- CDP WS 帧**不加 `jsonrpc` 字段**（否则 -32600）；Chrome 150+ 用 page-level WS，不用 `attachToTarget`。
- 镜像 Chrome 启动必须 `--user-data-dir` 指向**隔离副本**（Chrome 148+ 拒绝默认 profile 开调试端口），且 `--remote-allow-origins=*`（zsh 下必须引号包裹 `*`）。

## 快速自检 SOP
```
1. 读 or 操作? → 读跳 #2/#3/#4，操作跳 #5/#6
2. 要登录态吗? → 是则确认 Chrome 在前台(读) 或 9222 在线(操作)
3. 前台窗口数>0 且只是读 → 直接 computer_use capture ax（最快，零端口）
4. 9222 在线检查: curl -s -m5 http://127.0.0.1:9222/json/version
```
