#!/usr/bin/env python3
"""
verify_vision_cache.py — 视觉缓存 5 步验证脚本

跑这个脚本, 能验证 vision_cache 的所有关键场景:
  1. miss → VLM 调用 → 缓存写入
  2. hit → 0ms 返回
  3. 不同 prompt → 不同 key → miss
  4. DOM 变化 → 不同 key → miss
  5. stats 显示命中率

用法: python3 verify_vision_cache.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))
from vision_cache import VisionCache, make_key


def main():
    print("=" * 60)
    print("Vision Cache 5 步验证")
    print("=" * 60)

    cache = VisionCache(ttl=300)

    # 测试 1: miss + hit
    print("\n[1] miss → hit 模式")
    test_url = "https://example.com"
    test_dom = "dom_v1"
    test_prompt = "页面有按钮吗?"

    call_count = [0]
    def fake_vlm():
        call_count[0] += 1
        time.sleep(0.05)  # 模拟 50ms VLM
        return f"vlm_call_{call_count[0]}"

    r1, h1 = cache.get_or_compute(test_url, test_dom, test_prompt, fake_vlm)
    r2, h2 = cache.get_or_compute(test_url, test_dom, test_prompt, fake_vlm)
    r3, h3 = cache.get_or_compute(test_url, test_dom, test_prompt, fake_vlm)
    assert h1 == False, "第 1 次应该 miss"
    assert h2 == True, "第 2 次应该 hit"
    assert h3 == True, "第 3 次应该 hit"
    assert call_count[0] == 1, f"VLM 应该只调 1 次, 实际 {call_count[0]}"
    print(f"  ✓ 3 次访问 → 1 次 VLM, r1={r1}, h={h1}/{h2}/{h3}")

    # 测试 2: 不同 prompt → miss
    print("\n[2] 不同 prompt → miss")
    r4, h4 = cache.get_or_compute(test_url, test_dom, "页面有图片吗?", fake_vlm)
    assert h4 == False, "不同 prompt 应该 miss"
    print(f"  ✓ 不同 prompt → miss, r4={r4}")

    # 测试 3: 不同 DOM → miss
    print("\n[3] 不同 DOM → miss")
    r5, h5 = cache.get_or_compute(test_url, "dom_v2", test_prompt, fake_vlm)
    assert h5 == False, "不同 DOM 应该 miss"
    print(f"  ✓ 不同 DOM → miss, r5={r5}")

    # 测试 4: 不同 URL → miss
    print("\n[4] 不同 URL → miss")
    r6, h6 = cache.get_or_compute("https://other.com", test_dom, test_prompt, fake_vlm)
    assert h6 == False, "不同 URL 应该 miss"
    print(f"  ✓ 不同 URL → miss, r6={r6}")

    # 测试 5: stats
    print("\n[5] stats 统计")
    s = cache.stats()
    print(f"  entries={s['entries']}  hits={s['hits']}  misses={s['misses']}  rate={s['hit_rate']}")
    assert s['misses'] == 4, f"应该有 4 次 miss, 实际 {s['misses']}"
    assert s['hits'] >= 2, f"应该至少 2 次 hit, 实际 {s['hits']}"

    # 清理测试数据
    cache.clear()
    print("\n  ✅ 5 步验证全部通过")


if __name__ == "__main__":
    main()
