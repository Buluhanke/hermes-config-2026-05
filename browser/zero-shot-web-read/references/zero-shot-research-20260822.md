# 零截图读取 — 全网调研浓缩（2026-08-22）

> 来源：本次会话 web_search 的权威结论。仅供本 skill 使用，非上游文档镜像。

## 1. Accessibility Tree vs Screenshot（2026 行业共识，Prophet）
- AX 树比截图快 **2-4×**、便宜 **4×**、文字**零 OCR 误差**、确定性（不靠视觉概率）。
- 截图仅胜在：Canvas/WebGL 纯像素、依赖空间布局（"右边那个按钮"）、图片内信息、视觉 QA。
- 截图式感知是概率性的：小字体/低对比/重叠元素/相似按钮易误读，多步任务误差累积。
- 结论：交互/提取/导航类任务 AX 树全面占优；截图仅作边界场景兜底。

## 2. 你通常不需要 DOM，要的是 Network 拦截的 JSON（pickuma 实战）
- 启用 `Network`，监听 `responseReceived`，用 requestId 调 `Network.getResponseBody` → 拿到前端消费的**原始 JSON**。
- 11 个无 API 目标：8 个只需拦截 1 个 XHR；仅 3 个真需 DOM 读（且这 3 个最易碎）。
- 抗重构对比：DOM 读 9 个月坏 6 次（class 改名），XHR 只坏 2 次（字段改名，schema 校验会 loudly 报错）。
- 成本：Chromium 空闲 ~180MB、峰值 400-500MB；等价 `fetch` ~40ms vs 浏览器 2-6s。
- **前置习惯**：动手写浏览器代码前，先在 DevTools Network 过滤 XHR/Fetch 手动点一遍。3 个目标从"需 Chrome"塌缩为"1 个 POST + session cookie"。

## 3. 观察 / 拦截 / 重放 的信任梯度（Skynet / exzilcalanza）
- DOM 优先 → Network 观察次之 → Fetch 拦截仅在有理由时 → 重放只在校验过不变量后。
- 观察 ≠ 拦截：Passive observation（Network 事件）最不侵入；Fetch 拦截改变执行路径，需更紧作用域；重放绕过正常页面流，信任边界不同。
- 重放风险：认证可能绑定浏览器会话、nonce 过期、签名 URL 一次性、Service Worker 介入、CSRF/客户端状态依赖。
- 已发现路由 ≠ 稳定 API；当作待证假设，不当中转捷径。

## 4. Shadow DOM 穿透（Crawl4AI v0.8.5+）
- `flatten_shadow_dom=True` 通过 patch `attachShadow` 强制展开 closed shadow root，递归解析 projection，剥离 shadow-scoped 标签。
- Playwright 原生 selector 默认穿透 **open** shadow root；**closed** shadow root 需 CDP 调试 API 或拦截 `attachShadow`。
- 标准 HTML 解析器（BeautifulSoup/Cheerio）只读 light DOM，读不到 shadow 内容。

## 5. 无 DevTools 扩展读 React/Redux 运行时状态
- Redux：装 React DevTools 扩展后 `$r.store.getState()`。
- SSR 注入：`window.__NEXT_DATA__` / `__INITIAL_STATE__` / `reduxStore.getState()` 等全局键。
- 无 store 暴露：遍历 DOM 节点的 `__reactInternalInstance$*` 属性递归找 state（脆弱，依赖内部结构命名）。

## 6. 工具线索（本次验证状态）
- `fuse-browser`：启发式/CSS 确定性/虚拟列表穷举，读渲染后 DOM — **npm 不可装（000）**。
- `mantis`（`@yrstm/mantis`）：单文件零依赖 DOM→结构化 JSON — **npm 404 不可装**。
- 替代：本 skill 的 `scripts/curl_xhr.py`（L2 直连重放 + 字段抽取）已落地可用。
