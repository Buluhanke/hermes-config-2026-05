#!/usr/bin/env python3
"""
captcha_solver.py — 验证码统一解题器
支持: 滑块 / 点选 / 拼图 / 旋转 / reCAPTCHA v2/v3 / Turnstile

使用方式:
    python3 captcha_solver.py slider <slider_b64> <bg_b64>
    python3 captcha_solver.py click <image_b64> <instruction>
    python3 captcha_solver.py jigsaw <image_b64>
"""

import sys
import json
import time
import base64
import random
import subprocess
import re
import os
from pathlib import Path

# ============ 配置 ============
CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY", "")
OLLAMA_URL = "http://localhost:11434/api/generate"

# ============ 1. 滑块验证码 ============
def solve_slider_captcha(slider_b64: str, bg_b64: str) -> dict:
    """
    通过 CapSolver 解决滑动验证码，返回 {"point": {"x": int}}
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Slide",
            "images": [slider_b64, bg_b64],
            "method": "common"
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    # 轮询结果
    for _ in range(20):
        time.sleep(1)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"]["point"]
        if result["status"] == "failed":
            raise RuntimeError(f"CapSolver 失败: {result}")
    
    raise RuntimeError("CapSolver 滑块任务超时")

# ============ 2. 点选验证码 ============
def solve_click_captcha_local(image_b64: str, instruction: str) -> list[dict]:
    """
    用 smolvlm2 本地解决点选验证码，返回 [{"x": int, "y": int}, ...]
    """
    payload = {
        "model": "ahmadwaqar/smolvlm2-agentic-gui",
        "prompt": (
            f"这是一个点选验证码。按照指令点击图中对应物体。\n"
            f"指令: {instruction}\n"
            f"请用中文简短回答你点击的位置，格式: click(x=0.XXX, y=0.XXX)\n"
            f"如果有多个目标，按顺序回答每个的坐标。\n<image>"
        ),
        "images": [image_b64],
        "stream": False
    }
    
    resp = _ollama_request(payload)
    response_text = resp.get("response", "")
    
    coords = []
    # 解析 click(x=0.XXX, y=0.XXX)
    for m in re.finditer(r'click\s*\(\s*x\s*=\s*([\d.]+)\s*,\s*y\s*=\s*([\d.]+)\s*\)', response_text):
        norm_x, norm_y = float(m.group(1)), float(m.group(2))
        # 需要屏幕分辨率来反算，这里返回归一化坐标
        coords.append({"norm_x": norm_x, "norm_y": norm_y})
    
    return coords

def solve_click_captcha_capsolver(image_b64: str, instruction: str) -> list[dict]:
    """
    通过 CapSolver 解决点选验证码
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Custom",
            "image": image_b64,
            "instructions": instruction,
            "module": "clickCaptcha"
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(30):
        time.sleep(1)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            clicks = result["solution"].get("click", [])
            return clicks
    
    raise RuntimeError("CapSolver 点选任务超时")

# ============ 3. 拼图验证码 ============
def solve_jigsaw_captcha(image_b64: str) -> dict:
    """
    通过 CapSolver 解决拼图验证码，返回 {"refPoint": {"x": int, "y": int}}
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Jigsaw",
            "images": [image_b64]
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(20):
        time.sleep(1)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"]
    
    raise RuntimeError("CapSolver 拼图任务超时")

# ============ 4. 旋转验证码 ============
def solve_rotation_captcha(image_b64: str) -> float:
    """
    通过 CapSolver 解决旋转验证码，返回角度（度）
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Rotate",
            "image": image_b64,
            "module": "rotateCaptcha"
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(30):
        time.sleep(1)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"].get("angle", 0)
    
    raise RuntimeError("CapSolver 旋转任务超时")

# ============ 5. reCAPTCHA / Turnstile ============
def solve_recaptcha_v2(site_url: str, site_key: str) -> str:
    """
    通过 CapSolver 解决 reCAPTCHA v2，返回 token
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "RecaptchaV2Task",
            "websiteURL": site_url,
            "websiteKey": site_key
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(60):
        time.sleep(2)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"]["gRecaptchaResponse"]
    
    raise RuntimeError("CapSolver reCAPTCHA v2 任务超时")

def solve_recaptcha_v3(site_url: str, site_key: str, min_score: float = 0.3) -> str:
    """
    通过 CapSolver 解决 reCAPTCHA v3，返回 token
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "RecaptchaV3Task",
            "websiteURL": site_url,
            "websiteKey": site_key,
            "minScore": min_score
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(60):
        time.sleep(2)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"]["gRecaptchaResponse"]
    
    raise RuntimeError("CapSolver reCAPTCHA v3 任务超时")

def solve_turnstile(site_url: str, site_key: str) -> str:
    """
    通过 CapSolver 解决 Cloudflare Turnstile，返回 token
    """
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY 未设置")

    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "TurnstileTask",
            "websiteURL": site_url,
            "websiteKey": site_key
        }
    }
    
    resp = _capsolver_request("createTask", payload)
    task_id = resp["taskId"]
    
    for _ in range(30):
        time.sleep(1)
        result = _capsolver_request("getTaskResult", {
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })
        if result["status"] == "ready":
            return result["solution"]["token"]
    
    raise RuntimeError("CapSolver Turnstile 任务超时")

