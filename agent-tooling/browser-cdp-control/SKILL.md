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

### CDP Port Requirement
Chrome 148+ **refuses** `--remote-debugging-port` on the default user data directory. You must use a **custom** directory.

### Gateway Restart Recovery (proven workflow)
After gateway restart/Chrome crash:
```bash
# 1. Kill all Chrome processes + clear lock files
pkill -9 -f "Google Chrome" 2>/dev/null
sleep 2
rm -f "/Users/aimac/Library/Application Support/Google/Chrome/SingletonLock" \
      "/Users/aimac/Library/Application Support/Google/Chrome/SingletonSocket" \
      "/Users/aimac/Library/Application Support/Google/Chrome/SingletonCookie" 2>/dev/null

# 2. Copy Default profile to custom dir, EXCLUDING large cache dirs
rm -rf /Users/aimac/.hermes/chrome-debug 2>/dev/null
cp -R "/Users/aimac/Library/Application Support/Google/Chrome/Default/" \
      "/Users/aimac/.hermes/chrome-debug/"  # 实测4.7GB, ~30-60s
# Or use rsync --exclude=Cache --exclude='Code Cache' --exclude=GPUCache for faster copy

# 3. Launch with custom profile and remote debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="/Users/aimac/.hermes/chrome-debug" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  --disable-blink-features=AutomationControlled \
  --new-window about:blank 2>/dev/null &
sleep 10  # CRITICAL: wait for CDP to be ready

# 4. Verify
curl -s --max-time 5 http://127.0.0.1:9222/json/version | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:' + d['Browser'])"
```

If `--disable-remote-debugging-check` doesn't work, the copy+launch method is the only reliable way.

Config: `engine: cdp`, `cdp_url: http://127.0.0.1:9222` in `~/.hermes/config.yaml`

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

## AI网站交互工作流（实战验证）

### 正确流程（问题→发送→等待→提取）

AI聊天网站（ChatGPT/豆包/DeepSeek/智谱清言/Gemini）使用 WebSocket 流式输出+虚拟DOM渲染，**必须在同一页面完成发送+等待+提取，不能刷新或导航离开。**

```
Step 1: browser_navigate(url)                  → 打开目标AI网站
Step 2: browser_type(ref, text)                → 向textbox输入问题
Step 3: browser_press(key='Enter')             → 发送消息
Step 4: terminal("sleep 20")                   → 等待AI回复（必须等待！）
Step 5: browser_console(expression=...)        → 用CDP提取页面文本
       or browser_vision(question=...)         → 截图提取（模型支持时）
```

### ⚠️ 关键坑

1. **不要 browser_navigate 刷新** — 导航离开当前对话页面会丢失整个对话。SPA页面不保存状态。想在同一个页面内等待回复。
2. **等待时间必须充足** — AI回复需要15-25秒，尤其是搜索+多轮推理（DeepSeek深度思考更久）
3. **textbox ref每次navigate都会变** — ref编号每次页面加载都重新生成
4. **browser_press Enter可能不触发发送** — 某些网站（如Doubao）需要点发送按钮而不是按Enter
5. **Gemini对话不持久** — Gemini在新标签页中打开时对话状态会丢失，回复不可靠

### 提取方法优先级（已验证）

| 方法 | 适用网站 | 效果 |
|------|---------|------|
| `browser_console(expression='document.body.innerText.slice(0,6000)')` | DeepSeek, 智谱清言 | ✅ 可靠 |
| `browser_vision(question=...)` | 所有网站 | ✅ 有效但模型需支持vision |
| CDP Runtime.evaluate (shadow DOM脚本) | ChatGPT | ⚠️ 有时返回空 |
| `web_extract(url)` | 非AI网站 | ✅ 静态页面最快 |

### 多AI站并行采集策略

不要同时打开多个AI网站（每个browser_navigate会覆写当前标签页）。正确方式：**串行处理，逐个完成**。

```
1. 开豆包 → 输入 → Enter → 等待 → 提取 → 完成
2. 开DeepSeek → 输入 → Enter → 等待 → 提取 → 完成
3. 开智谱清言 → 输入 → Enter → 等待 → 提取 → 完成
4. 开Gemini → 输入 → Enter → 等待 → 提取 → 完成
```

