#!/usr/bin/env python3
"""
Hermes vision-connect: 截屏 → VLM分析 → 拟真执行
免费优先：本地Ollama Qwen2.5-VL > OpenRouter Gemini Flash

流程：
1. capture_screen() 截屏
2. send_to_vlm() 发给视觉模型
3. parse_response() 解析坐标和动作
4. execute_action() 用human-rpa执行
5. capture_verify() SSIM验证
"""

import random
import os
import sys
import json
import time
import base64
import mss
import numpy as np
import requests
import subprocess

SCREENSHOT_PATH = "/tmp/hermes_screen.png"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ─────────────────────────────────────────
# 1. 截屏
# ─────────────────────────────────────────
def capture_screen(path: str = SCREENSHOT_PATH) -> str:
    """截屏保存到指定路径，返回路径"""
    with mss.mss() as s:
        s.shot(output=path)
    return path

# ─────────────────────────────────────────
# 2. 发给VLM分析
# ─────────────────────────────────────────
def ask_screen(question: str, timeout: int = 60) -> str:
    """
    看屏幕，问问题，返回回答。
    优先 Ollama Qwen2.5-VL，失败则用 OpenRouter Gemini Flash。
    """
    img_path = capture_screen()
    
    # 优先 Ollama
    try:
        return ask_ollama_vlm(img_path, question, timeout=timeout)
    except Exception as e:
        print(f"[vision] Ollama不可用: {e}, 切换OpenRouter")
        try:
            return ask_openrouter_vlm(img_path, question, timeout=timeout)
        except Exception as e2:
            print(f"[vision] OpenRouter也失败: {e2}")
            return ""

def ask_ollama_vlm(img_path: str, question: str, timeout: int = 60) -> str:
    """调用本地 Ollama Qwen2.5-VL / smolvlm2（优先smolvlm2，备选qwen2.5vl）"""
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    prompt = f"你是一个屏幕理解助手。用户问：{question}\n请仔细看图，直接回答。"
    
    # 优先 smolvlm2（轻量，2GB，24GB可用）
    models_to_try = [
        ("ahmadwaqar/smolvlm2-agentic-gui:latest", 60),
        ("qwen2.5vl:7b", 90),
    ]
    
    for model, tout in models_to_try:
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False
            }
            resp = requests.post(OLLAMA_URL, json=payload, timeout=tout)
            resp.raise_for_status()
            result = resp.json().get("response", "").strip()
            if result:
                print(f"[vision] Ollama {model} 成功")
                return result
        except Exception as e:
            print(f"[vision] Ollama {model} 失败: {e}")
            continue
    
    raise RuntimeError("所有Ollama模型都不可用")

def ask_openrouter_vlm(img_path: str, question: str, timeout: int = 60) -> str:
    """调用 OpenRouter Gemini Flash（兜底方案）"""
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # 读取 OpenRouter API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        # 尝试从 ~/.hermes/.env 读
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"')
                        break
    
    if not api_key:
        raise RuntimeError("未配置 OPENROUTER_API_KEY")
    
    payload = {
        "model": "google/gemini-2.0-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": question}
            ]
        }]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

