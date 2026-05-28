#!/usr/bin/env python3
"""
Hermes humanization-core 核心动作库
Phase 1: 穿上人的衣服

包含：
- human_type()  : 模拟人类打字（含错字回退）
- human_move()  : 贝塞尔曲线鼠标移动
- human_click() : 先悬停再点击
- human_scroll(): 模拟人类滚轮（快滚+停顿）
- capture_screen(): 极速截屏
- ask_vlm(): 调用本地 smolvlm2 视觉模型
- analyze_emotion(): 情绪分析（Qwen3:8b）
"""

import pyautogui
import random
import time
import numpy as np
import json
import base64
import mss
import os
import requests

# 安全设置：pyautogui 失控保护
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

SCREENSHOT_PATH = "/tmp/hermes_screen.png"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# ─────────────────────────────────────────
# 1. 打字拟真
# ─────────────────────────────────────────
def human_type(text: str, speed: float = 0.1):
    """模拟人类打字：随机延迟 + 1% 概率错字回退"""
    for char in text:
        pyautogui.write(char, interval=random.uniform(0.03, speed))
        if random.random() < 0.01:
            # 打错一个字符
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            pyautogui.write(wrong_char, interval=random.uniform(0.03, 0.08))
            time.sleep(random.uniform(0.1, 0.25))
            # 回退修正
            pyautogui.press('backspace')
            time.sleep(random.uniform(0.08, 0.15))


# ─────────────────────────────────────────
# 2. 鼠标移动（贝塞尔曲线）
# ─────────────────────────────────────────
def human_move(x: int, y: int, duration: float = None):
    """模拟人类鼠标移动：贝塞尔曲线轨迹 + 随机弧度"""
    if duration is None:
        # 根据距离动态决定速度（越远越慢，模拟人类抬手移动的习惯）
        current_x, current_y = pyautogui.position()
        distance = ((x - current_x)**2 + (y - current_y)**2) ** 0.5
        duration = max(0.3, min(distance / 400, 1.5))  # 距离400px时约1秒

    start_x, start_y = pyautogui.position()

    # 生成有弧度的控制点（避免直线）
    mid_x = (start_x + x) // 2 + random.randint(-80, 80)
    mid_y = (start_y + y) // 2 + random.randint(-60, 60)

    # 二阶贝塞尔曲线
    points = []
    steps = max(int(duration * 120), 20)  # 至少20步
    for t in np.linspace(0, 1, steps):
        bx = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * x
        by = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * y
        points.append((int(bx), int(by)))

    # 移动（带微小随机扰动）
    for i, (px, py) in enumerate(points):
        # 末尾几帧稍微减速（模拟人类接近目标时的犹豫）
        if i > len(points) * 0.8:
            delay = duration / steps * 1.5
        else:
            delay = duration / steps * random.uniform(0.8, 1.2)
        pyautogui.moveTo(px, py, _pause=False)
        time.sleep(delay)


# ─────────────────────────────────────────
# 3. 人类点击（先悬停再按下）
# ─────────────────────────────────────────
def human_click(x: int, y: int, button: str = 'left'):
    """模拟人类点击：移动 -> 悬停 -> 按下 -> 抬起"""
    human_move(x, y)
    time.sleep(random.uniform(0.3, 0.9))  # 悬停思考时间
    pyautogui.mouseDown(button=button)
    time.sleep(random.uniform(0.05, 0.15))  # 按下和抬起之间的自然停顿
    pyautogui.mouseUp(button=button)


def human_right_click(x: int, y: int):
    return human_click(x, y, button='right')


# ─────────────────────────────────────────
# 4. 滚轮拟真（快滚 + 停顿）
# ─────────────────────────────────────────
def human_scroll(clicks: int, direction: str = 'down'):
    """模拟人类滚轮：分多次，有停顿"""
    direction_map = {'down': -1, 'up': 1}
    delta = direction_map.get(direction, -1)

    # 分3-5次滚动，每次间隔不同
    parts = random.randint(3, 5)
    per_part = clicks // parts
    remainder = clicks % parts

    for i in range(parts):
        actual = per_part + (1 if i < remainder else 0)
        pyautogui.scroll(actual * delta)
        time.sleep(random.uniform(0.15, 0.4))


# ─────────────────────────────────────────
# 5. 截屏
# ─────────────────────────────────────────
def capture_screen(output_path: str = SCREENSHOT_PATH, monitor: int = 1) -> str:
    """极速截屏，返回图片路径"""
    with mss.MSS() as sct:
        sct.shot(output=output_path, mon=monitor)
    return output_path


