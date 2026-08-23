# 不靠截图看懂网页 — 分层方案 + 全网迭代结论

> 适用：用户铁律 = 禁用调试端口(9222)、禁用另起 Chrome 实例、优先用真实登录态。
> 核心结论：**截图是信息最差的一层，文字/结构化数据才是「看懂」的本源。**

## 一、四层「看懂」能力（自下而上，越往上越准、越快、越省）

| 层 | 方法 | 是否需要截图 | 准确率 | 适用 |
|----|------|-------------|--------|------|
| L0 静态HTML | `web_extract` / `curl` → markdown | ❌ | 高(服务端渲染) | 博客/文档/新闻 |
| L1 DOM文本 | `Runtime.evaluate(document.body.innerText)` / AX树 | ❌ | 高(零OCR误差) | SPA/登录站/现代网页 |
| L2 JS运行时 | 读 `window.__NEXT_DATA__`/Redux store；`Network.getResponseBody` 抓 XHR 原始 JSON | ❌ | 最高(后端真数据) | 表格/列表/仪表盘/数据驱动页 |
| L3 直接API | 官方 REST/curl + cookie | ❌ | 最高 | 已知接口 |
| (兜底) 截图OCR | `computer_use`截图 + Tesseract | ✅ | 低(有损/常失败) | Canvas/WebGL 纯像素 |

## 二、本机实测踩坑（已验证 2026-08-22）
1. `browser_exec`(browser-use daemon) 默认连**云端**而非本地 Chrome → CDP 握手 HTTP 403。
   → 不要依赖 browser-use 读本地登录态；它不是读页面的工具，是操作工具。
2. `computer_use(list_windows)` **只枚举 Cua Driver + Hermes**，枚举不到 Chrome/其他 app 窗口。
   → 对第三方 app 抓 AX 树当前走不通；合规主路径是让 Hermes 自己开受控浏览器去读。
3. 用户 Chrome 实例常驻但**窗口为 0** 时，所有「读你屏幕浏览器」路径无目标。
   → 此时改走 Hermes 内置 browser 后端，而非截屏。
4. `vision_analyze` 对有效 PNG 反复「看不到图片」→ 截图链失效 1 次即降级，绝不重试。

## 三、全网搜到的新认知（迭代点）
- **AX 树 > 截图是 2026 行业共识**（Prophet/Playwright-MCP/microsoft 均选 AX 树）：
  - 快 2-4×、便宜 4×、文字零 OCR 误差、确定性（不靠视觉概率）。
  - 唯一输给截图的场景：Canvas/WebGL 纯像素、依赖空间布局（"右边那个按钮"）、图片内信息。
- **「你通常不需要 DOM，要的是 Network 拦截的 JSON」**（pickuma/dev.to 实战）：
  - 11 个无 API 目标里 8 个只要拦截 1 个 XHR JSON 就够；XHR 比 DOM 抗前端重构。
  - DOM 读 9 个月坏 6 次（class 改名），XHR 只坏 2 次（字段改名，且 schema 校验会 loudly 报错）。
  - 做法：DevTools Network 过滤 XHR/Fetch → 找到 JSON 请求 → 用 cookie 重放（注意 nonce/CSRF/签名 URL 风险）。
  - **铁律（Skynet 经验）**：DOM 优先 → Network 观察次之 → Fetch 拦截仅在有理由时 → 重放只在校验过不变量后。
- **Shadow DOM**：Crawl4AI v0.8.5+ `flatten_shadow_dom=True` 已能 force-open closed shadow root；
  Playwright 原生 selector 默认穿透 open shadow root；AI 站(ChatGPT/豆包)回复在 shadow 里，用 AX 树/递归 `shadowRoot` 读。
- **本地运行时读 Redux/React 状态**（无 DevTools 扩展时）：
  - Redux：`$r.store.getState()`（需 React DevTools 扩展），或用 `window.__NEXT_DATA__` 等 SSR 注入。
  - React 无 store 暴露：遍历 `__reactInternalInstance$*` 属性递归找 state（stackoverflow 方案，脆弱）。
