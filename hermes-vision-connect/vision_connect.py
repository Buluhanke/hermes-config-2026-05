#!/usr/bin/env python3
"""
vision_connect.py — Hermes 三层视觉连接器 v2
VisionConnect 主类 + 视觉心跳 + 失败降级策略

免费优先: L1 Apple Vision OCR → L2 Qwen2.5VL(smolVLM备用) → L3 硅基流动 → L4 OpenRouter
"""
import sys
import os
import time
import re
import io
import json
import base64
import subprocess
import random
import threading
import requests

try:
    from PIL import Image
    Image.LANCZOS  # verify available
except Exception:
    # Pillow < 10: LANCZOS is direct attribute
    # Pillow >= 10: use RESAMPLING enum
    pass

SCREENSHOT_PATH = "/tmp/hermes_screen.png"
OLLAMA_GENERATE = "http://127.0.0.1:11434/api/generate"
OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen2.5vl:7b"           # 主力视觉模型
FALLBACK_MODEL = "ahmadwaqar/smolvlm2-agentic-gui:latest"

_no_proxy = {'http': None, 'https': None}


# ─── 依赖检查 ───
def _check_deps():
    missing = []
    for m in ['mss', 'PIL', 'cv2', 'numpy', 'requests']:
        try:
            __import__(m)
        except ImportError:
            missing.append(m)
    if missing:
        print(f"  [vision_connect] 缺少依赖: {missing}，请 pip install {' '.join(missing)}")


# ─── 截屏 ───
def capture_screen(output_path: str = SCREENSHOT_PATH) -> str:
    """截屏，返回路径。优先 mss(更快)，兜底 screencapture"""
    try:
        import mss
        with mss.MSS() as s:
            s.shot(output=output_path)
        return output_path
    except Exception:
        subprocess.run(["screencapture", "-x", "-d", output_path],
                      check=True, capture_output=True)
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


# ─── 层级1: Vision OCR ───
def vision_ocr_texts():
    """Apple Vision框架识别屏幕文字，返回[(text, x, y, w, h), ...]"""
    try:
        import Vision
        import Quartz
        import Foundation

        img_path = capture_screen()
        url = Foundation.NSURL.fileURLWithPath_(img_path)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(1)
        request.setRecognitionLanguages_(["zh-Hans", "en-US"])
        handler.performRequests_error_([request], None)

        results = request.results()
        screen_w, screen_h = get_screen_size()
        texts = []
        for r in results:
            if r.confidence() < 0.5:
                continue
            bbox = r.boundingBox()
            x = int(bbox.origin.x * screen_w)
            y = int((1 - bbox.origin.y - bbox.size.height) * screen_h)
            w = int(bbox.size.width * screen_w)
            h = int(bbox.size.height * screen_h)
            text = r.topCandidates_(1)[0].string()
            if text.strip():
                texts.append((text.strip(), x, y, w, h))
        return texts
    except Exception as e:
        print(f"  [VisionOCR] 异常: {e}")
        return []


def ocr_find_coordinates(description: str, texts=None) -> tuple:
    """OCR快速定位文字元素，返回像素坐标(x, y)或(None, None)"""
    if texts is None:
        texts = vision_ocr_texts()
    desc_lower = description.lower()
    words = desc_lower.split()

    # 精确匹配
    for text, x, y, w, h in texts:
        if desc_lower in text.lower():
            return x + w // 2, y + h // 2
    # 模糊匹配（所有词都出现）
    for text, x, y, w, h in texts:
        text_lower = text.lower()
        if all(wd in text_lower for wd in words):
            return x + w // 2, y + h // 2
    # 部分词匹配
    for text, x, y, w, h in texts:
        text_lower = text.lower()
        if any(wd in text_lower for wd in words):
            return x + w // 2, y + h // 2
    return None, None


# ─── 层级2: VLM 定位（Qwen2.5VL / smolVLM2）───
def _compress_image(img_path: str, max_width: int = 800) -> tuple:
    """压缩图片，返回(b64字符串, PIL_img, original_size)"""
    from PIL import Image
    import io
    img = Image.open(img_path)
    orig_size = img.size
    if img.size[0] > max_width:
        img_small = img.resize((max_width, int(max_width * img.size[1] / img.size[0])),
                                Image.LANCZOS)
        buf = io.BytesIO()
        img_small.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return b64, img_small, orig_size
    else:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8'), img, orig_size


