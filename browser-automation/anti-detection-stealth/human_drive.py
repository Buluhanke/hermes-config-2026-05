#!/usr/bin/env python3
"""
human_drive.py — 用 websockets 库 + human_mouse.py 拟人化操控 Chrome
走 Hermes 同款库 (websockets==16.0), Origin 头不会被加

用法:
  from human_drive import HermesMouse
  mouse = HermesMouse("ws://127.0.0.1:9333", target_id="...")
  await mouse.connect()
  await mouse.human_click(500, 300, current_x=0, current_y=0)
  await mouse.close()
"""
import asyncio
import json
import time
import math
import random
import sys

# 用路径绕过 import
sys.path.insert(0, "/Users/aimac/.hermes/skills/browser-automation/anti-detection-stealth")
from human_mouse import _bezier_path, _gauss


class HermesMouse:
    """拟人化鼠标操控 — 走 Hermes 用的 websockets 库, 绕过 origin check"""

    def __init__(self, ws_url, target_id=None, debug=False):
        self.ws_url = ws_url
        self.target_id = target_id
        self.session_id = None
        self._next_id = 1
        self.debug = debug
        self._ws = None

    async def connect(self):
        import websockets
        # 关键: websockets 库不主动加 Origin 头, 所以不会触发 Chrome 148 的 origin check
        self._ws = await websockets.connect(
            self.ws_url,
            max_size=None,
            open_timeout=10,
            ping_interval=None,
        )
        if self.target_id:
            # attach to target first
            self.session_id = await self._send(
                "Target.attachToTarget",
                {"targetId": self.target_id, "flatten": True}
            )
        return self

    async def close(self):
        if self._ws:
            await self._ws.close()

    async def _send(self, method, params=None, wait=True):
        """发 CDP 命令, 阻塞等响应"""
        self._next_id += 1
        msg_id = self._next_id
        msg = {"id": msg_id, "method": method}
        if self.session_id:
            msg["sessionId"] = self.session_id
        if params:
            msg["params"] = params
        await self._ws.send(json.dumps(msg))
        if not wait:
            return msg_id
        # 等响应
        while True:
            raw = await self._ws.recv()
            data = json.loads(raw)
            if data.get("id") == msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error: {data['error']}")
                return data.get("result", {}).get("data", {}).get("sessionId") or data.get("result", {})

    async def _send_mouse(self, x, y, event_type="mouseMoved", button="left", buttons=0, click_count=0):
        params = {
            "type": event_type,
            "x": int(x),  # CDP 期望 int (避免 double deserialize 错)
            "y": int(y),
            "button": button,
            "buttons": buttons,
            "clickCount": click_count,
        }
        await self._send("Input.dispatchMouseEvent", params, wait=False)

    async def human_move(self, x0, y0, x1, y1, overshoot_prob=0.4):
        """拟人化鼠标移动 (异步, 不阻塞 IO)"""
        overshoot = random.random() < overshoot_prob
        points = _bezier_path(x0, y0, x1, y1, overshoot=overshoot)
        if self.debug:
            print(f"  [轨迹] {len(points)} 点, 过冲={overshoot}")
        for x, y, dt in points:
            await asyncio.sleep(dt / 1000.0)
            await self._send_mouse(x, y, "mouseMoved", "none", 0)

    async def human_click(self, x, y, current_x=0, current_y=0, jitter=0.5, button="left"):
        """拟人化点击"""
        # 1. 移动
        await self.human_move(current_x, current_y, x, y, overshoot_prob=0.4 * jitter)
        # 2. 停顿 (高斯)
        await asyncio.sleep(_gauss(mu=80 + jitter * 40, sigma=20 + jitter * 10) / 1000.0)
        # 3. 瞄准微动
        if jitter > 0.2:
            dx = random.gauss(0, 0.8 * jitter)
            dy = random.gauss(0, 0.8 * jitter)
            await self._send_mouse(x + dx, y + dy, "mouseMoved", "none", 0)
            await asyncio.sleep(random.uniform(0.005, 0.020))
        # 4. 按下
        await self._send_mouse(x, y, "mousePressed", button, 1, 1)
        # 5. 按下到抬起 (真人 60-150ms)
        await asyncio.sleep(_gauss(mu=85, sigma=25, min_v=40, max_v=180) / 1000.0)
        # 6. 抬起
        await self._send_mouse(x, y, "mouseReleased", button, 0, 1)

    async def human_double_click(self, x, y, current_x=0, current_y=0, jitter=0.5):
        await self.human_click(x, y, current_x, current_y, jitter)
        await asyncio.sleep(_gauss(mu=90, sigma=30, min_v=40, max_v=200) / 1000.0)
        await self.human_click(x, y, x, y, jitter)


