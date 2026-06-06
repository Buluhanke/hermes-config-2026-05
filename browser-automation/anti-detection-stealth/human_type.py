#!/usr/bin/env python3
"""
human_type.py — 拟人化输入
撞 bot.sannysoft 行为检测核心 — 真人打字节奏 + 错字 + 退格 + 不等距

真人打字 5 特征:
  1. 速度有节奏 — burst (连打) + pause (思考)
  2. 偶尔打错 — 退格改字 (5-10% 概率)
  3. 键与键之间不等距 — 50-200ms
  4. 长字符串"低头赶路" — 越打越快
  5. 回车前会犹豫

使用:
  from human_type import human_type_text
  await human_type_text(mouse._ws, mouse.session_id, "hello world", into="input#x")
"""
import asyncio
import json
import random


def _typing_interval(prev_char, curr_char):
    """
    真人键间隔 (ms)
    - 同手指连击: 慢 (90-140ms)
    - 异指连击: 快 (60-100ms)
    - 思考停顿: 200-500ms
    - 标点后: 慢 (150-250ms)
    """
    base = random.gauss(80, 20)  # 真人平均 80ms
    # 标点/空格后慢一拍
    if prev_char in " .,!?;:":
        base += random.uniform(80, 180)
    # 长串中爆发 (连续快速)
    if random.random() < 0.15:
        base = random.gauss(55, 12)
    # 偶尔"想词"停顿
    if random.random() < 0.05:
        base += random.uniform(200, 500)
    # 低头赶路 — 字符越长, 平均越快
    # (这是 length-aware 的, 调用方传)
    return max(35, min(800, base))


def _should_typo(char):
    """
    5-10% 概率打错 — 真实研究是 1-3% 误触
    真风控关心的是 "节奏模式", 错字反而是真人标志
    """
    return random.random() < 0.06


def _nearby_key(char):
    """键盘相邻键位 (QWERTY)"""
    nearby = {
        'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'ersfcx', 'e': 'wrds',
        'f': 'rtdgcv', 'g': 'tyfhbv', 'h': 'yugjbn', 'i': 'ujko', 'j': 'uikhmn',
        'k': 'ijolm', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'iplk',
        'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'awedxz', 't': 'ryfg',
        'u': 'yijh', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tugh',
        'z': 'asx',
    }
    if char.lower() in nearby:
        return random.choice(nearby[char.lower()])
    return char


async def human_type_text(ws, session_id, text, into_selector=None,
                          min_interval=40, max_interval=300,
                          typo_rate=0.06, wpm=None,
                          press_key_fn=None):
    """
    拟人化输入文本

    ws: websockets 连接
    session_id: CDP session id
    text: 要输入的内容
    into_selector: 可选, CSS selector (输入前先点一下)
    min_interval/max_interval: 键间隔范围 (ms)
    typo_rate: 错字率
    wpm: 如果指定, 覆盖 min/max 按 WPM 计算 (真人 40-100 WPM, 中等 60)
    press_key_fn: 自定义按键函数 (默认用 Input.insertText + dispatchKeyEvent)
    """
    if wpm:
        # WPM -> 平均键间隔 (按 5 字符/词)
        avg_interval = 60000 / (wpm * 5)
        min_interval = avg_interval * 0.5
        max_interval = avg_interval * 2

    # 可选: 先点输入框
    if into_selector:
        # 这里需要调用 mouse.click, 简化版先省略
        pass

    typed_so_far = ""
    i = 0
    while i < len(text):
        char = text[i]
        prev = text[i - 1] if i > 0 else 'a'

        # 1. 错字 + 退格
        if _should_typo(char) and i > 0:
            wrong = _nearby_key(char)
            await _send_key(ws, session_id, wrong)
            await asyncio.sleep(_typing_interval('a', 'a') / 1000.0)
            # 退格
            await _send_key_event(ws, session_id, 'Backspace', 'char')
            await asyncio.sleep(_typing_interval('a', 'a') / 1000.0 * 0.7)
            # 输入正确字符
            await _send_key(ws, session_id, char)
        else:
            await _send_key(ws, session_id, char)

        # 2. 间隔
        interval = _typing_interval(prev, char)
        interval = max(min_interval, min(max_interval, interval))
        await asyncio.sleep(interval / 1000.0)
        i += 1

    return typed_so_far


async def _send_key(ws, session_id, char):
    """发单个字符 (用 Input.insertText 走 IME 路径, 中文/emoji 友好)"""
    params = {"text": char}
    msg = {"id": random.randint(10000, 99999), "method": "Input.insertText", "params": params}
    if session_id:
        msg["sessionId"] = session_id
    await ws.send(json.dumps(msg))


