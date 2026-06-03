#!/usr/bin/env python3
"""
hermes_web_bot.py — Playwright-based browser automation (no Docker)

pip install playwright && playwright install chromium

Uses Playwright's built-in Chromium 147 (headless=False, visible window).
No Docker, no manual driver download, no system Chrome dependency.

4 input strategies (in priority order):
  1. real_typing       → loc.click() + loc.press_sequentially(text, delay=50)
                        Triggers OS-level keydown/keyup/input events.
                        Works on: React, Vue, Angular, Tiptap, Semi Design, SyncInputEngine
  2. insert_text_enter → page.keyboard.type(text, delay=10) + Enter
                        Works on: DeepSeek, ChatGLM (plain textarea sites)
  3. insert_text       → page.keyboard.type + manual Enter press
  4. synthetic_event   → React fiber __reactProps onChange/onInput (last resort)

Usage:
  python hermes_web_bot.py                         # run all sites
  python hermes_web_bot.py -s chatgpt             # run single site
  python hermes_web_bot.py -q "your question"    # custom question
  python hermes_web_bot.py -s chatgpt -q "..."    # single site + custom question
"""

import time
import json
import re
import requests
import urllib.request
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser

# ================= 配置 =================
MINIMAX_API_KEY = ""  # 留空表示直接问 AI 网站，不走 MiniMax API
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

SITES = {
    "chatgpt": {
        "url": "https://chatgpt.com",
        "input_selector": "#prompt-textarea",
        "strategy": "real_typing",
        "wait_seconds": 30,
        "login_required": True,
    },
    "deepseek": {
        "url": "https://chat.deepseek.com",
        "input_selector": 'textarea[placeholder="给 DeepSeek 发送消息 "]',
        "strategy": "insert_text_enter",
        "wait_seconds": 60,  # SSE 流式，标题先出，需等
        "login_required": True,
    },
    "doubao": {
        "url": "https://www.doubao.com/chat/",
        "input_selector": 'textarea[placeholder="发消息..."]',
        "strategy": "real_typing",  # press_sequentially 在豆包有效，需等 90s
        "wait_seconds": 90,
        "login_required": True,
    },
    "chatglm": {
        "url": "https://chatglm.cn",
        "input_selector": "textarea.scroll-display-none",
        "strategy": "insert_text_enter",
        "wait_seconds": 90,
        "login_required": True,
    },
    "grok": {
        "url": "https://grok.com",
        "input_selector": "textarea",
        "strategy": "real_typing",
        "wait_seconds": 60,
        "login_required": True,
    },
    "gemini": {
        "url": "https://gemini.google.com",
        "input_selector": "[data-testid='prompt-input']",
        "strategy": "insert_text_enter",
        "wait_seconds": 30,
        "login_required": True,
    },
}

DEFAULT_QUESTION = (
    "按当前 Mac mini M4 24GB 内存配置，有哪些方法可以直接读取电脑屏幕"
    "做精确内容识别（OCR/视觉）？要求：免费、本地运行、不依赖云API。"
)

# ================= MiniMax API =================