# CLI 调试
async def main():
    import urllib.request
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
    target = next(t for t in targets if t.get("type") == "page")
    print(f"[*] target: {target['id'][:14]} url={target['url'][:60]}")

    # 装测试页
    test_html = """
    <!DOCTYPE html>
    <html><head><title>Test</title><style>
      body { font-family: sans-serif; padding: 40px; background: #f0f0f0; }
      button { padding: 20px 40px; font-size: 20px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; margin: 20px; }
      #log { background: white; padding: 20px; border-radius: 8px; max-width: 800px; height: 300px; overflow: auto; font-family: monospace; font-size: 12px; }
    </style></head><body>
      <h1>🖱️ Hermes 拟人化鼠标测试</h1>
      <button id="b1">按钮 1 (200,150)</button>
      <button id="b2">按钮 2 (500,400)</button>
      <button id="b3">按钮 3 (1000,650)</button>
      <h3>事件日志 (mouse events 顺序):</h3>
      <div id="log"></div>
      <script>
        let count = 0;
        const log = document.getElementById('log');
        document.querySelectorAll('button').forEach((btn, i) => {
          btn.style.position = 'absolute';
          btn.style.left = (200 + i * 400) + 'px';
          btn.style.top = (150 + i * 250) + 'px';
          btn.addEventListener('mousedown', e => {
            count++;
            log.innerHTML = `[${Date.now()}] mousedown x=${Math.round(e.clientX)} y=${Math.round(e.clientY)} btn=${btn.id} count=${count}<br>` + log.innerHTML;
          });
          btn.addEventListener('click', e => {
            log.innerHTML = `[${Date.now()}] click btn=${btn.id}<br>` + log.innerHTML;
          });
        });
        document.addEventListener('mousemove', e => {
          window.__lastX = e.clientX;
          window.__lastY = e.clientY;
        });
      </script>
    </body></html>
    """
    encoded = "data:text/html;base64," + __import__('base64').b64encode(test_html.encode()).decode()

    ws_url = "ws://127.0.0.1:9333"
    browser_url = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json/version").read())["webSocketDebuggerUrl"]

    import websockets
    async with websockets.connect(browser_url, max_size=None, ping_interval=None) as bws:
        # attach
        await bws.send(json.dumps({"id": 1, "method": "Target.attachToTarget",
                                    "params": {"targetId": target["id"], "flatten": True}}))
        session_id = None
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 1:
                session_id = data["result"]["sessionId"]
                break
        print(f"[+] session={session_id[:12]}")

        # navigate
        await bws.send(json.dumps({"id": 2, "sessionId": session_id, "method": "Page.navigate",
                                    "params": {"url": encoded}}))
        await asyncio.sleep(1)

        # 构造 HermesMouse 用同一 ws
        mouse = HermesMouse.__new__(HermesMouse)
        mouse.ws_url = ws_url
        mouse.target_id = None
        mouse.session_id = session_id
        mouse._next_id = 100
        mouse.debug = True
        mouse._ws = bws

        # 测试 1: 直线机点 (对照)
        print("\n[*] 测试 1: 直线机点 (对照) — 从 0,0 到 200,150")
        for i in range(10):
            t01 = (i + 1) / 10
            x = 200 * t01
            y = 150 * t01
            await mouse._send_mouse(x, y, "mouseMoved", "none", 0)
            await asyncio.sleep(0.005)
        await mouse._send_mouse(200, 150, "mousePressed", "left", 1, 1)
        await asyncio.sleep(0.08)
        await mouse._send_mouse(200, 150, "mouseReleased", "left", 0, 1)
        print("[+] 直线点击完成")

        await asyncio.sleep(0.5)

        # 测试 2: 拟人点击
        print("\n[*] 测试 2: human_click 拟人点击 — 当前位置 → 500,400")
        await mouse.human_click(500, 400, current_x=200, current_y=150, jitter=0.5)
        print("[+] 拟人点击完成")

        await asyncio.sleep(0.3)

        # 测试 3: 拟人点击 1000,650
        print("\n[*] 测试 3: human_click → 1000,650")
        await mouse.human_click(1000, 650, current_x=500, current_y=400, jitter=0.7)
        print("[+] 完成")

        await asyncio.sleep(0.5)

        # 读日志
        await bws.send(json.dumps({"id": 200, "sessionId": session_id, "method": "Runtime.evaluate",
                                    "params": {"expression": "document.getElementById('log').innerText.substring(0, 2000)"}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 200:
                log_text = data["result"]["result"]["value"]
                break
        print("\n[页面事件日志 — 最近 20 条]:")
        for line in log_text.split("\n")[:20]:
            print(" ", line)

        # 截图
        await bws.send(json.dumps({"id": 201, "sessionId": session_id, "method": "Page.captureScreenshot",
                                    "params": {"format": "png"}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 201:
                import base64
                with open("/tmp/hermes_human_click.png", "wb") as f:
                    f.write(base64.b64decode(data["result"]["data"]))
                break
        print(f"\n[+] 截图: /tmp/hermes_human_click.png ({__import__('os').path.getsize('/tmp/hermes_human_click.png')} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