- **新工具线索（待验证）**：
  - `fuse-browser`：`browser_extract`(启发式) / `browser_extract_schema`(CSS 确定性) / `browser_collect`(虚拟列表滚动穷举) — 读渲染后 DOM，值得试。
  - `mantis`：单文件零依赖，把可见内容→结构化 JSON/Markdown（Readability 风格），适合读后内容压缩。
  - `webscrapingapi json_dom`：一站返回结构化 DOM JSON（云端，需 key）。

## 四、推荐工作流（写进 skill 的 SOP）
1. 公开静态页 → `web_extract`（L0，最快，已验证可用）
2. 登录站/SPA → 让 Hermes 浏览器后端打开 → `Runtime.evaluate(innerText)`（L1）
3. 数据驱动页 → `Network.getResponseBody` 抓 XHR JSON（L2，最准）
4. AI 站回复 → AX 树 / shadow 递归（L1 变体）
5. 以上全失败才截图 OCR（降级链尽头）

## 五、迭代实验进度（2026-08-22 已执行）
- A ✅ L2 curl 重放 XHR 实证通过：HackerNews/GitHub/JSONPlaceholder 三类数据源均零截图拿到结构化 JSON。泛化能力证实。
- A2（实测，2026-08-23）：`read_url.py` 抓 `https://www.1688.com/` 首页成功（via scrapling-fetch，250KB，含挑好货/找工厂/工业品导航）；但抓 `s.1688.com/selloffer/offer_search.htm?keywords=纸箱` **被登录墙/滑块拦截**（返回 2584 字节登录页，非商品列表）。→ **实证边界**：1688 公开首页无头可抓，搜索/商品流需登录态；登录态页走 L1 前台 AX 树（read_chrome.py，你已登录的前台窗口）或 A2 curl_xhr.py --cookie。
- L1 前台 AX 树实证（2026-08-23）：前台 Chrome 打开 1688 首页，`computer_use(mode='ax')` 抓到 1157 节点，read_chrome.py 解析成功（首页非商品列表，匹配 1 弱卡片正常）。导航到搜索页即可读商品流。

- B ⚠️ `mantis` / `fuse-browser` 在 npm registry **不可装**（`@yrstm/mantis` 404、`mantis`/`fuse-browser` 000 不可达）。放弃。
- B2 ✅ **前台 Chrome AX 树读取打通（2026-08-22 实证）**——这是关键突破：**不需要 9222、不需要调试端口、不需要新实例**。
  **方法**：`computer_use(action='capture', app='Google Chrome', mode='ax')` 直接读前台真实 Chrome 窗口的无障碍树（1035~1184 节点），点击用 `coordinate` = native bounds ÷ 1.36（Cua Driver 0.17 不接受裸 element_index，需传坐标）。
  **实证**：在登录态 1688 搜索页 `s.1688.com/selloffer/offer_search.htm?keywords=16*16*16cm纸箱`，零截图读出 14 个商品（标题/价格/销量/供应商）；点进第 1 名详情页，AX 树完整读出规格 SKU 矩阵（40+ 尺寸含半高箱）、材质硬度等级、件重尺表（长×宽×高×体积×重量）。
  **结论**：L1 对任意页面（含登录态真实页）的实时读取已「随时」——只要该页面在你前台打开的 Chrome 里。9222 阻塞点被绕过。
  **注意**：Cua Driver 0.17 的 click 返回 `unverifiable` 是假阴性（页面跳转后 capture_after 拍照过早）；重抓 AX 树即可验证，无需重试。

## 六、已落地的可复用资产
- `scripts/read_chrome.py`：**一键 L1 解析层**（2026-08-22 新增，已实跑验证）。自动定位 `~/.hermes/cache/computer_use/elements_*.json` 最新 AX 缓存并结构化：
  - `--products` 商品卡片(标题/价格/销量/供应商) ｜ `--sku` SKU 尺寸矩阵 ｜ `--spec` 件重尺表 ｜ `--links` 可点击链接+bounds ｜ `--watch` 报告最新缓存路径 ｜ 默认自动判电商页/全量文本
  - **用法闭环**：对话里让我 `computer_use(mode='ax', app='Google Chrome')` 抓一次 → 脚本解析。零截图/零调试端口/零新实例。
