#!/usr/bin/env python3
"""
human_scroll.py — 拟人化滚轮
撞 bot.sannysoft 行为检测核心 — 惯性 + 加速/减速 + 不规则间隔

真人滚轮 4 特征:
  1. 惯性 — wheelDelta 逐渐衰减 (不像程序每次一样)
  2. 加速/减速 — 开头慢, 中间快, 结束慢
  3. 方向微调 — 偶尔反向滚
  4. 触觉间隔 — 1-3ms 不规则

使用:
  from human_scroll import human_scroll
  await human_scroll(mouse._ws, mouse.session_id, delta_y=-600)  # 向下滚 600px
"""
import asyncio
import json
import random
import math


def _wheel_deltas(total_delta, n_events=None):
    """
    生成单个 wheelDelta 序列, 模拟真人惯性
    返回: [(deltaX, delta_y, dt_ms), ...]
    """
    if n_events is None:
        # 真人 1 次滚轮触发 3-8 个 wheelEvent
        n_events = random.randint(4, 10)
    if n_events < 2:
        n_events = 2

    # 真人滚动签名: 第一次大 (手指猛推), 后续小 (惯性), 最后反向小 (回弹)
    # 用指数衰减: delta(t) = total * exp(-k*t) * sign
    sign = -1 if total_delta < 0 else 1
    total_abs = abs(total_delta)

    deltas = []
    cumulative = 0
    for i in range(n_events):
        t = i / (n_events - 1) if n_events > 1 else 0.5
        # 衰减: 第 0 个 0.4, 后续 0.2/0.15/0.1/...
        if i == 0:
            weight = 0.40
        elif i == 1:
            weight = 0.25
        elif i == 2:
            weight = 0.15
        else:
            weight = 0.20 / (n_events - 3) if n_events > 3 else 0.1
        # 加点抖动
        weight *= random.gauss(1.0, 0.15)
        delta = total_abs * weight
        # 真人"回弹" 30% 概率: 最后一个 5% 是反向
        if i == n_events - 1 and random.random() < 0.3:
            delta = -delta * 0.3  # 反向小滚动
        cumulative += delta
        deltas.append(delta)

    # 归一化使总和 = total_delta
    scale = total_abs / sum(abs(d) for d in deltas) if sum(abs(d) for d in deltas) > 0 else 1
    deltas = [d * scale * sign for d in deltas]

    # 时间间隔: 1-3ms 不规则 (wheel 事件触发很快)
    intervals = []
    for i in range(len(deltas)):
        dt = random.gauss(2.0, 0.8)
        # 中间稍慢 (惯性), 结尾慢 (减速)
        if i < len(deltas) // 3:
            dt *= 0.7
        elif i > len(deltas) * 2 // 3:
            dt *= 1.3
        intervals.append(max(0.5, dt))

    return list(zip([0] * len(deltas), deltas, intervals))


async def human_scroll(ws, session_id, delta_y, x=500, y=400,
                       n_events=None, speed="normal"):
    """
    拟人化滚轮

    delta_y: 负数向下, 正数向上
    x, y: 鼠标在屏幕上的位置 (wheel 事件需要坐标)
    speed: "slow" (6 events) / "normal" (4-10) / "fast" (3-5, 大 delta)
    """
    if n_events is None:
        if speed == "slow":
            n_events = random.randint(8, 14)
        elif speed == "fast":
            n_events = random.randint(2, 4)
        else:
            n_events = random.randint(4, 10)

    deltas = _wheel_deltas(delta_y, n_events=n_events)

    for dx, dy, dt in deltas:
        params = {
            "type": "mouseWheel",
            "x": int(x),
            "y": int(y),
            "deltaX": int(round(dx)),
            "deltaY": int(round(dy)),
        }
        msg = {
            "id": random.randint(10000, 99999),
            "method": "Input.dispatchMouseEvent",
            "params": params,
        }
        if session_id:
            msg["sessionId"] = session_id
        await ws.send(json.dumps(msg))
        await asyncio.sleep(dt / 1000.0)


async def human_scroll_to(ws, session_id, scroll_fn, target_y, max_attempts=20,
                          tolerance=50, x=500, y=400):
    """
    滚到指定 Y 位置 (模拟真人"找位置"行为)

    scroll_fn: async (delta_y) -> current_y — 当前页面 scrollY
    """
    current = await scroll_fn(0)  # 初始
    attempts = 0
    while abs(current - target_y) > tolerance and attempts < max_attempts:
        diff = target_y - current
        # 每次滚一部分 (60-80%)
        step = int(diff * random.uniform(0.5, 0.8))
        # 真人: 接近目标时滚动幅度变小
        if abs(diff) < 200:
            step = int(diff * random.uniform(0.3, 0.6))
        await human_scroll(ws, session_id, step, x=x, y=y,
                           n_events=random.randint(3, 6),
                           speed="slow" if abs(diff) < 200 else "normal")
        await asyncio.sleep(random.uniform(0.1, 0.3))
        current = await scroll_fn(0)
        attempts += 1
    return current


