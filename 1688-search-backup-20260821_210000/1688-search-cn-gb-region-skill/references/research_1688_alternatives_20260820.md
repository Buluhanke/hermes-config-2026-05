# 1688 找品「更优方案」全网调研结论（2026-08-20）

本机环境：个人 Chrome 登录态 + macOS + 无企业营业执照 + 无中国住宅代理。本次为验证 skill 是否该升级而做的横向调研。结论：**维持方案0（真 Chrome + AppleScript），不切换。**

## 候选方案对比

### A. 1688 开放平台官方 API（alibaba.item.get / 1688.item_get）
- 能力：合规、JSON 结构化、返回完整 SKU/阶梯批发价/MOQ/工厂资质，无需反爬。
- 接入：open.1688.com 创建应用 → 拿 app_key/app_secret → HMAC-SHA1/MD5 签名 → `gw.open.1688.com/openapi/param2/...`。
- **本机不适用根因**：
  - 须**企业实名认证 + 中国营业执照**；个人号权限极低，批发价/供应商字段拿不到。
  - 须固定 IP 白名单；本机出口 IP 不满足。
  - 数据 10–30 分钟缓存，非实时。
- 定位：合规升级路径，留给有企业账号的用户；个人场景不现实。

### B. 第三方 1688-Scraper-MCP（DrissionPage 真实 Chromium）
- 代表：`xiayumu034-crypto/1688-Scraper-MCP`（search_1688_products / get_product_detail_and_price / update_auth_cookie / get_product_reviews / analyze_supplier_reliability）。
- 能力：本地过滤地域/工厂、抠阶梯价、防语水评价、供应商背调（牛头标/回头率）。
- **本机状态**：已集成进本 skill（见 `references/1688_mcp_setup.md`）。搜索端点仍被 1688 风控踢回 login.taobao.com；详情页端点可用（drission_user_data 登录态持久化）。维持「搜索走方案0、详情走 MCP」半自治。

### C. MTop 签名逆向 + h5api.m.1688.com 直连
- 算法：`sign = MD5(_m_h5_tk前半 + "&" + timestamp_ms + "&" + appKey + "&" + data)`，token TTL ~24h。参考 `ihmily/1688-Decryptor`、`QuoVadis86/ai-reverse`。
- **本机已排除（坑12）**：无中国住宅代理 + 无登录态 cookie 时，直连返回 `RGV587_ERROR` 验证码惩罚页或 CORS 空返回；阿里对非完整浏览器流程直接丢验证码。本机无代理，**纯接口直连走不通**。

### D. 商业爬虫 API / 代理（Oxylabs / Bright Data / Scraperly）
- 能力：托管代理+解析，返回 HTML/JSON。
- **本机不适用**：按量付费 + 需中国住宅代理池；本机无代理，且增加外部依赖与成本。

### E. 油猴脚本（Tampermonkey）
- **本机已排除（坑13）**：1688 返回严格 CSP，阻止 content script 注入，装了不执行。

## 结论速记
| 方案 | 合规 | 本机可行 | 备注 |
|---|---|---|---|
| 方案0 真Chrome+AppleScript | 中（登录态爬） | ✅ | 当前默认 |
| A 官方API | ✅ | ❌ 无企业账号 | 升级路径 |
| B 第三方MCP | 中 | ⚠️ 详情可用/搜索风控 | 已集成 |
| C MTop逆向 | ❌ | ❌ 无代理 | 已排除 |
| D 商业爬虫API | 中 | ❌ 无代理/付费 | 不适用 |
| E 油猴 | ❌ | ❌ CSP拦截 | 已排除 |

**给未来 session 的指令**：除非用户明确提供「企业认证 app_key/app_secret」或「中国住宅代理」，否则不要重试 A/C/D/E——直接走方案0（本 skill 已固化）。若用户给了企业账号，优先 A（合规+结构化），详情页接口 `alibaba.item.get` 一步拿全 SKU 阶梯价，可淘汰 price_clean3.js 的 DOM 抠取法。
