#!/usr/bin/env python3
"""
1688真人化浏览器 - 一键启动脚本
自动：连接CDP Chrome → 找/新开1688页面 → 注入真人化补丁
Ctrl+C 退出
"""
import sys, time

TARGET_KEYWORD = "1688"

def main():
    from playwright.sync_api import sync_playwright
    from cloakbrowser.human import patch_context, patch_page, HumanConfig, _CursorState

    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    ctx = browser.contexts[0]

    # 找1688页面，没有则新开
    page = None
    for pg in ctx.pages:
        if TARGET_KEYWORD in pg.url or TARGET_KEYWORD in pg.title():
            page = pg
            break

    if page is None:
        page = ctx.new_page()
        page.goto("https://www.1688.com", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"新开页面: {page.title()}")

    cfg = HumanConfig(
        typing_delay=70, typing_delay_spread=40,
        mistype_chance=0.02,
        mouse_min_steps=25, mouse_max_steps=80,
        idle_between_actions=True, idle_between_duration=(0.3, 0.8),
    )
    cursor = _CursorState()
    patch_context(ctx, cfg)
    patch_page(page, cfg, cursor)

    print(f"✅ 真人化补丁注入成功")
    print(f"   页面: {page.title()}")
    print(f"   URL: {page.url}")
    print(f"   打字: {cfg.typing_delay}±{cfg.typing_delay_spread}ms")
    print(f"   鼠标: {cfg.mouse_min_steps}-{cfg.mouse_max_steps}步曲线路径")
    print(f"   操作间停顿: {cfg.idle_between_duration}s")
    print(f"\n按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        browser.close()
        p.stop()
        print("已关闭")

if __name__ == "__main__":
    main()