def capture_region(x: int, y: int, w: int, h: int) -> str:
    """截取屏幕指定区域（修复：以前忽略了x,y,w,h参数，总是截全屏）"""
    output_path = f"/tmp/hermes_region_{int(time.time())}.png"
    with mss.MSS() as sct:
        region = {"left": x, "top": y, "width": w, "height": h}
        sct.img_to_png(sct.grab(region), output=output_path)
    return output_path


# ─────────────────────────────────────────
# 6. 本地 VLM（默认 qwen2.5vl:7b，备选 smolvlm2）
# ─────────────────────────────────────────
VLM_MODEL_DEFAULT = "qwen2.5vl:7b"
VLM_MODEL_FALLBACK = "ahmadwaqar/smolvlm2-agentic-gui:latest"

def ask_vlm(image_path: str, question: str, model: str = VLM_MODEL_DEFAULT,
            num_ctx: int = 4096, timeout: int = 90) -> str:
    """将截图发给本地 VLM 模型，返回回答"""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "model": model,
        "prompt": question,
        "images": [img_b64],
        "stream": False,
        "options": {"num_ctx": num_ctx}
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        d = r.json()
        if "error" in d:
            return f"[VLM错误] {d['error']}"
        return d.get("response", "")
    except requests.exceptions.Timeout:
        return "[VLM超时]"
    except Exception as e:
        return f"[VLM异常] {e}"


def ask_vlm_fast(image_path: str, question: str) -> str:
    """快速版：用 smolvlm2 做简单视觉问答（更快但更弱）"""
    return ask_vlm(image_path, question,
                   model=VLM_MODEL_FALLBACK, num_ctx=2048, timeout=30)


def find_element_by_vision(description: str) -> tuple:
    """视觉找坐标：如果找到返回 (x, y)，找不到返回 None"""
    img = capture_screen()
    prompt = (
        f"DIRECT指令：找到屏幕截图中「{description}」的位置。\n"
        f"不要解释，不要思考过程。\n"
        f"只返回一行JSON：{{\"x\": 中心点X坐标整数, \"y\": 中心点Y坐标整数}}\n"
        f"如果找不到，返回：{{\"x\": -1, \"y\": -1}}\n"
        f"只返回JSON，不要其他文字。"
    )
    result = ask_vlm(img, prompt)

    try:
        # 清理 JSON：去代码块标记、去多余换行、单引号转双引号
        clean = result.strip()
        clean = clean.replace("```json", "").replace("```", "").strip()
        clean = clean.replace("'", '"')

        # 尝试解析（可能返回数组 [{...}] 或单对象 {...}）
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}

        x, y = int(parsed.get('x', -1)), int(parsed.get('y', -1))
        if x < 0 or y < 0:
            return None
        return (x, y)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