# CLI 调试
async def main():
    import urllib.request
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
    target = next(t for t in targets if t.get("type") == "page")
    browser_url = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json/version").read())["webSocketDebuggerUrl"]

    test_html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Scroll Test</title><style>
      body { font-family: sans-serif; margin: 0; }
      .block { height: 200px; background: linear-gradient(45deg, #4CAF50, #2196F3); color: white; padding: 20px; font-size: 24px; margin-bottom: 5px; }
      #info { position: fixed; top: 0; right: 0; background: yellow; padding: 10px; font-family: monospace; z-index: 100; }
    </style></head><body>
      <div id="info">scrollY: 0 | wheel events: 0</div>
      <div class="block">Block 1 — scroll down</div>
      <div class="block">Block 2</div>
      <div class="block">Block 3</div>
      <div class="block">Block 4</div>
      <div class="block">Block 5</div>
      <div class="block">Block 6</div>
      <div class="block">Block 7</div>
      <div class="block">Block 8</div>
      <div class="block">Block 9</div>
      <div class="block">Block 10 — bottom</div>
      <script>
        let wheelCount = 0;
        window.addEventListener('wheel', e => {
          wheelCount++;
          document.getElementById('info').textContent = `scrollY: ${window.scrollY} | wheel events: ${wheelCount} | last deltaY: ${e.deltaY}`;
        });
        // 立即更新
        setInterval(() => {
          document.getElementById('info').textContent = `scrollY: ${window.scrollY} | wheel events: ${wheelCount}`;
        }, 200);
      </script>
    </body></html>
    """
    import base64
    encoded = "data:text/html;base64," + base64.b64encode(test_html.encode()).decode()

    import websockets
    async with websockets.connect(browser_url, max_size=None, ping_interval=None) as bws:
        await bws.send(json.dumps({"id": 1, "method": "Target.attachToTarget",
                                    "params": {"targetId": target["id"], "flatten": True}}))
        sid = None
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 1:
                sid = data["result"]["sessionId"]
                break

        await bws.send(json.dumps({"id": 2, "sessionId": sid, "method": "Page.navigate",
                                    "params": {"url": encoded}}))
        await asyncio.sleep(1)

        # 程序化滚轮 (对照)
        print("[*] 测试 1: 程序化滚轮 -1000 (对照)")
        msg = {"id": 3, "sessionId": sid, "method": "Input.dispatchMouseEvent",
               "params": {"type": "mouseWheel", "x": 500, "y": 400, "deltaX": 0, "deltaY": -1000}}
        await bws.send(json.dumps(msg))
        # 关键: 消费响应避免后续消息错位
        await asyncio.sleep(0.3)
        # 收掉所有 pending (含 wheel event 异步响应)
        try:
            while True:
                await asyncio.wait_for(bws.recv(), timeout=0.05)
        except asyncio.TimeoutError:
            pass

        # 读 scrollY
        await bws.send(json.dumps({"id": 4, "sessionId": sid, "method": "Runtime.evaluate",
                                    "params": {"expression": "window.scrollY", "returnByValue": True}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 4:
                sy1 = data["result"]["result"]["value"]
                break
        print(f"[+] 程序化滚后 scrollY: {sy1}")

        # 拟人化滚回顶部
        print("\n[*] 测试 2: 拟人化滚 +1000 (回到顶部)")
        await human_scroll(bws, sid, 1000, x=500, y=400, speed="normal")
        await asyncio.sleep(0.5)

        await bws.send(json.dumps({"id": 5, "sessionId": sid, "method": "Runtime.evaluate",
                                    "params": {"expression": "window.scrollY", "returnByValue": True}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 5:
                sy2 = data["result"]["result"]["value"]
                break
        print(f"[+] 拟人化滚后 scrollY: {sy2}")

        # 拟人化滚到目标位置
        print("\n[*] 测试 3: 拟人化滚到 scrollY=400 (找位置)")
        # 先滚到底
        await human_scroll(bws, sid, -2000, speed="fast")
        await asyncio.sleep(0.3)

        async def get_y(req_id):
            await bws.send(json.dumps({"id": req_id, "sessionId": sid,
                                        "method": "Runtime.evaluate",
                                        "params": {"expression": "window.scrollY", "returnByValue": True}}))
            while True:
                raw = await bws.recv()
                data = json.loads(raw)
                if data.get("id") == req_id and "result" in data:
                    return data["result"]["result"]["value"]

        final = await human_scroll_to(bws, sid, lambda _: get_y(7001), 400, x=500, y=400)
        print(f"[+] 最终 scrollY: {final} (目标 400, 容差 50)")

        # 截图
        await bws.send(json.dumps({"id": 6, "sessionId": sid, "method": "Page.captureScreenshot",
                                    "params": {"format": "png"}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 6:
                with open("/tmp/human_scroll_test.png", "wb") as f:
                    f.write(base64.b64decode(data["result"]["data"]))
                break
        print("[+] 截图: /tmp/human_scroll_test.png")


if __name__ == "__main__":
    asyncio.run(main())