# ─────────────────────────────────────────
# 3. 解析坐标
# ─────────────────────────────────────────
def parse_click_instruction(response: str) -> tuple:
    """
    从VLM响应中解析出坐标。
    期望格式：坐标或"未找到"
    """
    import re
    
    # 尝试找坐标格式 (x, y) 或 x,y
    patterns = [
        r'\((\d+),\s*(\d+)\)',
        r'坐标[：:]\s*(\d+)[,，]\s*(\d+)',
        r'x[=：]\s*(\d+)[,，]\s*y[=：]\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            return int(match.group(1)), int(match.group(2))
    
    # 尝试从文字描述中提取
    numbers = re.findall(r'\b(\d{2,4})\b', response)
    if len(numbers) >= 2:
        # 取最后两个（通常是坐标）
        return int(numbers[-2]), int(numbers[-1])
    
    return None, None

# ─────────────────────────────────────────
# 4. 找元素并点击
# ─────────────────────────────────────────
def find_and_click(description: str, retry: int = 2) -> dict:
    """
    主流程：截屏 → VLM找坐标 → 拟真点击 → SSIM验证
    
    返回：{"success": bool, "coords": (x,y), "ssim": float, "retry_count": int}
    """
    for attempt in range(retry + 1):
        # 截屏
        img_path = capture_screen()
        
        # 构造提示
        prompt = (
            f'你是一个屏幕理解助手。用户在屏幕上找"{description}"。'
            f'如果找到了，返回格式：坐标(x, y) = 具体像素坐标，x是列（从左到右），y是行（从上到下）。'
            f'如果没找到，直接说"未找到"。'
            f'只返回一个坐标，不要多余文字。'
        )
        
        # 发给VLM
        try:
            response = ask_ollama_vlm(img_path, prompt, timeout=90)
        except:
            try:
                response = ask_openrouter_vlm(img_path, prompt, timeout=60)
            except Exception as e:
                print(f"[vision] VLM调用失败: {e}")
                continue
        
        # 解析坐标
        x, y = parse_click_instruction(response)
        if x is None or y is None:
            print(f"[vision] 第{attempt+1}次：VLM未返回坐标，响应: {response[:100]}")
            time.sleep(1)
            continue
        
        print(f"[vision] 第{attempt+1}次：找到{description}坐标({x}, {y})")
        
        # 执行拟真点击（用human-rpa插件）
        success = execute_human_click(x, y)
        
        if not success:
            print(f"[vision] 点击执行失败")
            continue
        
        # SSIM验证
        time.sleep(0.5)
        ssim_val = capture_verify(img_path)
        print(f"[vision] SSIM验证: {ssim_val:.3f}")
        
        if ssim_val < 0.95:
            print(f"[vision] 点击成功，页面有变化 (SSIM={ssim_val:.3f})")
            return {"success": True, "coords": (x, y), "ssim": ssim_val, "retry_count": attempt}
        else:
            print(f"[vision] 页面无变化，重新尝试")
            time.sleep(1)
    
    return {"success": False, "coords": None, "ssim": None, "retry_count": retry}

# ─────────────────────────────────────────
# 5. 拟真点击执行
# ─────────────────────────────────────────
def execute_human_click(x: int, y: int) -> bool:
    """
    调用human-rpa插件执行拟真点击。
    优先用cliclick（已安装），备选pyautogui。
    """
    try:
        # 曲线移动 + 点击
        out = subprocess.check_output(["cliclick", "p"], text=True, timeout=2)
        cur_x, cur_y = map(float, out.strip().split(","))
    except:
        cur_x, cur_y = 640, 400
    
    # 贝塞尔曲线移动
    path = generate_bezier_path((cur_x, cur_y), (x, y), roughness=0.8)
    for px, py in path:
        try:
            subprocess.run(["cliclick", f"m:{px:.1f},{py:.1f}"],
                         check=True, capture_output=True, timeout=0.5)
            time.sleep(random.uniform(0.005, 0.015))
        except:
            pass
    
    time.sleep(random.uniform(0.05, 0.15))
    
    # 点击
    try:
        subprocess.run(["cliclick", f"c:{x:.0f},{y:.0f}"],
                     check=True, capture_output=True, timeout=1)
        return True
    except:
        return False

def generate_bezier_path(start: tuple, end: tuple, roughness: float = 0.8) -> list:
    """生成贝塞尔曲线路径"""
    import random
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    dist = (dx**2 + dy**2) ** 0.5
    
    jitter = dist * roughness * 0.2
    cx1 = sx + dx * 0.3 + random.uniform(-jitter, jitter)
    cy1 = sy + dy * 0.3 + random.uniform(-jitter, jitter)
    cx2 = sx + dx * 0.7 + random.uniform(-jitter, jitter)
    cy2 = sy + dy * 0.7 + random.uniform(-jitter, jitter)
    
    steps = max(8, int(dist / 20))
    path = []
    for i in range(steps + 1):
        t = i / steps
        one_minus_t = 1 - t
        bx = one_minus_t**2 * sx + 2*one_minus_t*t*cx1 + t**2*ex
        by = one_minus_t**2 * sy + 2*one_minus_t*t*cy1 + t**2*ey
        path.append((bx, by))
    
    return path

# ─────────────────────────────────────────
# 6. SSIM验证
# ─────────────────────────────────────────
def capture_verify(before_path: str) -> float:
    """
    截图对比，SSIM验证。
    返回SSIM值：<0.92表示显著变化（成功），>0.98表示几乎无变化（失败）
    """
    after_path = "/tmp/hermes_screen_after.png"
    capture_screen(after_path)
    
    try:
        from PIL import Image
        import math
        
        img1 = Image.open(before_path).convert("RGB")
        img2 = Image.open(after_path).convert("RGB")
        
        # 缩放到小图加速
        w1, h1 = img1.size
        img1_small = img1.resize((128, 72))
        img2_small = img2.resize((128, 72))
        
        arr1 = np.array(img1_small, dtype=np.float64)
        arr2 = np.array(img2_small, dtype=np.float64)
        
        # SSIM
        mu1 = arr1.mean()
        mu2 = arr2.mean()
        sigma1 = arr1.std()
        sigma2 = arr2.std()
        sigma12 = ((arr1 - mu1) * (arr2 - mu2)).mean()
        
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        
        ssim = ((2*mu1*mu2 + c1) * (2*sigma12 + c2)) / \
               ((mu1**2 + mu2**2 + c1) * (sigma1**2 + sigma2**2 + c2))
        
        return float(ssim)
    except Exception as e:
        print(f"[vision] SSIM计算失败: {e}")
        return 0.95  # 不确定的情况

# ─────────────────────────────────────────
# 7. 入口函数
# ─────────────────────────────────────────
def vlm_click(description: str, retry: int = 2) -> dict:
    """对外接口：vlm_click("按钮描述") → 自动完成找+点+验证"""
    return find_and_click(description, retry=retry)

# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes vision-connect 自检 ===")
    
    # 测试截屏
    path = capture_screen()
    print(f"截屏: {path}, 大小: {os.path.getsize(path)} bytes")
    
    # 测试VLM（优先smolvlm2）
    print("\n测试VLM（问屏幕内容）...")
    try:
        result = ask_ollama_vlm(path, "当前屏幕是什么内容？用一句话描述。", timeout=60)
        print(f"屏幕内容: {result[:200]}")
    except Exception as e:
        print(f"VLM失败: {e}")
    
    # 测试找元素（用"访达图标"这种明确描述）
    print("\n测试find_and_click（找Safari图标）...")
    coords = find_and_click("Safari图标", retry=1)
    print(f"结果: {coords}")