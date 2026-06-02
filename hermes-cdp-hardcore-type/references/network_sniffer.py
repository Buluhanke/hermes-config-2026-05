#!/usr/bin/env python3
"""
Hermes 天眼模式: CDP Network拦截 + SSE流解析
直接拿服务器返回的最原始AI回复, 跳过前端渲染.
用法: python3 network_sniffer.py "问题" "deepseek"
"""
import asyncio, json, websockets, urllib.request, time, sys, base64, os

def find_tab(site):
    tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
    for t in tabs:
        if t.get("type") == "page" and site in (t.get("title","")+t.get("url","")).lower():
            return t
    return None

class Eyes:
    """单recv循环 + 队列分发, 解决websockets库ConcurrencyError"""
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0
        self.pending = {}
        self.events = asyncio.Queue()
        self.running = True

    async def start(self):
        return asyncio.create_task(self._loop())

    async def _loop(self):
        while self.running:
            try:
                raw = await self.ws.recv()
                data = json.loads(raw)
                mid = data.get("id")
                if mid is not None and mid in self.pending:
                    self.pending[mid].set_result(data)
                else:
                    await self.events.put(data)
            except: return

    async def send(self, method, params=None):
        self.msg_id += 1
        fut = asyncio.get_event_loop().create_future()
        self.pending[self.msg_id] = fut
        await self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params or {}}))
        return await fut


async def hardcore_type(eyes, text, delay=0.05):
    for ch in text:
        await eyes.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ""})
        await eyes.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
        await eyes.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        await asyncio.sleep(delay)


def parse_sse_text(body):
    """解析SSE流, 支持OpenAI/delta和DeepSeek/patch双协议"""
    all_text = ""
    for line in body.split("\n"):
        if not line.startswith("data: "):
            continue
        raw = line[6:].strip()
        if not raw or raw == "[DONE]":
            continue
        try:
            data = json.loads(raw)
        except: continue
        # OpenAI/ChatGPT流式
        for ch in data.get("choices", []):
            content = ch.get("delta", {}).get("content", "")
            if content:
                all_text += content
        # DeepSeek patch协议: {"v": "x"} 增量
        if "v" in data and isinstance(data["v"], str):
            all_text += data["v"]
        # DeepSeek老格式: v.response.fragments[].content
        v = data.get("v", {})
        if isinstance(v, dict):
            for frag in v.get("response", {}).get("fragments", []):
                content = frag.get("content", "")
                if content and frag.get("type") in ("RESPONSE", "THINK"):
                    if len(content) > len(all_text):
                        all_text = content
        for key in ["text", "message", "content"]:
            val = data.get(key)
            if isinstance(val, str) and len(val) > len(all_text):
                all_text = val
    return all_text


async def sniff(site_key, question, wait=50):
    tab = find_tab(site_key)
    if not tab:
        return f"❌ {site_key}: tab不存在"

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
        eyes = Eyes(ws)
        await eyes.start()
        await eyes.send("Page.enable")
        await eyes.send("Network.enable")
        await eyes.send("Runtime.enable")
        await asyncio.sleep(0.5)

        # 聚焦
        await eyes.send("Runtime.evaluate", {
            "expression": "(() => { for (let t of document.querySelectorAll('textarea')) { if (!t.readOnly && t.offsetParent !== null) { t.focus(); return; } } })()",
            "returnByValue": True
        })
        await asyncio.sleep(0.3)

        # 逐字输入
        print(f"[{site_key}] 输入: {question[:30]}...")
        await hardcore_type(eyes, question)
        await asyncio.sleep(0.3)

        # Enter发送
        for t in ["keyDown", "keyUp"]:
            await eyes.send("Input.dispatchKeyEvent", {
                "type": t, "modifiers": 0, "timestamp": 0,
                "text": "\r", "unmodifiedText": "\r",
                "key": "Enter", "code": "Enter",
                "keyCode": 13, "windowsVirtualKeyCode": 13,
                "location": 0, "isKeypad": False, "isAutoRepeat": False
            })

        # 监听 + 等loadingFinished再读body
        print(f"[{site_key}] 天眼监听 {wait}秒...")
        inflight = {}
        finished = {}
        start = time.time()

        while time.time() - start < wait:
            try:
                event = await asyncio.wait_for(eyes.events.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            method = event.get("method", "")
            params = event.get("params", {})

            if method == "Network.responseReceived":
                url = params.get("response", {}).get("url", "")
                if site_key + ".com" in url.lower() or "deepseek" in url.lower():
                    rid = params.get("requestId")
                    ct = params.get("response", {}).get("mimeType", "")
                    inflight[rid] = {"url": url, "ct": ct, "t": time.time()-start}

            elif method == "Network.loadingFinished":
                rid = params.get("requestId")
                if rid in inflight:
                    info = inflight.pop(rid)
                    try:
                        r = await eyes.send("Network.getResponseBody", {"requestId": rid})
                        result = r.get("result", {})
                        body = result.get("body", "")
                        if result.get("base64Encoded"):
                            body = base64.b64decode(body).decode("utf-8", errors="ignore")
                        finished[rid] = {"url": info["url"], "ct": info["ct"], "body": body}
                        print(f"  [{time.time()-start:.1f}s] FIN {info['ct'][:25]} {len(body)}B: {info['url'][:60]}")
                    except Exception as e:
                        print(f"  body fail: {e}")

        eyes.running = False

        # 解析所有completion响应
        all_text = ""
        os.makedirs("/tmp/ai_screenshots", exist_ok=True)
        debug_path = f"/tmp/ai_screenshots/sse_{site_key}_{int(time.time())}.txt"
        all_bodies = []
        for rid, f in finished.items():
            if "completion" in f.get("url","") or "event-stream" in f.get("ct",""):
                all_bodies.append(f"=== {f['url']} ===\n{f['body']}")
                all_text += parse_sse_text(f["body"])
        if all_bodies:
            with open(debug_path, "w") as fp:
                fp.write("\n".join(all_bodies))

        if all_text:
            return f"✅ {site_key}: 原始流 {len(all_text)} 字符\n\n{all_text}\n\n[完整body: {debug_path}]"
        elif finished:
            return f"⚠️ {site_key}: 解析失败, body在 {debug_path}"
        else:
            return f"⚠️ {site_key}: 0响应"


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "1+1等于几"
    site = sys.argv[2] if len(sys.argv) > 2 else "deepseek"
    print("="*60)
    result = asyncio.run(sniff(site, q, 50))
    print(result[:5000])
