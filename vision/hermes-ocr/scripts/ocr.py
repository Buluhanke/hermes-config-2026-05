#!/usr/bin/env python3
"""
Hermes 统一OCR引擎
Usage:
  python3 ocr.py screenshot [--region x,y,w,h] [--json]
  python3 ocr.py read <image_path> [--json]
  python3 ocr.py pdf <pdf_path> [--json]
  python3 ocr.py detect
"""

import argparse, json, os, subprocess, sys, base64, io
from pathlib import Path

# ── 配置 ──────────────────────────────────────────
VISION_PYTHON = "/opt/homebrew/bin/python3"
HERMES_VENV = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python3")
HERMES_HOME = os.path.expanduser("~/.hermes")
ENV_FILE = os.path.join(HERMES_HOME, ".env")

# ── 引擎检测 ──────────────────────────────────────

def _run(args, timeout=15):
    """运行外部Python并返回 stdout/stderr"""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1

def detect_engines():
    engines = {}

    # 1. Vision OCR
    code = "import Vision, Quartz, Foundation; print('OK')"
    out, _, rc = _run([VISION_PYTHON, "-c", code])
    engines['vision'] = rc == 0

    # 2. PaddleOCR
    code = "import paddleocr; print(paddleocr.__version__)"
    out, _, rc = _run([HERMES_VENV, "-c", code])
    engines['paddleocr'] = rc == 0

    # 3. Baidu OCR
    api_key = get_env("BAIDU_API_KEY") or get_env("BAIDU_CLIENT_ID")
    engines['baidu'] = api_key is not None

    # 4. ddddocr
    code = "import ddddocr; print('OK')"
    out, _, rc = _run([VISION_PYTHON, "-c", code])
    engines['ddddocr'] = rc == 0

    # 5. pymupdf
    for py in [HERMES_VENV, VISION_PYTHON]:
        out, _, rc = _run([py, "-c", "import pymupdf; print(pymupdf.__version__)"])
        if rc == 0:
            engines['pymupdf'] = True
            engines['_pymupdf_python'] = py
            break

    return engines


def get_env(key):
    """从 .env 读取值"""
    try:
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    except FileNotFoundError:
        pass
    return os.environ.get(key)


# ── OCR 引擎实现 ──────────────────────────────────

def ocr_vision(image_path):
    """Apple Vision OCR (macOS原生)"""
    code = f'''import sys
sys.path.insert(0, "/opt/homebrew/lib/python3.11/site-packages")
import Quartz, Foundation, Vision, json

url = Foundation.NSURL.fileURLWithPath_("{image_path}")
handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
req = Vision.VNRecognizeTextRequest.alloc().init()
req.setRecognitionLevel_(1)
req.setRecognitionLanguages_(["zh-Hans", "en-US"])
handler.performRequests_error_([req], None)

results = []
for obs in req.results():
    text = obs.topCandidates_(1)[0].string()
    conf = obs.confidence()
    bbox = obs.boundingBox()
    results.append({{
        "text": text,
        "confidence": round(conf, 3),
        "bbox": {{
            "x": round(bbox.origin.x, 4),
            "y": round(bbox.origin.y, 4),
            "w": round(bbox.size.width, 4),
            "h": round(bbox.size.height, 4)
        }}
    }})
print(json.dumps(results, ensure_ascii=False))
'''
    out, err, rc = _run([VISION_PYTHON, "-c", code], timeout=10)
    if rc != 0:
        return None, f"Vision OCR failed: {err}"
    return json.loads(out), None


