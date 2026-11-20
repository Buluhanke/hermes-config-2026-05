#!/usr/bin/env python3
"""
并行 OCR：百度 OCR + macOS Vision，取准确率更高的结果

使用方法：
    python3 parallel_ocr.py <图片路径>

原理：
- 同时调用百度 OCR 和 macOS Vision
- macOS Vision 结果额外 +10 分（准确率优势）
- 取分数更高的结果输出
"""
import subprocess, sys, os, re

def baidu_ocr(image_path):
    """调用百度 OCR 脚本（已配置 BAIDU_API_KEY/BAIDU_SECRET_KEY）。"""
    try:
        result = subprocess.run(
            ["python3", os.path.expanduser("~/.hermes/scripts/baidu_ocr.py"), image_path],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception as e:
        return f"ERROR: {e}"

def macos_vision_ocr(image_path):
    """调用 macOS Vision Framework OCR（本地离线）。"""
    try:
        result = subprocess.run(
            ["swift", os.path.expanduser("~/.hermes/scripts/macos_vision_ocr.swift"), image_path],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception as e:
        return f"ERROR: {e}"

def score_text(text):
    """启发式评分：中文字符数 * 2 + 总字符数。"""
    if not text or text.startswith("ERROR"):
        return 0
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total = len(text.strip())
    return cn_chars * 2 + total

def main():
    if len(sys.argv) < 2:
        print("Usage: parallel_ocr.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        sys.exit(1)
    
    print("正在并行调用百度 OCR 和 macOS Vision...")
    
    baidu_result = baidu_ocr(image_path)
    vision_result = macos_vision_ocr(image_path)
    
    # macOS Vision 识别更准确，优先使用它
    baidu_score = score_text(baidu_result)
    vision_score = score_text(vision_result) + 10  # macOS Vision 准确率优势
    
    print(f"\n=== 百度 OCR (score={baidu_score}) ===")
    print(baidu_result[:500])
    print(f"\n=== macOS Vision (score={vision_score}) ===")
    print(vision_result[:500])
    
    if vision_score >= baidu_score:
        print(f"\n✅ 选择 macOS Vision (score {vision_score} vs {baidu_score})")
        print(vision_result)
    else:
        print(f"\n✅ 选择百度 OCR (score {baidu_score} vs {vision_score})")
        print(baidu_result)

if __name__ == "__main__":
    main()