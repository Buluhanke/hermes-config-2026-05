# SearXNG MCP 故障应急方案（2026-06-02 实测）

## 故障现象

- `web_search` → SearXNG HTTP 502
- `mcp_searxng` → 同上
- 配置：`config.yaml` 中 `mcp_servers.searxng.env.SEARXNG_URL=https://searx.be`

## 根因

searx.be 对 API 请求返回 403 Forbidden（OpenResty 拒绝非浏览器请求）。

公开 SearXNG 实例大面积失效或限流：
- searx.be → 403（不可用）
- searxng.org → 200（但 GitHub Pages 跳转，非真实搜索）
- searx.tuxcloud.net → 429（限流）
- 其他测试实例 → 000 / 530（不可达）

## 搜索降级链（更新）

1. `ddgs`（DuckDuckGo SDK，免费）— 首选
2. GitHub API（免认证，rate limit 宽松）
3. `browser_navigate` 直接访问目标站点
4. 全部失败 → 读本地 Brain_Lab 最新存档

**当前结论**：日常搜索用 ddgs，SearXNG MCP 仅作本地开发测试。

## 参考实例可用性（2026-06-02）

| 实例 | 状态 | 备注 |
|------|------|------|
| searx.be | ❌ 403 | 不可用 |
| searxng.org | ✅ 200 | 但路由跳GitHub Pages，需验证 |
| searx.tuxcloud.net | ⚠️ 429 | 限流 |
| search.kavin.rocks | ⚠️ 530 | 不可达 |

## 预防

SearXNG MCP 不适合依赖公开实例（稳定性差）。优先用 ddgs，需要本地 SearXNG 时自建。