# ============ 6. 人类轨迹拖动 ============
def humanoid_slider_drag(start_x: int, start_y: int, end_x: int, end_y: int):
    """
    人类拖拽轨迹：变速度 + Bezier曲线 + overshoot回退
    集成自 references/captcha-slider-2026-05-13.md
    """
    import math
    
    def lerp(a, b, t):
        return a + (b - a) * t
    
    def random_uniform(low, high):
        return low + random.random() * (high - low)
    
    # Bezier 曲线路径
    roughness = 0.8
    cx1 = start_x + (end_x - start_x) * 0.3 + random_uniform(-30, 30) * roughness
    cy1 = start_y + random_uniform(-20, 20) * roughness
    cx2 = start_x + (end_x - start_x) * 0.7 + random_uniform(-30, 30) * roughness
    cy2 = end_y + random_uniform(-20, 20) * roughness
    
    path = []
    for i in range(21):
        t = i / 20
        t1 = 1 - t
        x = t1**3 * start_x + 3 * t1**2 * t * cx1 + 3 * t1 * t**2 * cx2 + t**3 * end_x
        y = t1**3 * start_y + 3 * t1**2 * t * cy1 + 3 * t1 * t**2 * cy2 + t**3 * end_y
        path.append((x, y))
    
    # 鼠标按下
    time.sleep(random_uniform(0.05, 0.15))  # 起点犹豫
    subprocess.run(["cliclick", f"m:{start_x:.0f},{start_y:.0f}"], check=True)
    time.sleep(random_uniform(0.03, 0.08))
    
    # 移动路径（前70%快速，后30%慢速）
    split = int(len(path) * 0.7)
    for i, (x, y) in enumerate(path):
        delay = random_uniform(0.005, 0.015) if i < split else random_uniform(0.03, 0.08)
        subprocess.run(["cliclick", f"m:{x:.0f},{y:.0f}"], check=True)
        time.sleep(delay)
    
    # overshoot + 回退
    direction = 1 if end_x > start_x else -1
    overshoot_px = random.randint(5, 15)
    overshoot_x = end_x + direction * overshoot_px
    subprocess.run(["cliclick", f"m:{overshoot_x:.0f},{end_y:.0f}"], check=True)
    time.sleep(random_uniform(0.05, 0.15))
    
    # 回退
    backtrack_px = random.randint(3, 8)
    backtrack_x = overshoot_x - direction * backtrack_px
    for step in range(3):
        intermediate_x = overshoot_x - direction * backtrack_px * (step + 1) / 3
        subprocess.run(["cliclick", f"m:{intermediate_x:.0f},{end_y:.0f}"], check=True)
        time.sleep(random_uniform(0.02, 0.05))
    
    # 松开
    time.sleep(random_uniform(0.05, 0.1))
    subprocess.run(["cliclick", "ku:0"], check=True)

# ============ 内部工具 ============
def _capsolver_request(endpoint: str, payload: dict) -> dict:
    """发送 CapSolver API 请求"""
    import urllib.request
    
    url = f"https://api.capsolver.com/{endpoint}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def _ollama_request(payload: dict) -> dict:
    """发送 Ollama 请求"""
    import urllib.request
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

def image_to_b64(path: str) -> str:
    """图片文件转 base64"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ============ CLI 入口 ============
def main():
    if len(sys.argv) < 2:
        print("用法: python3 captcha_solver.py <action> [args...]")
        print("  slider <slider.png> <bg.png>          — 滑块验证码")
        print("  click <image.png> <instruction>       — 点选验证码")
        print("  jigsaw <image.png>                    — 拼图验证码")
        print("  rotate <image.png>                    — 旋转验证码")
        print("  recaptcha_v2 <site_url> <site_key>    — reCAPTCHA v2")
        print("  recaptcha_v3 <site_url> <site_key>   — reCAPTCHA v3")
        print("  turnstile <site_url> <site_key>       — Turnstile")
        print("  drag <start_x> <start_y> <end_x> <end_y> — 人类轨迹拖动")
        sys.exit(1)
    
    action = sys.argv[1]
    
    try:
        if action == "slider":
            slider_b64 = image_to_b64(sys.argv[2])
            bg_b64 = image_to_b64(sys.argv[3])
            result = solve_slider_captcha(slider_b64, bg_b64)
            print(json.dumps(result))
        
        elif action == "click":
            image_b64 = image_to_b64(sys.argv[2])
            instruction = sys.argv[3]
            # 优先本地 smolvlm2，失败再用 CapSolver
            try:
                result = solve_click_captcha_local(image_b64, instruction)
            except Exception:
                result = solve_click_captcha_capsolver(image_b64, instruction)
            print(json.dumps(result))
        
        elif action == "jigsaw":
            image_b64 = image_to_b64(sys.argv[2])
            result = solve_jigsaw_captcha(image_b64)
            print(json.dumps(result))
        
        elif action == "rotate":
            image_b64 = image_to_b64(sys.argv[2])
            result = solve_rotation_captcha(image_b64)
            print(json.dumps({"angle": result}))
        
        elif action == "recaptcha_v2":
            result = solve_recaptcha_v2(sys.argv[2], sys.argv[3])
            print(json.dumps({"token": result}))
        
        elif action == "recaptcha_v3":
            result = solve_recaptcha_v3(sys.argv[2], sys.argv[3])
            print(json.dumps({"token": result}))
        
        elif action == "turnstile":
            result = solve_turnstile(sys.argv[2], sys.argv[3])
            print(json.dumps({"token": result}))
        
        elif action == "drag":
            start_x, start_y = int(sys.argv[2]), int(sys.argv[3])
            end_x, end_y = int(sys.argv[4]), int(sys.argv[5])
            humanoid_slider_drag(start_x, start_y, end_x, end_y)
            print(json.dumps({"success": True}))
        
        else:
            print(f"未知动作: {action}")
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