def call_minimax(prompt: str, api_key: str) -> Optional[str]:
    if not api_key:
        return None
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "MiniMax-2.7",
            "messages": [
                {"role": "system", "content": "你是自动化助手，请生成一句适合填入网页对话框的回复（限50字）。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 200,
        }
        resp = requests.post(MINIMAX_API_URL, json=payload, headers=headers, timeout=15)
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [MiniMax API 错误] {e}")
        return None


# ================= 输入策略 =================

def type_real_typing(page: Page, selector: str, text: str):
    """策略 1: press_sequentially 逐字键入（50ms/字）— 触发 OS 级 keydown/keyup/input"""
    loc = page.locator(selector).first
    loc.click()
    loc.press_sequentially(text, delay=50)


def type_insert_text(page: Page, selector: str, text: str):
    """策略 2: keyboard.type"""
    page.wait_for_selector(selector, timeout=10000)
    page.evaluate(f"document.querySelector('{selector}').focus()")
    page.keyboard.type(text, delay=10)


def type_insert_text_enter(page: Page, selector: str, text: str):
    """策略 3: keyboard.type + Enter"""
    page.wait_for_selector(selector, timeout=10000)
    page.evaluate(f"document.querySelector('{selector}').focus()")
    page.keyboard.type(text, delay=10)
    page.keyboard.press("Enter")


def type_synthetic_event(page: Page, selector: str, text: str):
    """策略 4: React 18 合成事件（兜底）"""
    page.wait_for_selector(selector, timeout=10000)
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    js = f"""
    (() => {{
        const t = document.querySelector('{selector}');
        if (!t) return 'NO_EL';
        const proto = Object.getPrototypeOf(t);
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(t, '{escaped}');
        const tk = Object.keys(t).find(x => x.startsWith('__reactProps'));
        if (!tk) return 'NO_PROPS';
        const p = t[tk];
        function se(type, data) {{
            const ne = new Event(type, {{ bubbles: true, cancelable: true }});
            return {{
                type, bubbles: true, cancelable: true, defaultPrevented: false,
                currentTarget: t, target: t, nativeEvent: ne,
                isDefaultPrevented: () => false, isPropagationStopped: () => false,
                preventDefault() {{}}, stopPropagation() {{}}, persist() {{}},
                data, inputType: 'insertText'
            }};
        }}
        if (p.onCompositionEnd) p.onCompositionEnd(se('compositionend', '{escaped}'));
        if (p.onChange) p.onChange(se('change', '{escaped}'));
        if (p.onInput) p.onInput(se('input', '{escaped}'));
        return 'OK';
    }})()
    """
    return page.evaluate(js)


# ================= 等待回复 =================

def wait_for_reply(page: Page, wait_seconds: int) -> bool:
    """轮询等待回复出现（检测流式 SSE 渲染）"""
    interval = 5
    checks = max(wait_seconds // interval, 1)
    prev_len = 0
    body_len = 0
    for _ in range(checks):
        time.sleep(interval)
        try:
            body_len = page.evaluate("() => document.body.innerText.length")
        except Exception:
            body_len = 0
        if body_len > 1000 and body_len == prev_len:
            return True
        prev_len = body_len
    return body_len > 1000


# ================= 核心流程 =================

def run_single_site(browser: Browser, site_key: str, question: str = DEFAULT_QUESTION) -> Optional[str]:
    cfg = SITES[site_key]
    page = browser.new_page()

    try:
        print(f"  🌐 [{site_key}] 打开 {cfg['url']}...")
        page.goto(cfg["url"], timeout=25000, wait_until="domcontentloaded")
        page.wait_for_selector(cfg["input_selector"], timeout=15000)
        print(f"  ✅ [{site_key}] 页面加载完成")
    except Exception as e:
        print(f"  ❌ [{site_key}] 加载失败: {e}")
        page.close()
        return None

    selector = cfg["input_selector"]
    strategy = cfg["strategy"]

    try:
        if strategy == "real_typing":
            type_real_typing(page, selector, question)
        elif strategy == "insert_text":
            type_insert_text(page, selector, question)
            page.keyboard.press("Enter")
        elif strategy == "insert_text_enter":
            type_insert_text_enter(page, selector, question)
        elif strategy == "synthetic_event":
            result = type_synthetic_event(page, selector, question)
            print(f"    [{site_key}] synthetic_event: {result}")
        print(f"    [{site_key}] 输入完成，等待回复...")
    except Exception as e:
        print(f"    ❌ [{site_key}] 输入失败: {e}")
        page.close()
        return None

    wait_for_reply(page, cfg["wait_seconds"])

    body = page.inner_text("body")
    print(f"    [{site_key}] 回复长度: {len(body)} 字符")

    page.close()
    return body


def connect_cdp_to_existing_tab(page_ws_url: str):
    """CDP 连接已打开的 Chrome tab（保留登录态）"""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(page_ws_url)
        ctx = browser.contexts[0]
        return ctx.pages[0] if ctx.pages else None


def run_all(question: str = DEFAULT_QUESTION):
    # 先尝试 CDP 连接已登录的 Chrome
    cdp_page = None
    try:
        data = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
        targets = {t["id"]: t for t in data if t.get("url")}
        cg_target = next((t for t in targets.values() if "chatgpt.com" in t.get("url", "")), None)
        if cg_target:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(cg_target["webSocketDebuggerUrl"])
                pages = browser.contexts[0].pages
                if pages:
                    cdp_page = pages[0]
                    print(f"✅ CDP 连接成功，已登录 tab: {cdp_page.url[:60]}")
    except Exception as e:
        print(f"  ⚠️ CDP 连接失败（或无可用 tab）: {e}")
        cdp_page = None

    if cdp_page:
        print("✅ 使用已登录 Chrome（CDP）运行演示...")
        site_key = "chatgpt_cdp"
        cfg = SITES["chatgpt"]
        selector = cfg["input_selector"]
        try:
            cdp_page.wait_for_selector(selector, timeout=10000)
            type_real_typing(cdp_page, selector, question)
            cdp_page.keyboard.press("Enter")
            wait_for_reply(cdp_page, cfg["wait_seconds"])
            body = cdp_page.inner_text("body")
            ts = int(time.time())
            out = Path(f"/tmp/hermes_bot_{site_key}_{ts}.txt")
            out.write_text(body, encoding="utf-8")
            print(f"  ✅ [{site_key}] 存档: {out} ({len(body)} 字符)")
        except Exception as e:
            print(f"  ❌ [{site_key}] 失败: {e}")
    else:
        print("🚀 启动 Playwright Chromium 147（无登录态）...")
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--no-first-run", "--no-default-browser-check"]
            )
            print("✅ 浏览器启动成功\n")

            results = {}
            for site_key in SITES:
                print(f"{'='*50}")
                print(f"[{site_key}] 开始")
                try:
                    reply = run_single_site(browser, site_key, question)
                    if reply and len(reply) > 500:
                        ts = int(time.time())
                        out = Path(f"/tmp/hermes_bot_{site_key}_{ts}.txt")
                        out.write_text(reply, encoding="utf-8")
                        print(f"  ✅ 存档: {out}")
                        results[site_key] = {"status": "ok", "len": len(reply)}
                    else:
                        results[site_key] = {"status": "skipped", "len": len(reply) if reply else 0}
                        print(f"  ⚠️ 回复过短（可能需要登录）")
                except Exception as e:
                    print(f"  ❌ 异常: {e}")
                    results[site_key] = {"status": "error"}

            browser.close()

            print(f"\n{'='*50}")
            print("📊 总览:")
            for k, v in results.items():
                icon = "✅" if v["status"] == "ok" else "⚠️"
                print(f"  {icon} {k}: {v.get('len', '?')} 字符")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--question", default=DEFAULT_QUESTION)
    parser.add_argument("-s", "--site", help="只跑指定网站，如 'doubao'")
    args = parser.parse_args()

    if args.site:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            reply = run_single_site(browser, args.site, args.question)
            if reply:
                print(f"\n✅ 回复 ({len(reply)} 字符):\n{reply[:2000]}")
    else:
        run_all(args.question)