#!/usr/bin/env python3
"""
Hermes vision-connect: 三层感知视觉闭环
Layer 1: Apple Vision OCR（60-240ms，极速文字定位）
Layer 2: smolvlm2 本地VLM（2-5s，兜底语义理解）
Layer 3: OpenRouter Gemini Flash（云端兜底，$0.001/M）

执行：human-rpa 贝塞尔曲线拟真点击
验证：SSIM截图对比
"""

import os
import sys
import json
import time
import base64
import random
import mss
import numpy as np
import requests
import subprocess
try:
    import Vision
    import AppKit
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

SCREENSHOT_PATH = "/tmp/hermes_screen.png"
SCREENSHOT_AFTER = "/tmp/hermes_screen_after.png"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ─────────────────────────────────────────
# Layer 1: Apple Vision OCR（极速）
# ─────────────────────────────────────────
def vision_ocr(query: str, region=None) -> list:
    """
    用 Apple Vision 做极速文字识别。
    返回：[(text, x, y, width, height), ...]
    坐标是归一化的（0-1），需要乘以屏幕宽高转换。
    如果 Vision 不可用，fallback 到 tesseract OCR。
    """
    if not HAS_VISION:
        # Fallback: 用 tesseract（需 brew install tesseract tesseract-lang）
        try:
            out_path = SCREENSHOT_PATH.replace(".png", "_ocr.txt")
            r = subprocess.run(
                ["tesseract", SCREENSHOT_PATH, out_path.replace(".txt", ""),
                 "-l", "eng+chi_sim", "--psm", "6"],
                capture_output=True, timeout=15
            )
            if r.returncode == 0 and os.path.exists(out_path):
                with open(out_path) as f:
                    text = f.read().strip()
                # 简单返回：整页文字，坐标未知
                return [{"text": text, "x": 0, "y": 0, "w": 0, "h": 0, "confidence": 0.5}]
        except Exception as e:
            print(f"[vision] tesseract fallback失败: {e}")
        return []

    img = AppKit.NSImage.alloc().initWithContentsOfFile_(SCREENSHOT_PATH)
    if not img:
        return []
    
    cg_image = img.CGImageForProposedRect_context_hints_(None, None, None)[0]
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(1)  # 1=fast, 2=accurate
    
    # 可选：限定区域加速
    if region:
        req.setRegionOfInterest_(region)
    
    handler.performRequests_error_([req], None)
    results = req.results()
    
    if not results:
        return []
    
    w, h = img.size().width, img.size().height
    texts = []
    for r in results:
        bbox = r.boundingBox()
        # Vision坐标是左下角原点，转成左上角
        x = bbox.origin.x * w
        y = (1 - bbox.origin.y - bbox.size.height) * h
        texts.append({
            "text": r.text(),
            "x": x,
            "y": y,
            "w": bbox.size.width * w,
            "h": bbox.size.height * h,
            "confidence": r.confidence()
        })
    
    return texts

def ocr_find_coordinates(query: str, screen_w=None, screen_h=None) -> tuple:
    """
    用 OCR 找文字的像素坐标。
    模糊匹配：query 是目标文字的部分匹配即可。
    返回：(x, y) 或 (None, None)
    """
    texts = vision_ocr(query)
    if not texts:
        return None, None
    
    query_lower = query.lower()
    
    # 模糊匹配：找包含query或者query包含它的
    for t in texts:
        t_text = t["text"].lower().strip()
        if not t_text:
            continue
        
        # 完全包含
        if query_lower in t_text or t_text in query_lower:
            cx = t["x"] + t["w"] / 2
            cy = t["y"] + t["h"] / 2
            return int(cx), int(cy)
        
        # 编辑距离小于3（打字错误容错）
        if levenshtein_distance(query_lower, t_text) <= 3:
            cx = t["x"] + t["w"] / 2
            cy = t["y"] + t["h"] / 2
            return int(cx), int(cy)
    
    return None, None

