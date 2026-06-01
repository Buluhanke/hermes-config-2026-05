# 浏览器降级参考

## 验证结果（2026-06-01）

| 工具 | 状态 |
|------|------|
| mcp_chrome_* | ❌ 报错 "Failed to connect to MCP server" |
| browser_navigate/click/type | ✅ 正常 |
| Playwright CDP ws://localhost:9333 | 备用方案 |

## AI网站可访问性

| 网站 | curl | 备注 |
|------|------|------|
| Gemini | 200 | 未登录 |
| 豆包 | 301 | ✅ 已登录 |
| ChatGLM | 200 | ✅ 已登录 |
| DeepSeek | 429 | 限速 |
| ChatGPT | 403 | 未登录 |
| Grok | 200 | 未登录 |

## 问题
Chrome debug profile (9333端口) 没有继承用户正常Chrome的登录cookies。
