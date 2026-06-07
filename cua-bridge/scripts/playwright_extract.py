#!/usr/bin/env python3
"""
playwright_extract.py — 用 Playwright 抓 JS 渲染页面（v1，2026-06-07）

补位：fetch_url.py (Trafilatura) 拿不到 JS 渲染后的 DOM 时升级到这条。

工作流：
  1. 后台启动 headless chromium（不抢焦点）
  2. 等待 JS 渲染 / networkidle
  3. 拿 article/main/[role=main] 的 innerText
  4. 返回 markdown

依赖：playwright + chromium
  ~/.hermes/hermes-agent/venv/bin/python -m playwright install chromium

降级：chromium 没装 → 自动用 system Chrome via CDP（可选）
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

# ── 缓存（DiskCache） ──────────────────────
try:
    import diskcache  # type: ignore
    CACHE_DIR = Path.home() / ".hermes" / "cache" / "playwright_extract"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache = diskcache.Cache(str(CACHE_DIR), expiry=3600)  # 1h TTL
    USE_CACHE = True
except ImportError:
    USE_CACHE = False


# ── 检测 Playwright + chromium ──────────────────
def check_playwright() -> dict:
    """返回 {playwright: bool, chromium: bool, error: str}"""
    result = {"playwright": False, "chromium": False, "error": ""}
    try:
        from playwright.sync_api import sync_playwright  # type: ignore # noqa: F401
        result["playwright"] = True
    except ImportError:
        result["error"] = "playwright not installed"
        return result

    # chromium 检测（macOS 默认路径）
    chromium_paths = [
        Path.home() / ".cache" / "ms-playwright" / "chromium-1187" / "chrome-mac" / "Chromium.app" / "Contents" / "MacOS" / "Chromium",
        Path.home() / ".cache" / "ms-playwright" / "chromium_headless_shell-1187" / "chrome-mac" / "headless_shell",
    ]
    # 模糊找
    pw_cache = Path.home() / ".cache" / "ms-playwright"
    if pw_cache.exists():
        for p in pw_cache.rglob("Chromium"):
            if p.is_file() and p.stat().st_mode & 0o111:
                result["chromium_path"] = str(p)
                result["chromium"] = True
                return result
        for p in pw_cache.rglob("headless_shell"):
            if p.is_file() and p.stat().st_mode & 0o111:
                result["chromium_path"] = str(p)
                result["chromium"] = True
                return result

    # 退路：检查 system Chrome（macOS /Applications/Google Chrome.app）
    system_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if system_chrome.is_file() and system_chrome.stat().st_mode & 0o111:
        result["chromium"] = True  # 复用这个字段
        result["chromium_path"] = str(system_chrome)
        result["system_chrome"] = True
        return result

    if not result["chromium"]:
        result["error"] = ("chromium not installed. Run: "
                           "~/.hermes/hermes-agent/venv/bin/python -m playwright install chromium "
                           "(or install Google Chrome.app)")
    return result


# ── 主提取函数 ──────────────────────

def extract_via_playwright(url: str, timeout: int = 30, use_cache: bool = True,
                            wait_selector: str | None = None) -> dict:
    """用 Playwright 抓 URL（处理 JS 渲染）"""
    cache_key = f"{url}|pw"
    if use_cache and USE_CACHE:
        hit = _cache.get(cache_key)
        if hit:
            hit["cache_hit"] = True
            return hit

    from playwright.sync_api import sync_playwright  # type: ignore

    result: dict = {"url": url, "extractor": "playwright"}
    try:
        with sync_playwright() as p:
            # 优先 system Chrome（已装、免下载）；fallback 到 chromium
            system_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            if system_chrome.is_file():
                browser = p.chromium.launch(channel="chrome", headless=True)
                result["browser"] = "system-chrome"
            else:
                browser = p.chromium.launch(headless=True)
                result["browser"] = "chromium-downloaded"
            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.set_default_timeout(timeout * 1000)

                page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

                # 可选：等特定 selector
                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=timeout * 1000)

                # 拿 title
                result["title"] = page.title()

                # 拿正文（优先 article / main / [role=main]）
                content = page.evaluate("""() => {
                    const candidates = [
                        document.querySelector('article'),
                        document.querySelector('main'),
                        document.querySelector('[role="main"]'),
                        document.querySelector('#content'),
                        document.querySelector('.content'),
                        document.body,
                    ].filter(Boolean);
                    const el = candidates[0];
                    if (!el) return '';
                    return el.innerText || el.textContent || '';
                }""")

                result["content"] = content[:8000] if content else ""
                result["content_length"] = len(content) if content else 0

                if not result["content"] or result["content_length"] < 50:
                    result["error"] = "empty_content"
            finally:
                browser.close()
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        result.setdefault("content", "")

    # 写缓存
    if use_cache and USE_CACHE and not result.get("error"):
        _cache.set(cache_key, result, expire=3600)

    return result


# ── CLI ──────────────────────

def main():
    ap = argparse.ArgumentParser(description="用 Playwright 抓 JS 渲染页面")
    ap.add_argument("urls", nargs="+", help="要抓的 URL")
    ap.add_argument("--no-cache", action="store_true", help="跳过缓存")
    ap.add_argument("--max-chars", type=int, default=8000)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--title-only", action="store_true")
    ap.add_argument("--wait-selector", help="等特定 selector 出现再抓")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    # 环境检查
    env = check_playwright()
    print(f"📦 playwright: {'✅' if env['playwright'] else '❌'} | "
          f"chromium: {'✅' if env['chromium'] else '❌'} | "
          f"DiskCache: {'✅' if USE_CACHE else '❌'}",
          file=sys.stderr)
    if not env["playwright"]:
        print(f"❌ {env['error']}", file=sys.stderr)
        sys.exit(1)
    if not env["chromium"]:
        print(f"❌ {env['error']}", file=sys.stderr)
        sys.exit(1)

    for url in args.urls:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        result = extract_via_playwright(
            url, use_cache=not args.no_cache,
            timeout=args.timeout, wait_selector=args.wait_selector
        )
        if args.title_only:
            print(f"📄 {result.get('title', '?')}")
            print(f"   {url}")
            continue
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            tag = "💾" if result.get("cache_hit") else "🌐"
            ext = result.get("extractor", "?")
            print(f"\n{tag} [{ext}] {result.get('title', '?')}")
            print(f"   {url}")
            if result.get("error"):
                print(f"   ❌ {result['error']}")
            elif result.get("content"):
                print()
                print(result["content"][:args.max_chars])


if __name__ == "__main__":
    main()