async def _send_key_event(ws, session_id, key, event_type="char"):
    """发 keyDown/keyUp (用于 Backspace, Enter 等控制键)"""
    windows_virtual_key_code = {
        "Backspace": 8, "Tab": 9, "Enter": 13, "Escape": 27,
        "ArrowLeft": 37, "ArrowUp": 38, "ArrowRight": 39, "ArrowDown": 40,
        "Delete": 46, "Home": 36, "End": 35,
    }
    code = windows_virtual_key_code.get(key)
    if not code:
        # 退路: 用 dispatchKeyEvent 但 key 是字符串
        code = ord(key[0]) if len(key) == 1 else 0
    params = {
        "type": "keyDown" if event_type != "rawKeyDown" else "rawKeyDown",
        "key": key,
        "windowsVirtualKeyCode": code,
        "nativeVirtualKeyCode": code,
    }
    msg = {"id": random.randint(10000, 99999), "method": "Input.dispatchKeyEvent", "params": params}
    if session_id:
        msg["sessionId"] = session_id
    await ws.send(json.dumps(msg))
    # 抬起
    params2 = dict(params)
    params2["type"] = "keyUp"
    msg2 = {"id": random.randint(10000, 99999), "method": "Input.dispatchKeyEvent", "params": params2}
    if session_id:
        msg2["sessionId"] = session_id
    await ws.send(json.dumps(msg2))


async def human_press_enter(ws, session_id):
    """拟人化回车 — 按下前犹豫一下"""
    await asyncio.sleep(random.uniform(0.15, 0.45))  # 犹豫
    await _send_key_event(ws, session_id, "Enter", "char")


async def human_clear(ws, session_id):
    """清空输入框 — 三连击选中 + 删除"""
    # Ctrl+A
    await _send_key_event(ws, session_id, "a", "char")
    # 这里简化, 实际要传 modifiers
    await asyncio.sleep(0.05)


# CLI 调试
async def main():
    import urllib.request
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
    target = next(t for t in targets if t.get("type") == "page")
    browser_url = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json/version").read())["webSocketDebuggerUrl"]

    test_html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Type Test</title><style>
      body { font-family: sans-serif; padding: 40px; background: #f0f0f0; }
      input { padding: 15px; font-size: 18px; width: 400px; border: 2px solid #4CAF50; border-radius: 8px; }
      #log { background: white; padding: 20px; border-radius: 8px; max-width: 600px; height: 300px; overflow: auto; font-family: monospace; font-size: 12px; margin-top: 20px; }
    </style></head><body>
      <h1>⌨️ Hermes 拟人化输入测试</h1>
      <input id="i1" placeholder="点这里然后看 input 事件" autofocus>
      <div id="log"></div>
      <script>
        const input = document.getElementById('i1');
        const log = document.getElementById('log');
        let prev = '';
        input.addEventListener('input', e => {
          const now = Date.now();
          const dt = prev ? (now - prev) : 0;
          prev = now;
          log.innerHTML = `[${now}] input value="${e.target.value}" dt=${dt}ms<br>` + log.innerHTML;
        });
        input.focus();
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

        # navigate
        await bws.send(json.dumps({"id": 2, "sessionId": sid, "method": "Page.navigate",
                                    "params": {"url": encoded}}))
        await asyncio.sleep(1.5)

        # 测试拟人化输入
        print("[*] 拟人化输入 'Hello, World! This is a test.'")
        await human_type_text(bws, sid, "Hello, World! This is a test.", wpm=65)
        print("[+] 完成")

        await asyncio.sleep(0.5)

        # 读 input 实际值
        await bws.send(json.dumps({"id": 3, "sessionId": sid, "method": "Runtime.evaluate",
                                    "params": {"expression": "document.getElementById('i1').value",
                                              "returnByValue": True}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 3:
                val = data["result"]["result"]["value"]
                break
        print(f"\n[+] Input 实际值: '{val}'")

        # 截图
        await bws.send(json.dumps({"id": 4, "sessionId": sid, "method": "Page.captureScreenshot",
                                    "params": {"format": "png"}}))
        while True:
            raw = await bws.recv()
            data = json.loads(raw)
            if data.get("id") == 4:
                with open("/tmp/human_type_test.png", "wb") as f:
                    f.write(base64.b64decode(data["result"]["data"]))
                break
        print("[+] 截图: /tmp/human_type_test.png")


if __name__ == "__main__":
    asyncio.run(main())
