#!/usr/bin/env python3
"""
真人化浏览器自动化 - 一键注入脚本
用法: python3 humanize_inject.py [page_title关键词]
示例: python3 humanize_inject.py 1688
"""
import sys, time

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    from playwright.sync_api import sync_playwright
    from cloakbrowser.human import patch_context, patch_page, HumanConfig, _CursorState

    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp("http://localhost:9333")

    # 找目标页面
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if target is None or target.lower() in pg.title().lower():
                page = pg
                print(f"✅ 找到页面: {pg.title()}")
                break
        if page:
            break

    if page is None:
        # 取第一个页面
        if browser.contexts:
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else None
        if page is None:
            print("❌ 未找到可用页面")
            browser.close()
            p.stop()
            return

    cfg = HumanConfig(
        typing_delay=70,
        typing_delay_spread=40,
        mistype_chance=0.02,
        mouse_steps_divisor=8,
        mouse_min_steps=25,
        mouse_max_steps=80,
        idle_between_actions=True,
        idle_between_duration=(0.3, 0.8),
    )
    cursor = _CursorState()

    for ctx in browser.contexts:
        patch_context(ctx, cfg)
    patch_page(page, cfg, cursor)

    print(f"✅ 真人化补丁注入成功")
    print(f"   页面: {page.title()}")
    print(f"   打字: {cfg.typing_delay}±{cfg.typing_delay_spread}ms")
    print(f"   鼠标: {cfg.mouse_min_steps}-{cfg.mouse_max_steps}步")
    print(f"   误触: {cfg.mistype_chance}")
    print(f"   操作间停顿: {cfg.idle_between_duration}")

    # 保持连接不断
    print("\n按 Ctrl+C 退出")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        browser.close()
        p.stop()

if __name__ == "__main__":
    main()