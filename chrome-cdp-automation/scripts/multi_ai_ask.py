#!/usr/bin/env python3
"""
Hermes Multi-Ask: ask the same question to multiple AI sites via CDP,
read replies from the Accessibility Tree (no OCR needed for most sites).

Usage: python3 multi_ai_ask.py "your question here"

Prerequisites:
- Chrome launched with --remote-debugging-port=9333
- Tabs open to deepseek.com, doubao.com/chat, kimi.com, grok.com (logged in)
- Python 3.x with `websockets` library

Tested 2026-06-02 — 3/4 sites returned readable AI replies via AX tree.
"""
import asyncio, json, websockets, subprocess, os, time, sys, urllib.request

# Site configuration: matcher substring + input element type
SITES = {
    "deepseek": {"match": ["deepseek"], "input_type": "textarea"},
    "doubao":   {"match": ["doubao"],   "input_type": "textarea"},
    "kimi":     {"match": ["kimi"],     "input_type": "contenteditable"},
    "grok":     {"match": ["grok"],     "input_type": "textarea"},
}

WAIT_AFTER_SEND = 30  # seconds to wait for AI to generate the reply

def get_tabs():
    """HTTP-poll Chrome's tab list. /devtools/browser WS returns 404; use HTTP."""
    return json.loads(urllib.request.urlopen("http://localhost:9333/json").read())

def find_tab(site_key):
    """Pick a tab whose title or url contains the site match string."""
    matcher = SITES[site_key]["match"][0]
    tabs = get_tabs()
    candidates = [t for t in tabs if t.get("type") == "page" and
                  (matcher in t.get("title","").lower() or matcher in t.get("url","").lower())]
    if not candidates:
        return None
    # Prefer tabs with non-default title (have conversation history)
    candidates.sort(key=lambda t: (t.get("title","") == SITES[site_key]["match"][0],
                                    -len(t.get("title",""))))
    return candidates[0]


class CDP:
    """Minimal CDP client with monotonic msg_id and event filtering."""
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0

    async def send(self, method, params=None, timeout=10):
        self.msg_id += 1
        await self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params or {}}))
        while True:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                return {"error": "timeout"}
            data = json.loads(raw)
            if data.get("id") == self.msg_id:
                return data


async def hardcore_type(cdp, text, delay=0.05):
    """Real keyboard: keyDown(text='') + char + keyUp per character.
    ⚠️ text='' in keyDown is MANDATORY — otherwise React double-counts."""
    for ch in text:
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ""})
        await cdp.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        await asyncio.sleep(delay)


def screencapture(path):
    subprocess.run(["screencapture", "-x", "-t", "png", path], capture_output=True)
    return os.path.getsize(path)


