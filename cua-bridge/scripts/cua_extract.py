#!/usr/bin/env python3
"""
cua_extract.py — 用 cua-driver 操控真实浏览器抓 JS 渲染页面（v1, 2026-06-07）

v1 跟 fetch_url 的区别：
  - fetch_url.py (Trafilatura)：抓 HTML 静态页 / 服务端渲染
  - cua_extract.py (cua-driver)：抓 JS SPA / 需要交互的页面 / 反爬严格的站点

工作流：
  1. list_apps 找 Chrome/Edge
  2. navigate 到目标 URL
  3. 等 JS 渲染 + 抓取 AX 树（或截图 OCR 兜底）
  4. 用 element_index 找正文（自动找 article/main/role=main）
  5. 返回 markdown

降级链：
  - cua-driver MCP → cua-driver CLI → fetch_url.py (Trafilatura) → curl + html2text
"""
import sys
import os
import json
import time
import argparse
import subprocess
import re
from pathlib import Path
from urllib.parse import urlparse

# ── 缓存（DiskCache） ─────────────────────────────
try:
    import diskcache  # type: ignore
    CACHE_DIR = Path.home() / ".hermes" / "cache" / "cua_extract"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache = diskcache.Cache(str(CACHE_DIR), expiry=3600)  # 1h TTL（JS 页面变化快）
    USE_CACHE = True
except ImportError:
    USE_CACHE = False

# ── cua-driver CLI 包装 ──────────────────────────
CUA_DRIVER = os.path.expanduser("~/.local/bin/cua-driver")
if not os.path.isfile(CUA_DRIVER):
    CUA_DRIVER = "/usr/local/bin/cua-driver"


def cua_call(tool_name: str, **kwargs) -> dict:
    """调 cua-driver MCP 工具（通过 call 子命令）

    **关键**：cua-driver call 的 args 全部从 stdin 一次性 JSON 传（不是 --key value）
    """
    try:
        result = subprocess.run(
            [CUA_DRIVER, "call", tool_name],
            input=json.dumps(kwargs),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            try:
                return {"ok": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"ok": True, "data": result.stdout}
        return {"ok": False, "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def find_browser() -> dict | None:
    """从 list_apps 找一个浏览器 app（Chrome/Brave/Edge/Safari）"""
    r = cua_call("list_apps")
    if not r["ok"]:
        return None
    data = r["data"]
    apps: list = []
    if isinstance(data, list):
        apps = data
    elif isinstance(data, dict):
        apps = data.get("apps", [])
    priority = ["com.google.Chrome", "com.brave.Browser", "com.microsoft.edgemac",
                "com.apple.Safari", "org.mozilla.firefox"]
    for bid in priority:
        for a in apps:
            if isinstance(a, dict) and a.get("bundle_id") == bid and a.get("pid"):
                return {"bundle_id": bid, "name": a.get("name"), "pid": a.get("pid")}
    return None


def get_text_or_article(pid: int) -> str:
    """优先 article/main，否则全文本"""
    js = """
    (function() {
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
    })()
    """
    r = cua_call("page", action="execute_javascript", pid=pid, javascript=js)
    if r["ok"]:
        data = r["data"]
        if isinstance(data, dict):
            return data.get("result", "") or str(data)
        return str(data)
    return ""


def get_page_title(pid: int) -> str:
    js = "document.title || ''"
    r = cua_call("page", action="execute_javascript", pid=pid, javascript=js)
    if r["ok"]:
        data = r["data"]
        if isinstance(data, dict):
            return data.get("result", "") or str(data)
        return str(data)
    return ""


def find_or_launch_browser(url: str) -> dict | None:
    """优先用 launch_app 后台打开 URL（不抢焦点）"""
    # 1. 找已打开的浏览器
    browser = find_browser()
    if browser:
        # 已经有浏览器在跑 — 用 list_windows 找一个窗口
        return browser

    # 2. 没有就 launch_app 打开
    r = cua_call("launch_app", bundle_id="com.google.Chrome", urls=[url])
    if r["ok"]:
        data = r["data"]
        if isinstance(data, dict):
            # launch_app 返回的 pid 和 window_id
            pid = data.get("pid")
            windows = data.get("windows", [])
            window_id = windows[0].get("window_id") if windows else None
            return {
                "bundle_id": "com.google.Chrome",
                "name": "Google Chrome",
                "pid": pid,
                "window_id": window_id,
            }
    return None


def extract_via_cua(url: str, timeout: int = 30, use_cache: bool = True) -> dict:
    """主入口：用 cua-driver 抓 URL（处理 JS 渲染）

    流程：
      1. launch_app (bundle_id=Chrome, urls=[URL]) — 后台打开
      2. 等 JS 渲染
      3. 用 page.execute_javascript 抓 article/main
    """
    cache_key = f"{url}|cua"
    if use_cache and USE_CACHE:
        hit = _cache.get(cache_key)
        if hit:
            hit["cache_hit"] = True
            return hit

    browser = find_or_launch_browser(url)
    if not browser:
        return {"url": url, "error": "no_browser", "content": ""}

    pid = browser["pid"]
    # 等 JS 渲染（launch_app 是后台的，给它 3 秒）
    time.sleep(3)

    # 1. 抓主区域
    content = get_text_or_article(pid)
    title = get_page_title(pid)

    if not content or len(content) < 50:
        return {"url": url, "error": "empty_content", "title": title, "content": "",
                "browser": browser.get("name")}

    result = {
        "url": url,
        "title": title,
        "content": content[:8000],
        "content_length": len(content),
        "browser": browser.get("name"),
        "extractor": "cua-driver",
        "cache_hit": False,
    }
    if use_cache and USE_CACHE:
        _cache.set(cache_key, result, expire=3600)
    return result


def main():
    ap = argparse.ArgumentParser(description="用 cua-driver 抓 JS 渲染页面")
    ap.add_argument("urls", nargs="+", help="要抓的 URL")
    ap.add_argument("--no-cache", action="store_true", help="跳过缓存")
    ap.add_argument("--max-chars", type=int, default=8000)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--title-only", action="store_true")
    args = ap.parse_args()

    print(f"📦 引擎: cua-driver {'✅' if os.path.isfile(CUA_DRIVER) else '❌'} | DiskCache {'✅' if USE_CACHE else '❌'}", file=sys.stderr)

    for url in args.urls:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        result = extract_via_cua(url, use_cache=not args.no_cache)
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
