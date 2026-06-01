# 浏览器降级参考

## 验证结果（2026-06-01）

| 工具 | 状态 |
|------|------|
| browser_navigate/click/type (CDP engine → 9222) | ✅ 主要方案，用户Chrome已登录 |
| mcp_chrome_* | ❌ 报错 "Failed to connect to MCP server"（不影响） |
| Playwright CDP ws://localhost:9333 | 备用方案，chrome-debug独立profile无登录态 |

## 架构结论

用户Chrome（9222）为主力，Hermes Browser CDP engine直连：
- 1688首页：307个可交互元素，@eN ref_id可用
- 1688/淘宝/京东/AI网站：直接操作，不需要截图/VLM
- 只有Canvas验证码/复杂图表才需要Vision

## AI网站可访问性

| 网站 | curl | 备注 |
|------|------|------|
| Gemini | 200 | 用户Chrome已登录 ✅ |
| 豆包 | 301 | 用户Chrome已登录 ✅ |
| ChatGLM | 200 | 用户Chrome已登录 ✅ |
| DeepSeek | 429 | 限速 |
| ChatGPT | 403 | 未登录 |
| Grok | 200 | 未登录 |

## 端口说明

- **9222**：用户日常Chrome（已登录，生产主力）
- **9333**：chrome-debug独立profile（无登录态，备用）

## 问题
Chrome debug profile (9333端口) 没有继承用户正常Chrome的登录cookies。
