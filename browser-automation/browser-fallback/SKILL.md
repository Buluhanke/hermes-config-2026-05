---
name: browser-fallback
description: 浏览器控制降级策略 — MCP chrome bridge失效时自动切换到browser工具
triggers:
  - MCP chrome连接失败
  - "Failed to connect to MCP server"
  - chrome_navigate报错
  - browser工具可用但MCP不可用
---

# Browser Fallback（浏览器控制降级）

## 优先级
1. **Browser工具** (`browser_navigate/click/type`) — 主要，完全可用
2. **Playwright CDP** (`ws://localhost:9333`) — 备用，需要Chrome开启debug端口

## 降级触发
当 `mcp_chrome_chrome_navigate` 返回 "Failed to connect to MCP server" 时，切换到 `browser_navigate`。

## 验证结果
- MCP chrome bridge: 报错 "Failed to connect to MCP server"
- browser工具: ✅ 正常，可打开网站、点击、输入、截图
- Playwright CDP备用: ws://localhost:9333 直连

## 已验证可用的AI对话网站
| 网站 | 状态 | 备注 |
|------|------|------|
| Gemini | ✅ 可访问 | 需要debug profile登录态 |
| 豆包 | ❌ 需登录 | Playwright临时实例无cookies，显示登录按钮 |
| ChatGLM | ❌ 需登录 | Playwright临时实例无cookies，显示登录按钮 |
| DeepSeek | ⚠️ 429限速 | 未登录 |
| ChatGPT | ⚠️ 403 | 未登录 |
| Grok | ✅ 可访问 | 未登录 |

## 当前限制
- browser工具Playwright临时实例：无用户cookies，每次session重新创建
- MCP chrome bridge：报错 "Failed to connect to MCP server"
- **所有AI网站在临时实例里均需重新登录或被风控拦截**
- 长期方案：用户手动在chrome-debug Chrome登录，cookies持久化

## 相关
- chrome-debug: Chrome debug配置
