#!/usr/bin/env python3
"""
Hermes 真人化底层驱动 — 贝塞尔鼠标轨迹 + 生物识别打字律动
双剑合璧，直接注入到 hermes_vision_click.py 和 hermes_reactor_v3.py 的 Act 层

用法（独立测试）:
  python3 hermes_human_biometrics.py <tab_match> "点击文字" "输入内容"

CDP 集成示例:
  from hermes_human_biometrics import human_mouse_click, human_type_text
  last_pos = await human_mouse_click(cdp, 890, 910, current_mouse_pos=last_pos)
  await human_type_text(cdp, "Hello MiniMax 2.7...")
"""
import asyncio
import random
import math

# ==========================================
# 算法一：人类鼠标轨迹生成器（Bézier Curve）
# ==========================================

def calculate_bezier_point(p0, p1, p2, p3, t):
    """根据三阶贝塞尔公式计算 t (0->1) 时刻的坐标"""
    x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
    y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
    return int(x), int(y)

def generate_human_mouse_path(start, end, steps_count=None):
    """
    输入起点和终点，动态生成一段带有微幅抖动、
    符合物理加速与减速惯性（S型速度曲线）的真人鼠标轨迹点阵
    """
    x0, y0 = start
    x1, y1 = end

    # 1. 动态计算步数：距离越远，步数越多；加入随机扰动
    distance = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    if steps_count is None:
        steps_count = max(15, int(distance / random.choice([15, 20, 25])))

    # 2. 随机生成两个贝塞尔控制点，让鼠标划出极其自然的人类非直线弧度
    control_offset = distance * 0.2
    p1 = (x0 + (x1 - x0) * 0.25 + random.uniform(-control_offset, control_offset),
          y0 + (y1 - y0) * 0.25 + random.uniform(-control_offset, control_offset))
    p2 = (x0 + (x1 - x0) * 0.75 + random.uniform(-control_offset, control_offset),
          y0 + (y1 - y0) * 0.75 + random.uniform(-control_offset, control_offset))

    path = []
    for i in range(steps_count + 1):
        # 3. 速度曲线真人化：利用 sin 函数实现两头慢、中间快的"物理加速与减速对准"效果
        progress = i / steps_count
        t = (1 - math.cos(progress * math.pi)) / 2  # 经典 S-curve 缓动算法

        x, y = calculate_bezier_point(start, p1, p2, end, t)

        # 4. 微幅抖动：人类手部肌肉天然无法画出完美平滑曲线，越接近终点对准时抖动越小
        if i < steps_count:
            shake_reduce = (1.0 - progress)
            x += int(random.uniform(-1, 1) * shake_reduce)
            y += int(random.uniform(-1, 1) * shake_reduce)

        path.append((x, y))
    return path

async def human_mouse_click(cdp, target_x, target_y, current_mouse_pos=(100, 100)):
    """核心函数：让 Hermes 像真人一样滑行鼠标到指定坐标、悬停、点击、并松开"""
    start_pos = current_mouse_pos
    end_pos = (target_x, target_y)

    print(f"  🖱️ 规划贝塞尔轨迹：{start_pos} → {end_pos}...")
    path = generate_human_mouse_path(start_pos, end_pos)

    # 1. 模拟鼠标沿贝塞尔轨迹划行
    for x, y in path:
        await cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseMoved",
            "x": x,
            "y": y,
            "button": "none"
        })
        await asyncio.sleep(random.uniform(0.008, 0.015))

    # 2. 视觉反射停留（Hover）：鼠标到了按钮上，停顿一下准备点下去
    await asyncio.sleep(random.uniform(0.12, 0.28))

    # 3. 按下鼠标（MouseDown）
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": target_x,
        "y": target_y,
        "button": "left",
        "clickCount": 1
    })

    # 4. 模拟肉体手指按压按钮的时间延迟（人类一般持续 50~100ms 才会抬起手指）
    await asyncio.sleep(random.uniform(0.05, 0.10))

    # 5. 抬起鼠标（MouseUp）
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": target_x,
        "y": target_y,
        "button": "left",
        "clickCount": 1
    })
    print(f"  ✅ 贝塞尔点击完成")
    return end_pos  # 返回最新鼠标位置，作为下一次划行的起点


# ==========================================
# 算法二：生物识别打字律动器（Biometric Typing）
# ==========================================

PUNCTUATION = {",", ".", "!", "?", "，", "。", "！", "？", " ", "\n"}

