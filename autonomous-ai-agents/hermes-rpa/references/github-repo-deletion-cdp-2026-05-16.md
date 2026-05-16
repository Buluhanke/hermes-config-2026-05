# GitHub 仓库删除 — CDP WebSocket + websockets 库方案 (2026-05-16)

> 通过 Chrome CDP 9333 端口，用 Python `websockets` 库直连 WebSocket，绕过 MCP bridge 完成 GitHub 仓库删除。

## 适用场景

- MCP Chrome bridge 不可用（崩溃/超时/连接失败）
- 需要操作**浏览器中已登录**的 GitHub 会话
- 需要处理 GitHub 的多层 Dialog 交互（`<dialog>` + `native DOM`）

## 前置条件

- Chrome 9333 端口运行中（`curl -s http://localhost:9333/json/version` 能返回）
- GitHub 已在浏览器登录（`meta[name=user-login]` 能读到用户名）
- Python 安装 `websockets` 库

## 完整删除流水线

GitHub 删除仓库需要经过 4 步 UI 交互 + 1 步表单提交：

```
Step 1: 点"删除此存储库" → 弹出 Dialog-1
Step 2: 点"我想删除这个仓库" → Dialog-1 切换为 Dialog-2 内容
Step 3: 点"我已阅读并理解这些影响" → Dialog-2 展开文本输入
Step 4: 输入仓库名 "Buluhanke/repo-name" → 启用确认按钮
Step 5: 用 fetch() + FormData 直接提交 delete form → 完成
```

## 核心代码

```python
import asyncio, json, websockets

cid = 200  # 全局 ID 计数器

async def send(ws, data):
    """发送 CDP 指令"""
    await ws.send(json.dumps(data))

async def recv(ws, expected_id, timeout=10):
    """接收匹配指定 id 的 CDP 响应（过滤掉事件消息）"""
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
        if msg.get("id") == expected_id:
            return msg

async def js(ws, sid, code):
    """在页面中执行 JavaScript 并返回结果"""
    global cid; cid += 1
    await send(ws, {"id": cid, "sessionId": sid, "method": "Runtime.evaluate",
        "params": {"expression": f"(function() {{ {code} }})()", "returnByValue": True, "awaitPromise": True}})
    resp = await recv(ws, cid)
    exc = resp.get("result",{}).get("exceptionDetails")
    if exc: return f"ERR: {exc.get('text','')}"
    return resp.get("result",{}).get("result",{}).get("value")

async def connect():
    """连接 CDP 并获取标签页 session"""
    ws = await websockets.connect("ws://localhost:9333/devtools/browser/c663f186-bb9e-4d5a-aeef-bf9333e432e7")
    await send(ws, {"id": 1, "method": "Target.getTargets"})
    resp = await recv(ws, 1)
    pages = [t for t in resp["result"]["targetInfos"] if t["type"] == "page"]
    target_id = pages[0]["targetId"]
    await send(ws, {"id": 2, "method": "Target.attachToTarget", 
        "params": {"targetId": target_id, "flatten": True}})
    resp = await recv(ws, 2)
    return ws, resp["result"]["sessionId"]

async def delete_repo(ws, sid, repo_name):
    """删除 Buluhanke 名下的一个仓库"""
    # 导航到 settings 页
    await send(ws, {"id": 100, "sessionId": sid, "method": "Page.navigate",
        "params": {"url": f"https://github.com/Buluhanke/{repo_name}/settings"}})
    await recv(ws, 100)
    await asyncio.sleep(3)

    # 检查是否已是 404
    title = await js(ws, sid, "return document.title")
    if "404" in str(title):
        return True

    # 滚动到底部（Danger Zone）
    await js(ws, sid, "window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1)

    # Step 1: 点击"删除此存储库"
    await js(ws, sid, """document.querySelector('#dialog-show-repo-delete-menu-dialog')
        ?.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))""")
    await asyncio.sleep(2)

    # Step 2: 点击"我想删除这个仓库"
    await js(ws, sid, """document.querySelector('#repo-delete-proceed-button')
        ?.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))""")
    await asyncio.sleep(2)

    # Step 3: 点击"我已阅读并理解这些影响"
    await js(ws, sid, """document.querySelector('#repo-delete-proceed-button')
        ?.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))""")
    await asyncio.sleep(2)

    # Step 4: 填写仓库名确认
    confirm_text = f"Buluhanke/{repo_name}"
    await js(ws, sid, f"""
        const inputs = document.querySelectorAll('input[type=text]');
        for (const inp of inputs) {{
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, '{confirm_text}');
            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
            inp.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    """)
    await asyncio.sleep(1)

    # Step 5: 直接用 fetch + FormData 提交表单（绕过 UI dialog 限制）
    await js(ws, sid, """
        const forms = document.querySelectorAll('form');
        for (const f of forms) {
            if (f.action && f.action.includes('/delete')) {
                const formData = new FormData(f);
                fetch(f.action, {method: 'POST', body: formData, credentials: 'same-origin'});
                break;
            }
        }
    """)
    await asyncio.sleep(4)

    # 验证
    await send(ws, {"id": 200, "sessionId": sid, "method": "Page.navigate",
        "params": {"url": f"https://github.com/Buluhanke/{repo_name}"}})
    await recv(ws, 200)
    await asyncio.sleep(3)
    title = await js(ws, sid, "return document.title")
    return "404" in str(title)

async def main():
    ws, sid = await connect()
    for repo in ["repo-to-delete-1", "repo-to-delete-2"]:
        ok = await delete_repo(ws, sid, repo)
        print(f"{repo}: {'✅' if ok else '❌'}")
```

