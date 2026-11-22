#!/usr/bin/env python3
"""
visual_verifier.py — L2 视觉验证最小可用实现（补 decision_engine 缺失依赖）

提供 decision_engine 需要的两个接口：
  - spot_by_text_heuristic(image, keywords) -> {"found": bool, "hits":[{x,y,w,h,text,matched_keyword}]}
  - frame_fingerprint(image) -> str

OCR 用 macOS 原生 Vision（Swift），带 bbox 坐标。零第三方依赖。
设计原则：任何失败都返回空结构，绝不抛异常（感知层铁律）。
"""
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_VISION_SWIFT = _SCRIPT_DIR / "_vision_ocr_bbox.swift"


def _ensure_swift():
    """生成带 bbox 的 Vision OCR Swift 脚本（只写一次）。"""
    if _VISION_SWIFT.exists():
        return
    src = '''import Vision
import Foundation
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else { print("[]"); exit(0) }
guard let image = NSImage(contentsOfFile: args[1]),
      let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cg = bitmap.cgImage else { print("[]"); exit(0) }

let W = CGFloat(bitmap.pixelsWide)
let H = CGFloat(bitmap.pixelsHigh)
let sem = DispatchSemaphore(value: 0)
var out: [[String: Any]] = []

let req = VNRecognizeTextRequest { r, _ in
    if let obs = r.results as? [VNRecognizedTextObservation] {
        for o in obs {
            guard let c = o.topCandidates(1).first else { continue }
            let bb = o.boundingBox
            let x = bb.origin.x * W
            let y = (1 - bb.origin.y - bb.height) * H
            out.append([
                "text": c.string,
                "x": Int(x), "y": Int(y),
                "w": Int(bb.width * W), "h": Int(bb.height * H),
                "conf": c.confidence
            ])
        }
    }
    sem.signal()
}
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
req.usesLanguageCorrection = true
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([req])
sem.wait()
print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
'''
    try:
        _VISION_SWIFT.write_text(src)
    except Exception:
        pass


def _ocr(image_path):
    """跑 Vision OCR，返回 [{text,x,y,w,h,conf}]。失败返回 []。"""
    try:
        _ensure_swift()
        for k in ["HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(k, None)
        r = subprocess.run(["/usr/bin/swift", str(_VISION_SWIFT), str(image_path)],
                           capture_output=True, timeout=30)
        if r.returncode != 0:
            return []
        data = json.loads(r.stdout.decode("utf-8", "replace").strip())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def spot_by_text_heuristic(image_path, keywords):
    """L2.OCR: 在截图里找关键词，返回命中坐标。"""
    if not image_path or not Path(image_path).exists():
        return {"found": False, "hits": []}
    hits = []
    for item in _ocr(image_path):
        text = item.get("text", "")
        matched = next((k for k in (keywords or []) if k and k.lower() in text.lower()), None)
        if matched:
            hits.append({
                "x": item.get("x", 0), "y": item.get("y", 0),
                "w": item.get("w", 0), "h": item.get("h", 0),
                "text": text, "matched_keyword": matched,
            })
    return {"found": bool(hits), "hits": hits}


def frame_fingerprint(image_path):
    """整图指纹：文件 md5（快且稳定，用于缓存一致性粗校验）。"""
    try:
        h = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "ocr":
        print(json.dumps(spot_by_text_heuristic(sys.argv[2], sys.argv[3:]), ensure_ascii=False))
    elif len(sys.argv) > 1:
        print(frame_fingerprint(sys.argv[1]))
