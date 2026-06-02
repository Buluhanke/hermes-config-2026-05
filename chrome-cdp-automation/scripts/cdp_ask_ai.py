#!/usr/bin/env python3
"""
Minimal CDP bot: ask DeepSeek a question, take a screenshot.
Requires: pip install websockets
The screenshot should be fed to a vision model to read the AI's reply.
"""
import asyncio, json, websockets, subprocess, os, sys, time

# Get from: curl -s http://localhost:9333/json | python3 -m json.tool
TAB = sys.argv[1] if len(sys.argv) > 1 else "9500172557FFD5EE04AFFC54B7BE4E99"
QUESTION = sys.argv[2] if len(sys.argv) > 2 else "用3句话介绍DeepSeek"
WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 25

WS_URL = f"ws://localhost:9333/devtools/page/{TAB}"


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0

    async def send(self, method, params=None):
        self.id += 1
        await self.ws.send(json.dumps({"id": self.id, "method": method, "params": params or {}}))
        while True:
            data = json.loads(await self.ws.recv())
            if data.get("id") == self.id:
                return data


async def type_chars(cdp, text, delay=0.05):
    for ch in text:
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": ch,
            "text": "", "unmodifiedText": ""  # empty to avoid double-count
        })
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "char", "text": ch, "unmodifiedText": ch, "key": ch
        })
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        await asyncio.sleep(delay)


async def main():
    async with websockets.connect(WS_URL, max_size=20*1024*1024) as ws:
        cdp = CDP(ws)

        # Navigate
        await cdp.send("Page.enable")
        await cdp.send("Page.navigate", {"url": "https://chat.deepseek.com"})
        await asyncio.sleep(5)

        # Find textarea
        await cdp.send("DOM.enable")
        r = await cdp.send("DOM.getDocument")
        root = r["result"]["root"]["nodeId"]
        r = await cdp.send("DOM.querySelector", {"nodeId": root, "selector": "textarea"})
        ta = r["result"]["nodeId"]
        if not ta:
            print("No textarea found")
            return

        # Focus
        await cdp.send("DOM.focus", {"nodeId": ta})
        await asyncio.sleep(0.2)

        # Type
        print(f"Typing: {QUESTION}")
        await type_chars(cdp, QUESTION)
        await asyncio.sleep(0.3)

        # Press Enter
        for t in ["keyDown", "keyUp"]:
            await cdp.send("Input.dispatchKeyEvent", {
                "type": t, "text": "\r", "unmodifiedText": "\r",
                "key": "Enter", "code": "Enter",
                "keyCode": 13, "windowsVirtualKeyCode": 13,
                "location": 0, "isKeypad": False, "isAutoRepeat": False
            })

        # Wait for AI
        print(f"Waiting {WAIT}s for reply...")
        await asyncio.sleep(WAIT)

        # Screenshot
        os.makedirs("/tmp/ai_screenshots", exist_ok=True)
        path = f"/tmp/ai_screenshots/ds_{int(time.time())}.png"
        subprocess.run(["screencapture", "-x", "-t", "png", path])
        print(f"Screenshot: {path}")


if __name__ == "__main__":
    asyncio.run(main())
