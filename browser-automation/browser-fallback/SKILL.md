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

## 优先级（已确认 2026-06-01）

1. **Browser工具 CDP engine** (`browser_navigate/click/type/snapshot`) — 主要，完全可用
   - 直连 `http://127.0.0.1:9222`（用户真实Chrome）
   - 不走 MCP bridge，MCP失败不影响
2. **Playwright CDP** (`ws://localhost:9333`) — 备用，需要Chrome开启debug端口

## 降级触发

当 `browser_navigate` 报错（独立Chromium实例问题）时，尝试：
1. `computer_use` 控制用户真实Chrome（已登录态）
2. Playwright CDP 直连 `ws://localhost:9333`（需要chrome-debug Chrome在跑）

## 验证结果
- MCP chrome bridge: 报错 "Failed to connect to MCP server"
- browser工具: ✅ 正常，可打开网站、点击、输入、截图
- Playwright CDP备用: ws://localhost:9333 直连

## 已验证可用的AI对话网站
| 网站 | 状态 | 备注 |
|------|------|------|
| Gemini | ✅ 可访问 | 需要用户Chrome登录态 |
| 豆包 | ❌ 需登录 | 临时实例无cookies |
| ChatGLM | ❌ 需登录 | 临时实例无cookies |
| DeepSeek | ⚠️ 429限速 | 未登录 |
| ChatGPT | ⚠️ 403 | 未登录 |
| Grok | ✅ 可访问 | 未登录 |

## 架构结论（2026-06-01 确认）

用户Chrome（9222）已达最优，无需额外配置：
- `browser_navigate` → 307元素Accessibility Tree，@eN ref_id可用
- 1688/淘宝/京东/AI网站：直接操作，不需要截图/VLM
- 只有Canvas验证码/复杂图表才需要Vision

**browser工具临时实例**：无用户cookies，每次session重新创建，适合不需要登录的网页操作。

## 相关
- chrome-debug: Chrome debug配置
