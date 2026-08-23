# 找品技能 2026-08-21 全网升级调研

> 目的：把 1688 找品工作流 8 个环节逐个拆开，搜罗 2026 年全网最优解，对比当前固化方案，标注本机可落地性。
> 调研来源：GitHub（ai-reverse / 1688-Scraper-MCP / zcode-cdp / superjack2050/1688-cli / jiyun/1688 / sakasa.cn 实战）、Scraperly、Browse.sh skill、火山引擎/腾讯云/AdsPower 博客、IPWeb 反检测指南。

## 环节拆解与最优解

### ① 搜索端点 / 关键词编码
- **当前固化**：真实登录 Chrome 跑 `s.1688.com/selloffer/offer_search.htm?keywords=<GBK>` + `province=江浙沪`，翻页+滚动懒加载，解析内联 HTML 抓 offerId。
- **2026 最优（有代理）**：MTOP JSON API `h5api.m.1688.com`，方法 `mtop.relationrecommend.WirelessRecommend.recommend`（appId=32517），md5 sign = `MD5(token & ts & appKey & data)`，token 取自 `_m_h5_tk` cookie。返回干净结构化 JSON（标题/最低价/MOQ/省份/销量），无需解析 HTML。
  - 签名算法已开源：`sign = MD5(token + "&" + timestamp_ms + "&" + appKey + "&" + data)`，appKey=12574478（QuoVadis86/ai-reverse 完整还原）。
- **本机限制**：MTOP 直连需**中国住宅代理 + 登录态**，非中国 IP / 数据中心 IP 被 geo-block 到登录墙（Scraperly 2026-06 实测）。本机真实 Chrome 是浙江家庭宽带，无此问题，但**没有代理就不能走 MTOP 直连**。故本机保持现状端点即可（已是最优可落地）。

### ② 登录态持久化
- **当前固化**：MCP 独立 Chromium `drission_user_data` profile。
- **2026 最优**：CDP 接管真实 Chrome（zcode-cdp：首次 `rsync` 日常 Chrome profile 继承登录态，端口租约池 9223-9229 防多 agent 抢端口，三层看门狗防僵尸）。或 `--user-data-dir` 持久目录（chrome-devtools-mcp `--autoConnect`）。
- **本机可落地**：✅ 已有真实 Chrome 登录态。可加 zcode-cdp 式端口租约治理（防并发抢端口），属锦上添花。

### ③ 浏览器驱动
- **当前固化**：AppleScript `execute javascript` + CDP。
- **2026 最优**：Playwright `connectOverCDP('http://127.0.0.1:9222')` + **CDP 协议点击**（`input.dispatchMouseEvent` → `isTrusted=true`，反爬无法区分真人与 CDP）。SeleniumBase CDP Mode 同原理。
- **本机可落地**：✅ 已用 CDP。AppleScript 点击也是 CDP 底层，等价。无需改。

### ④ 列表提取（offerId）
- **当前固化**：解析 `document.documentElement.outerHTML` 抓 `detail.1688.com/offer/(\d+)` + `offerId=`。
- **2026 最优（有代理）**：MTOP `getOfferList` 直出 offerId 列表（见①）。
- **本机可落地**：⚠️ 无代理退化为现状（已是最优可落地）。

### ⑤ 尺寸规格识别（连写 + 矩阵）
- **当前固化**：`verify_carton_matrix.js` —— 三路命中（连写 L*W*H / 长宽轴 `8x8（长宽）` / 高轴 `9cm（高）` 组合）。已修全角左括号 `（` 漏判。
- **2026 最优**：同。矩阵式（长宽×高）是 1688 彩盒定制类特有写法，连写+矩阵双识别已覆盖全部已知格式。
- **本机可落地**：✅ 已固化，无需改。

### ⑥ 品类过滤（排礼盒）
- **当前固化**：`cartonSig`（纸箱/包装盒/纸盒…） + `giftSig`（礼盒/烫金/巧克力…）二次过滤。
- **2026 最优**：同。MTOP `isShiliDangKou`（实力商家）字段可加，但品类判断逻辑不变。
- **本机可落地**：✅ 已固化。

### ⑦ 价格 / 库存 / SKU 提取 —— **本轮重点升级点**
- **当前固化**：`price_clean3.js` —— DOM 点击目标尺寸 chip 读 `.item-price-stock`，或正则从 SKU 块抠 `尺寸 ¥价 库存`。
- **2026 最优**：**Playwright 拦截 MTOP `queryofferskuselectormodel` 响应包**（sakasa.cn 实战），无需逆向签名——浏览器合法请求已被发出，脚本只做"中间人"拦截：
  - `skuPropsList`：规格维度（颜色/尺寸）。
  - `skuMapOriginal`：Key=规格组合，Value 含 `discountPrice`（真实成交价）+ `canBookCount`（实时库存）。
  - 由 Playwright `page.on("response", ...)` 监听，JSONP 去括号后 `json.loads`。
  - 比 DOM 点击稳 10 倍：不依赖页面渲染、不踩 size-bar 点击失效、能拿**全 SKU 价格表**而非单一尺寸。
- **本机可落地**：⚠️ 当前用 AppleScript 驱动，未用 Playwright 拦截。可升级为 Playwright CDP 接管同一真实 Chrome + 拦截 MTOP 包。脚本草稿见 `scripts/price_mtop_capture.py`（待补）。**注意**：仍走真实登录 Chrome（非 headless），geo-block 不触发。

### ⑧ 反爬 / CAPTCHA 对抗
- **当前固化**：降速（每个详情页 6-8s）+ 真人手动过验证。
- **2026 最优**：
  - 行为层：CDP 协议点击（`isTrusted=true`）+ 随机延迟 + 拟人滚动（已部分具备）。
  - 验证码层：**自动识别 + 人工介入混合**（火山引擎实战）：简单图形/滑块接打码平台（超级鹰 ~1分/次，滑块 DrissionPage 模拟轨迹成功率 50%；打码平台坐标返回 70%）；复杂/极验升级版秒转人工。优先顺序：避免（保持登录态）→ 人工 → 打码 → 弃号。
  - 环境层：住宅代理轮换（本机无需，真实 Chrome 已是中国 IP）。
- **本机可落地**：⚠️ 打码平台需付费账号（超级鹰/图鉴），属可选升级。当前降速+真人过对本机够用。

## 本机可立即落地的升级（按性价比排序）
1. **环节⑦ 价格提取升级为 Playwright MTOP 拦截**（scripts/price_mtop_capture.py）—— 最值得，稳10倍，无需代理/付费。
2. **环节② 端口租约治理**（防并发抢 9222）—— 多 agent 并发时才有用，单机当前够用。
3. **环节⑧ 接打码平台** —— 需付费账号，非必需。

## 受本机限制的环节（保持现状即最优）
- ① 搜索端点 / ④ 列表提取：MTOP 直连需中国住宅代理，本机真实 Chrome 无代理走 HTML 解析已是此地最优。
- ⑧ 打码平台：需付费，降速+真人过够用。

## 结论
当前固化方案（真实 Chrome + CDP + HTML 解析 + 矩阵尺寸识别）在**无代理条件下已是 2026 最优可落地形态**。唯一明确可升级的是**环节⑦ 改用 Playwright 拦截 MTOP SKU 包**，能显著提升价格/库存提取的稳定性和完整度。其余环节或已最优、或受本机无代理/无付费账号限制。
