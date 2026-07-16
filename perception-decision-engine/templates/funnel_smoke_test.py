"""
funnel_smoke_test.py — Decision Engine 4 层漏斗烟雾测试模板

复制后修改 find_element 调用即可. 默认测 6 个核心场景:
  1. L0 命中 (重复任务)
  2. L1 AX 命中 (新任务但 AX 可见)
  3. L2 OCR 命中 (canvas / 无 AX label)
  4. L2 Color 命中 (canvas 按钮)
  5. 全 miss (VLM 默认禁用)
  6. enable_vlm=True 但实际 disabled (验证 budget 拦截)

依赖:
  ~/.hermes/scripts/perception_memory.py
  ~/.hermes/scripts/decision_engine.py
  ~/.hermes/scripts/visual_verifier.py
  ~/.hermes/scripts/local_detector.py

用法:
  python3 funnel_smoke_test.py
  python3 funnel_smoke_test.py --iterations 100  # 压测
  python3 funnel_smoke_test.py --scenario L0     # 只跑某个场景
"""
import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))

import decision_engine as de
import perception_memory as pm
from PIL import Image, ImageDraw, ImageFont


def make_screenshot(text: str = "", with_red: bool = False, path: str = "/tmp/_funnel_test.png"):
    """造测试截图 — 必须 close 避免 fd 泄漏."""
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    img = Image.new("RGB", (800, 500), "white")
    d = ImageDraw.Draw(img)
    if text:
        d.text((100, 100), text, fill="black", font=font)
    if with_red:
        d.rectangle([400, 300, 580, 360], fill=(255, 0, 0))
    img.save(path, "PNG")
    img.close()
    del d, img
    return path


def scenario_l0_hit():
    """L0 命中: 预热缓存后查询."""
    print("\n=== Scenario 1: L0 hit ===")
    pm.element_remember("Safari", "Checkout", "AXButton", "Submit",
                          500, 300, 80, 30, enabled=True, fingerprint="")
    r = de.find_element(app="Safari", window_title="Checkout",
                        target_role="AXButton", target_title="Submit")
    assert r["path"] == "L0_cache", f"expected L0_cache, got {r['path']}"
    print(f"  ✓ path={r['path']}, latency={r['latency_ms']}ms")


def scenario_l1_ax_hit():
    """L1 命中: 新任务 + AX 树提供元素."""
    print("\n=== Scenario 2: L1 AX hit ===")
    fake_ax = [
        {"role": "AXButton", "label": "Confirm Order",
         "frame": {"x": 500, "y": 300, "w": 120, "h": 30}, "enabled": True},
    ]
    r = de.find_element(app="Safari", window_title="NewWindow",
                        ax_elements=fake_ax,
                        target_role="AXButton", target_title="Confirm")
    assert r["path"] == "L1_ax_tree", f"expected L1_ax_tree, got {r['path']}"
    print(f"  ✓ path={r['path']}, latency={r['latency_ms']}ms, x={r['element']['x']}")


def scenario_l2_ocr_hit():
    """L2 OCR 命中: AX 读不到, 走 macOS Vision."""
    print("\n=== Scenario 3: L2 OCR hit ===")
    ss = make_screenshot("Click here to continue")
    r = de.find_element(app="Unknown", window_title="Web",
                        screenshot_path=ss, target_title="Click")
    assert r["path"] == "L2_ocr", f"expected L2_ocr, got {r['path']}"
    print(f"  ✓ path={r['path']}, latency={r['latency_ms']}ms")


def scenario_l2_color_hit():
    """L2 Color 命中: canvas 按钮, 颜色块定位."""
    print("\n=== Scenario 4: L2 Color hit ===")
    ss = make_screenshot(with_red=True)
    r = de.find_element(app="Game", window_title="Canvas",
                        screenshot_path=ss,
                        target_title="Nonexistent",
                        target_color=(255, 0, 0))
    assert r["found"], "should hit L2_ocr or L2_color"
    print(f"  ✓ path={r['path']}, latency={r['latency_ms']}ms")


def scenario_full_miss():
    """全 miss: VLM 默认禁用."""
    print("\n=== Scenario 5: Full miss (VLM disabled) ===")
    ss = make_screenshot()
    r = de.find_element(app="X", window_title="Y",
                        screenshot_path=ss,
                        target_title=f"Nonexistent_{random.randint(10000, 99999)}")
    assert r["path"] == "miss"
    assert r["recovery"] == "human_in_loop"
    print(f"  ✓ path={r['path']}, candidates={[c['layer'] for c in r['candidates']]}")


def scenario_vlm_budget_block():
    """enable_vlm=True 但实际禁用 (验证 budget 拦截)."""
    print("\n=== Scenario 6: enable_vlm=True + actual disabled ===")
    ss = make_screenshot()
    r = de.find_element(app="X", window_title="Y",
                        screenshot_path=ss,
                        target_title="None", enable_vlm=True)
    assert r["path"] == "miss"
    vlm_cand = [c for c in r["candidates"] if c["layer"] == "L3"][0]
    assert vlm_cand.get("error") == "vlm_disabled"
    print(f"  ✓ vlm disabled correctly intercepted")


def scenario_funnel_stats():
    """funnel_stats API 工作正常."""
    print("\n=== Scenario 7: funnel_stats API ===")
    stats = de.funnel_stats(days=1)
    assert "total_calls" in stats
    print(f"  ✓ total_calls={stats['total_calls']}, layers={list(stats.get('layers', {}).keys())}")


SCENARIOS = {
    "L0": scenario_l0_hit,
    "L1": scenario_l1_ax_hit,
    "L2_ocr": scenario_l2_ocr_hit,
    "L2_color": scenario_l2_color_hit,
    "miss": scenario_full_miss,
    "vlm_block": scenario_vlm_budget_block,
    "stats": scenario_funnel_stats,
}


def main():
    args = sys.argv[1:]
    iterations = 1
    only = None
    for i, arg in enumerate(args):
        if arg == "--iterations":
            iterations = int(args[i + 1])
        elif arg == "--scenario":
            only = args[i + 1]

    if only:
        SCENARIOS[only]()
        return

    print(f"Running {len(SCENARIOS)} scenarios x {iterations} iterations...")
    for _ in range(iterations):
        for name, fn in SCENARIOS.items():
            try:
                fn()
            except AssertionError as e:
                print(f"  ✗ {name}: {e}")
                sys.exit(1)

    # 清理
    Path("/tmp/_funnel_test.png").unlink(missing_ok=True)
    print("\n✅ All scenarios passed")


if __name__ == "__main__":
    main()