async def ask_one(site_key, question, wait=WAIT_AFTER_SEND):
    """Ask one site, return (status_str, screenshot_path, ax_reply_text)."""
    tab = find_tab(site_key)
    if not tab:
        return f"❌ {site_key}: tab not found", None, ""

    tab_id = tab["id"]
    title = tab.get("title","")[:30]
    print(f"\n=== [{site_key}] {title} ===")

    try:
        async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("DOM.enable")
            await asyncio.sleep(0.5)

            # Step 1: detect input element type
            r = await cdp.send("Runtime.evaluate", {
                "expression": "({ta: document.querySelectorAll('textarea').length, "
                              "ce: document.querySelectorAll('[contenteditable=true]').length, "
                              "url: location.href})",
                "returnByValue": True
            })
            info = r.get("result",{}).get("result",{}).get("value",{})
            ta_count = info.get("ta", 0)
            input_type = SITES[site_key]["input_type"]
            print(f"  url={info.get('url','')[:50]} ta={ta_count}")

            # Step 2: focus the right input
            if ta_count > 1:
                # Multi-textarea: JS-pick by visible + placeholder + non-readonly
                r = await cdp.send("Runtime.evaluate", {
                    "expression": """
                        (() => {
                            const tas = document.querySelectorAll('textarea');
                            let target = null;
                            for (let t of tas) {
                                if (t.offsetParent !== null && !t.readOnly && t.placeholder) {
                                    target = t; break;
                                }
                            }
                            if (!target) for (let t of tas) if (!t.readOnly) { target = t; break; }
                            if (!target) target = tas[tas.length-1];
                            target.focus();
                            return {ph: target.placeholder, idx: Array.from(tas).indexOf(target), total: tas.length};
                        })()
                    """,
                    "returnByValue": True
                })
                print(f"  multi-ta focus: {r.get('result',{}).get('result',{}).get('value',{})}")
            elif ta_count == 1:
                r = await cdp.send("DOM.getDocument")
                root_id = r["result"]["root"]["nodeId"]
                r = await cdp.send("DOM.querySelector", {"nodeId": root_id, "selector": "textarea"})
                ta_node = r["result"]["nodeId"]
                if ta_node:
                    await cdp.send("DOM.focus", {"nodeId": ta_node})
                    await asyncio.sleep(0.2)
            elif input_type == "contenteditable" and info.get("ce", 0) > 0:
                r = await cdp.send("Runtime.evaluate", {
                    "expression": "(() => { const e = document.querySelector('[contenteditable=true]'); e.focus(); return e.className; })()",
                    "returnByValue": True
                })
                print(f"  contenteditable focus: {r.get('result',{}).get('result',{}).get('value','')}")
            else:
                return f"❌ {site_key}: no usable input element", None, ""

            await asyncio.sleep(0.3)

            # Step 3: hardcore_type the question
            print(f"  → type: {question[:30]}...")
            await hardcore_type(cdp, question, delay=0.05)

            # Step 4: verify
            r = await cdp.send("Runtime.evaluate", {
                "expression": """
                    (() => {
                        const tas = document.querySelectorAll('textarea');
                        if (tas.length > 0) return tas[tas.length-1].value;
                        const ce = document.querySelector('[contenteditable=true]');
                        return ce ? ce.textContent : '';
                    })()
                """,
                "returnByValue": True
            })
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"  value: '{val[:30]}' ({len(val)} chars)")

            if not val:
                return f"❌ {site_key}: input failed", None, ""

            # Step 5: send Enter
            print(f"  → send Enter")
            for t in ["keyDown", "keyUp"]:
                await cdp.send("Input.dispatchKeyEvent", {
                    "type": t, "modifiers": 0, "timestamp": 0,
                    "text": "\r", "unmodifiedText": "\r",
                    "key": "Enter", "code": "Enter",
                    "keyCode": 13, "windowsVirtualKeyCode": 13,
                    "location": 0, "isKeypad": False, "isAutoRepeat": False
                })

            print(f"  → wait {wait}s for AI...")
            await asyncio.sleep(wait)

            # Step 6: AX tree read
            print(f"  → read AX tree")
            r = await cdp.send("Accessibility.getFullAXTree", {"depth": 25, "fetchRelatives": True})
            nodes = r.get("result",{}).get("nodes",[])

            ai_text = []
            for n in nodes:
                role = n.get("role",{}).get("value","")
                name = n.get("name",{}).get("value","")
                if role == "StaticText" and len(name) > 30 and name not in ai_text:
                    ai_text.append(name)

            ai_reply = "\n".join(ai_text)

            # Screenshot fallback
            os.makedirs("/tmp/ai_screenshots", exist_ok=True)
            path = f"/tmp/ai_screenshots/multi_{site_key}_{int(time.time())}.png"
            screencapture(path)

            if ai_reply:
                print(f"  ✅ AX read {len(ai_text)} segments ({len(ai_reply)} chars)")
                return f"✅ {site_key}: success", path, ai_reply
            else:
                print(f"  ⚠️ AX empty, screenshot saved")
                return f"⚠️ {site_key}: AX empty, screenshot saved", path, ""

    except Exception as e:
        return f"❌ {site_key}: {type(e).__name__}: {e}", None, ""


async def main(question):
    print(f"=== Multi-AI Comparison ===")
    print(f"Q: {question}\n")

    results = {}
    for site in SITES:
        status, path, reply = await ask_one(site, question)
        results[site] = {"status": status, "path": path, "reply": reply}
        print(f"  {status}")

    print(f"\n{'='*80}\nResults:\n{'='*80}")
    for site, r in results.items():
        print(f"\n--- {site.upper()} ({r['status']}) ---")
        if r['reply']:
            text = r['reply']
            print(text[:800] + (f"... ({len(text)} chars total)" if len(text) > 800 else ""))
        elif r['path']:
            print(f"[no AX reply, screenshot: {r['path']}]")
        else:
            print("[empty]")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else \
        "Mac Mini 24G跑Hermes, 文字能输入到textarea但发送按钮灰色, 怎么解决?"
    asyncio.run(main(q))
