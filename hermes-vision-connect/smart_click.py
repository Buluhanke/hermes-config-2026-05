#!/usr/bin/env python3
"""
smart_click 三层感知系统 v2
基于 smolvlm2（1.8B，24GB M4 可跑）

架构:
层级1: Vision OCR (60-240ms) - Apple原生，文字按钮零Token
层级2: smolvlm2 视觉 (5-15s) - 复杂元素兜底，/api/chat 接口
层级3: SSIM验证 (5ms) - 像素级点击确认

思路: 看见->看清->看懂->动手->精确
随着画面变化调整动手位置
"""
import sys, os, time, re, json, base64, subprocess, random
import pyautogui
import numpy as np
import requests

SCREENSHOT_PATH = "/tmp/hermes_screen.png"
OLLAMA_GENERATE = "http://127.0.0.1:11434/api/generate"
OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "ahmadwaqar/smolvlm2-agentic-gui:latest"

# 不走代理
_no_proxy = {'http': None, 'https': None}

# ─── 截屏 ───
def capture_screen(output_path: str = SCREENSHOT_PATH) -> str:
    subprocess.run(["screencapture", "-x", "-d", output_path], check=True)
    return output_path

def get_screen_size():
    """获取屏幕分辨率"""
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True, text=True, timeout=5
        )
        data = json.loads(result.stdout)
        displays = data.get("SPDisplaysDataType", [])
        for d in displays:
            if "spdisplays_main" in d:
                res = d.get("spdisplays_resolution", "")
                parts = res.split(" x ")
                if len(parts) == 2:
                    return int(parts[0].strip()), int(parts[1].strip())
    except:
        pass
    return 1920, 1080

# ─── 层级1: Vision OCR (Apple原生，60-240ms) ───
def vision_ocr_texts():
    """用Apple Vision框架识别屏幕文字，返回[(text, x, y, w, h), ...]"""
    try:
        import Vision
        import Quartz
        import Foundation

        img_path = capture_screen()
        url = Foundation.NSURL.fileURLWithPath_(img_path)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(1)  # 1=fast
        request.setRecognitionLanguages_(["zh-Hans", "en-US"])
        handler.performRequests_error_([request], None)

        results = request.results()
        screen_w, screen_h = get_screen_size()
        texts = []
        for r in results:
            if r.confidence() < 0.5:
                continue
            bbox = r.boundingBox()
            # Vision归一化坐标，原点左下角
            x = int(bbox.origin.x * screen_w)
            y = int((1 - bbox.origin.y - bbox.size.height) * screen_h)
            w = int(bbox.size.width * screen_w)
            h = int(bbox.size.height * screen_h)
            text = r.topCandidates_(1)[0].string()
            if text.strip():
                texts.append((text.strip(), x, y, w, h))
        return texts
    except Exception as e:
        print(f"  [OCR] 异常: {e}")
        return []

def ocr_find(description: str, texts=None) -> tuple:
    """层级1: OCR快速定位文字元素，返回(x,y)或None"""
    if texts is None:
        texts = vision_ocr_texts()
    desc_lower = description.lower()
    words = desc_lower.split()

    # 精确匹配
    for text, x, y, w, h in texts:
        if desc_lower in text.lower():
            cx, cy = x + w // 2, y + h // 2
            print(f"  [OCR] 找到「{text}」-> ({cx}, {cy})")
            return cx, cy

    # 模糊匹配（所有词都出现）
    for text, x, y, w, h in texts:
        text_lower = text.lower()
        if all(wd in text_lower for wd in words):
            cx, cy = x + w // 2, y + h // 2
            print(f"  [OCR模糊] 找到「{text}」-> ({cx}, {cy})")
            return cx, cy

    # 部分词匹配
    for text, x, y, w, h in texts:
        text_lower = text.lower()
        if any(wd in text_lower for wd in words):
            cx, cy = x + w // 2, y + h // 2
            print(f"  [OCR部分] 找到「{text}」-> ({cx}, {cy})")
            return cx, cy

    return None