## AI网站内容提取（Shadow DOM专用，备用方案）

ChatGPT、豆包、智谱清言等使用 **shadow DOM**，标准 `document.querySelector` 返回空。必须用特殊JS脚本提取。

## AI网站内容提取（Shadow DOM专用，备用方案）

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

## 批量打开多标签页（纯HTTP）

Chrome 的 CDP HTTP API 支持直接创建新标签页，无需走 WebSocket：

```python
import urllib.request, json

# 创建新标签（HTTP POST，无需 WebSocket）
req = urllib.request.Request(
    'http://localhost:9333/json/new',
    method='POST',
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req, timeout=10) as f:
    new_tab = json.loads(f.read())
print(f"新标签ID: {new_tab['id']}")

# 批量为多个站点创建标签
sites = [
    ('https://chatgpt.com/', 'ChatGPT'),
    ('https://chat.deepseek.com/', 'DeepSeek'),
    ('https://www.doubao.com/chat', 'Doubao'),
    ('https://chatglm.cn/main/alltoolsdetail?lang=zh', 'ChatGLM'),
    ('https://grok.com/z', 'Grok'),
    ('https://gemini.google.com/app', 'Gemini'),
]
tab_ids = {}
for url, name in sites:
    req = urllib.request.Request('http://localhost:9333/json/new', method='POST')
    with urllib.request.urlopen(req, timeout=10) as f:
        tab = json.loads(f.read())
    tab_ids[name] = tab['id']
    # 用 CDP Page.navigate 导航到目标 URL
    ws = websocket.create_connection(f"ws://localhost:9333/devtools/page/{tab['id']}", timeout=15)
    ws.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":url}}))
    ws.recv(); ws.close()
    time.sleep(2)
```

**关键点**：
- `/json/new` 是 **HTTP POST**，返回新标签信息（含 id、webSocketDebuggerUrl）
- 导航需用 WebSocket 发 `Page.navigate`，因为 HTTP 没有这个方法
- 标签 ID 在本次 session 内持久，Chrome 重启后会变
- Gemini tab 的 `type` 是 `webview` 而非 `page`，某些 CDP 操作会受限

## pending_tasks 持久化脚本

轻量任务跟踪，重启后自动续命：

```python
#!/usr/bin/env python3
"""pending_tasks.py — 任务持久化管理"""
import json, pathlib, datetime, sys

TASK_FILE = pathlib.Path.home() / '.hermes' / 'pending_tasks.json'

def load():
    if TASK_FILE.exists():
        return json.loads(TASK_FILE.read_text())
    return {'tasks': [], 'last_updated': None}

def save(data):
    data['last_updated'] = datetime.datetime.now().isoformat()
    TASK_FILE.write_text(json.dumps(data, indent=2))

def add(title):
    data = load()
    tid = max([t['id'] for t in data['tasks']], default=0) + 1
    data['tasks'].append({'id': tid, 'title': title, 'status': 'pending', 'created': datetime.datetime.now().isoformat()})
    save(data); print(f'✅ Added #{tid}: {title}')

def complete(tid):
    data = load()
    for t in data['tasks']:
        if t['id'] == int(tid):
            t['status'] = 'completed'; t['completed'] = datetime.datetime.now().isoformat()
    save(data); print(f'✅ Completed #{tid}')

def status():
    data = load()
    pending = [t for t in data['tasks'] if t['status'] == 'pending']
    completed = [t for t in data['tasks'] if t['status'] == 'completed']
    print(f"Pending: {len(pending)}, Completed: {len(completed)}, Last updated: {data.get('last_updated', 'N/A')}")
    if pending:
        print('Active:')
        for t in pending: print(f"  #{t['id']}: {t['title']}")

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    {'add': lambda: add(sys.argv[2]), 'complete': lambda: complete(sys.argv[2]), 'status': status}[cmd]()
```

用法：
```bash
python3 scripts/pending_tasks.py add "AI知识采集"
python3 scripts/pending_tasks.py complete 3
python3 scripts/pending_tasks.py status
```

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