def _parse_vlm_coords(raw: str, fallback_nx1=0.5, fallback_ny1=0.5) -> tuple:
    """
    解析VLM返回的归一化坐标。
    策略：取最后两个小数（避免被其他数字干扰）。
    """
    coords = re.findall(r'0\.\d+', raw)
    if len(coords) >= 2:
        return float(coords[-2]), float(coords[-1])
    return fallback_nx1, fallback_ny1


def vlm_locate(description: str, model: str = OLLAMA_MODEL,
               screen_size: tuple = None) -> tuple:
    """
    两阶段Zoom-In精确定位（R-VLM启发）。
    返回像素坐标(x, y)，失败返回(-1, -1)。
    """
    if screen_size is None:
        screen_size = get_screen_size()
    screen_w, screen_h = screen_size

    img_path = capture_screen()
    b64, img, orig_size = _compress_image(img_path)

    # 阶段1: 全图预测
    prompt1 = (
        f"屏幕分辨率 {orig_size[0]}x{orig_size[1]}。找到「{description}」的精确中心点。"
        f"只返回归一化坐标(0-1)：x,y（两个小数用逗号分隔）"
    )

    try:
        # Qwen2.5VL 需要 num_gpu:0（CPU模式，M4 Mac必须）
        opts = {"num_ctx": 4096, "temperature": 0.1}
        if "qwen2.5vl" in model.lower():
            opts["num_gpu"] = 0  # CPU模式，防止OOM

        r = requests.post(OLLAMA_CHAT, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt1, "images": [b64]}],
            "stream": False,
            "options": opts
        }, timeout=180, proxies=_no_proxy)

        raw = r.json().get("message", {}).get("content", "").strip()
        nx1, ny1 = _parse_vlm_coords(raw)
        if not (0 <= nx1 <= 1 and 0 <= ny1 <= 1):
            nx1, ny1 = 0.5, 0.5

        # 阶段2: 局部放大
        cx, cy = nx1 * img.size[0], ny1 * img.size[1]
        crop_w, crop_h = img.size[0] // 3, img.size[1] // 3
        left = max(0, int(cx - crop_w // 2))
        top = max(0, int(cy - crop_h // 2))
        right = min(img.size[0], left + crop_w)
        bottom = min(img.size[1], top + crop_h)

        img_crop = img.crop((left, top, right, bottom))
        buf2 = io.BytesIO()
        img_crop.save(buf2, format='PNG')
        b64_crop = base64.b64encode(buf2.getvalue()).decode('utf-8')
        crop_screen_w = right - left
        crop_screen_h = bottom - top

        prompt2 = (
            f"局部放大图，分辨率{crop_screen_w}x{crop_screen_h}。"
            f"这是屏幕的一部分。找到「{description}」的精确中心坐标。"
            f"只返回归一化坐标(0-1)：x,y"
        )

        r2 = requests.post(OLLAMA_CHAT, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt2, "images": [b64_crop]}],
            "stream": False,
            "options": opts
        }, timeout=180, proxies=_no_proxy)

        raw2 = r2.json().get("message", {}).get("content", "").strip()
        nx2, ny2 = _parse_vlm_coords(raw2, nx1, ny1)

        # 局部坐标 → 全图坐标 → 像素坐标
        px = int((left + nx2 * crop_screen_w) / orig_size[0] * screen_w)
        py = int((top + ny2 * crop_screen_h) / orig_size[1] * screen_h)
        px = max(0, min(px, screen_w - 1))
        py = max(0, min(py, screen_h - 1))
        return px, py

    except Exception as e:
        print(f"  [vlm_locate/{model}] 异常: {e}")
        return -1, -1


# ─── 层级2备用: smolVLM2 ──
def smolvlm_locate(description: str) -> tuple:
    """smolVLM2 备用定位（轻量，2GB）"""
    return vlm_locate(description, model=FALLBACK_MODEL)


# ─── 层级3: SSIM 验证 ───
def _compute_ssim_np(img1_np, img2_np) -> float:
    """numpy数组间快速SSIM"""
    import cv2
    scale = 200 / max(img1_np.shape[0], img1_np.shape[1])
    h, w = int(img1_np.shape[0] * scale), int(img1_np.shape[1] * scale)
    s1 = cv2.resize(img1_np, (w, h))
    s2 = cv2.resize(img2_np, (w, h))
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu1, mu2 = s1.mean(), s2.mean()
    sigma1 = ((s1 - mu1) ** 2).mean()
    sigma2 = ((s2 - mu2) ** 2).mean()
    sigma12 = ((s1 - mu1) * (s2 - mu2)).mean()
    num = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    den = (mu1**2 + mu2**2 + C1) * (sigma1 + sigma2 + C2)
    return float(num / den) if den > 0 else 1.0


def compute_ssim(img1_path: str, img2_path: str) -> float:
    """计算两张图片SSIM相似度"""
    try:
        from PIL import Image
        import numpy as np
        img1 = np.array(Image.open(img1_path).convert('RGB'))
        img2 = np.array(Image.open(img2_path).convert('RGB'))
        return _compute_ssim_np(img1, img2)
    except Exception as e:
        print(f"  [compute_ssim] 异常: {e}")
        return 0.96


def compute_dynamic_threshold(img_path: str) -> float:
    """基于画面复杂度自适应SSIM阈值"""
    try:
        import cv2
        img = cv2.imread(img_path)
        if img is None:
            return 0.93
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = edges.sum() / (edges.size + 1e-9)
        base = 0.93
        complexity_factor = edge_ratio * 0.05
        return max(0.90, base - complexity_factor)
    except Exception:
        return 0.93


def ssim_verify(img_before: str, img_after: str) -> dict:
    """
    增强版SSIM验证：动态阈值 + 变化率双重判断。
    返回: {success: bool|None, ssim, change_rate, threshold, reason}
    """
    try:
        from PIL import Image
        import numpy as np
        b = np.array(Image.open(img_before).convert("RGB"))
        a = np.array(Image.open(img_after).convert("RGB"))
        ssim_val = _compute_ssim_np(b, a)
        dyn_thresh = compute_dynamic_threshold(img_after)
        change_rate = abs(ssim_val - 1.0)

        if ssim_val < dyn_thresh:
            return {"success": True, "ssim": ssim_val, "change_rate": change_rate,
                    "threshold": dyn_thresh, "reason": "ssim_below_dynamic"}
        if change_rate > 0.05:
            return {"success": True, "ssim": ssim_val, "change_rate": change_rate,
                    "threshold": dyn_thresh, "reason": "change_rate_exceeded"}
        return {"success": None, "ssim": ssim_val, "change_rate": change_rate,
                "threshold": dyn_thresh, "reason": "uncertain_vlm_confirm"}
    except Exception as e:
        return {"success": None, "ssim": 1.0, "change_rate": 0,
                "threshold": 0.93, "reason": f"error:{e}"}


# ─── 层级4: 硅基流动 / OpenRouter 兜底 ──
def siliconflow_locate(description: str, api_key: str = None) -> tuple:
    """硅基流动 API 定位（需要API Key）"""
    if not api_key:
        return -1, -1
    try:
        from PIL import Image
        import io
        import numpy as np

        img_path = capture_screen()
        img = Image.open(img_path)
        img_small = img.resize((800, int(800 * img.size[1] / img.size[0])), Image.LANCZOS)
        buf = io.BytesIO()
        img_small.save(buf, format='JPEG', quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        screen_w, screen_h = get_screen_size()

        prompt = (
            f"屏幕分辨率 {screen_w}x{screen_h}。找到「{description}」的精确中心点。"
            f"只返回归一化坐标(0-1)：x,y"
        )

        r = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                "messages": [{"role": "user", "content": prompt, "images": [b64]}],
                "stream": False
            }, timeout=60, proxies=_no_proxy
        )
        raw = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        coords = re.findall(r'0\.\d+', raw)
        if len(coords) >= 2:
            nx, ny = float(coords[-2]), float(coords[-1])
            return int(nx * screen_w), int(ny * screen_h)
    except Exception as e:
        print(f"  [siliconflow] 异常: {e}")
    return -1, -1


