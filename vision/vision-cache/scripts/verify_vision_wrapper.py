#!/usr/bin/env python3
"""
verify_vision_wrapper.py — 透明 wrapper 端到端验证 (2026-06-05 新增)

跟 verify_vision_cache.py 互补:
  - verify_vision_cache.py  → 测核心 VisionCache 类 (LRU+TTL+key 隔离)
  - verify_vision_wrapper.py → 测 vision_with_cache.py 包装层 (hash + URL + DOM)

5 个测试场景:
  1. hash_image 同图同 hash / 改图 hash 变
  2. get_current_url 能拿到浏览器 URL
  3. make_key 稳定 + 区分 (URL/DOM/prompt 任一变化都生成不同 key)
  4. 缓存工作流: 3 次访问只 1 次 VLM
  5. TTL 过期: 1s TTL 时 1.5s 后应 miss

用法: python3 verify_vision_wrapper.py
"""
import sys
import time
import hashlib
import tempfile
from pathlib import Path

# 把 scripts/ 加进 path (因为 vision_with_cache 在 ~/.hermes/scripts)
SCRIPTS = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vision_with_cache import hash_image, get_current_url, make_key
from vision_cache import VisionCache


def test_hash_image():
    """同一图片 hash 稳定, 改图应不同"""
    print("\n[TEST 1] hash_image: 同图同 hash / 改图 hash 变")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"x" * 1000)
        tmp_path = f.name
    try:
        h1 = hash_image(tmp_path)
        h2 = hash_image(tmp_path)
        assert h1 == h2, f"同图 hash 应稳定: {h1} != {h2}"
        with open(tmp_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"y" * 1000)
        h3 = hash_image(tmp_path)
        assert h1 != h3, f"改图 hash 应不同: {h1} == {h3}"
        print(f"  h1={h1}, h3={h3} ✅ PASS")
    finally:
        Path(tmp_path).unlink()


def test_get_current_url():
    """拿当前浏览器 URL (CDP 9333)"""
    print("\n[TEST 2] get_current_url: 拿到浏览器 URL")
    url = get_current_url()
    assert url and url != "no-browser", f"应能拿到 URL, 实际: {url}"
    print(f"  URL={url[:80]} ✅ PASS")


def test_make_key_isolation():
    """key 生成稳定 + 4 维隔离"""
    print("\n[TEST 3] make_key: 4 维隔离")
    k1 = make_key("https://a.com", "dom1", "prompt1")
    k2 = make_key("https://a.com", "dom1", "prompt1")
    k3 = make_key("https://b.com", "dom1", "prompt1")  # URL 变
    k4 = make_key("https://a.com", "dom2", "prompt1")  # DOM 变
    k5 = make_key("https://a.com", "dom1", "prompt2")  # prompt 变
    assert k1 == k2, "稳定"
    assert k1 != k3, "URL 变应不同"
    assert k1 != k4, "DOM 变应不同"
    assert k1 != k5, "prompt 变应不同"
    print(f"  k1={k1[:12]} URL变={k3[:12]} DOM变={k4[:12]} prompt变={k5[:12]} ✅ PASS")


def test_cache_workflow():
    """完整缓存工作流: 3 次访问, 1 次 VLM"""
    print("\n[TEST 4] 缓存工作流: 3 次访问只 1 次 VLM")
    cache = VisionCache()
    cache.clear()
    call_count = [0]
    def fake_vlm():
        call_count[0] += 1
        time.sleep(0.05)
        return f"vlm_result_{call_count[0]}"

    for i in range(3):
        r, hit = cache.get_or_compute("u1", "d1", "p1", fake_vlm, model="test")
        print(f"  第 {i+1} 次: hit={hit}")

    assert call_count[0] == 1, f"VLM 应只调 1 次, 实际 {call_count[0]}"
    print(f"  VLM 调用 1/3 次 ✅ PASS")
    cache.clear()


def test_ttl_expiry():
    """TTL 过期: TTL=1s, 等 1.5s 后应 miss"""
    print("\n[TEST 5] TTL 过期: 1s TTL 时 1.5s 后应 miss")
    cache = VisionCache(ttl=1)
    cache.clear()
    call_count = [0]
    def fake():
        call_count[0] += 1
        return f"r{call_count[0]}"

    cache.get_or_compute("u", "d", "p", fake)
    time.sleep(1.5)
    cache.get_or_compute("u", "d", "p", fake)
    assert call_count[0] == 2, f"应重算, 实际 call={call_count[0]}"
    print(f"  1.5s 后重算, call=2/2 ✅ PASS")
    cache.clear()


if __name__ == "__main__":
    print("=" * 60)
    print("Vision Wrapper 端到端验证 (5 步)")
    print("=" * 60)
    test_hash_image()
    test_get_current_url()
    test_make_key_isolation()
    test_cache_workflow()
    test_ttl_expiry()
    print("\n" + "=" * 60)
    print("✅ 5/5 全部通过")
