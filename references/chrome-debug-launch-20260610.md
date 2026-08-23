---
name: chrome-debug-launch-isolated-profile
topic: Chrome 149+ isolated profile clone recipe for CDP automation with inherited login state
created: 2026-06-10
---

# Isolated Chrome Profile — CDP Debug Launch with Login State Inheritance

## TL;DR

把 `~/Library/Application Support/Google/Chrome/Default/` 整个 cp -R 到 `~/.hermes/chrome-profile-mirror/`,用这个目录做 user-data-dir 调 Chrome + `--remote-debugging-port=9222`。**Google / OpenAI / xAI / 智谱 / 腾讯** cookies 全部继承,真登录态可用。**DeepSeek (字节系)** cookies 失效,需在该 Chrome 里重新登录一次。

## 触发场景

- 用户的日常 Chrome 不在跑 / 想独占一个调试 Chrome
- 但 AI 站(Gemini/ChatGPT/豆包/智谱/Grok)需要已登录态
- 不想污染用户日常 Chrome 也不需要 Keychain 加密的字节系 cookie

## 完整步骤

### Step 1: 杀残留 Chrome

```bash
pkill -9 -f "Google Chrome" 2>/dev/null
sleep 2
```

⚠️ 必须先杀光。否则 SingletonLock 会冲突,新 Chrome 启动失败但 pid 在 ps 里。

### Step 2: 拷 profile

```bash
SRC="/Users/aimac/Library/Application Support/Google/Chrome"
DST="$HOME/.hermes/chrome-profile-mirror"

rm -rf "$DST"
mkdir -p "$DST"

# Local State 是 profile 级配置,必须单独拷
cp "$SRC/Local State" "$DST/Local State"
# Default/ 包含 Cookies / Cookies-journal / Login Data / Local Storage / Extensions 等
cp -R "$SRC/Default" "$DST/Default"

# 放宽权限(cp -R 复制的是 700/600,Chrome 内部 helper 进程读不到 shared 文件)
chmod -R u+rwX "$DST"
```

**实测数据(2026-06-10)**:
- 源 `~/Library/Application Support/Google/Chrome/` = **10 GB**(包含 Crashpad / Cache / Code Cache 等)
- 目标 `~/.hermes/chrome-profile-mirror/` = **5.3 GB**(只拷了 Local State + Default/)
- 拷贝耗时 ~30 秒

**优化版(只拷必要文件,降到 ~1GB,耗时 5 秒)**:

```bash
DST="$HOME/.hermes/chrome-profile-min"
rm -rf "$DST" && mkdir -p "$DST/Default"
cp "$SRC/Local State" "$DST/Local State"
for f in Cookies Cookies-journal "Extension Cookies" "Extension Cookies-journal" \
         "Login Data" "Login Data For Account" "Login Data-journal" \
         "Login Data For Account-journal" "Local Storage" "Extension Rules" \
         "Extension Scripts" "Extension State" "Extensions" \
         "Local Extension Settings" "Secure Preferences" "Preferences"; do
    cp -R "$SRC/Default/$f" "$DST/Default/$f" 2>/dev/null
done
chmod -R u+rwX "$DST"
```

**取舍**:全拷 = 完整继承(扩展/历史/书签全在);精简版 = 只继承登录态,扩展可能丢。**推荐先全拷试,有问题再精简**。

### Step 3: 启动 Chrome

⚠️ **必须用 `terminal(background=true)`**。foreground + `&` 后台符号会被 Hermes 拒执行。

```python
# Hermes 工具调用
terminal(
  command='/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome '
          '--remote-debugging-port=9222 '
          '--remote-allow-origins=* '
          '--user-data-dir=$HOME/.hermes/chrome-profile-mirror '
          '--no-first-run --no-default-browser-check '
          '> /tmp/chrome_debug.log 2>&1',
  background=True
  # 注意:NOT notify_on_complete=True(长生命周期进程,不会自然结束)
)
```

### Step 4: 验证端口

```bash
sleep 4  # 端口绑定需要 ~3-5 秒
curl -s -m 5 http://127.0.0.1:9222/json/version | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:', d['Browser'])"
```

**预期输出**:`OK: Chrome/149.0.7827.54`(或更新版本号)

**错误排查**:

| 错误 | 原因 | 修法 |
|---|---|---|
| `exit code 7 / Failed to connect to host` | 端口还没绑定 | 再 `sleep 2` 再 curl |
| `DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.` | DST 路径被 Chrome 当 default | 改用 `$HOME/.hermes/chrome-debug-<timestamp>` 这种新路径 |
| 启动后立即退出 | SingletonLock 残留 | `rm -f "$SRC/SingletonLock" "$SRC/SingletonSocket" "$SRC/SingletonCookie"` |

## 登录态验证 SOP (必跑)

⚠️ **不要**光看 tab title 报"登录态 OK"。title 是 "(no title)" 可能是页面没渲染完,"DeepSeek - 探索未至之境" 在登录前后都可能出现。

### 完整验证脚本