- `scripts/parse_ax.py`：L1 AX 树解析层（同上，但手动指定 `--file` 输入路径）。
- `scripts/read_url.py`：**L0/L2 失败降级链**（2026-08-23 新增，已实跑验证）。纯本地可验证工具三层重试：`scrapling extract get` → `scrapling extract fetch --network-idle` → `curl -sL`。不依赖对话沙箱外的 hermes_tools。用法：`python3 read_url.py <url> [--out file] [--json]`。
  `python3 scripts/curl_xhr.py "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=2" "hits.0.title" "hits.0.points"`
- `SKILL.md` 顶部「零截图读懂（首选路径）」整节 + 四层表 + L2 黄金法则 + 本机 5 坑 + L2 实证。
- `ZERO_SHOT_READ_MAP.md`：本文件。

## 六·五、生态技能补充（2026-08-23）
- **用户铁律（2026-08-23 新增，最高优先）：默认不走无头**。`read_url.py` / `scrapling` / `curl` 无头抓取全部**禁用**为默认路径。只读你**已登录的前台 Chrome**（L1 `read_chrome.py`，`computer_use(mode='ax')` 抓取）。无头仅在你**显式要求**后台无前台窗口时才可用（且仍走 A2 `curl_xhr.py --cookie`，不裸用 scrapling/curl 猜页）。
  - 理由：无头抓登录态页必被墙（1688 搜索页实测 2584 字节登录页拦截）；前台真登录态才读得到真实内容，且符合「不另起实例/不碰调试端口」原则。

  - **定位**：强化 L0/L2 的**无头批量抓取**（尤其反爬/JS 渲染站），与 L1 前台 AX 树**互补**：scrapling 抓公开/无登录页，L1 读你已登录的前台页。两者都不碰调试端口、不另起 Chrome 登录态。
  - 用法：`scrapling extract get <url> out.md`（静态）｜ `scrapling extract fetch <url> out.md --network-idle`（JS 渲染）｜ `scrapling extract stealthy-fetch <url> out.html --solve-cloudflare`（反爬）。
  - **降级链接入**：SKILL.md 读取优先级图已含 Scrapling 第二层，旧 `Paparazzi.fetch()` 已改为实测 `scrapling extract` CLI。
- **未装（已决策跳过）**：`1688-shopkeeper`（community / skills.sh，Repo: next-1688/1688-shopkeeper，2964 stars，1688 官方「开店 Claw」）—— 实跑核对 GitHub README + SKILL.md 原文后判定：**不装**。理由：(1) 它是「选品铺货到抖店/拼多多/小红书/淘宝」的电商运营技能，靠 `ALI_1688_AK`（1688 AI版 APP 凭证）驱动 `cli.py`，与 browser-read-funnel 的「零截图读网页/L1 前台 AX 树」定位不重合；(2) 需 AK 凭证 + 绑定店铺，引入无关凭证和平台依赖，违反「不引入无关凭证」原则；(3) 其 `prod_detail` 走官方 AK 接口而非读前台 Chrome 登录态，与我的 L1 路径是两套不同机制。保留为「已知但不用」参考项。

## 七、当前「随时识别」能力边界（诚实版 · 2026-08-23 更新）
- ✅ 随时：公开静态页(L0 web_extract / scrapling HTTP) / 有 XHR·REST 端点的数据页(L2 curl 重放) / 纯文本 API
- ✅ 随时（已打通）：**你前台 Chrome 里打开的任意页面**（含登录态真实页如 1688），用 `computer_use` 抓前台 AX 树(L1)，零截图、零调试端口、零新实例
- ✅ 随时（新增）：**反爬/JS渲染/Cloudflare 站** 用 scrapling 无头抓取（官方技能，已装+验证）
- ⏸️ 待解：完全无头/后台的登录页（无前台窗口时）——仍需 A2（`scripts/curl_xhr.py --cookie`）；豆包/Gemini 等需 Cookie 重放的页尚未实跑

## 八、下一步
- 无前台窗口的登录页 → 给 URL + 从浏览器复制的 Cookie，跑 A2（`curl_xhr.py --cookie`）补全后台通道。
- 把 scrapling 接入 L0/L2 失败降级链（web_extract 取不到时自动用 scrapling 重试）。
- 把「前台 Chrome AX 树读 L1」沉淀为可复用函数/脚本（自动缩放坐标 + 解析 AX 树为结构化表格）。
