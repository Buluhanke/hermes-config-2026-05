#!/usr/bin/env python3
"""
Playwright Web Automation — AI 网站自动对话脚本
用法: python3 auto_web_chat.py <网站名> "<消息>"
例:  python3 auto_web_chat.py chatglm "Mac Mini M4不用OCR能读屏吗"
"""
import sys, time, subprocess, json
from playwright.sync_api import sync_playwright

SITES = {
    "chatglm": {
        "url": "https://chatglm.cn/main/alltoolsdetail?t=1780109684914&lang=zh",
        "input": "textarea",
        "button": "div[role=button].ds-button--primary",
        "reply": "p",
    },
    "deepseek": {
        "url": "https://chat.deepseek.com/",
        "input": "textarea",
        "button": "div[role=button].ds-button--primary",
        "reply": "p",
    },
    "doubao": {
        "url": "https://www.doubao.com/chat/",
        "input": "textarea, input[type=text]",
        "button": ".send-btn, button[type=submit]",
        "reply": "p",
    },
}

def call_cdp(method, params, tab_id):
    """通过 browser_cdp 工具写死的 WebSocket 端口调CDP（备用）"""
    r = subprocess.run(["curl", "-s", "-X", "POST",
        f"http://127.0.0.1:9333/json/{tab_id}/{method}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"id": 1, "method": method, "params": params})],
        capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except:
        return r.stdout

def run(site_name, message, timeout=60):
    if site_name not in SITES:
        print(f"未知网站: {site_name}，可用: {list(SITES.keys())}")
        return

    cfg = SITES[site_name]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"→ 打开 {site_name}...")
        page.goto(cfg["url"])
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # 方案1：逐字打字（触发 React onChange）
        print(f"→ 输入: {message}")
        page.click(cfg["input"])
        page.locator(cfg["input"]).press_sequentially(message, delay=50)
        time.sleep(0.3)

        # 发送
        print("→ 发送...")
        page.press(cfg["input"], "Enter")
        # 或 JS 点击按钮
        # page.evaluate(f"""
        #     (sel) => {{
        #         const btn = document.querySelector(sel);
        #         if(btn) {{ btn.removeAttribute('disabled'); btn.click(); }}
        #     }}
        # """, cfg["button"])

        # 等待回复（body 长度增长停止）
        print("→ 等待 AI 回复...")
        prev_len = 0
        for i in range(timeout // 2):
            time.sleep(2)
            body_len = len(page.inner_text("body"))
            delta = body_len - prev_len
            print(f"  [{i+1}] bodyLen={body_len} ({'+' if delta>0 else '='} {abs(delta)})")
            if i > 2 and delta == 0:
                print("→ AI 已完成")
                break
            prev_len = body_len

        # 读取回复
        print("\n=== AI 回复 ===")
        try:
            replies = page.query_selector_all(cfg["reply"])
            for r in replies[-3:]:
                txt = r.inner_text().strip()
                if txt:
                    print(txt)
        except Exception as e:
            print(f"读取失败: {e}")

        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])