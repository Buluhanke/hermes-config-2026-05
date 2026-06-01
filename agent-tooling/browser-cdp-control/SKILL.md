---
name: browser-cdp-control
description: Direct CDP browser control — DOM extraction, form submission, AI site interaction. Use this when reading/extracting content from browser-controlled websites (ChatGPT, DeepSeek, Gemini, 豆包, etc.).
triggers:
  - "read page content from browser"
  - "fetch text from ChatGPT/DeepSeek/豆包"
  - "extract DOM content via CDP"
  - "browser automation for AI sites"
  - "submit form in Chrome"
---

# Browser CDP Control — Direct DOM Extraction

## Core Principle
**Text content → text extraction. Screenshot → only when text extraction fails.**

Priority order:
1. `web_extract` — fastest, for static/lightweight pages
2. `browser_get_web_content` — for structured page content
3. **CDP Runtime.evaluate** — direct DOM query via WebSocket, most reliable for complex/SPA pages
4. `browser_vision` / `computer_use` — last resort only (dynamic rendering, CAPTCHA, rich text that resists text extraction)

## Architecture

### Chrome Setup (macOS)
- Chrome must run with `--remote-debugging-port=9222` on user's Default profile
- 同一 profile 不能同时以普通模式+调试模式运行 → 先 `pkill -9 -f "Chrome"`，再启动调试模式
- Config: `engine: cdp`, `cdp_url: http://127.0.0.1:9222` in `~/.hermes/config.yaml`

### CDP Direct Access
```python
import urllib.request, json, websocket

# List tabs
with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as f:
    tabs = json.load(f)

# Connect to specific tab
ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id":1,"method":"Runtime.enable"}))
ws.recv()

# Query DOM
ws.send(json.dumps({
    "id": 2,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "document.querySelector('selector').innerText",
        "returnByValue": True
    }
}))
result = json.loads(ws.recv())
ws.close()
```

### Useful DOM Scripts

**Get all conversation messages (ChatGPT etc.)**
```javascript
(function(){
    var msgs = document.querySelectorAll('[data-message-author-role="user"], [data-message-author-role="assistant"]');
    var result = [];
    msgs.forEach(function(m){
        var role = m.getAttribute('data-message-author-role');
        var text = m.innerText.trim();
        if(text) result.push({'role': role, 'text': text.substring(0,600)});
    });
    return JSON.stringify(result.slice(-8));
})()
```

**Get visible text content**
```javascript
(function(){
    var els = document.querySelectorAll('article, .markdown, [class*="message"], p, h1, h2, h3');
    var texts = [];
    els.forEach(function(e){var t=e.innerText.trim(); if(t&&t.length>20) texts.push(t.substring(0,500));});
    return JSON.stringify(texts.slice(-15));
})()
```

## Common Pitfalls

### Tab Discovery
- `browser_navigate` changes URL but may not switch to that tab — always check `curl http://127.0.0.1:9222/json/list` to find the right tab ID
- Look for tab by URL pattern: `'chatgpt.com' in tab.get('url','') and 'newtab' not in tab.get('url','')`

### Slow Page Loads
- AI sites (ChatGPT, 豆包) load slowly — `sleep 15` before capturing response
- Always re-check with `browser_snapshot` after waiting

### WebSocket Timeout
- Set `timeout=15` on WebSocket creation
- If tab URL gives 404, the tab may have been navigated away — re-fetch tab list

### Chrome Profile Conflict
- If CDP returns empty results, Chrome may have crashed/restarted — verify with `curl http://127.0.0.1:9222/json/version`
- If Chrome has restarted, the WebSocket URL changes — re-fetch tabs

## AI网站内容提取（Shadow DOM专用）

ChatGPT、豆包、智谱清言等使用 **shadow DOM**，标准 `document.querySelector` 返回空。必须用特殊JS脚本提取。

### 方法A：全页面递归文本提取（通用首选）
```javascript
// 递归遍历所有shadow DOM，提取所有文本内容
(function(){
    function extractText(node, depth) {
        if(depth > 8) return '';
        var texts = [];
        if(node.nodeType === 3 && node.textContent.trim()) {
            texts.push(node.textContent.trim());
        }
        if(node.shadowRoot) {
            Array.from(node.shadowRoot.childNodes).forEach(function(child){
                texts.push(extractText(child, depth+1));
            });
        }
        if(node.childNodes) {
            Array.from(node.childNodes).forEach(function(child){
                texts.push(extractText(child, depth+1));
            });
        }
        return texts.join(' ');
    }
    return extractText(document.body, 0).substring(0, 8000);
})()
```

### 方法B：AI网站专用的message气泡提取
```javascript
// ChatGPT
(function(){
    var msgs = document.querySelectorAll('[data-message-author-role="user"], [data-message-author-role="assistant"]');
    var result = [];
    msgs.forEach(function(m){
        var role = m.getAttribute('data-message-author-role');
        var text = m.innerText.trim();
        if(text && text.length > 5) result.push({'role':role, 'text': text.substring(0,600)});
    });
    return JSON.stringify(result.slice(-10));
})()

// DeepSeek
(function(){
    var msgs = document.querySelectorAll('.chat-item, .message-item, [class*="message-content"]');
    var result = [];
    msgs.forEach(function(m){
        var t = m.innerText.trim();
        if(t && t.length > 10) result.push(t.substring(0,500));
    });
    return JSON.stringify(result.slice(-10));
})()

// 豆包
(function(){
    var els = document.querySelectorAll('[class*="bubble"], [class*="message-content"], .chat-msg');
    var result = [];
    els.forEach(function(e){
        var t = e.innerText.trim();
        if(t && t.length > 5) result.push(t.substring(0,400));
    });
    return JSON.stringify(result.slice(-10));
})()
```

### 方法C：browser_vision截图（最终兜底）
在 **方法A/B都返回空或内容不完整** 时，才用 `browser_vision`。

**判断流程（严格按顺序）：**
1. `browser_get_web_content` → 有内容？✅ 用
2. CDP Runtime.evaluate + 方法A/B → 有内容？✅ 用
3. 以上皆空或不完整 → `browser_vision` 截图 ✅

**禁止**：不试方法1-2就直接截图。

## Workflow
1. `curl http://127.0.0.1:9222/json/version` — verify Chrome alive
2. `curl http://127.0.0.1:9222/json/list` — find target tab ID
3. `browser_navigate` to target URL (or switch to existing tab)
4. Wait for page load (`sleep` if needed)
5. `browser_snapshot` to get element refs for interaction
6. **Try方法A/B（CDP Runtime.evaluate）**
7. On failure → `browser_vision` as last resort

## Quick Verify
```bash
curl -s http://127.0.0.1:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Chrome {d.get('Browser-Version','?')}\")"
```

## Connected AI Sites (pre-authenticated)
- https://chatgpt.com/
- https://www.doubao.com/chat
- https://chat.deepseek.com/
- https://gemini.google.com/app
- https://chatglm.cn/main/alltoolsdetail
- https://grok.com/z