def ocr_paddle(image_path):
    """PaddleOCR (高精度中文) - v5 API"""
    code = f'''import json
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
results = ocr.predict("{image_path}")
blocks = []
for res in results:
    j = res.json
    rec_texts = j.get("res", {{}}).get("rec_texts", [])
    rec_scores = j.get("res", {{}}).get("rec_scores", [])
    rec_boxes = j.get("res", {{}}).get("rec_boxes", [])
    for i, text in enumerate(rec_texts):
        if not text:
            continue
        b = rec_boxes[i] if i < len(rec_boxes) else None
        blocks.append({{
            "text": text,
            "confidence": round(float(rec_scores[i]), 3) if i < len(rec_scores) else None,
            "bbox": {{
                "x1": int(b[0]), "y1": int(b[1]),
                "x2": int(b[2]), "y2": int(b[3])
            }} if b and len(b) >= 4 else None
        }})
print(json.dumps(blocks, ensure_ascii=False))
'''
    out, err, rc = _run([HERMES_VENV, "-c", code], timeout=30)
    if rc != 0:
        return None, f"PaddleOCR failed: {err}"
    return json.loads(out), None


def ocr_baidu(image_path):
    """百度OCR (云端备份)"""
    api_key = get_env("BAIDU_API_KEY")
    secret_key = get_env("BAIDU_SECRET_KEY")
    if not api_key or not secret_key:
        return None, "Baidu OCR: no credentials"

    # 获取token
    token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
    import urllib.request
    try:
        resp = urllib.request.urlopen(token_url, timeout=5)
        token = json.loads(resp.read())["access_token"]
    except Exception as e:
        return None, f"Baidu token failed: {e}"

    # Base64编码图片
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # 调用OCR
    import urllib.parse
    data = urllib.parse.urlencode({"image": b64}).encode()
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"
    try:
        req = urllib.request.Request(ocr_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        blocks = [{"text": w["words"], "confidence": None, "bbox": None}
                  for w in result.get("words_result", [])]
        return blocks, None
    except Exception as e:
        return None, f"Baidu OCR call failed: {e}"


def ocr_ddddocr(image_path):
    """ddddocr (验证码)"""
    code = f'''import json, base64
import ddddocr
ocr = ddddocr.DdddOcr(show_ad=False)
with open("{image_path}", "rb") as f:
    img = f.read()
ret = ocr.classification(img)
print(json.dumps([{{"text": ret, "confidence": None, "bbox": None}}], ensure_ascii=False))
'''
    out, err, rc = _run([VISION_PYTHON, "-c", code], timeout=15)
    if rc != 0:
        return None, f"ddddocr failed: {err}"
    return json.loads(out), None


def ocr_pymupdf_pdf(file_path):
    """pymupdf PDF文字提取"""
    py = HERMES_VENV  # pymupdf在venv里
    code = f'''import json, pymupdf
doc = pymupdf.open("{file_path}")
blocks = []
for page_num, page in enumerate(doc):
    text = page.get_text().strip()
    if text:
        blocks.append({{"page": page_num + 1, "text": text}})
print(json.dumps(blocks, ensure_ascii=False))
'''
    out, err, rc = _run([py, "-c", code], timeout=15)
    if rc != 0:
        return None, f"pymupdf failed: {err}"
    return json.loads(out), None


def pdf_to_images(file_path, dpi=200):
    """PDF每页转图片"""
    code = f'''import json, pymupdf
doc = pymupdf.open("{file_path}")
paths = []
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi={dpi})
    p = "/tmp/hermes_pdf_page_{{i}}.png"
    pix.save(p)
    paths.append(p)
print(json.dumps(paths))
'''
    out, err, rc = _run([HERMES_VENV, "-c", code], timeout=15)
    if rc != 0:
        return None, f"PDF to image failed: {err}"
    return json.loads(out), None


def ocr_image_auto(image_path):
    """自动选择最佳引擎读图片"""
    engines = detect_engines()

    # 尝试顺序: Vision → PaddleOCR → Baidu → ddddocr
    pipelines = []

    if engines.get('vision'):
        pipelines.append(('vision', ocr_vision))
    if engines.get('paddleocr'):
        pipelines.append(('paddleocr', ocr_paddle))
    if engines.get('baidu'):
        pipelines.append(('baidu', ocr_baidu))
    if engines.get('ddddocr'):
        pipelines.append(('ddddocr', ocr_ddddocr))

    errors = []
    for name, func in pipelines:
        result, err = func(image_path)
        if result and len(result) > 0:
            return result, name, None
        if err:
            errors.append(f"{name}: {err}")

    return None, None, "; ".join(errors) if errors else "No engine available"


# ── 截图 ──────────────────────────────────────────

def screenshot(region=None):
    """macOS截图，返回临时文件路径"""
    if region:
        x, y, w, h = [int(v) for v in region.split(",")]
    else:
        x, y, w, h = 0, 0, 1920, 1080

    code = f'''import Quartz, Foundation
img = Quartz.CGWindowListCreateImage(
    Quartz.CGRectMake({x}, {y}, {w}, {h}),
    Quartz.kCGWindowListOptionOnScreenOnly,
    Quartz.kCGNullWindowID,
    Quartz.kCGWindowImageDefault
)
dest = Quartz.CGImageDestinationCreateWithURL(
    Foundation.NSURL.fileURLWithPath_("/tmp/hermes_ocr_shot.png"),
    "public.png", 1, None
)
Quartz.CGImageDestinationAddImage(dest, img, None)
Quartz.CGImageDestinationFinalize(dest)
print("OK")
'''
    out, err, rc = _run([VISION_PYTHON, "-c", code])
    if rc != 0:
        return None
    return "/tmp/hermes_ocr_shot.png"


# ── 快速找字 + 坐标 ────────────────────────────────

def fast_ocr_find(target_text, image_path=None, confidence=0.5):
    """
    Apple Vision 极速找字 + 返回屏幕坐标 (30-50ms)
    坐标转换: Vision左下角原点(归一化) → Mac屏幕左上角原点(像素)
    """
    # 截图：用screencapture绕过Chrome GPU合成层
    if not image_path:
        shot_path = "/tmp/hermes_fast_ocr.png"
        import subprocess
        subprocess.run(["screencapture", "-x", shot_path], timeout=5)
        image_path = shot_path

    # Vision OCR (Fast模式, 1=fast, 0=accurate)
    code = f'''import sys
sys.path.insert(0, "/opt/homebrew/lib/python3.11/site-packages")
import Quartz, Foundation, Vision, json

screen_w = Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID())
screen_h = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())

url = Foundation.NSURL.fileURLWithPath_("{image_path}")
handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
req = Vision.VNRecognizeTextRequest.alloc().init()
req.setRecognitionLevel_(1)
req.setRecognitionLanguages_(["zh-Hans", "en-US"])
handler.performRequests_error_([req], None)

found = None
for obs in req.results():
    if obs.confidence() < {confidence}:
        continue
    text = obs.topCandidates_(1)[0].string()
    if "{target_text}" in text:
        bbox = obs.boundingBox()
        cx = (bbox.origin.x + bbox.size.width / 2) * screen_w
        cy = (1 - bbox.origin.y - bbox.size.height / 2) * screen_h
        found = {{"text": text, "x": int(cx), "y": int(cy)}}
        break

print(json.dumps(found))
'''
    out, err, rc = _run([VISION_PYTHON, "-c", code], timeout=10)
    if rc != 0 or not out or out == "null":
        return None
    return json.loads(out)


# ── CLI 入口 ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Hermes 统一OCR")
    sub = parser.add_subparsers(dest="command")

    # find (快速找字)
    p = sub.add_parser("find", help="极速找字并返回屏幕坐标")
    p.add_argument("text", help="要查找的文字")
    p.add_argument("--image", help="图片路径(默认截全屏)")
    p.add_argument("--json", action="store_true", help="JSON输出")

    # screenshot
    p = sub.add_parser("screenshot", help="截图并识别")
    p.add_argument("--region", help="区域 x,y,w,h")
    p.add_argument("--json", action="store_true", help="JSON输出")

    # detect
    sub.add_parser("detect", help="检测可用引擎")

    args = parser.parse_args()

    if args.command == "detect":
        engines = detect_engines()
        print("=== Hermes OCR 引擎状态 ===")
        for name in ["vision", "paddleocr", "baidu", "ddddocr", "pymupdf"]:
            status = "✅" if engines.get(name) else "❌"
            label = {
                "vision": "Apple Vision OCR",
                "paddleocr": "PaddleOCR",
                "baidu": "百度OCR",
                "ddddocr": "ddddocr (验证码)",
                "pymupdf": "pymupdf (PDF)",
            }[name]
            print(f"  {status} {label}")
        print(f"\nVision Python: {VISION_PYTHON}")
        print(f"Venv Python: {HERMES_VENV}")
        return

    if args.command == "find":
        import time
        t0 = time.time()
        result = fast_ocr_find(args.text, args.image)
        elapsed = (time.time() - t0) * 1000
        if result:
            print(f"[Fast OCR] 找到 '{result['text']}' 含 '{args.text}', 耗时: {elapsed:.0f}ms, 坐标: ({result['x']}, {result['y']})")
            if args.json:
                print(json.dumps({**result, "ms": round(elapsed, 1)}, ensure_ascii=False))
        else:
            print(f"[Fast OCR] 未找到 '{args.text}', 耗时: {elapsed:.0f}ms")
            if args.json:
                print(json.dumps({"found": False, "text": args.text, "ms": round(elapsed, 1)}, ensure_ascii=False))
        return

    if args.command == "screenshot":
        path = screenshot(args.region)
        if not path:
            print("截图失败")
            sys.exit(1)

        if args.json:
            result, engine, err = ocr_image_auto(path)
            output = {"text": [], "engine": engine}
            if result:
                output["text"] = [b["text"] for b in result]
                output["blocks"] = result
            if err:
                output["error"] = err
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            result, engine, err = ocr_image_auto(path)
            print(f"引擎: {engine or 'N/A'}")
            if result:
                for b in result:
                    print(f"  {b['text']}")
            if err:
                print(f"错误: {err}")
        return

    if args.command == "read":
        if not os.path.exists(args.path):
            print(f"文件不存在: {args.path}")
            sys.exit(1)

        if args.engine == "vision":
            result, err = ocr_vision(args.path)
            engine = "vision"
        elif args.engine == "paddleocr":
            result, err = ocr_paddle(args.path)
            engine = "paddleocr"
        elif args.engine == "baidu":
            result, err = ocr_baidu(args.path)
            engine = "baidu"
        elif args.engine == "ddddocr":
            result, err = ocr_ddddocr(args.path)
            engine = "ddddocr"
        else:
            result, engine, err = ocr_image_auto(args.path)

        if args.json:
            output = {"text": [], "engine": engine}
            if result:
                output["text"] = [b["text"] for b in result]
                output["blocks"] = result
            if err:
                output["error"] = err
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"引擎: {engine or 'N/A'}")
            if result:
                for b in result:
                    print(f"  {b['text']}")
            if err:
                print(f"错误: {err}")
        return

    if args.command == "pdf":
        if not os.path.exists(args.path):
            print(f"文件不存在: {args.path}")
            sys.exit(1)

        if args.scan:
            # 扫描件：PDF转图片 → OCR
            pages = pdf_to_images(args.path)
            if not pages:
                print("PDF转换失败")
                sys.exit(1)
            all_blocks = []
            for page_path in pages:
                result, engine, err = ocr_image_auto(page_path)
                if result:
                    all_blocks.extend(result)
                os.remove(page_path)
            result = all_blocks
            engine = engine if all_blocks else None
        else:
            # 文本PDF：直接提取
            result, err = ocr_pymupdf_pdf(args.path)
            engine = "pymupdf"

        if args.json:
            output = {"text": [], "engine": engine}
            if isinstance(result, list):
                if args.scan:
                    output["text"] = [b["text"] for b in result]
                    output["blocks"] = result
                else:
                    output["text"] = [p["text"] for p in result]
                    output["pages"] = result
            if err:
                output["error"] = err if isinstance(err, str) else err
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"引擎: {engine or 'N/A'}")
            if result:
                for b in result:
                    if isinstance(b, dict):
                        if "page" in b:
                            print(f"\n--- 第{b['page']}页 ---")
                            print(f"  {b['text'][:200]}")
                        else:
                            print(f"  {b['text']}")
            if err:
                print(f"错误: {err}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
