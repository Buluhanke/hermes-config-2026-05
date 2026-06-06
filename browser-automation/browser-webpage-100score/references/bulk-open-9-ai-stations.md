# 批量开 9 站 Tab 标准模式

**适用场景**：跑 multi_ask_v3 / 9 站交叉问 / 全站知识采集前，必须先批量打开 9 站 tab。

**前置条件**：
- Chrome 用 `--disable-extensions` 启动（避免 uBlock 挡 4 站）
- CDP 9333 在跑
- 反指纹已注入（`python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333 --verify`）

## 9 站 URL 清单（SKILL 官方）

| 站 | URL | 输入方式 |
|---|---|---|
| Gemini | https://gemini.google.com/app | AppleScript Cmd+V (zone.js 拦截) |
| 豆包 | https://www.doubao.com/chat | `ta.value=`+Event / Shadow DOM 需 vision |
| ChatGLM | https://chatglm.cn/main/alltoolsdetail | `ta.value=`+Event |
| DeepSeek | https://chat.deepseek.com/ | 逐字 `Input.dispatchKeyEvent` |
| ChatGPT | https://chatgpt.com/ | `Input.insertText` on ProseMirror |
| Grok | https://grok.com/ | ⚠️ 难用，换 Gemini/豆包 |
| Poe | https://poe.com/ | React SPA, try `Input.insertText` |
| Claude | https://claude.ai/ | ProseMirror 类 ChatGPT |
| Perplexity | https://www.perplexity.ai/ | textarea 标准 |
| Kimi | https://kimi.moonshot.cn/ | 长文本 React 输入 |
| 通义千问 | https://tongyi.aliyun.com/qianwen/ | ProseMirror/React |

## 批量开 + navigate 一气呵成（Python）

```python
import json, urllib.request, asyncio, websockets, time

SITES = [
    ("Gemini",   "https://gemini.google.com/app"),
    ("Doubao",   "https://www.doubao.com/chat"),
    ("ChatGLM",  "https://chatglm.cn/main/alltoolsdetail"),
    ("DeepSeek", "https://chat.deepseek.com/"),
    ("ChatGPT",  "https://chatgpt.com/"),
    ("Grok",     "https://grok.com/"),
    ("Poe",      "https://poe.com/"),
    ("Claude",   "https://claude.ai/"),
    ("Perplexity", "https://www.perplexity.ai/"),
    ("Kimi",     "https://kimi.moonshot.cn/"),
    ("Tongyi",   "https://tongyi.aliyun.com/qianwen/"),
]

ver = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json/version").read())
browser_ws = ver['webSocketDebuggerUrl']

async def open_and_navigate_all():
    async with websockets.connect(browser_ws, max_size=10*1024*1024) as ws:
        results = []
        msg_id = 0
        for name, url in SITES:
            # 1. createTarget (background=true, 不抢前台)
            msg_id += 1
            await ws.send(json.dumps({
                "id": msg_id, "method": "Target.createTarget",
                "params": {"url": "about:blank", "background": True}
            }))
            r = json.loads(await ws.recv())
            tid = r.get('result', {}).get('targetId')
            if not tid:
                results.append((name, "create_failed"))
                continue

            # 2. attach (flatten=True 让 sessionId 一起扁平)
            msg_id += 1
            await ws.send(json.dumps({
                "id": msg_id, "method": "Target.attachToTarget",
                "params": {"targetId": tid, "flatten": True}
            }))
            r = json.loads(await ws.recv())
            sid = r.get('params', {}).get('sessionId')

            # 3. Page.navigate
            msg_id += 1
            await ws.send(json.dumps({
                "id": msg_id, "method": "Page.navigate",
                "params": {"url": url}, "sessionId": sid
            }))
            # 等 navigate ack
            try:
                for _ in range(8):
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                    if m.get('id') == msg_id:
                        results.append((name, "ok"))
                        break
            except asyncio.TimeoutError:
                results.append((name, "navigate_timeout"))
        return results

results = asyncio.run(open_and_navigate_all())
for n, s in results:
    print(f"  {n:12s} → {s}")

# 等 8 秒让页面加载登录态
time.sleep(8)

# 验证: 实地抓 innerText（不是看 title 字符串）
tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
pages = [t for t in tabs if t.get('type') == 'page']
print(f"\n=== /json 端点 {len(pages)} 个 page tab ===")
for p in pages:
    print(f"  {p.get('title','')[:30]:30s} | {p.get('url','')[:65]}")
```

## 已知坑

- **ERR_BLOCKED_BY_CLIENT** × 4 = uBlock 没禁，**必加 `--disable-extensions`**
- **DeepSeek 跳 /sign_in** = 登录态过期，需手动重登
- **background=True 的 tab 5-10 秒才出现在 /json 列表**，不能 navigate 完就立刻报成功
- **Tab 总数对 ≠ 内容对**，必须 Runtime.evaluate 抓 `document.body.innerText` 实测
- **Grok Next.js 流式占位符**（textarea 16px 高，__reactProps 无 onChange）→ 直接换 Gemini/豆包

## 反例（2026-06-05 13:45 打脸）

```python
# ❌ 错: 看 title 字符串就汇报成功
tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
for t in tabs:
    if 'gemini' in t.get('url',''):
        print("✅ Gemini OK")  # ← title 是 "Google Gemini" 但内容可能是 about:blank
        # 用户: "你开的都是空白网页 about:blank"
```

```python
# ✅ 对: 实地抓 innerText
async with websockets.connect(ws_url) as ws:
    await ws.send(json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": "document.body.innerText.slice(0,200)", "returnByValue": True}
    }))
    text = json.loads(await ws.recv())['result']['result']['value']
    if 'NO_BODY' in text or len(text) < 10:
        print("❌ 真空白")
    else:
        print(f"✅ 渲染了 ({len(text)} 字符): {text[:80]}")
```