```python
import asyncio, json, urllib.request
import websockets

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())

async def cdp_call(ws, mid, method, params=None, timeout=15):
    """CDP 发请求,循环 recv 跳过事件,直到收到 id 匹配的响应"""
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

async def check_login(t):
    ws_url = t.get("webSocketDebuggerUrl")
    if not ws_url:
        return None
    try:
        async with websockets.connect(ws_url, max_size=8*1024*1024) as ws:
            mid = 0
            for m in ["Runtime.enable"]:
                mid += 1
                await cdp_call(ws, mid, m)
            await asyncio.sleep(2.5)  # 等页面渲染
            mid += 1
            expr = """
            JSON.stringify({
                title: document.title,
                href: location.href,
                bodyLen: (document.body && document.body.innerText || '').length,
                text200: (document.body && document.body.innerText || '').slice(0, 250),
                hasSignIn: /登录|登入|Sign\\s*in|Log\\s*in|注册/.test(document.body && document.body.innerText || ''),
            })
            """
            r = await cdp_call(ws, mid, "Runtime.evaluate",
                {"expression": expr, "returnByValue": True, "awaitPromise": True})
            val = json.loads(r.get("result", {}).get("result", {}).get("value", "{}"))
            val["_tab_id"] = t.get("id", "")[:20]
            return val
    except Exception as e:
        return {"_tab_id": t.get("id", "")[:20], "error": str(e)[:200]}

async def main():
    page_tabs = [t for t in tabs if t.get("type") == "page"
                 and not t.get("url", "").startswith("chrome://")]
    return [(t, await check_login(t)) for t in page_tabs]

results = asyncio.run(main())
for t, r in results:
    if not r:
        continue
    if "error" in r:
        print(f"⚠️  ERR {r['_tab_id']}: {r['error'][:100]}")
        continue
    signin = "❌登出" if r.get("hasSignIn") else "✅"
    print(f"{signin}  bodyLen={r.get('bodyLen',0):4d}  href={r.get('href','?')[:55]}")
    print(f"     title='{(r.get('title') or '')[:40]}'")
    if r.get("hasSignIn") or r.get("bodyLen", 0) < 50:
        print(f"     text: {r.get('text200','')[:200]}")
```

### 关键判定

- **bodyLen = 0** = 页面还没渲染完,再 sleep + 重试
- **hasSignIn = True** = 登出态(出现"登录/登入/Sign in/Log in/注册"字样)
- **bodyLen > 100 且 hasSignIn = False** = 真登录态,但**还要看 text 前 200 字**确认不是空 page chrome
- **历史对话关键词命中**(见下表) = 铁证真登录

### 6 站登录证据关键词表

| 站 | 登录铁证关键词 | bodyLen 期望 |
|---|---|---|
| DeepSeek | "开启新对话" + sidebar 历史(任一用户历史标题) | 400-800 |
| ChatGPT | "历史聊天记录" + sidebar 历史 | 300-500 |
| Grok | "历史记录" + sidebar 历史 | 400-800 |
| ChatGLM | "最近对话" + sidebar 历史 | 400-600 |
| 豆包 | "历史对话" + sidebar 历史 | 400-600 |
| Gemini | "Conversation with Gemini" / "Ready when you are" | 50-200(简洁 UI) |

**最终铁律**:报"X/Y 站真登录"前**必须**把每个站的 bodyLen + text200 头 50 字**给用户看**,让用户确认是登录后的 chat 界面(不是空 page / 登出 welcome)。

## 实测 2026-06-10 数据

- Chrome 149.0.7827.54 在 `/Users/aimac/.hermes/chrome-profile-mirror/` 启动,端口 9222
- 6 站全开 + 全登录,**bodyLen 范围 69 ~ 818,无 hasSignIn 命中**
- 验证证据(节选):
  - ChatGPT text 头: "跳至内容 / 历史聊天记录 / 新聊天 / 搜索聊天 / 库 / 项目 / 应用 / Codex / 更多 / 最近 / 北京天气情况..."
  - 豆包 text 头: "豆包 / 新对话 / ⌘ K / AI 创作 / 云盘 / 更多 / 历史对话 / 主对话 / 北京天气查询..."
  - DeepSeek text 头: "开启新对话 / 7 天内 / 免费网页内容识别工具 / AI Agent核心价值..."
  - 用户历史对话关键词命中:**AI Agent 核心价值**、**1688跨境选品指标**、**量子纠缠解释**(说明这 3 个站用户都用过,且历史跨设备同步)
- 扩展继承:检测到"沉浸式翻译" + "Media Interceptor" 两个扩展在 isolated context 运行

## 已知限制

1. **DeepSeek cookies 失效**(字节系 Keychain 加密) → 需要在 isolated Chrome 里手动登录,或者走 Playwright system Chrome(`~/.hermes/skills/browser-automation/multi-ask-broadcast/references/ai-site-backend-api-not-agnes.md` 里的 fallback 路径)
2. **大 profile(10GB)全拷耗时 30-60 秒** → 用 Step 2 的优化版可降到 5 秒,但扩展可能丢
3. **不能跟用户日常 Chrome 同时跑同一 user-data-dir** → SingletonLock 互斥
4. **chromedp-py / playwright-python 同样适用这个 profile**(只要它们的 Chrome launcher 支持 `--user-data-dir` 参数)

## 相关引用

- 主 skill: `agent-tooling/browser-cdp-control/SKILL.md` "Isolated Profile Clone Recipe" 段
- 对应 fallback: `browser-automation/multi-ask-broadcast/SKILL.md` "Fallback 兜底流程" 段
- CDP 双层 result 链: `browser-automation/multi-ask-broadcast/references/cdp-result-chain-pitfall.md`