# ─────────────────────────────────────────
# 7. 情绪分析（Qwen3:8b）
# ─────────────────────────────────────────
def analyze_emotion(text: str) -> dict:
    """分析文本情绪，返回 {'emotion': str, 'urgency': str}"""
    prompt = (
        f"分析以下消息的情绪和紧急程度：\n「{text}」\n\n"
        f"只返回一行JSON：{{'emotion': '急躁|平静|愤怒|开心|疑惑', 'urgency': '高|中|低'}}\n"
        f"只返回JSON，不要其他文字。"
    )

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "qwen3:8b",
            "prompt": prompt,
            "stream": False
        }, timeout=30)
        d = r.json()
        raw = d.get("response", "")

        # 括号计数法解析 JSON（处理嵌套问题）
        start = raw.find('{')
        if start == -1:
            return {"emotion": "平静", "urgency": "中"}
        depth = 0
        end = start
        for i, c in enumerate(raw[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        json_str = raw[start:end]
        # Qwen3 习惯用单引号，json.loads 只认双引号
        json_str = json_str.replace("'", '"')
        result = json.loads(json_str)
        return result
    except Exception:
        return {"emotion": "平静", "urgency": "中"}


# ─────────────────────────────────────────
# 8. 阅读时间计算
# ─────────────────────────────────────────
def human_reading_time(text_length: int, wpm: int = 500) -> float:
    """根据文本长度计算人类阅读时间（秒）"""
    minutes = text_length / wpm
    return max(0.5, minutes * 60)


# ─────────────────────────────────────────
# 9. 文本发送的"呼吸感"
# ─────────────────────────────────────────
def send_message_with_breath(text: str, contact_name: str = None):
    """
    分段发送消息，模拟"正在输入"的自然感。
    长文拆成2-3段，每段间隔3-8秒。
    适用于微信/QQ发送场景。
    """
    # 找输入框（通过视觉）
    input_coords = find_element_by_vision("输入框")
    if not input_coords:
        print("[humanization] 无法找到输入框坐标")
        return False

    x, y = input_coords
    human_click(x, y)
    time.sleep(random.uniform(0.2, 0.5))

    # 拆段
    paragraphs = text.split('\n')
    if len(paragraphs) < 2 and len(text) > 50:
        # 如果没有换行，按50字拆
        paragraphs = [text[i:i+50] for i in range(0, len(text), 50)]

    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        human_type(para)
        if i < len(paragraphs) - 1:
            # 发一段，停顿一下
            time.sleep(random.uniform(3, 8))

    return True


# ─────────────────────────────────────────
# 10. 一键截图找按钮并点击（主流程）
# ─────────────────────────────────────────
def vlm_click(target: str, max_retries: int = 2) -> bool:
    """
    主流程：截图 -> VLM找坐标 -> 拟真点击
    适用于：微信发送按钮、1688确认框、任意视觉元素
    """
    for attempt in range(max_retries):
        coords = find_element_by_vision(target)
        if coords:
            x, y = coords
            human_click(x, y)
            # 点击后等一下，然后截一张确认
            time.sleep(random.uniform(0.5, 1.0))
            confirm_img = capture_screen()
            confirm_result = ask_vlm(confirm_img,
                "简单描述：操作成功了吗？有没有报错？有就说是，没有就说否。")
            if "否" not in confirm_result and "错误" not in confirm_result and "报错" not in confirm_result:
                print(f"[humanization] ✓ 已点击: {target}")
                return True
            else:
                print(f"[humanization] ⚠ 点击后确认失败，重试 {attempt+1}/{max_retries}")
        else:
            print(f"[humanization] ⚠ 未找到: {target}，重试 {attempt+1}/{max_retries}")

    print(f"[humanization] ✗ 全部失败: {target}")
    return False


# ─────────────────────────────────────────
# 11. 人机控制权交接（pynput 实现）
# ─────────────────────────────────────────
_human_active = False
_last_human_time = time.time()
TAKEOVER_TIMEOUT = 3.0  # 人类停止操作后 3s 自动恢复

def _on_mouse_move(x, y):
    global _human_active, _last_human_time
    _human_active = True
    _last_human_time = time.time()

def _on_mouse_click(x, y, button, pressed):
    global _human_active, _last_human_time
    _human_active = True
    _last_human_time = time.time()

def _on_key_press(key):
    global _human_active, _last_human_time
    _human_active = True
    _last_human_time = time.time()

_listener = None

def start_human_takeover():
    """启动人机控制权监听（后台线程）"""
    global _listener, _human_active, _last_human_time
    try:
        from pynput import mouse, keyboard
        _listener = mouse.Listener(
            on_move=_on_mouse_move,
            on_click=_on_mouse_click
        )
        _listener.daemon = True
        _listener.start()

        _kb_listener = keyboard.Listener(on_press=_on_key_press)
        _kb_listener.daemon = True
        _kb_listener.start()

        _human_active = False
        _last_human_time = time.time()
        print("[humanization] 人机控制权监听已启动")
        return True
    except Exception as e:
        print(f"[humanization] 控制权监听启动失败: {e}")
        return False


def is_human_takeover_active() -> bool:
    """检查人类是否正在操作"""
    global _human_active, _last_human_time
    if not _human_active:
        return False
    # 如果超过 TAKEOVER_TIMEOUT 无人操作，认为已交还
    if time.time() - _last_human_time > TAKEOVER_TIMEOUT:
        _human_active = False
        return False
    return True


def wait_for_human_release(timeout: float = 30.0) -> bool:
    """等待人类松开控制权，返回是否在超时内恢复"""
    start = time.time()
    while is_human_takeover_active():
        time.sleep(0.5)
        if time.time() - start > timeout:
            print(f"[humanization] 等待人类交还控制超时 ({timeout}s)")
            return False
        print("[humanization] ⏳ 等待人类操作完毕...")
    print("[humanization] ✓ 人类操作完毕，Hermes 恢复控制")
    return True


# 自启动
if not _listener:
    start_human_takeover()
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes humanization-core 自检 ===")
    print(f"屏幕尺寸: {pyautogui.size()}")
    print(f"当前鼠标位置: {pyautogui.position()}")

    # 测试截屏
    img = capture_screen()
    print(f"截屏保存至: {img}")

    # 测试情绪分析
    test_texts = [
        "今天那个供应商又拖延了，很烦",
        "这个价格可以，你看着办",
        "！！！紧急：客户投诉了"
    ]
    for t in test_texts:
        r = analyze_emotion(t)
        print(f"情绪分析 「{t}」=> {r}")
