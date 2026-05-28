# 1688 详情页数据抓取 — 2026-05-29 实测

> ⚠️ **CDP端口已更新**：9222（用户Chrome，有登录态）已替代9333（Hermes专用，无登录态）。完整代码模板已移入SKILL.md，请参考SKILL.md内嵌的「✅ 2026-05-29 确认方案」章节。

## 价格选择器 `.item-price-stock`

1688 详情页价格字段选择器：`.item-price-stock`（阶梯价）

## CDP端口选择（2026-05-29 实测确认）

| 端口 | Chrome来源 | 1688登录态 | 状态 |
|------|-----------|-----------|------|
| **9333** | Hermes专用 `~/.hermes/chrome-debug` | ❌ 无 | ❌ 不可用 |
| **9222** | 用户Chrome（需手动启动时加参数） | ✅ 有 | **✅ 已跑通全流程** |

## 核心结论

1. **9333端口Chrome无用户登录态** — 搜索/详情页会被重定向到淘宝登录页，必须用9222
2. **价格字段渲染时机** — 需要 `time.sleep(5~6)` 等JS渲染
3. **offerId提取** — 从href中提取（格式：`offerId=数字&`），innerHTML的data属性为空
4. **cloakbrowser.launch() vs CDP连接** — 前者开新浏览器无登录态，后者连已有浏览器可继承cookies
5. **WebSocket需要suppress_origin=True** — 否则403 Forbidden
6. **详情页URL格式** — `https://detail.1688.com/offer/{offerId}.html`

完整代码模板见 SKILL.md 的「✅ 1688全流程已跑通（2026-05-29）」章节。
