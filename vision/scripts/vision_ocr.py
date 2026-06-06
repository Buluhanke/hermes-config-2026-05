#!/usr/bin/env python3
"""
vision_ocr.py — macOS Vision.framework OCR 桥（0 依赖、纯系统 API）

原理：fork swift 子进程跑 VNRecognizeTextRequest，stdout 吐 JSON
用法：
  python3 vision_ocr.py <image_path>           # 识别一张图，打印文本
  python3 vision_ocr.py --bench <image>         # 跑一次并报耗时
  python3 vision_ocr.py --json <image>          # 输出完整 JSON（含位置/置信度）
  python3 vision_ocr.py --screen                # 截全屏再 OCR

输出格式（默认）：
  <line1>
  <line2>
  ...

输出格式（--json）：
  {"elapsed_ms": 47, "lines": [{"text": "...", "confidence": 0.95, "box": [x,y,w,h]}, ...]}
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# 内嵌 Swift 源码（避免外部文件依赖）
SWIFT_SRC = r'''
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    FileHandle.standardError.write(Data("usage: swift_ocr <image_path>\n".utf8))
    exit(1)
}
let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let img = NSImage(contentsOf: url),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write(Data("ERR: cannot load image\n".utf8))
    exit(2)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = true
req.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([req])
} catch {
    FileHandle.standardError.write(Data("ERR: \(error)\n".utf8))
    exit(3)
}
let observations = (req.results ?? [])
var out: [[String: Any]] = []
for obs in observations {
    guard let cand = obs.topCandidates(1).first else { continue }
    let bb = obs.boundingBox  // 归一化坐标 (0~1)，y 翻转
    let w = Double(cg.width), h = Double(cg.height)
    out.append([
        "text": cand.string,
        "confidence": Double(cand.confidence),
        "box": [
            Double(bb.origin.x) * w,
            (1.0 - Double(bb.origin.y) - Double(bb.height)) * h,
            Double(bb.width) * w,
            Double(bb.height) * h,
        ]
    ])
}
let json = try JSONSerialization.data(
    withJSONObject: ["lines": out], options: [.sortedKeys]
)
FileHandle.standardOutput.write(json)
'''


def get_swift_bin():
    """Swift 编译器路径"""
    return "/usr/bin/swiftc"


def compile_swift():
    """把内嵌 Swift 源码编成一个小的可执行文件，返回路径"""
    cache = Path.home() / ".hermes" / "scripts" / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / "vision_ocr_bin"
    src = cache / "vision_ocr.swift"
    if out.exists() and src.exists() and out.stat().st_mtime > src.stat().st_mtime:
        return out
    src.write_text(SWIFT_SRC)
    # 编译，链接 AppKit + Vision
    subprocess.run(
        [get_swift_bin(), str(src), "-o", str(out),
         "-framework", "AppKit", "-framework", "Vision"],
        check=True, capture_output=True,
    )
    return out


def run_ocr(image_path: Path) -> dict:
    """调 Swift 二进制跑 OCR，返回 dict"""
    bin_path = compile_swift()
    t0 = time.perf_counter()
    proc = subprocess.run(
        [str(bin_path), str(image_path)],
        capture_output=True, timeout=30,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if proc.returncode != 0:
        raise RuntimeError(f"swift ocr failed (rc={proc.returncode}): {proc.stderr.decode()}")
    data = json.loads(proc.stdout)
    data["elapsed_ms"] = round(elapsed_ms, 1)
    return data


def capture_screen() -> Path:
    """截全屏到临时文件，返回路径"""
    out = Path(tempfile.gettempdir()) / "vision_ocr_screen.png"
    subprocess.run(["screencapture", "-x", "-t", "png", str(out)],
                   check=True, capture_output=True)
    return out


def main():
    ap = argparse.ArgumentParser(description="macOS Vision OCR 桥")
    ap.add_argument("image", nargs="?", help="图片路径")
    ap.add_argument("--bench", action="store_true", help="跑一次并打印耗时")
    ap.add_argument("--json", action="store_true", help="输出完整 JSON")
    ap.add_argument("--screen", action="store_true", help="截全屏再 OCR")
    args = ap.parse_args()

    if args.screen:
        img = capture_screen()
    elif args.image:
        img = Path(args.image).expanduser().resolve()
        if not img.exists():
            print(f"❌ 图片不存在: {img}", file=sys.stderr)
            sys.exit(1)
    else:
        ap.print_help()
        sys.exit(1)

    result = run_ocr(img)
    lines = result.get("lines", [])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 简洁模式：每行文本
        for ln in lines:
            print(ln["text"])
        if args.bench:
            print(f"\n── {len(lines)} 行 / {result['elapsed_ms']}ms / {img.name} ──",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
