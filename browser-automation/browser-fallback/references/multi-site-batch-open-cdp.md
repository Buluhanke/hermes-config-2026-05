# Multi-Site CDP Batch Open — Verified Recipe (2026-06-03)

End-to-end verified: opened 6 AI sites, all logged in, extracted page state for each in one session.

## Sites tested
- https://gemini.google.com/app
- https://www.doubao.com/chat
- https://chatglm.cn/main/alltoolsdetail?t=1780109684914&lang=zh
- https://chat.deepseek.com/
- https://chatgpt.com/
- https://grok.com/

## Working pattern (via `browser_cdp` tool)

**Why `browser_cdp` not `mcp_chrome_*`**:
- `mcp_chrome_chrome_navigate` was in 12-failure cooldown
- `mcp_chrome_chrome_close_tabs` failed with "Failed to connect to MCP server"
- `browser_cdp` worked first try — handles Chrome 148+ Origin check via Hermes supervisor

**Recipe**:
```python
# 1. Browser-level call: get all targets (returns existing tabs only)
result = browser_cdp(method="Target.getTargets")
# result.result.targetInfos is the list

# 2. For each site, create a new tab
new_id = browser_cdp(method="Target.createTarget", params={"url": "https://..."})
target_id = new_id["result"]["targetId"]

# 3. attach to that tab (returns sessionId for the tab)
attach = browser_cdp(method="Target.attachToTarget", params={"targetId": target_id})
# sessionId is attach["result"]["sessionId"]

# 4. For Runtime.evaluate, you can pass target_id instead of sessionId
title_resp = browser_cdp(
    method="Runtime.evaluate",
    params={"expression": "document.title"},
    target_id=target_id
)
# Note: do NOT pass "returnByValue" in params — the tool's validation rejects
# bool at that binding position. The tool wraps the call correctly on its own.

# 5. body content
body_resp = browser_cdp(
    method="Runtime.evaluate",
    params={"expression": "document.body ? document.body.innerText.substring(0, 500) : 'no body'"},
    target_id=target_id
)
```

**Common gotchas hit during this session**:

1. `/json/new` HTTP endpoint returns **405 Method Not Allowed** in Chrome 148+
   → Use `Target.createTarget` CDP method instead

2. `Target.attachToTarget` with `flatten: true` rejected with
   `'Failed to deserialize params.flatten - BINDINGS: bool value expected at position 59'`
   → Just omit `flatten`. The sessionId still comes back fine.

3. `Runtime.evaluate` with `returnByValue: true` rejected with
   `'Failed to deserialize params.returnByValue - BINDINGS: bool value expected at position 101'`
   → Just omit `returnByValue`. The tool returns the value as `.result.result.value` anyway.

4. Python `websocket-client` from a script gives **403 Forbidden** because Chrome
   148+ requires Origin header on the WebSocket handshake
   → `browser_cdp` tool handles this; if you must use raw websockets, you need
   Node `ws` with `headers: { 'Origin': 'http://127.0.0.1:9333' }` (Python's
   `websocket-client` doesn't support custom headers cleanly in some versions).

5. The `Target.attachToTarget` returns `sessionId` — but the **tool binding**
   doesn't easily let you route subsequent `Runtime.evaluate` calls by
   `sessionId`. Instead, pass `target_id` (the `targetId` from `createTarget`).
   The `browser_cdp` tool routes correctly.

## Verified page states (2026-06-03)

| Site | Login | Body preview (first 80 chars) |
|------|-------|-------------------------------|
| Gemini | ✅ Pro | "Gemini / 与 Gemini 对话 / 分享当前页面 / Pro" |
| Doubao | ✅ | "豆包 / 新对话 / ⌘ K / AI 创作 / 云盘 / 更多 / 历史对话 / 1+1等于几 / Mac Mini 24G Hermes自动化..." |
| ChatGLM | ✅ | "智谱清言 / GLM-5.1 / 升级 / 今天，有什么新想法？🤔" |
| DeepSeek | ✅ | "DeepSeek - 探索未至之境 / 使用快速模式开始对话 / 快速模式 / 专家模式 / 识图模式" |
| ChatGPT | ✅ | "ChatGPT / 跳至内容 / 历史聊天记录 / 新聊天 / ... 最近: 数学问题 / Mac Mini Hermes 解法" |
| Grok | ✅ | "Grok / 切换侧边栏 / 搜索 / ⌘K / 新建聊天 / Imagine / 项目 / 新项目 / 历史记录 / 昨天 / Hermes WebUI textarea sends but button gray" |

**All 6 had login state and were immediately usable** — the user's Chrome at
`~/.hermes/chrome-debug` (port 9333) has all these cookies persisted.

## Login detection snippet

```javascript
(() => {
    const t = (document.body ? document.body.innerText : '').toLowerCase();
    return t.includes('sign in') ||
           t.includes('登录') ||
           t.includes('log in') ||
           t.includes('欢迎回来');
})()
```

Returns `true` if the page is showing a login wall.

## Next step: input the question and read reply

The 6-site-open step is verified. The next stage ("fill textarea, send, read AI reply")
uses the patterns in `chrome-cdp-automation` skill (Tier 1 site-specific selectors,
bodyLen growth completion signal). Not yet verified in this session — out of scope
for the "open + verify login" milestone.
