#!/usr/bin/env python3
"""
vision_understand.py — 用本地 ollama 模型（默认 moondream）对图片做语义理解

注意：是"看懂画面在做什么"，不是 OCR。
用法：
  python3 vision_understand.py <image>                    # 用 prompt='描述这张图'
  python3 vision_understand.py <image> -p "图里有几个人"   # 自定义问题
  python3 vision_understand.py --screen                    # 截全屏再理解
  python3 vision_understand.py --bench <image>             # 跑一次并报耗时
  python3 vision_understand.py --model llava:7b <image>    # 换模型

依赖：
  - ollama serve 已在跑（默认 localhost:11434）
  - ollama pull moondream（或 llava/qwen-vl 等 VLM）
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# 默认用 qwen3-vl:2b — 中文原生，能点名识别界面内容，~25s/次
# moondream 速度更快(~3s) 但忽略中文 prompt，只在纯英文场景下用 --model moondream 切换
DEFAULT_MODEL = "qwen3-vl:2b"
DEFAULT_PROMPT = "用中文简洁描述这张图在做什么/显示什么内容。"


def ensure_model(model: str) -> None:
    """检查模型是否在 ollama 列表，不在则尝试 pull"""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            tags = json.loads(r.read())
        names = {m["name"].split(":")[0] for m in tags.get("models", [])}
        if model.split(":")[0] in names:
            return
    except Exception as e:
        print(f"⚠️  ollama 不可达 ({e})，尝试 pull", file=sys.stderr)
    # pull
    print(f"⏬ ollama pull {model} ...", file=sys.stderr)
    proc = subprocess.run(
        ["ollama", "pull", model],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ollama pull 失败: {proc.stderr}")


def encode_image(path: Path) -> str:
    """图片 → base64"""
    return base64.b64encode(path.read_bytes()).decode()


def chat_with_image(model: str, image: Path, prompt: str) -> tuple[str, float]:
    """调 ollama /api/generate 处理图片，返回 (回答, 毫秒)"""
    img_b64 = encode_image(image)
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return data.get("response", "").strip(), elapsed_ms


def capture_screen() -> Path:
    """截全屏到临时文件"""
    out = Path(tempfile.gettempdir()) / "vision_understand_screen.png"
    subprocess.run(["screencapture", "-x", "-t", "png", str(out)],
                   check=True, capture_output=True)
    return out


def main():
    ap = argparse.ArgumentParser(description="ollama VLM 图像语义理解")
    ap.add_argument("image", nargs="?", help="图片路径")
    ap.add_argument("-p", "--prompt", default=DEFAULT_PROMPT,
                    help=f"提问（默认：{DEFAULT_PROMPT}）")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL,
                    help=f"模型名（默认：{DEFAULT_MODEL}）")
    ap.add_argument("--screen", action="store_true", help="截全屏再理解")
    ap.add_argument("--bench", action="store_true", help="打印耗时")
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

    # 确保模型在（首次使用自动 pull）
    ensure_model(args.model)

    # 推理
    answer, elapsed = chat_with_image(args.model, img, args.prompt)
    print(answer)
    if args.bench:
        print(f"\n── 模型={args.model} 耗时={elapsed:.0f}ms  图={img.name} ──",
              file=sys.stderr)


if __name__ == "__main__":
    main()