async def human_type_text(cdp, text):
    """
    核心函数：升级版 CDP 逐字输入
    解决问题：突破无变化匀速特征，注入人类大脑组织语言时的"呼吸停顿感"
    """
    print(f"  ⌨️  真人打字注入：{len(text)} 字符，生物识别模式启动...")

    for ch in text:
        # 1. 计算按键时长（模拟物理按压和松开的时间差，符合高斯分布）
        press_duration = random.gauss(0.05, 0.015)
        press_duration = max(0.03, min(press_duration, 0.09))

        # 2. 发送 keyDown (text置空防止双字符 — 硬核发现)
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyDown",
            "key": ch,
            "text": ""
        })

        # 保持按压
        await asyncio.sleep(press_duration)

        # 3. 发送 char 事件真正写入字符并触发 React onChange
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "char",
            "text": ch
        })

        # 4. 释放按键
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyUp",
            "key": ch
        })

        # 5. 计算字与字之间的思考延迟（基础打字速度）
        char_interval = random.gauss(0.06, 0.02)
        char_interval = max(0.03, min(char_interval, 0.15))

        # 6. 特殊策略：遇到语义标点符号，额外追加"大脑停顿延迟"
        if ch in PUNCTUATION:
            char_interval += random.uniform(0.25, 0.55)

        await asyncio.sleep(char_interval)

    print(f"  ✅ 打字律动注入完成，已骗过行为模型")


# ==========================================
# 独立测试入口
# ==========================================
if __name__ == "__main__":
    import sys, json, websockets, urllib.request

    if len(sys.argv) < 3:
        print("用法: python3 hermes_human_biometrics.py <tab_match> \"点击关键词\" [\"输入文本\"]")
        sys.exit(1)

    tab_match = sys.argv[1]
    click_text = sys.argv[2]
    type_text = sys.argv[3] if len(sys.argv) > 3 else "Hello, this is a biometric test!"

    tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
    tab = next((t for t in tabs if t.get("type") == "page" and tab_match in (t.get("title","")+t.get("url","")).lower()), None)
    if not tab:
        print(f"❌ 找不到 tab: {tab_match}")
        sys.exit(1)

    class CDP:
        def __init__(self, ws):
            self.ws = ws
            self.msg_id = 0
        async def send(self, method, params=None):
            self.msg_id += 1
            await self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params or {}}))
            while True:
                data = json.loads(await self.ws.recv())
                if data.get("id") == self.msg_id:
                    return data

    async def main():
        async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=20*1024*1024) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("Runtime.enable")

            # 找输入框
            r = await cdp.send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const els = [];
                    // 优先 textarea / contenteditable
                    for (const ta of document.querySelectorAll('textarea,[contenteditable=true]')) {
                        if (ta.offsetParent === null) continue;
                        const rect = ta.getBoundingClientRect();
                        if (rect.width < 5 || rect.height < 5) continue;
                        els.push({type: 'input', x: Math.round(rect.left+rect.width/2), y: Math.round(rect.top+rect.height/2), text: (ta.innerText||ta.value||'').substring(0,20)});
                    }
                    // 按钮
                    for (const b of document.querySelectorAll('button,[role=button],div,span')) {
                        const t = (b.innerText||'').trim();
                        if (!t || t.length > 20) continue;
                        const rect = b.getBoundingClientRect();
                        if (rect.width < 20 || rect.height < 10) continue;
                        if (b.offsetParent === null) continue;
                        els.push({type: 'btn', x: Math.round(rect.left+rect.width/2), y: Math.round(rect.top+rect.height/2), text: t});
                    }
                    return els;
                })()
                """,
                "returnByValue": True
            })
            elements = r.get("result",{}).get("result",{}).get("value", [])

            input_el = next((e for e in elements if e["type"] == "input"), None)
            btn = next((e for e in elements if click_text in e["text"]), None)

            last_pos = (100, 100)

            if input_el:
                print(f"\n→ 点击输入框聚焦 ({input_el['x']}, {input_el['y']})")
                last_pos = await human_mouse_click(cdp, input_el["x"], input_el["y"], current_mouse_pos=last_pos)
                await asyncio.sleep(0.3)
                print(f"→ 输入文本: {type_text[:30]}...")
                await human_type_text(cdp, type_text)

            if btn:
                print(f"\n→ 点击按钮: '{btn['text']}' @ ({btn['x']}, {btn['y']})")
                last_pos = await human_mouse_click(cdp, btn["x"], btn["y"], current_mouse_pos=last_pos)

    asyncio.run(main())