def levenshtein_distance(s1: str, s2: str) -> int:
    """简单编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, prev[j] + (c1 != c2), curr[-1] + 1))
        prev = curr
    return prev[-1]

# ─────────────────────────────────────────
# Layer 2: Ollama smolvlm2 视觉
# ─────────────────────────────────────────
def ask_ollama_vlm(img_path: str, question: str, timeout: int = 60) -> str:
    """调用本地 Ollama smolvlm2"""
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    prompt = f"你是一个屏幕理解助手。用户问：{question}\n请仔细看图，直接回答。"
    
    models_to_try = [
        ("ahmadwaqar/smolvlm2-agentic-gui:latest", 60),
        ("qwen2.5vl:7b", 90),
    ]
    
    for model, tout in models_to_try:
        try:
            payload = {"model": model, "prompt": prompt, "images": [img_b64], "stream": False}
            resp = requests.post(OLLAMA_URL, json=payload, timeout=tout)
            resp.raise_for_status()
            result = resp.json().get("response", "").strip()
            if result:
                return result
        except Exception as e:
            continue
    
    raise RuntimeError("Ollama不可用")

# ─────────────────────────────────────────
# Layer 3: OpenRouter Gemini Flash
# ─────────────────────────────────────────
def ask_openrouter_vlm(img_path: str, question: str, timeout: int = 60) -> str:
    """调用 OpenRouter Gemini Flash"""
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
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
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

# ─────────────────────────────────────────
# 截屏
# ─────────────────────────────────────────
def capture_screen(path: str = SCREENSHOT_PATH) -> str:
    with mss.mss() as s:
        s.shot(output=path)
    return path

# ─────────────────────────────────────────
# 解析 VLM 坐标响应
# ─────────────────────────────────────────
def parse_click_instruction(response: str) -> tuple:
    import re
    patterns = [
        r'\((\d+),\s*(\d+)\)',
        r'坐标[：:]\s*(\d+)[,，]\s*(\d+)',
        r'x[=：]\s*(\d+)[,，]\s*y[=：]\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            return int(match.group(1)), int(match.group(2))
    
    numbers = re.findall(r'\b(\d{2,4})\b', response)
    if len(numbers) >= 2:
        return int(numbers[-2]), int(numbers[-1])
    
    return None, None

# ─────────────────────────────────────────
# 执行：human-rpa 拟真点击
# ─────────────────────────────────────────
def execute_human_click(x: int, y: int) -> bool:
    """贝塞尔曲线移动 + 点击"""
    try:
        out = subprocess.check_output(["cliclick", "p"], text=True, timeout=2)
        cur_x, cur_y = map(float, out.strip().split(","))
    except:
        cur_x, cur_y = 640, 400
    
    path = generate_bezier_path((cur_x, cur_y), (x, y), roughness=0.8)
    for px, py in path:
        try:
            subprocess.run(["cliclick", f"m:{px:.1f},{py:.1f}"],
                         check=True, capture_output=True, timeout=0.5)
            time.sleep(random.uniform(0.005, 0.015))
        except:
            pass
    
    time.sleep(random.uniform(0.05, 0.15))
    try:
        subprocess.run(["cliclick", f"c:{x:.0f},{y:.0f}"],
                     check=True, capture_output=True, timeout=1)
        return True
    except:
        return False

def generate_bezier_path(start: tuple, end: tuple, roughness: float = 0.8) -> list:
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
# SSIM 验证
# ─────────────────────────────────────────
def capture_verify(before_path: str) -> float:
    capture_screen(SCREENSHOT_AFTER)
    try:
        from PIL import Image
        img1 = Image.open(before_path).convert("RGB")
        img2 = Image.open(SCREENSHOT_AFTER).convert("RGB")
        img1_small = img1.resize((128, 72))
        img2_small = img2.resize((128, 72))
        arr1 = np.array(img1_small, dtype=np.float64)
        arr2 = np.array(img2_small, dtype=np.float64)
        mu1 = arr1.mean(); mu2 = arr2.mean()
        sigma1 = arr1.std(); sigma2 = arr2.std()
        sigma12 = ((arr1 - mu1) * (arr2 - mu2)).mean()
        c1 = (0.01 * 255) ** 2; c2 = (0.03 * 255) ** 2
        ssim = ((2*mu1*mu2 + c1) * (2*sigma12 + c2)) / \
               ((mu1**2 + mu2**2 + c1) * (sigma1**2 + sigma2**2 + c2))
        return float(ssim)
    except:
        return 0.95

# ─────────────────────────────────────────
# 三层感知主函数：smart_click
# ─────────────────────────────────────────
def smart_click(description: str, retry: int = 2) -> dict:
    """
    三层感知找元素并点击：
    1. Vision OCR（60-240ms）→ 快速文字定位
    2. smolvlm2 VLM（2-5s）→ 兜底语义理解
    3. Gemini Flash → 云端兜底
    
    返回：{"success": bool, "coords": (x,y), "layer": str, "ssim": float}
    """
    for attempt in range(retry + 1):
        # Layer 1: Vision OCR
        x, y = ocr_find_coordinates(description)
        if x is not None and y is not None:
            print(f"[vision] L1 Vision OCR找到 {description} @ ({x}, {y})")
            execute_human_click(x, y)
            time.sleep(0.5)
            ssim = capture_verify(SCREENSHOT_PATH)
            if ssim < 0.95:
                return {"success": True, "coords": (x, y), "layer": "vision_ocr", "ssim": ssim}
            else:
                print(f"[vision] L1 OCR命中但页面无变化，继续...")
        
        # Layer 2: smolvlm2 VLM
        img_path = capture_screen()
        try:
            response = ask_ollama_vlm(img_path, 
                f'用户要找"{description}"。如果找到了，返回坐标格式：(x, y)。没找到说"未找到"。')
            x, y = parse_click_instruction(response)
            if x is not None and y is not None:
                print(f"[vision] L2 smolvlm2找到 {description} @ ({x}, {y})")
                execute_human_click(x, y)
                time.sleep(0.5)
                ssim = capture_verify(img_path)
                return {"success": True, "coords": (x, y), "layer": "smolvlm2", "ssim": ssim}
        except Exception as e:
            print(f"[vision] L2 smolvlm2失败: {e}")
        
        # Layer 3: Gemini Flash
        try:
            response = ask_openrouter_vlm(img_path,
                f'用户要找"{description}"。如果找到了，返回坐标(x, y)。没找到说"未找到"。')
            x, y = parse_click_instruction(response)
            if x is not None and y is not None:
                print(f"[vision] L3 Gemini找到 {description} @ ({x}, {y})")
                execute_human_click(x, y)
                time.sleep(0.5)
                ssim = capture_verify(img_path)
                return {"success": True, "coords": (x, y), "layer": "gemini_flash", "ssim": ssim}
        except Exception as e:
            print(f"[vision] L3 Gemini失败: {e}")
        
        time.sleep(1)
    
    return {"success": False, "coords": None, "layer": "exhausted", "ssim": None}

# ─────────────────────────────────────────
# 入口函数
# ─────────────────────────────────────────
def find_and_click(description: str, retry: int = 2) -> dict:
    """find_and_click = smart_click（别名，方便记忆）"""
    return smart_click(description, retry=retry)

def ask_screen(question: str) -> str:
    """看屏幕，问问题"""
    img_path = capture_screen()
    try:
        return ask_ollama_vlm(img_path, question)
    except:
        return ask_openrouter_vlm(img_path, question)

# ─────────────────────────────────────────
# 自检
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=== Hermes vision-connect 三层感知自检 ===")
    
    # L1: OCR 测试
    print("\n[L1] Vision OCR 测试...")
    texts = vision_ocr("")
    print(f"  识别到 {len(texts)} 个文本块")
    for t in texts[:3]:
        print(f'  "{t["text"][:30]}" @ ({t["x"]:.0f}, {t["y"]:.0f})')
    
    # L2: VLM 测试
    print("\n[L2] smolvlm2 测试...")
    try:
        result = ask_ollama_vlm(capture_screen(), "当前屏幕是什么？一句话描述。")
        print(f"  屏幕内容: {result[:100]}")
    except Exception as e:
        print(f"  L2失败: {e}")
    
    # 全流程测试
    print("\n[全流程] smart_click 测试...")
    result = smart_click("Safari", retry=1)
    print(f"  结果: {result}")