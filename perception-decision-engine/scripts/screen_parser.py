#!/usr/bin/env python3
"""
screen_parser.py — 最强版结构化屏幕解析（UIAnchor / ScreenParse 思想落地）

不是"整图 md5 变没变"这种粗判断，而是把屏幕解析成结构化 UI 元素清单，
再做元素级 diff，精确回答每一步"哪个按钮消失了 / 哪个文字出现了 / 哪个框变了"。

三层感知：
  L-A Vision OCR    — 文字元素 + bbox（高召回文本，中文强）
  L-B OpenCV 轮廓   — 图标/按钮/输入框/色块（无 OCR 的结构元素）
  L-C 局部放大复核  — 对 diff 出的变化区域 crop+放大再 OCR（LBS/FocusUI 主动观察）

输出 element_diff:
  added / removed / changed / stable + focus_regions（变化区域，供 L-C 复核）

设计铁律：纯 stdlib + cv2/numpy/PIL，零 LLM，任何失败返回空结构不抛异常。
依赖：visual_verifier._ocr（macOS Vision）、cv2、numpy、PIL —— 本机全部具备。

用法：
  from screen_parser import parse_screen, diff_screens
  a = parse_screen("/tmp/before.png")
  b = parse_screen("/tmp/after.png")
  d = diff_screens(a, b)   # {added, removed, changed, stable, focus_regions, summary}
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import cv2

try:
    import visual_verifier
except Exception:
    visual_verifier = None

IOU_THRESHOLD = 0.45      # 元素匹配阈值
MOVE_THRESHOLD_PX = 12    # 位置变化超过此值算 moved
MIN_ELEMENT_AREA = 90     # 过滤噪声轮廓


def _elements_from_ocr(image_path: str) -> List[Dict[str, Any]]:
    """Vision OCR 文字元素（高召回文本层）。"""
    out: List[Dict[str, Any]] = []
    if not visual_verifier:
        return out
    try:
        for it in visual_verifier._ocr(image_path):
            text = (it.get("text") or "").strip()
            if not text:
                continue
            out.append({
                "kind": "text", "label": text,
                "x": int(it.get("x", 0)), "y": int(it.get("y", 0)),
                "w": int(it.get("w", 0)), "h": int(it.get("h", 0)),
                "conf": float(it.get("conf", 0)),
            })
    except Exception:
        pass
    return out


def _elements_from_contours(image_path: str) -> List[Dict[str, Any]]:
    """OpenCV 轮廓：检测按钮/图标/输入框/色块等结构元素（无 OCR 层）。"""
    out: List[Dict[str, Any]] = []
    try:
        img = cv2.imread(image_path)
        if img is None:
            return out
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 自适应阈值抓结构边界，再找轮廓
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            if area < MIN_ELEMENT_AREA or w < 8 or h < 8:
                continue
            # 分类：按长宽比 + 填充密度粗分
            roi = gray[y:y + h, x:x + w]
            fill = float(np.mean(roi < 128)) if roi.size else 0.0
            aspect = w / max(h, 1)
            if 0.7 <= aspect <= 1.4 and fill > 0.55:
                kind = "block"       # 实心块/按钮
            elif 0.6 <= aspect <= 1.8:
                kind = "box"         # 方框/按钮/输入框
            elif aspect > 3:
                kind = "bar"         # 条/进度/分割
            else:
                kind = "icon"
            out.append({"kind": kind, "label": "", "x": x, "y": y,
                        "w": w, "h": h, "fill": round(fill, 2)})
    except Exception:
        pass
    return out


def parse_screen(image_path: str, with_contours: bool = True) -> Dict[str, Any]:
    """把屏幕解析成结构化元素清单。失败返回空结构。"""
    result: Dict[str, Any] = {
        "path": image_path, "elements": [], "count": 0, "ok": False,
    }
    if not image_path or not Path(image_path).exists():
        return result
    try:
        els = _elements_from_ocr(image_path)
        if with_contours:
            els += _elements_from_contours(image_path)
        # 按 OCR 文字给邻近的轮廓元素打 label（融合）
        texts = [e for e in els if e["kind"] == "text"]
        for e in els:
            if e["kind"] == "text":
                continue
            for t in texts:
                if _iou(e, t) > 0.30 and not e.get("label"):
                    e["label"] = t["label"]
                    break
        result.update(elements=els, count=len(els), ok=True)
    except Exception:
        pass
    return result


def _iou(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    ax, ay, aw, ah = a.get("x", 0), a.get("y", 0), a.get("w", 0), a.get("h", 0)
    bx, by, bw, bh = b.get("x", 0), b.get("y", 0), b.get("w", 0), b.get("h", 0)
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _center(e: Dict[str, Any]):
    return (e.get("x", 0) + e.get("w", 0) / 2,
            e.get("y", 0) + e.get("h", 0) / 2)


def diff_screens(before: Dict[str, Any], after: Dict[str, Any],
                 inspect_fn=None) -> Dict[str, Any]:
    """
    元素级 diff。before/after 为 parse_screen 的结果。
    inspect_fn(bbox) -> 可选：对变化区域做局部放大 OCR（L-C 主动观察层）。
    返回 {added, removed, changed, stable, focus_regions, summary, ok}
    """
    out: Dict[str, Any] = {
        "added": [], "removed": [], "changed": [], "stable": [],
        "focus_regions": [], "summary": {}, "ok": False,
    }
    try:
        be = before.get("elements", [])
        ae = after.get("elements", [])
        matched_after = set()
        for b in be:
            best_i, best_iou = -1, 0.0
            for i, a in enumerate(ae):
                if i in matched_after:
                    continue
                iou = _iou(b, a)
                if iou > best_iou:
                    best_i, best_iou = i, iou
            if best_iou >= IOU_THRESHOLD:
                matched_after.add(best_i)
                a = ae[best_i]
                # 判定 changed：文字变了 或 中心位移大
                cb, ca = _center(b), _center(a)
                dist = ((cb[0] - ca[0]) ** 2 + (cb[1] - ca[1]) ** 2) ** 0.5
                label_changed = (b.get("label", "") != a.get("label", ""))
                if label_changed or dist > MOVE_THRESHOLD_PX:
                    out["changed"].append({
                        "before": b, "after": a,
                        "label_changed": label_changed,
                        "moved_px": round(dist, 1),
                    })
                else:
                    out["stable"].append(a)
            else:
                out["removed"].append(b)
        for i, a in enumerate(ae):
            if i not in matched_after:
                out["added"].append(a)

        # 变化区域（供主动观察复核）：added + changed 的 after bbox
        focus = []
        for e in [x["after"] for x in out["changed"]] + out["added"]:
            if e.get("w", 0) * e.get("h", 0) >= MIN_ELEMENT_AREA:
                focus.append({k: e.get(k, 0) for k in ("x", "y", "w", "h")})
        out["focus_regions"] = focus[:20]

        # L-C 主动观察：对变化区域局部放大复核（可选回调）
        if inspect_fn:
            refined = []
            for reg in focus[:8]:
                try:
                    detail = inspect_fn(reg)
                    if detail:
                        refined.append({"region": reg, "detail": detail})
                except Exception:
                    continue
            out["inspected"] = refined

        out["summary"] = {
            "before_count": len(be), "after_count": len(ae),
            "added": len(out["added"]), "removed": len(out["removed"]),
            "changed": len(out["changed"]), "stable": len(out["stable"]),
            "changed_ratio": round(
                (len(out["added"]) + len(out["removed"]) + len(out["changed"]))
                / max(len(be) + len(ae), 1), 3),
        }
        out["ok"] = True
    except Exception:
        pass
    return out


# ============================================================
# 自检
# ============================================================
def _selftest():
    import tempfile
    from PIL import Image, ImageDraw
    tmp = Path(tempfile.mkdtemp(prefix="screenparse_"))
    checks = []

    # before: 白底，画一个红色按钮 + 蓝块
    p1 = tmp / "a.png"
    im1 = Image.new("RGB", (300, 200), "white")
    d1 = ImageDraw.Draw(im1)
    d1.rectangle([50, 50, 150, 90], fill="red")
    d1.rectangle([180, 120, 260, 180], fill="blue")
    im1.save(p1)

    # after: 红按钮消失，新增绿色块（模拟"提交后成功提示"）
    p2 = tmp / "b.png"
    im2 = Image.new("RGB", (300, 200), "white")
    d2 = ImageDraw.Draw(im2)
    d2.rectangle([180, 120, 260, 180], fill="blue")   # stable
    d2.rectangle([60, 60, 160, 100], fill="green")    # added/changed
    im2.save(p2)

    a = parse_screen(str(p1))
    b = parse_screen(str(p2))
    checks.append(("parse ok", a["ok"] and b["ok"] and a["count"] > 0))
    d = diff_screens(a, b)
    checks.append(("diff ok", d["ok"]))
    checks.append(("detects change", d["summary"]["changed"] + d["summary"]["removed"] + d["summary"]["added"] > 0))
    checks.append(("has stable element", d["summary"]["stable"] > 0))
    checks.append(("focus regions present", len(d["focus_regions"]) > 0))
    # 同图 diff 应几乎无变化
    d2 = diff_screens(a, a)
    checks.append(("identical -> no change", d2["summary"]["changed"] == 0 and d2["summary"]["added"] == 0 and d2["summary"]["removed"] == 0))

    ok = sum(1 for _, p in checks if p)
    print(f"elements: before={a['count']} after={b['count']}")
    print("diff summary:", json.dumps(d["summary"], ensure_ascii=False))
    for name, passed in checks:
        print(("  PASS " if passed else "  FAIL ") + name)
    print(f"\n{ok}/{len(checks)} passed")
    return ok == len(checks)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(0 if _selftest() else 1)
    elif len(sys.argv) > 2 and sys.argv[1] == "diff":
        a = parse_screen(sys.argv[2])
        b = parse_screen(sys.argv[3])
        print(json.dumps(diff_screens(a, b), ensure_ascii=False, indent=2))
    else:
        print(__doc__)