## 关键陷阱

### 1. GitHub `<dialog>` 是原生元素，不是 div overlay

**问题**：`dialog.offsetParent !== null` 返回 false，即使 dialog 已打开。

**原因**：GitHub 用原生 `<dialog>` 元素，其 `open` 属性控制显示，不用 `display:none`。

**解决**：检查 `dialog.open` 而非 `offsetParent`：
```python
# ✅ 正确判断 dialog 是否可见
if dialog.open:
    # dialog 已打开
```

### 2. GitHub 删除流程是 5 步，不是 2 步

**错误认知**：点删除 → 确认 → 完事。
**实际流程**：`删除此存储库` → `我想删除这个仓库` → `我已阅读并理解这些影响` → 输仓库名 → 提交表单。

### 3. `.click()` 可能被 dialog 事件系统吞掉

**问题**：`element.click()` 返回错误 `ERR: Uncaught`。

**解决**：用 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}))` 代替。更可靠。

### 4. 表单提交用 fetch + FormData 绕过 UI 操作

**问题**：dialog 中的最后一层确认按钮很难精准点击（dialog 可能被回收或覆盖）。

**解决**：直接用 `fetch(form.action, {method: 'POST', body: new FormData(form)})` 提交表单，绕开 UI 层。

### 5. `websockets` vs `websocket-client` vs 原生 socket

| 库 | 优点 | 缺点 |
|-----|------|------|
| `websockets` (asyncio) | API 简洁，成熟 | 需要 async，可能被系统 SOCKS 代理干扰（shadowrocket 1082） |
| `websocket-client` | 同步调用，简单 | 功能稍少 |
| 原生 socket 手写帧 | 不受代理干扰 | 代码量大，容易出错 |

**推荐**：优先用 `websockets` 库（asyncio）。如果被代理干扰，fallback 到原生 socket（见 `cdp-websocket-native-python.md` reference）。

### 6. 登录态验证

操作前确认 GitHub 已登录：
```python
login = await js(ws, sid, 
    "document.querySelector('meta[name=user-login]')?.content || 'not logged in'")
```
如果返回 `not logged in`，先处理登录再继续。

## CDP 连接要点回顾

- WebSocket URL: `ws://localhost:9333/devtools/browser/xxx`（从 `/json/version` 获取）
- 必须 `Target.attachToTarget` 获得 sessionId 才能操控页面
- 每个 CDP 消息带 `id`（自增），通过 `id` 匹配响应（忽略中间的事件消息）
- `Runtime.evaluate` 的 `expression` 可以写多行立即执行函数
- `awaitPromise: true` 让 CDP 等待 async 函数完成
