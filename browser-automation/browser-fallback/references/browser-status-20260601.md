# 浏览器降级参考

## 验证结果（2026-06-01）

| 工具 | 状态 |
|------|------|
| browser_navigate/click/type (CDP engine → 9222) | ✅ 主要方案，用户Chrome已登录 |
| mcp_chrome_* | ❌ 报错 "Failed to connect to MCP server"（因stdio-config.json缺失，不影响） |
| Playwright CDP ws://localhost:9333 | 备用方案（chrome-debug独立profile无登录态） |
| Runtime.evaluate via CDP WebSocket | ✅ 直接JS注入读取DOM，React SPA内容完整 |

## 架构结论（2026-06-01 修正版）

用户Chrome（9222）为主力，Hermes Browser CDP engine直连：
- **不依赖截图**：CDP + DOM/Accessibility Tree 读取，200-4000 tokens
- **不依赖 VLM**：只有 Canvas 验证码/复杂图表才需要 Vision
- **不依赖 MCP Chrome Server**：stdio-config.json 缺失，但 browser 工具独立可用

## AI 网站当前状态

| 网站 | CDP 状态 | 登录态 |
|------|----------|--------|
| ChatGPT | ✅ textarea 可用，"有问题，尽管问" | ❌ 需要重新登录（杀进程时session掉了） |
| 豆包 | 待验证 | -- |
| ChatGLM | 待验证 | -- |
| Grok | 待验证 | -- |

## 操作记录

1. ✅ config.yaml → cdp_url='http://127.0.0.1:9222', engine='cdp'
2. ✅ Chrome 启动命令：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" --no-first-run --no-default-browser-check --remote-allow-origins=*`
3. ✅ browser_navigate(chatgpt.com) → 返回完整 snapshot 和 ref IDs
4. ⚠️ 用户需在浏览器中重新登录 ChatGPT 后才能使用对话

## 关键教训

- `pkill -f "Google Chrome"` 可能杀不干净子进程，用 `pkill -9 -f "Chrome"` 更彻底
- Chrome 重新启动后，有些网站的 session cookie 可能会过期，需要用户重新登录
- MCP Chrome server 需要 `stdio-config.json` 文件定义 CDP URL，缺失则永不可用
- built-in browser 工具和 MCP chrome 工具是两套独立的，其中一个失败不影响另一个
