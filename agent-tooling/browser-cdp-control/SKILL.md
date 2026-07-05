---
name: browser-cdp-control
description: Direct CDP browser control — DOM extraction, form submission, AI site interaction. Use this when reading/extracting content from browser-controlled websites (ChatGPT, DeepSeek, Gemini, 豆包, etc.).
triggers:
  - "read page content from browser"
  - "fetch text from ChatGPT/DeepSeek/豆包"
  - "extract DOM content via CDP"
  - "browser automation for AI sites"
  - "submit form in Chrome"
l1: 🤖AI站点对话
l2: browser-cdp
l3: core
---

# Browser CDP Control — Direct DOM Extraction

## 工具栈全景（2026-06-18 升级）

| 工具 | 职责 | 连接方式 |
|------|------|----------|
| **CDP Runtime.evaluate** | 原子操作（DOM query/eval） | ws://127.0.0.1:9222 |
| **chrome-devtools-mcp** (v1.2.0) | Chrome 调试能力（29 工具） | MCP stdio → npx, --browserUrl=http://127.0.0.1:9222 |
| **agent-browser CLI** (Rust, 70 命令) | Web 页面自动化（DOM 树） | --cdp 9222 复用同一 Chrome |
| **browser-use** (99.3K stars) | 自然语言多步任务（条件性） | Browser.from_system_chrome() 接 9222 |

## chrome-devtools-mcp (已集成)
- 配置: `~/.hermes/config.yaml` mcp_servers.chrome-devtools-mcp
- 29 工具: lighthouse_audit / take_heapsnapshot / fill_form / emulate / performance_start_trace / list_pages / take_snapshot 等
- 补全 Hermes 缺的能力面，不替换现有 CDP
- 连接: --browserUrl=http://127.0.0.1:9222 复用 chrome-profile-mirror 登录态

## agent-browser CLI (已安装)
- 安装: `npm install -g agent-browser` (~50MB Rust 单文件)
- 70 命令: open/click/fill/type/press/screenshot/pdf/scroll/network/console/eval/trace/vitals/chat/fill-form/highlight/annotate
- 连接: --cdp 9222 或 --auto-connect 复用同一 Chrome
- 与 cua-driver 互补：cua-driver 管 macOS 原生应用（AX 树），agent-browser 管 Web 页面（DOM 树）

## browser-use 安装触发条件（2026-06-18 评估）
目前**不装**，满足以下任一条件时再装：
1. 出现"30+ 字段表单自动填写"的明确需求
2. "SPA 页面总是选不中元素"反复失败 ≥3 次/周
3. 用户明确要求"让 AI 自主跑多步跨网站任务"

**不装原因**：7 天数据 130 次 browser 调用无"多步自然语言"痛点；browser-use 一个 10 步任务 ≈ $4 LLM 成本，月成本 $2000+；与 cua-driver 工具面重叠。

## Core Principle
**Text content → text extraction. Screenshot → only when text extraction fails.**

Priority order:
1. `web_extract` — fastest, for static/lightweight pages
2. `browser_get_web_content` — for structured page content
3. **CDP Runtime.evaluate** — direct DOM query via WebSocket, most reliable for complex/SPA pages
4. `browser_vision` / `computer_use` — last resort only (dynamic rendering, CAPTCHA, rich text that resists text extraction)

## Architecture
## Architecture
### Chrome Setup (macOS)
### CDP Port Requirement
Chrome 148+ **refuses** `--remote-debugging-port` on the default user data directory. You must use a **custom** directory.

