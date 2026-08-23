#!/usr/bin/env python3
"""
Screenshot Assertion — compare current screenshot with baseline.
Uses pixel-by-pixel RGB comparison.
"""

import argparse
import sys
from pathlib import Path


def compute_diff(current_path: str, baseline_path: str) -> dict:
    """Compare two images, return diff ratio and annotated diff image."""
    try:
        from PIL import Image
    except ImportError:
        print("PIL not installed, installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
        from PIL import Image

    current = Path(current_path)
    baseline = Path(baseline_path)

    if not current.exists():
        return {"error": f"Current image not found: {current_path}"}
    if not baseline.exists():
        return {"error": f"Baseline image not found: {baseline_path}"}

    img_cur = Image.open(current).convert("RGB")
    img_bas = Image.open(baseline).convert("RGB")

    # Resize to match if dimensions differ
    if img_cur.size != img_bas.size:
        img_bas = img_bas.resize(img_cur.size, Image.LANCZOS)

    pixels_cur = list(img_cur.getdata())
    pixels_bas = list(img_bas.getdata())

    if len(pixels_cur) != len(pixels_bas):
        w1, h1 = img_cur.size
        w2, h2 = img_bas.size
        return {"error": f"Dimension mismatch: current {w1}x{h1} vs baseline {w2}x{h2}"}

    diff_count = 0
    total = len(pixels_cur)
    diff_pixels = []

    # Threshold for "different" — tune sensitivity
    THRESHOLD = 30

    for i, (c, b) in enumerate(zip(pixels_cur, pixels_bas)):
        dr = abs(c[0] - b[0])
        dg = abs(c[1] - b[1])
        db = abs(c[2] - b[2])
        if max(dr, dg, db) > THRESHOLD:
            diff_count += 1
            # Mark diff pixel in red
            diff_pixels.append((255, 0, 0))
        else:
            diff_pixels.append(b)

    diff_ratio = diff_count / total

    # Build diff image
    w, h = img_cur.size
    diff_img = Image.new("RGB", (w, h))
    diff_img.putdata(diff_pixels)

    # Save diff image next to current
    diff_path = str(current.parent / f"{current.stem}_diff.png")
    diff_img.save(diff_path)

    return {
        "passed": True,
        "diff_ratio": round(diff_ratio, 4),
        "diff_count": diff_count,
        "total_pixels": total,
        "diff_image": diff_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Screenshot assertion")
    parser.add_argument("--current", required=True, help="Current screenshot path")
    parser.add_argument("--baseline", required=True, help="Baseline screenshot path")
    parser.add_argument("--threshold", type=float, default=0.05,
                        help="Max diff ratio to pass, 0.05 means 5 percent")
    parser.add_argument("--output", help="Save diff image to path")
    args = parser.parse_args()

    result = compute_diff(args.current, args.baseline)

    if "error" in result:
        print(f"✗ ERROR: {result['error']}")
        sys.exit(1)

    status = "✅ PASS" if result["diff_ratio"] <= args.threshold else "❌ FAIL"
    print(f"\n{status}")
    print(f"  Diff ratio:   {result['diff_ratio']:.2%}")
    print(f"  Diff pixels:  {result['diff_count']:,} / {result['total_pixels']:,}")
    print(f"  Diff image:   {result['diff_image']}")

    if args.output:
        from PIL import Image
        Image.open(result["diff_image"]).save(args.output)
        print(f"  Saved to:     {args.output}")

    if result["diff_ratio"] > args.threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