# ─── 层级2: smolvlm2 两阶段 zoom-in 精确定位 ───
def smolvlm_locate(description: str, image_path: str = None) -> tuple:
    """
    层级2: 两阶段zoom-in精确定位（R-VLM启发）

    阶段1: smolvlm2 全图预测，得到初始区域
    阶段2: 放大该区域，再次问smolvlm2精确坐标
    """
    if image_path is None:
        image_path = capture_screen()

    screen_w, screen_h = get_screen_size()

    with open(image_path, "rb") as f:
        img_b64_full = base64.b64encode(f.read()).decode('utf-8')

    # 缩小用于阶段1
    from PIL import Image
    import io
    img = Image.open(image_path)
    if img.size[0] > 800:
        img_small = img.resize((800, int(800 * img.size[1] / img.size[0])), Image.LANCZOS)
        buf = io.BytesIO()
        img_small.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    else:
        img_b64 = img_b64_full

    # ── 阶段1: 全图预测 ──
    prompt1 = (
        f"屏幕分辨率 {screen_w}x{screen_h}。"
        f"找到「{description}」的位置。"
        f"只返回归一化坐标(0-1)：x,y（两个小数用逗号分隔）"
    )

    try:
        r = requests.post(OLLAMA_CHAT, json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt1, "images": [img_b64]}],
            "stream": False,
            "options": {"num_ctx": 4096, "temperature": 0.1}
        }, timeout=120, proxies=_no_proxy)

        raw = r.json().get("message", {}).get("content", "").strip()
        print(f"  [smolvlm2-L1] 全图: {raw[:100]}")

        # 解析阶段1坐标
        nums = re.findall(r'[0-9.]+', raw)
        if len(nums) < 2:
            return -1, -1
        nx1, ny1 = float(nums[-2]), float(nums[-1])
        if not (0 <= nx1 <= 1 and 0 <= ny1 <= 1):
            return -1, -1

        # ── 阶段2: 局部放大 ──
        # 截取中心点周围20%区域
        cx, cy = nx1 * img.size[0], ny1 * img.size[1]
        crop_w, crop_h = img.size[0] // 3, img.size[1] // 3
        left = max(0, int(cx - crop_w // 2))
        top = max(0, int(cy - crop_h // 2))
        right = min(img.size[0], left + crop_w)
        bottom = min(img.size[1], top + crop_h)

        img_crop = img.crop((left, top, right, bottom))
        buf2 = io.BytesIO()
        img_crop.save(buf2, format='PNG')
        img_b64_crop = base64.b64encode(buf2.getvalue()).decode('utf-8')

        # 局部坐标系转全图坐标
        crop_screen_w = right - left
        crop_screen_h = bottom - top

        prompt2 = (
            f"局部放大图，分辨率{crop_screen_w}x{crop_screen_h}。"
            f"这是屏幕的一部分。找到「{description}」的精确中心坐标。"
            f"只返回归一化坐标(0-1)：x,y"
        )

        r2 = requests.post(OLLAMA_CHAT, json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt2, "images": [img_b64_crop]}],
            "stream": False,
            "options": {"num_ctx": 4096, "temperature": 0.1}
        }, timeout=120, proxies=_no_proxy)

        raw2 = r2.json().get("message", {}).get("content", "").strip()
        print(f"  [smolvlm2-L2] 局部: {raw2[:100]}")

        nums2 = re.findall(r'[0-9.]+', raw2)
        if len(nums2) < 2:
            # 阶段2失败，用阶段1结果
            px = int(nx1 * screen_w)
            py = int(ny1 * screen_h)
            print(f"  [smolvlm2] zoom-in回退到L1 -> ({px}, {py})")
            return px, py

        nx2, ny2 = float(nums2[-2]), float(nums2[-1])
        if 0 <= nx2 <= 1 and 0 <= ny2 <= 1:
            # 局部坐标 -> 全图坐标
            px = int((left + nx2 * crop_screen_w) / img.size[0] * screen_w)
            py = int((top + ny2 * crop_screen_h) / img.size[1] * screen_h)
            print(f"  [smolvlm2] zoom-in完成 -> ({px}, {py})")
            return px, py
        else:
            px = int(nx1 * screen_w)
            py = int(ny1 * screen_h)
            return px, py

    except Exception as e:
        print(f"  [smolvlm2] 异常: {e}")
        return -1, -1

# ─── 层级3: SSIM 像素验证 ───
def compute_ssim(img1_path: str, img2_path: str) -> float:
    """计算SSIM相似度"""
    try:
        import cv2
        from PIL import Image

        img1 = np.array(Image.open(img1_path).convert('RGB'))
        img2 = np.array(Image.open(img2_path).convert('RGB'))
        scale = 200 / max(img1.shape[0], img1.shape[1])
        h, w = int(img1.shape[0] * scale), int(img1.shape[1] * scale)
        img1_s = cv2.resize(img1, (w, h))
        img2_s = cv2.resize(img2, (w, h))

        # 简化SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        mu1, mu2 = img1_s.mean(), img2_s.mean()
        sigma1_sq = ((img1_s - mu1) ** 2).mean()
        sigma2_sq = ((img2_s - mu2) ** 2).mean()
        sigma12 = ((img1_s - mu1) * (img2_s - mu2)).mean()

        ssim = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2))
        return float(ssim)
    except Exception as e:
        print(f"  [SSIM] 异常: {e}")
        return 0.96