def openrouter_locate(description: str, api_key: str = None) -> tuple:
    """OpenRouter Gemini Flash 兜底定位"""
    if not api_key:
        return -1, -1
    try:
        from PIL import Image
        import io

        img_path = capture_screen()
        img = Image.open(img_path)
        img_small = img.resize((800, int(800 * img.size[1] / img.size[0])), Image.LANCZOS)
        buf = io.BytesIO()
        img_small.save(buf, format='JPEG', quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        screen_w, screen_h = get_screen_size()

        prompt = (
            f"Screen resolution {screen_w}x{screen_h}. Find the center of 「{description}」."
            f"Return only normalized coordinates (0-1): x,y"
        )

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt},
                                                          {"type": "image_url",
                                                           "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
                "stream": False
            }, timeout=60, proxies=_no_proxy
        )
        raw = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        coords = re.findall(r'0\.\d+', raw)
        if len(coords) >= 2:
            nx, ny = float(coords[-2]), float(coords[-1])
            return int(nx * screen_w), int(ny * screen_h)
    except Exception as e:
        print(f"  [openrouter] 异常: {e}")
    return -1, -1


# ─── 视觉心跳 ───
class VisionHeartbeat:
    """
    视觉系统心跳检测：定期确认视觉系统健康。
    独立线程，每interval秒执行一次。
    """

    def __init__(self, vc, interval: int = 30):
        self.vc = vc
        self.interval = interval
        self.running = False
        self.thread = None
        self.status = {
            "status": "unknown",
            "ocr_latency_ms": 0,
            "ollama_latency_ms": 0,
            "screenshot_ok": False,
            "last_heartbeat": None
        }
        self._lock = threading.Lock()

    def ping(self) -> dict:
        """执行一次心跳检测，返回状态字典"""
        result = {
            "status": "healthy",
            "ocr_latency_ms": 0,
            "ollama_latency_ms": 0,
            "screenshot_ok": False,
            "last_heartbeat": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        # 1. 截图测试
        t0 = time.time()
        try:
            path = capture_screen()
            import os
            result["screenshot_ok"] = os.path.exists(path) and os.path.getsize(path) > 10000
        except Exception:
            result["screenshot_ok"] = False
        result["screenshot_latency_ms"] = int((time.time() - t0) * 1000)

        # 2. OCR测试
        t0 = time.time()
        try:
            texts = vision_ocr_texts()
            result["ocr_latency_ms"] = int((time.time() - t0) * 1000)
            result["ocr_texts_count"] = len(texts)
        except Exception as e:
            result["ocr_latency_ms"] = -1
            result["status"] = "degraded"

        # 3. Ollama ping
        t0 = time.time()
        try:
            r = requests.get(f"{OLLAMA_CHAT.rsplit('/', 1)[0]}/api/tags",
                             timeout=5, proxies=_no_proxy)
            result["ollama_latency_ms"] = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                result["ollama_models"] = [m.get("name", "") for m in r.json().get("models", [])]
            else:
                result["status"] = "degraded"
        except Exception:
            result["ollama_latency_ms"] = -1
            result["status"] = "failed"

        with self._lock:
            self.status = result
        return result

    def _loop(self):
        while self.running:
            self.ping()
            time.sleep(self.interval)

    def start(self):
        """启动心跳线程"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止心跳"""
        self.running = False

    def get_status(self) -> dict:
        """获取最近一次心跳状态"""
        with self._lock:
            return dict(self.status)


# ─── 拟真点击 ───
def human_click(x: int, y: int):
    """贝塞尔曲线移动 + 点击"""
    try:
        import pyautogui
        current_x, current_y = pyautogui.position()
        distance = ((x - current_x)**2 + (y - current_y)**2) ** 0.5
        duration = max(0.3, min(distance / 400, 1.5))
        mid_x = (current_x + x) // 2 + random.randint(-80, 80)
        mid_y = (current_y + y) // 2 + random.randint(-60, 60)
        steps = max(int(duration * 120), 20)
        for t_val in __import__('numpy').linspace(0, 1, steps):
            bx = (1-t_val)**2 * current_x + 2*(1-t_val)*t_val * mid_x + t_val**2 * x
            by = (1-t_val)**2 * current_y + 2*(1-t_val)*t_val * mid_y + t_val**2 * y
            pyautogui.moveTo(int(bx), int(by), _pause=False)
            time.sleep(duration / steps * random.uniform(0.8, 1.2))
        time.sleep(random.uniform(0.3, 0.9))
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.mouseUp()
    except Exception:
        # 兜底: screencapture无焦点截图时用cliclick
        try:
            subprocess.run(["cliclick", f"cp:{x},{y}"], check=True, capture_output=True)
        except Exception:
            pass


# ─── VisionConnect 主类 ───
class VisionConnect:
    """
    Hermes 三层视觉连接器 v2。

    用法:
        from vision_connect import VisionConnect
        vc = VisionConnect()
        result = vc.find_and_click("登录按钮")
        print(result)
        status = vc.get_heartbeat_status()
        print(status)
    """

    def __init__(self,
                 screenshot_dir: str = "/tmp",
                 ollama_url: str = "http://127.0.0.1:11434",
                 ollama_model: str = OLLAMA_MODEL,
                 fallback_model: str = FALLBACK_MODEL,
                 use_siliconflow: bool = False,
                 siliconflow_api_key: str = None,
                 heartbeat_interval: int = 30,
                 ssim_threshold: float = 0.93,
                 dynamic_ssim: bool = True,
                 max_retries: int = 2,
                 verbose: bool = True):
        self.screenshot_dir = screenshot_dir
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.fallback_model = fallback_model
        self.use_siliconflow = use_siliconflow
        self.siliconflow_api_key = siliconflow_api_key or os.environ.get("SILICONFLOW_API_KEY")
        self.heartbeat_interval = heartbeat_interval
        self.ssim_threshold = ssim_threshold
        self.dynamic_ssim = dynamic_ssim
        self.max_retries = max_retries
        self.verbose = verbose

        self._heartbeat = VisionHeartbeat(self, interval=self.heartbeat_interval)
        self._heartbeat_started = False

        _check_deps()

    # ── 心跳 ──
    def start_heartbeat(self):
        if self.heartbeat_interval > 0 and not self._heartbeat_started:
            self._heartbeat.start()
            self._heartbeat_started = True

    def stop_heartbeat(self):
        self._heartbeat.stop()
        self._heartbeat_started = False

    def get_heartbeat_status(self) -> dict:
        return self._heartbeat.get_status()

    # ── 截图 ──
    def capture_screen(self) -> str:
        path = os.path.join(self.screenshot_dir, f"hermes_screen_{int(time.time())}.png")
        return capture_screen(path)

    # ── SSIM ──
    def compute_ssim(self, img1: str, img2: str) -> float:
        return compute_ssim(img1, img2)

    # ── 问屏幕 ──
    def ask_screen(self, question: str) -> str:
        """看屏幕问答，返回VLM回答"""
        img_path = capture_screen()
        from PIL import Image
        import io
        img = Image.open(img_path)
        img_small = img.resize((800, int(800 * img.size[1] / img.size[0])), Image.LANCZOS)
        buf = io.BytesIO()
        img_small.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        opts = {"num_ctx": 4096, "temperature": 0.1}
        if "qwen2.5vl" in self.ollama_model.lower():
            opts["num_gpu"] = 0

        try:
            r = requests.post(OLLAMA_CHAT, json={
                "model": self.ollama_model,
                "messages": [{"role": "user", "content": question, "images": [b64]}],
                "stream": False,
                "options": opts
            }, timeout=180, proxies=_no_proxy)
            return r.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"[错误] {e}"

    # ── 内部: 执行并验证 ──
    def _execute_and_verify(self, x: int, y: int, layer: str,
                            attempt: int) -> dict:
        """执行点击 + SSIM验证"""
        screenshot_before = capture_screen()
        human_click(x, y)
        time.sleep(0.8)
        screenshot_after = capture_screen()

        if self.dynamic_ssim:
            verify_result = ssim_verify(screenshot_before, screenshot_after)
            ssim = verify_result["ssim"]
            success = verify_result["success"]
            reason = verify_result["reason"]
        else:
            ssim = compute_ssim(screenshot_before, screenshot_after)
            success = ssim < self.ssim_threshold
            reason = "fixed_threshold"

        return {
            "success": success is True,
            "coords": (x, y),
            "layer": layer,
            "ssim": ssim,
            "attempt": attempt,
            "verify_reason": reason,
            "screenshot_before": screenshot_before,
            "screenshot_after": screenshot_after
        }

    # ── 内部: 清理缓存 ──
    def _cleanup_cache(self):
        """清理截图缓存"""
        try:
            for f in os.listdir(self.screenshot_dir):
                if f.startswith("hermes_screen") and f.endswith(".png"):
                    try:
                        os.remove(os.path.join(self.screenshot_dir, f))
                    except Exception:
                        pass
        except Exception:
            pass

    # ── 找元素并点击（带降级）───
    def find_and_click(self, description: str) -> dict:
        """
        带完整降级策略的 find_and_click。
        依次尝试: Vision OCR → Qwen2.5VL → smolVLM2 → 硅基流动 → OpenRouter
        每层最多重试 max_retries 次。
        """
        self.start_heartbeat()  # 确保心跳启动

        failures = []
        screen_w, screen_h = get_screen_size()

        for attempt in range(self.max_retries + 1):
            # ── L1: Vision OCR ──
            try:
                x, y = ocr_find_coordinates(description)
                if x is not None and y is not None:
                    result = self._execute_and_verify(x, y, "L1_VisionOCR", attempt)
                    if self.verbose:
                        print(f"  [L1 OCR] 找到「{description}」-> ({x},{y}), SSIM={result['ssim']:.3f}")
                    return result
            except Exception as e:
                failures.append({"layer": "L1_VisionOCR", "attempt": attempt, "error": str(e)})

            # ── L2: Qwen2.5VL ──
            try:
                x, y = vlm_locate(description, model=self.ollama_model)
                if x > 0 and y > 0:
                    result = self._execute_and_verify(x, y, "L2_Qwen25VL", attempt)
                    if self.verbose:
                        print(f"  [L2 Qwen2.5VL] 找到「{description}」-> ({x},{y}), SSIM={result['ssim']:.3f}")
                    return result
            except Exception as e:
                failures.append({"layer": "L2_Qwen25VL", "attempt": attempt, "error": str(e)})

            # ── L2b: smolVLM2 备用 ──
            try:
                x, y = smolvlm_locate(description)
                if x > 0 and y > 0:
                    result = self._execute_and_verify(x, y, "L2b_smolVLM2", attempt)
                    if self.verbose:
                        print(f"  [L2b smolVLM2] 找到「{description}」-> ({x},{y}), SSIM={result['ssim']:.3f}")
                    return result
            except Exception as e:
                failures.append({"layer": "L2b_smolVLM2", "attempt": attempt, "error": str(e)})

            # ── L3: 硅基流动 ──
            if self.use_siliconflow and self.siliconflow_api_key:
                try:
                    x, y = siliconflow_locate(description, api_key=self.siliconflow_api_key)
                    if x > 0 and y > 0:
                        result = self._execute_and_verify(x, y, "L3_SiliconFlow", attempt)
                        if self.verbose:
                            print(f"  [L3 SiliconFlow] 找到「{description}」-> ({x},{y}), SSIM={result['ssim']:.3f}")
                        return result
                except Exception as e:
                    failures.append({"layer": "L3_SiliconFlow", "attempt": attempt, "error": str(e)})

            # ── L4: OpenRouter ──
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if openrouter_key:
                try:
                    x, y = openrouter_locate(description, api_key=openrouter_key)
                    if x > 0 and y > 0:
                        result = self._execute_and_verify(x, y, "L4_OpenRouter", attempt)
                        if self.verbose:
                            print(f"  [L4 OpenRouter] 找到「{description}」-> ({x},{y}), SSIM={result['ssim']:.3f}")
                        return result
                except Exception as e:
                    failures.append({"layer": "L4_OpenRouter", "attempt": attempt, "error": str(e)})

            # 重试前清理
            self._cleanup_cache()
            if self.verbose:
                print(f"  [降级] 第{attempt+1}次尝试未找到「{description}」，清理缓存后重试...")
            time.sleep(1)

        # ── 彻底失败 ──
        return {
            "success": False,
            "coords": None,
            "layer": "exhausted",
            "ssim": None,
            "retries": self.max_retries,
            "failures": failures[-5:],
            "suggestion": "目标元素可能不在当前屏幕，请尝试滚动或切换视图"
        }

    # ── 别名 ──
    def smart_click(self, description: str) -> dict:
        """find_and_click 的别名"""
        return self.find_and_click(description)


# ─── legacy API 兼容 ───
def find_and_click(description: str, max_retries: int = 2) -> dict:
    """legacy API：直接调用 VisionConnect"""
    vc = VisionConnect(max_retries=max_retries)
    return vc.find_and_click(description)


def ask_screen(question: str = None) -> str:
    """legacy API：问屏幕"""
    if question is None:
        question = "简单描述屏幕上有什么，3句话以内"
    vc = VisionConnect()
    return vc.ask_screen(question)


if __name__ == "__main__":
    print("=== vision_connect 自检 ===")
    print(f"屏幕尺寸: {get_screen_size()}")

    print("\n--- Vision OCR ---")
    t0 = time.time()
    texts = vision_ocr_texts()
    print(f"  {len(texts)} 个文字块, {time.time()-t0:.1f}s")
    for t, x, y, w, h in texts[:10]:
        print(f"  「{t}」@ ({x},{y})")

    print("\n--- VisionConnect ---")
    vc = VisionConnect(heartbeat_interval=0)  # 自检时禁用心跳
    print(f"  心跳状态: {vc.get_heartbeat_status()}")