> **Need a clean debug profile (not the user's daily Chrome)?** See `references/chrome-debug-launch-20260610.md` for the full recipe: terminal(background=true) requirement, the exact rejection error message, 4-5 second wait for port binding, Singleton lock cleanup, and a verification checklist. The foreground-profile recipe in `cdp-session-20260604.md` is preferred when you need to inherit login state; the launch reference covers the **isolated/sandbox** case.

### Isolated Profile Clone Recipe — 登录态继承 (2026-06-10)

**适用场景**:用户的日常 Chrome 没在跑 / 用户不想被打扰 / 需要 CDP 自动化时独占浏览器,但仍要 AI 站登录态。

**核心思路**:把 `~/Library/Application Support/Google/Chrome/Default/` **整目录拷到独立路径**作为 user-data-dir,调新 Chrome 用这个独立目录。**登录态(cookies / Local Storage / IndexedDB / 扩展)完整继承**,且不污染用户日常 Chrome。

**为什么这能 work**:与"Keychain 加密 cookie 跨 profile 无效"那条**不矛盾** —— 那条说的是"Keychain-bound encrypted_value"(macOS Chrome 的字节系域名加密),普通 AI 站(Google/OpenAI/xAI/智谱/腾讯)的 cookies 是普通 httpOnly cookies,**复制文件直接有效**。**DeepSeek 是字节系域名**,在 isolated clone 下它的 cookies **会失效**(encrypted_value 解不出来) —— 这站需要用户在 isolated Chrome 里重新登录一次,或者走 Playwright system Chrome 接管。

**完整 Recipe**(实测 2026-06-10,clone 出 5.3GB profile,6 站全登录):

```bash
SRC="/Users/aimac/Library/Application Support/Google/Chrome"
DST="$HOME/.hermes/chrome-profile-mirror"

# 1. 杀掉任何残留 Chrome(包括调试实例)
pkill -9 -f "Google Chrome" 2>/dev/null
sleep 2

# 2. 清掉目标
rm -rf "$DST"
mkdir -p "$DST"

# 3. 拷 Local State(profile 级配置)+ Default/(cookies / Local Storage / extensions)
cp "$SRC/Local State" "$DST/Local State"
cp -R "$SRC/Default" "$DST/Default"

# 4. 放宽权限(cp -R 把 700/600 复制过来了,Chrome 内部 helper 进程会读不到 shared 文件)
chmod -R u+rwX "$DST"

# 5. 启动 — 必走 terminal(background=true) !foreground + `&` 会被 Hermes 拒
#    terminal 工具参数:background=true, NOT notify_on_complete=true(长生命周期进程)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$DST" \
  --no-first-run \
  --no-default-browser-check \
  > /tmp/chrome_debug.log 2>&1 &

# 6. 等 4 秒(端口绑定时间),验证
sleep 4
curl -s -m 5 http://127.0.0.1:9222/json/version | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:', d['Browser'])"

# 7. 如果报 "non-default data directory required" → 说明 DST 路径被 Chrome 当 default,
#    改用更隐蔽的路径:$HOME/.hermes/chrome-debug-<timestamp>
```

**为什么不用 `~/.hermes/chrome-debug` 而用 `chrome-profile-mirror`**:前者路径已经被某些 Chrome 版本判定"default-like"(SingletonLock 历史 list)。`chrome-profile-mirror` 这种含"profile-mirror"关键词的命名实测更稳。

**登录态真验证 SOP(必跑,否则汇报 = 假阳性)**:用 `websockets` 库连每个 tab 的 page WS,`Runtime.evaluate` 抓 `document.body.innerText`,详见 `references/chrome-debug-launch-20260610.md` 的 "登录态验证 SOP" 段。

**已验证站登录证据关键词**(任一命中即可判定"真登录态"):
- DeepSeek: "开启新对话" + sidebar 历史对话标题
- ChatGPT: "历史聊天记录" + sidebar 历史对话标题
- Grok: "历史记录" + sidebar 历史对话标题
- ChatGLM: "最近对话" + sidebar 历史对话标题
- 豆包: "历史对话" + sidebar 历史对话标题
- Gemini: "Conversation with Gemini" / "Ready when you are"

**铁律**:
- ❌ 不看 title 就报"登录态 OK"(title 可能还是 "(no title)" 因为页面没渲染完)
- ❌ 不看 URL 就报"OK"(/sign_in 这种 URL 可能是登出态)
- ✅ 必须 Runtime.evaluate 拿 `document.body.innerText` + hasSignIn 正则 + 关键历史关键词
- ✅ 验证完报"X/Y 站真登录"前**必须**把每个站的 bodyLen + text 前 200 字打出来**给用户看**

**CDP WebSocket 调用踩坑(2026-06-10 实测)**:
- ❌ `ws.recv()` 直接拿到响应 = 错 !CDP 发请求后会先推一堆 `Runtime.executionContextCreated` 事件,recv 第一次拿到的是事件不是 Response
- ✅ 必须循环 recv 直到 `msg.get("id") == mid` 才是真正响应。模板:

```python
async def cdp_call(ws, mid, method, params=None, timeout=15):
    await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            return {"_timeout": True, "id": mid}
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
        except asyncio.TimeoutError:
            return {"_timeout": True, "id": mid}
        msg = json.loads(raw)
        if msg.get("id") == mid:
            return msg
```

- ✅ Runtime.evaluate 返回值在 `r.result.result.value`(双层 result 链,memory 第 8 段已记,这里固化代码)
- ⚠️ `extensions` 会注入 isolated context,`Runtime.executionContextCreated` 事件会带 `chrome-extension://...` origin —— 正常现象,跳过即可

### `browser.cdp_url` Config — Critical Pitfall

**Symptom**: `browser_navigate` returns "404 Not Found" or "ERR_BLOCKED_BY_CLIENT" even though Chrome is running on the configured port and `curl localhost:<port>/json/version` returns正确.

**Root cause**: `hermes config set` writes empty-string fields for keys it can't delete. When multiple bad `hermes config set` calls accumulate, the YAML parser or the code that reads `browser.cdp_url` gets confused and the value is never read correctly.

### CDP port config: 4 drift-prone locations, not just `config.yaml` (2026-06-10)

When the user says "browser tools 全部报错" / "browser_navigate 失败" / `curl 9222 成功` 但 `browser_*` 报 `Connection refused`, **不要只改 `~/.hermes/config.yaml`**。CDP 端口在 4 个地方都可能写错,且相互不一致会让 browser tool 拿错端口。

**优先级链** (browser_tool.py:288 `_get_cdp_override` 决定):
1. `BROWSER_CDP_URL` 环境变量 (来自 `/browser connect` 或 `~/.bash_profile` / `~/.zshrc` / `~/.hermes/.env`)
2. `browser.cdp_url` in `~/.hermes/config.yaml`
3. 自动启动 local headless Chromium

**任何 1 个指向 9222 而 Chrome 实际在 9222 监听 → 工具全报"Connection refused"。**

**SOP (60 秒内定位, 不要先动手改)**:

```bash
# 1. Chrome 实际在哪个端口?
netstat -an | grep -E "9222|9222" | grep LISTEN
curl -s -m 3 http://127.0.0.1:9222/json/version | head -3   # 验证能连
curl -s -m 3 http://127.0.0.1:9222/json/version | head -3   # 验证不能连

# 2. 配置层全扫一遍
echo "shell env: $BROWSER_CDP_URL"
grep -n "cdp_url\|BROWSER_CDP_URL" ~/.bash_profile ~/.zshrc 2>/dev/null
grep -n "cdp_url" ~/.hermes/config.yaml
grep -n "BROWSER_CDP_URL\|cdp_url" ~/.hermes/.env

# 3. 哪条链生效? (env > config > auto)
#    grep 命中数 > 0 → 列出每一条 + 它指什么端口 + 是否与 Chrome 一致

# 4. 改之前先**逐条告诉用户** 4 个地方分别写的是什么、哪条生效、Chrome 实际在哪个端口
#    100% 确定再改。绝不能"先改 config.yaml 试试看"
```

**反面教材 (2026-06-10)**: 报告 "config 写错 9222 应改 9222" 时, 我只列了 `config.yaml` 第 81 行, 没扫 `~/.bash_profile` / `~/.hermes/.env` / skill 文档, 用户立刻戳"敷衍"——其实 `.bash_profile` 第 1 行和 `.env` 第 88 行也写 9222, 单改 config 没用 (`BROWSER_CDP_URL` env 优先级更高)。**铁律**: 报告 CDP port 问题 → **必须 grep 4 个地方**, 不能漏。

**Proven fix** (2026-06-04):
```python
# 1. 先看config.yaml里browser.cdp_url附近的原始内容
# 找到类似 server: '' 或 cdp_url: '' 这类脏空行

# 2. 用Python精确删除，不要用sed（sed范围匹配可能伤到相邻块）
import pathlib
cfg = pathlib.Path('/Users/aimac/.hermes/config.yaml')
lines = cfg.read_text().splitlines()
# 精确定位并删除脏行（value为空字符串的那行）
cleaned = [l for l in lines if not (
    l.strip().startswith(('server:', 'cdp_url:', 'engine:')) 
    and l.strip().endswith("''")
)]
cfg.write_text('\n'.join(cleaned) + '\n')
```

**正确的config写法**（手动写入或`hermes config set`后立即人工检查）:
```yaml
browser:
  cdp_url: ws://127.0.0.1:9222   # 格式必须完全正确，不能有相邻空行
  inactivity_timeout: 120
  command_timeout: 30
```

**验证修复成功**:
```bash
curl -s http://127.0.0.1:9222/json/version | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:', d['Browser'])"
```
然后 `browser_navigate https://www.doubao.com` 应该立即返回完整页面（已登录状态）。

### Foreground Chrome Profile — Direct Connection (2026-06-04)

Instead of copying the Chrome profile (which breaks Keychain-encrypted cookies), connect CDP directly to the user's foreground Chrome:

```bash
# Kill any existing debug Chrome
pkill -9 -f "Google Chrome" 2>/dev/null; sleep 2

# Launch user's real foreground profile with debug port
# NOTE: Hermes terminal() requires background=true for processes like this —
# the inline `&` syntax below only works in raw shells, not in terminal(foreground).
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  --disable-blink-features=AutomationControlled \
  --new-window about:blank 2>/dev/null &
sleep 10

# Verify
curl -s http://127.0.0.1:9222/json/version | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('Chrome:', d['Browser'])"
```

**Result**: All login states (豆包 session cookies, ChatGPT, DeepSeek, etc.) are preserved — same cookies, same Keychain access, no migration needed. The foreground Chrome IS the logged-in session.

**When NOT to use this approach**: When you need to install extensions (uBlock Origin, etc.) without disturbing the user's daily browsing. Use a separate profile for that.

### ⚠️ CDP 9222 可能连到镜子 Chrome，不是你的 Chrome（2026-07-06 新增）

**症状**：用户说"已经登录了"，但 CDP 看到登录框。

**根因**：9222 端口可能被两套 Chrome 之一占用：
1. **Hermes mirror Chrome**（`chrome-profile-mirror`）— Hermes 独立启动的 Chrome，cookie store 与用户主 Chrome 完全隔离
2. **用户主 Chrome**（`Default` profile）— 用户日常用的，需要手动加 `--remote-debugging-port` 才会暴露 9222

**鉴别方法**：查 CDP 返回的 `webSocketDebuggerUrl` 对应的 Chrome 版本路径，或对比用户 Chrome PID：
```bash
# 用户主 Chrome PID
ps aux | grep "Google Chrome" | grep -v Helper | grep -v crash | awk '{print $1, $2}'

# CDP 连的是哪个
curl -s http://127.0.0.1:9222/json/version
# 看 Browser 字段里的版本号，是否和用户 Chrome 版本一致
```

**镜子 Chrome 特征**：
- CDP 看到企业微信 doc 页面有 `login_frame` iframe（未登录的登录框）
- 但用户屏幕上同一 URL 已经登录了文档内容
- `curl /json/list` 的 page URL 和用户屏幕上的 URL 一致，但 session 状态完全不同

**两种解法**：

**解法 A：接用户的 Chrome**（推荐，需要用户配合一次）
1. 用户关闭自己的 Chrome
2. 用命令行重启用户 Chrome 并开启 9222：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check &
sleep 5
```
→ CDP 9222 现在是用户主 Chrome，cookie/登录态 100% 继承

**解法 B：Chrome 扩展**（无需重启用户 Chrome）
写一个 `chrome.debugger` API 扩展，装到用户 Chrome 里，通过扩展 transport 把 CDP 暴露出来。这个方案不需要重启，但需要用户手动安装一次扩展。

**解法 C：pasky chrome-cdp-skill**（不需要重启，最理想）
通过 Unix socket 自动发现运行中的 Chrome 实例，不需要调试端口，不需要重启。详见 `references/pasky-chrome-cdp-skill.md`。

**铁律**：用户说"已经登录了"但 CDP 显示登录页 → 不要 reload、不要 attachToTarget → 先鉴别是镜子 Chrome 还是用户 Chrome → 再决定走哪条解法。

### 操作用户独立运行的 Chrome（2026-07-06 修正）

**之前 technique 失效**：之前认为直接 `browser_cdp` + `target_id` 可以操作用户已有标签页，实测连到的是 mirror Chrome，用户登录态不在里面。

**修正后的 technique**：
1. 鉴别 — 先 `ps aux` 确认用户 Chrome PID，再 `curl /json/version` 对比版本
2. 如果是镜子 Chrome → 走上面"解法 A"重启用户 Chrome 开 9222
3. 如果是用户主 Chrome → 直接 `browser_cdp` + `target_id` 操作

**绝对禁止**：
- ❌ 不鉴别就 reload（会丢失用户已在浏览器里完成的登录状态）
- ❌ 不鉴别就在两个 CDP session 之间跳转（mirror vs user 隔离）
- ❌ 假设 9222 = 用户 Chrome（2026-07-06 实测：9222 是镜子 Chrome）

**和"Foreground Chrome Profile"方法的关系**：
| 场景 | 方法 |
|------|------|
| 镜子 Chrome 占 9222，用户 Chrome 无 9222 | 解法 A：重启用户 Chrome 开 9222 |
| 用户 Chrome 已开 9222 | 直接 browser_cdp + target_id |
| 不想重启用户 Chrome | 解法 B：Chrome 扩展 |


### ⚠️ Chrome 149+ CDP 兼容：page-level WS vs browser-level attach (2026-06-21 新增)

**症状**：用 browser-level WebSocket + `Target.attachToTarget` 拿到 sessionId 后，所有 CDP 命令报 `Session with given id not found.`

**根因**：Chrome 149+ 每个 page target 有自己的独立 `webSocketDebuggerUrl`（在 `/json` 返回的每个 tab 对象的 `webSocketDebuggerUrl` 字段）。直接用 page-level WS 连接，不需要 `attachToTarget` + `sessionId`。旧代码用 browser ws + attachToTarget 拿到的 sessionId 在 page-level WS 下无效。

**修复模式**：
1. 优先用 page-level WS：从 `/json` 拿到 tab 的 `webSocketDebuggerUrl`，直接 connect
2. 所有 CDP 命令通过封装函数发送，session_id=None 时不加 `sessionId` 字段
3. 保留 browser-attach 作为 fallback（兼容旧 Chrome）

**CDP 响应容错**：`Runtime.evaluate` 返回格式可能变化，不要硬取 `msg["result"]["result"]["value"]`。先检查 `msg.get("error")`，再 try `result.result.value` → `result.value`。

```python
def _cdp_cmd(bws, msg_id, method, params, session_id=None):
    """构建 CDP 命令，page-level WS 时 session_id 为 None 不加 sessionId 字段"""
    cmd = {"id": msg_id, "method": method, "params": params}
    if session_id is not None:
        cmd["sessionId"] = session_id
    bws.send(json.dumps(cmd))

# attach 时优先 page-level WS
def attach(t):
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
    for tgt in targets:
        if tgt.get("id") == t["id"]:
            page_ws = tgt.get("webSocketDebuggerUrl", "")
            if page_ws:
                bws = create_connection(page_ws, timeout=10)
                return bws, None  # page-level WS 不需要 sessionId
    # fallback: browser ws + attachToTarget
    ...
```

**触发词**：`"Session not found" / CDP 命令全部失败 / Chrome 149+ attachToTarget 报错` → 0 思考切换 page-level WS 模式。

### Critical: Chrome CDP Does NOT Support JSON-RPC 2.0

**This is the #1 pitfall.** Chrome's CDP WebSocket protocol is **not** JSON-RPC 2.0 compliant.

❌ WRONG (will cause `-32600` errors):
```python
msg = {"jsonrpc": "2.0", "id": 1, "method": "Page.bringToFront"}
```

✅ CORRECT:
```python
msg = {"id": 1, "method": "Page.bringToFront"}  # No jsonrpc field
```

This single issue causes CDP to fail silently for many tasks. Always omit the `jsonrpc` field.

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

### Playwright `connect_over_cdp` 不能用 `browser.pages` / `browser.targets()` (2026-06-10)

当用 `pw.chromium.connect_over_cdp("http://127.0.0.1:9222")` 接管已登录 Chrome 复用登录态时, `Browser` 对象**没有标准 page 枚举方法**:

```python
browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
browser.pages           # AttributeError: 'Browser' object has no attribute 'pages'
browser.targets()       # AttributeError
browser.contexts        # 存在,但 list
browser.contexts[0].pages  # ✅ 这才是真路径
```

**正确解法**:

```python
ctx = browser.contexts[0]
existing_page = None
for p in ctx.pages:
    if "grok.com" in p.url:
        existing_page = p
        break

# 接管已有 tab 走 attach,不创建新 page (新 page 没登录态)
# CDP 的 `Target.getTargets` 虽能列 targets, 但 ws URL 为空 (Chrome/148+ bug),
# 实战中不如直接 enumerate `contexts[0].pages` 简单稳定
```

**铁律**:
- ❌ 不要尝试 `browser.pages` / `browser.targets()` / `Target.getTargets` 直构 (前者 AttributeError, 后者 ws URL 拿到空字符串)
- ✅ 用 `browser.contexts[0].pages` 拿现有 tab list
- ❌ 不要 `browser.contexts[0].new_page()` 创建新 tab 跑已登录站 (新 page 无 session cookie, 需重新登录)
- ✅ 找到匹配的现有 tab → 直接 `await page.goto(url)` 或 `page.locator(...).fill(...)` 操作

**反面教材 (2026-06-10)**: 在 broadcast_v2.py 里写 `browser.pages` / `browser.targets()` 反复踩坑, 浪费 5+ 轮, 最终发现正确路径是 `browser.contexts[0].pages`。**0 思考就走这个 SOP, 别再实验**。

### Chrome Profile Conflict
- If CDP returns empty results, Chrome may have crashed/restarted — verify with `curl http://127.0.0.1:9222/json/version`
- If Chrome has restarted, the WebSocket URL changes — re-fetch tabs

## AI网站交互工作流（实战验证）

**用户铁律：不要空话。** 直接做，不解释过程，不汇报系统状态，除非用户明确要求。动作→结果，两句话内。

### 正确流程（问题→发送→等待→提取）

AI聊天网站（ChatGPT/豆包/DeepSeek/智谱清言/Gemini）使用 WebSocket 流式输出+虚拟DOM渲染，**必须在同一页面完成发送+等待+提取，不能刷新或导航离开。**

```
Step 1: curl http://localhost:9222/json           → 找到tab ID
Step 2: WebSocket连接 + Page.bringToFront         → 激活目标tab
Step 3: Runtime.evaluate (JS填充)                  → 向输入框写入问题
Step 4: Input.dispatchKeyEvent (Enter)            → 提交
Step 5: sleep 15-25秒                            → 等待AI回复（深度思考模式更久）
Step 6: Accessibility.getFullAXTree               → 读取回复内容（推荐，无OCR）
       或 Runtime.evaluate (innerText)            → 直接读DOM文本
```

### 推荐：Accessibility Tree 读取内容

**为什么优先于截图/OCR**：Chrome原生API，~50ms，不需要模型支持视觉，可读取所有Shadow DOM内容。

```python
import json, asyncio, websockets

async def read_ai_site(tab_id):
    async with websockets.connect(f"ws://localhost:9222/devtools/page/{tab_id}") as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.bringToFront"})); await ws.recv()
        await asyncio.sleep(0.5)
        await ws.send(json.dumps({"id": 2, "method": "Accessibility.getFullAXTree", "params": {"depth": 25}}))
        resp = json.loads(await ws.recv())
        nodes = resp["result"]["nodes"]
        
        # 提取有意义的元素
        for n in nodes:
            role = n["role"]["value"]
            name = n["name"]["value"][:100]
            if role in ["link", "button", "textbox", "radio", "heading"] and name:
                print(f"[{role}] {name}")
```

**读取到的内容类型**：对话历史链接(21条DeepSeek历史)/输入框/backendDOMNodeId/模式选择(radio)。

### 备选：Runtime.evaluate 读取innerText

当Accessibility Tree不够时，用JS直接读DOM：

```javascript
// 递归遍历shadow DOM（通用方法）
(function(){
    function extractText(node, depth) {
        if(depth > 8) return '';
        var texts = [];
        if(node.nodeType === 3 && node.textContent.trim()) {
            texts.push(node.textContent.trim());
        }
        if(node.shadowRoot) {
            Array.from(node.shadowRoot.childNodes).forEach(function(c){
                texts.push(extractText(c, depth+1));
            });
        }
        if(node.childNodes) {
            Array.from(node.childNodes).forEach(function(c){
                texts.push(extractText(c, depth+1));
            });
        }
        return texts.join(' ');
    }
    return extractText(document.body, 0).substring(0, 8000);
})()
```

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

⚠️ **Chrome 148+ 警告**：`/json/new` 端点已被禁用（返回 405 Method Not Allowed）。该章节保留以供旧版 Chrome 参考；新代码应使用 CDP `Target.createTarget` 替代。

Chrome 的 CDP HTTP API 原本支持直接创建新标签页：

```python
import urllib.request, json

# 创建新标签（HTTP POST，无需 WebSocket）
req = urllib.request.Request(
    'http://localhost:9222/json/new',
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
    req = urllib.request.Request('http://localhost:9222/json/new', method='POST')
    with urllib.request.urlopen(req, timeout=10) as f:
        tab = json.loads(f.read())
    tab_ids[name] = tab['id']
    # 用 CDP Page.navigate 导航到目标 URL
    ws = websocket.create_connection(f"ws://localhost:9222/devtools/page/{tab['id']}", timeout=15)
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

## Enhanced Actions (browser-use 对照吸收, 2026-06-14)

| 缺的 browser-use action | 我有 | 通过 |
|---|---|---|
| `find_text` 文本定位 + scroll | ✅ | `python3 ~/.hermes/scripts/hermes_find_text.py "文本" [--exact] [--case-sensitive]` (默认自动 scrollIntoView) |
| `switch` 按 index 切 tab | ✅ | `python3 ~/.hermes/scripts/hermes_tab_switch.py switch N` (Page.bringToFront via browser-level WS) |
| `close` 关 tab | ✅ | `python3 ~/.hermes/scripts/hermes_tab_switch.py close N` (Target.closeTarget) |
| `new` 开新 tab + navigate | ✅ | `python3 ~/.hermes/scripts/hermes_tab_switch.py new "URL"` (Target.createTarget) |
| `dropdown_options` 列出 select | ✅ | `python3 ~/.hermes/scripts/hermes_dropdown.py list` (querySelectorAll('select') → options[]) |
| `select_dropdown` 选中 | ✅ | `python3 ~/.hermes/scripts/hermes_dropdown.py select "文本"` / `select-index N` / `select-value "value"` (dispatchEvent change) |

**所有脚本**: 0 新依赖, 纯 CDP (`Runtime.evaluate` + `Target.createTarget/closeTarget/activateTarget`), 用 `websocket-client` 库 (已装).

**实际验证 (2026-06-14)**: 3 脚本在 Chrome 9222 + chrome-profile-mirror 实跑全部 ok. Gemini 主页 `find_text "Gemini"` 命中 7 处. example.com + w3school tab 切换/新建正常. dropdown 0 hits 符合预期 (example.com/w3school iframe 都没顶层 `<select>`).

**新覆盖度**: browser-use 18 个核心 action 我现有覆盖 **100%** (3 个真缺的都补了).

### 增强浏览器工具栈（2026-06-18 新增）

Hermes 现在有 **3 层浏览器控制工具**，互补不冲突：

| 工具 | 定位 | 安装方式 | 关键能力 |
|------|------|---------|---------|
| **CDP + cua-driver** | 基础层 | 内置 | Runtime.evaluate, DOM query, AX tree, 9222 端口直连 |
| **chrome-devtools-mcp** | 调试增强层 | `npx -y chrome-devtools-mcp@latest --browserUrl=http://127.0.0.1:9222` | Lighthouse 审计, heap snapshot, 多字段表单 fill_form, 移动端/弱网 emulate, 性能追踪 |
| **agent-browser** | CLI 增强层 | `npm install -g agent-browser` | 70 命令 CLI, `--cdp 9222` 复用登录态, snapshot -i, network har, highlight, annotate |

**触发规则**:
- 日常浏览器操作 → CDP + cua-driver（最快，不需要额外工具）
- 需要 Lighthouse/heap/表单批量填写/移动端模拟 → chrome-devtools-mcp
- 需要 CLI 快捷操作（截图、network 调试、fill-form 多字段）→ agent-browser
- 三个工具**共享 CDP 9222 端口**，不会互相干扰

**chrome-devtools-mcp 已配置**: config.yaml `mcp_servers.chrome-devtools-mcp`
**agent-browser 已安装**: `~/.hermes/skills/agent-browser-cli/SKILL.md`
**集成详情**: `references/chrome-devtools-mcp-integration.md`

## Canvas-Rendered Enterprise Apps (smartsheet / spreadsheet / 表格类)

Modern enterprise productivity apps (Tencent docs smartsheet, Feishu sheets, Lark Base, etc.) render grid content on `<canvas>` — **text is not in the DOM**. Standard `querySelectorAll('.cell, [data-row]')` returns 0 hits.

**The hooks that DO work** (verified 2026-06-29 on `doc.weixin.qq.com/sheet/...`):

| Hook | Selector | Purpose |
|---|---|---|
| Formula bar (current active cell content) | `#alloy-simple-text-editor` (`contenteditable=true` div) | Read/write active cell |
| Cell address name box | `input.bar-label` (A1, B5...) | Jump to any cell |
| Sheet tab | `[role="tab"]` (text match) | Switch between sheets |
| Editor zone (focus target) | `.editor-zone_grid___TyIk` | DOM focus container |

**Golden rules for canvas-rendered grid automation:**

1. **All-in-one `evaluate_script`** — never mix `mcp_chrome_devtools_mcp_press_key` (CDP `Input.dispatchKeyEvent`) with JS-driven cell-ref navigation. React's keydown handler listens on the editor zone, not document — `Tab`/`ArrowRight` from `press_key` will be silently dropped.
2. **`await sleep(400)` after every cell-ref change** — formula bar value is async-rendered, synchronous reads return the previous cell.
3. **React controlled input pattern** — direct `cellRef.value = 'B1'` doesn't trigger onChange. Need both `new Event('input', { bubbles: true })` AND `new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })`.
4. **Formula bar submit requires Enter** — `textContent = '...'` updates DOM but not React state. Enter triggers onKeyDown → store commit.
5. **Sheet switch needs `sleep(1500)`** — the entire canvas redraws; reading formula bar before that gives the old sheet's content.

Full read/write recipes + a 30×6 table scan template: **`references/doc-weixin-smartsheet-cdp.md`**.

### ⚠️ "⚡ Interrupting current task" 是 MCP 噪声 — 绝不复述 (2026-06-29)

**用户原话**: "你的反应跟不上，看看这个怎么去提升，每一次我跟你对话以后你都要来一串这个"

**真坑**:
- `mcp_chrome_devtools_mcp_evaluate_script` + `await sleep()` 链路长时, MCP server 内部**周期性广播** "⚡ Interrupting current task (iteration N/80). I'll respond to your message shortly."
- 这是 MCP server 的内部通知, 跟 agent 反应速度无关 — 复述/重复只会让用户更焦虑
- 用户看到的体验: 跑一长串 evaluate 都附上 "⚡ Interrupting..." → 觉得 agent 卡 → 实际跑得挺快

**修法**:
1. **绝不**复述 "⚡ Interrupting" 文本到输出里
2. **批量合并** evaluate_script: 把多个 cell 跳转/读合并到一次 evaluate_script, 减少 iteration 数 (1 次 = 1 iteration = 0 interruption)
3. **compress 输出**: 返 200 行大 JSON → 用 `.map(v=>[v.row, v.name]).slice(0,30)` 精简
4. **后台 + notify**: 真长 (3s+) 用 `terminal(background=true, notify_on_complete=true)`, **不要**让用户盯着"⚡ Interrupting"焦虑
5. **检测规则**: 输出中带 "⚡ Interrupting current task" 字样 → 这是 MCP 噪声, 不是状态报告, 0 思考当噪音处理

### ⚠️ 报"有多少行/个/条"前必独立 count, 不信脑补 (2026-06-29)

**反面教材**: 扫 `报价表` 我只读 row 1-30 → 直接信 "30 个物料" → 后续所有自动化方案按 30 个白名单建. 用户纠正 "不止30个, 应该有一百多 / 所以你没有去看报价单里面的详细内容". 真扫 row 2-144 = **143 个物料**.

**修法**:
1. **扩范围**: 扫表前至少扫 row 1-200, 默认上限 row 250 + 连续 3 行空就停
2. **不报 N 之前必数清楚** (写代码自动数, 不要"差不多是 X 个")
3. **不要停在前 30 行就报** — 看不到表底 = 错
4. **触发词**: "总共有多少 / 一共 X 个 / 大概多少" → 0 思考走完整扫描, 不抽样估

### Real active element is `#alloy-rich-text-editor` (2026-06-29 实测)

The formula bar `#alloy-simple-text-editor` shows the active cell content, but the **real focused element** when a cell is selected is `#alloy-rich-text-editor` (AlloyEditor instance). User-reported "Alt+↓ doesn't open the dropdown" comes from sending keystrokes to the wrong element.

**判定 SOP after cell-ref jump + sleep(400)**:
```javascript
return {
  activeId: document.activeElement.id,  // 期望: "alloy-rich-text-editor"
  activeTag: document.activeElement.tagName
};
```

If not alloy-rich-text-editor → re-trigger cell-ref change (React's onBlur is async, focus hasn't settled yet).

**Alt+↓ / Alt+ArrowDown 在 AlloyEditor 里不触发下拉** (2026-06-29 实测):
- ❌ 给 `#alloy-rich-text-editor` → 0 popup 出现, 只剩 `smart-selection-board` 高亮板
- ❌ 给 document → 同样无响应
- ❌ F2 + Alt+ArrowDown 组合 → 同样无响应
- ✅ **唯一可靠路径**: 用户的"下拉点选"本质 = 保证输入物料名在合法白名单内. 用 CDP 直接键入物料名 + 客户端 30 行白名单校验代替下拉 UI.

**Why this matters**: `doc.weixin.qq.com` 是企业微信 AlloyEditor, 不是 Excel. Excel 的 Alt+↓ 触发数据验证下拉是 IE-era 行为, AlloyEditor 没继承. 不要把 Excel 经验套到这上面.

### Formula-bar 永远读公式字符串, 不是渲染值

公式栏 `#alloy-simple-text-editor` 在任何状态下读到的是**公式字符串**, 不是 VLOOKUP 计算后的值:

```
B6 = "趣集狗挡风帘"           ← 直接输入, 显示原值
C6 = "=IFERROR(VLOOKUP(@$B:$B,报价表!$B:$I,8,0),\"\")"  ← 永远是公式!
```

**用户视角看到 VLOOKUP 算出的真实值**, 但脚本读公式栏永远是公式文本. 这是 AlloyEditor 设计: 公式栏 = 编辑器, 渲染层 = canvas.

**怎么拿真实渲染值**:
- 写场景不需要读 (用户浏览器 canvas 自己重算)
- 读场景用 `take_screenshot` → `vision_analyze` (Ollama LLaVA 本地 / 云端 VLM) OCR 出像素文字. 2-5s/次, 不准, 兜底用.

#### ⚠️ 切工作表/扫表前先确认"行数", 不要凭印象报 (2026-06-29)

**反面教材**: 用户说"物料名称不止30个, 应该有一百多" + "你没有去看报价单里面的详细内容".

**真坑**: 我之前扫 `报价表` 只读 row 1-30 看到 30 个物料 → 直接信这个数 → 后续所有自动化方案都按"30 个白名单"建. 实际 row 2-144 = **143 个物料**, 我漏了 113 个.

**修法**:
1. 扫表前**先扩范围**: 至少扫 row 1-200, 默认设上限 row 250 + 连续 3 行空就停
2. **不报"有 N 个"前必**数清楚 (或写代码自动数)
3. 看到行 1-30 就停 = **错**, 看不到表底 = **错**
4. 修正后实际跑: `报价表` row 2-144 = 143 个物料 (B 列从 `男士造型梳三件套` 到 `胡桃木纹9格文玩盒` 之后还有 113 个没看)

### ⚠️ 写到用户真实在线表 = 不可逆, 必须先报"我要写 X 到 Y"再写 (2026-06-29 反面教材)

**反面教材**: 用户让我研究"doc.weixin.qq.com 销售单" → 我连续 3 轮没问就写入: B8="测试产品 99", B9="趣集狗挡风帘 200", B10="测试产品" (全部写入到用户真实在线表, 企业文档自动保存, **无法撤回**). 用户问"你自己看一下你输入的产品名称, 后面就不会出单和总价" 才意识到错.

**修法**:
1. **写之前**: 0 思考确认 — "这是测试环境 / 沙箱 / 还是用户真实数据?" 真实数据 → **先报用户**: "我准备写 X 到 row Y, 确认吗?" (即使只写 1 cell 也要问)
2. **写测试数据时**: 用明显标注的前缀 (`__TEST__`, `__DELETE_ME__`), 让用户一眼能识别
3. **测试通过后**: 主动清理测试数据, 不要留给用户手动删
4. **不要把测试值当功能验证**: 第一次测 B 列接受"趣集狗挡风帘"是因为它**真的在报价表**, 不代表 B 列接受所有字符串. 测试物料名 = 报价表白名单第一条 (`男士造型梳三件套`) 才能保证 VLOOKUP 算得出价
5. **触发词**: "企业微信表格 / 在线文档 / 真实数据库 / 用户表" → 0 思考走"先问再写"路径, 不要"先写再告诉用户"

## 单次 vs 批量的语义侦测 (2026-06-29 用户纠正)

**触发场景**: 用户说 "我开个单 / 做个表 / 填个东西" / 任何"我要填一次"的请求.

**0 思考自检表**:
- "开**一张** / 一次 / 一个 / 这条" → **单条模式**: 不做批量工具, 直接交互填表, 让用户给一条数据跑一次.
- "每天 / 批量 / 一些 / 多个 / 100 条" → **批处理模式**: 写脚本.
- 没上下文 → **默认单条先 ship**, 一句话告知: "如果以后要批量我再包装自动化".

**反面教材 (2026-06-29)**: 用户说 "有客户下单, 我就开一张销售单", 我立刻做了 CSV 批量工具 (`fill_sales_fast.py`), 用户指出 "不是要批量". 浪费 3 轮 + 一个长脚本 + 两次误写入真实表格.

**铁律**: "开一张 / 帮我填一个" 这种语义 = **0 思考** 走交互填表路径. 即使心里觉得 "以后可能要批量", **也等用户说**. 不要提前 YAGNI 反向 (不要提前批量化).

**Trigger phrases**: "开张 / 一个 / 一次 / 帮我填" → 单条; "批量 / 每天 / 很多 / 循环" → 批量.

**Trigger phrases**: "企业微信表格编辑" / "企微文档自动化" / "doc.weixin.qq.com 写入" / "智能表格自动化" / "没 API key 怎么改表格" / user pastes a `doc.weixin.qq.com/sheet/...` link and asks for automation.

## 子文件 / Templates

- `references/doc-weixin-smartsheet-cdp.md` — **doc.weixin.qq.com 智能表格** 完整 CDP 读写实战 (AlloyEditor 坑/Alt+↓ 不响应/143 物料白名单/单次vs批量语义侦测)
- `references/doc-weixin-sheet-login-state.md` — **企业微信文档登录态判断**（2026-07-06 实测）：login_frame iframe 特征、未登录 vs 已登录 状态区分、chrome-profile-mirror 与用户主 Chrome 的 CDP 端口隔离
- `templates/fill_sales_smart.py` — **企业微信销售单填表脚本模板** (已验证 2026-06-29, 单/多 row, 客户端白名单校验; 复用改 SMARTSHEET_URL + TARGET_SHEET)

## Quick Verify
```bash
curl -s http://127.0.0.1:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Chrome {d.get('Browser-Version','?')}\")"
```

## Critical Limitation: AI Chat Replies — Shadow DOM Penetration Varies by Site

**实测 2026-07-06: Gemini 的 AI 回复可以用 AX tree 读取。**

Gemini 页面 `browser_snapshot` 成功读到了：
```
heading "You said Reply with just OK"
paragraph "Reply with just OK"
heading "Gemini said"
paragraph "OK"
```

**不同 AI 站的 Shadow DOM 穿透能力不同：**

| 站点 | AX Tree 读回复 | Runtime.evaluate 读 innerText | 备注 |
|---|---|---|---|
| **Gemini** | ✅ 可读 | ✅ 可读 | 本次实测成功 |
| **ChatGPT** | ❌ 通常不可读 | ❌ Shadow DOM 隔离 | 主流 AI 站 |
| **豆包** | ❌ 可能不可读 | ❌ Shadow DOM 隔离 | 待测 |
| **DeepSeek** | ❌ 可能不可读 | ❌ Shadow DOM 隔离 | 待测 |

**判断 SOP**：先跑 `browser_snapshot` 看AX tree里有没有回复内容（paragraph/StaticText里有没有AI回复文字），有就用，没有再试Runtime.evaluate。都不行才用 browser_vision 截图。

**Workaround for sites where CDP can't read replies**:
```
Instead of browser → read reply → process
Do: browser → send message → call AI API directly

DeepSeek  → direct DeepSeek API (free tier available)
ChatGPT   → direct OpenAI API
Gemini    → direct Google API
豆包      → direct ByteDance API (if available)
```

## Verified Working: hermes_cdp_bot.py

The canonical working script is `scripts/hermes_cdp_bot.py`. It:
- Connects via WebSocket to existing Chrome tab (no new browser launch)
- Uses correct CDP message format (no `jsonrpc` field)
- Gets full 36-char tab ID from HTTP `http://localhost:9222/json`
- Fills textarea via `Runtime.evaluate` + `dispatchEvent`
- Sends via `KeyboardEvent('keydown', {key:'Enter', ...})`
- Reads AX tree for structure confirmation
- Supports multiple AI sites via command-line: `python3 hermes_cdp_bot.py deepseek`

### Screenshot Fallback (CDP screenshots return 0 bytes on this Mac)

`Page.captureScreenshot` returns empty on this macOS setup (GPU compositing issue). Use macOS native instead:

```bash
screencapture -x /tmp/ai_screenshots/chrome_full.png
```

### Port Architecture (2026-06-02 verified, 2026-06-04 updated)

| Port | Chrome Instance | Login State | Notes |
|------|---------------|-------------|-------|
| **9222** | Foreground Chrome real profile (`--user-data-dir=~/Library/Application Support/Google/Chrome/Default`) | ✅ All sites logged in (same Keychain) | User's daily Chrome, use this |
| **9222** | (was user real Chrome in earlier session) | — | Older approach, superseded |

**2026-06-04 关键发现：`browser.cdp_url` 配置后 browser_navigate 的行为**

设置 `hermes config set browser.cdp_url ws://127.0.0.1:9222` 后，Hermes browser 工具连接的是**真实 Chrome 当前活跃的 tab**（不是开新 tab）。如果该 tab 是 `chrome://newtab/` 或 `about:blank`，导航到新 URL 会返回 `ERR_BLOCKED_BY_CLIENT`。

**解决**：
1. 先用 `curl http://localhost:9222/json/list` 找到有效 tab（有 URL 的 page type tab）
2. 或者用 `Target.createTarget` 在 browser endpoint 创建新 tab（见下方 CDP 脚本模板）

**Keychain 加密cookie复制无效的根本原因**：
Chrome（macOS）对字节系域名使用 OS X Keychain 主密钥加密 cookie。加密密钥绑定到 Chrome 实例身份，复制 cookie 文件到另一个 profile 后，新 Chrome 实例无法用自己的 Keychain 解密别人的加密值。症状：`value` 字段为空，`encrypted_value` 非空。

**正确解法**：在 debug Chrome 中完成一次登录（session token 是设备 UUID，换设备重新登录即可）。

**Key insight**: Do NOT copy user Chrome profile to chrome-debug — cookies are encrypted with user Keychain and won't work in a different profile. Instead, connect CDP directly to user's real Chrome at **port 9222** (already running with debug port).

```python
# Connect to user's real Chrome (port 9222)
with urllib.request.urlopen('http://localhost:9222/json') as f:
    tabs = json.load(f)
# Find the AI site tab you want to interact with
for t in tabs:
    if 'deepseek' in t.get('url','') and t.get('type') == 'page':
        tab_id = t['id']  # full 32-char ID
        break
```

## Connected AI Sites (pre-authenticated, verified 2026-07-06)
- https://chatgpt.com/           — 待验证
- https://www.doubao.com/chat    — ✅ 登录（K H账号，有历史对话）
- https://chat.deepseek.com/    — 待验证
- https://gemini.google.com/app  — ✅ 登录（K H账号，Gemini实测发送+接收全流程OK）
- https://chatglm.cn/            — 待验证
- https://grok.com/z            — ❌ Cloudflare拦截，无法自动化