# ─── 核心: smart_click ───
def smart_click(description: str, verbose: bool = True) -> bool:
    """
    完整三层感知闭环:
    OCR(60-240ms) -> smolvlm2(5-15s) -> SSIM验证(5ms)
    """
    screen_w, screen_h = get_screen_size()
    screenshot_before = capture_screen()
    coords = None
    found_by = None

    if verbose:
        print(f"\n[smart_click] 目标: 「{description}」")

    # 层级1: OCR
    t0 = time.time()
    ocr_texts = vision_ocr_texts()
    t1 = time.time()
    if verbose:
        print(f"  [L1 OCR] {len(ocr_texts)}个文字块, {t1-t0:.1f}s")

    coords = ocr_find(description, ocr_texts)
    if coords:
        found_by = "OCR"
    else:
        # 层级2: smolvlm2
        t2 = time.time()
        cx, cy = smolvlm_locate(description, screenshot_before)
        t3 = time.time()
        if verbose:
            print(f"  [L2 smolvlm2] {t3-t2:.1f}s")
        if cx > 0 and cy > 0:
            coords = (cx, cy)
            found_by = "smolvlm2"

    if not coords:
        print(f"  [smart_click] ✗ 找不到: 「{description}」")
        return False

    # 动手
    x, y = coords
    print(f"  [执行] 点击 ({x}, {y}) [来源: {found_by}]")
    _human_click(x, y)

    # 层级3: SSIM验证
    time.sleep(0.5)
    screenshot_after = capture_screen()
    ssim = compute_ssim(screenshot_before, screenshot_after)
    print(f"  [L3 SSIM] 相似度: {ssim:.3f}")

    if ssim > 0.98:
        print(f"  [SSIM] ⚠ 无变化，点击可能失效")
        return False
    elif ssim < 0.92:
        print(f"  [SSIM] ✓ 页面跳转成功")
        return True
    else:
        print(f"  [SSIM] △ 轻微变化（弹窗/局部刷新）")
        return True

def _human_click(x: int, y: int):
    """贝塞尔曲线移动 + 点击"""
    current_x, current_y = pyautogui.position()
    distance = ((x - current_x)**2 + (y - current_y)**2) ** 0.5
    duration = max(0.3, min(distance / 400, 1.5))

    mid_x = (current_x + x) // 2 + random.randint(-80, 80)
    mid_y = (current_y + y) // 2 + random.randint(-60, 60)

    steps = max(int(duration * 120), 20)
    for t_val in np.linspace(0, 1, steps):
        bx = (1-t_val)**2 * current_x + 2*(1-t_val)*t_val * mid_x + t_val**2 * x
        by = (1-t_val)**2 * current_y + 2*(1-t_val)*t_val * mid_y + t_val**2 * y
        pyautogui.moveTo(int(bx), int(by), _pause=False)
        time.sleep(duration / steps * random.uniform(0.8, 1.2))

    time.sleep(random.uniform(0.3, 0.9))
    pyautogui.mouseDown()
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.mouseUp()

def ask_screen(question: str = None) -> str:
    """直接问屏幕内容"""
    img = capture_screen()
    if question is None:
        question = "简单描述屏幕上有什么，3句话以内"

    with open(img, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    try:
        r = requests.post(OLLAMA_CHAT, json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": question, "images": [img_b64]}],
            "stream": False,
            "options": {"num_ctx": 4096, "temperature": 0.1}
        }, timeout=120, proxies=_no_proxy)
        d = r.json()
        return d.get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[错误] {e}"

if __name__ == "__main__":
    print("=== smart_click 自检 ===")
    print(f"屏幕尺寸: {get_screen_size()}")

    print("\n--- OCR文字识别 ---")
    t0 = time.time()
    texts = vision_ocr_texts()
    print(f"  {len(texts)} 个文字块, {time.time()-t0:.1f}s")
    for t, x, y, w, h in texts[:10]:
        print(f"  「{t}」@ ({x},{y})")

    print("\n--- ask_screen ---")
    t0 = time.time()
    result = ask_screen("简单描述屏幕内容")
    print(f"  耗时: {time.time()-t0:.1f}s")
    print(f"  结果: {result[:300]}")
