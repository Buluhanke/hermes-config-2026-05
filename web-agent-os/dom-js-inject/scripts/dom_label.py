#!/usr/bin/env python3
"""
DOM元素打标签 — Playwright CDP直连chrome-debug 9333
给所有可见交互元素打 data-hermes-id 标签，返回精简元素列表供LLM决策
"""
import json, sys, time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed")
    sys.exit(1)

CDP_URL = "http://localhost:9333"

def get_browser():
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    return p, browser

def inject_labels():
    p, browser = get_browser()
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    
    result = page.evaluate("""
    (function() {
        var idx = 0;
        var result = [];
        var sel = 'a,button,input,textarea,select,[onclick],[role="button"],[role="link"],summary,label';
        var allEls = document.querySelectorAll(sel);
        allEls.forEach(function(el) {
            var r = el.getBoundingClientRect();
            if (r.width > 2 && r.height > 2) {
                var style = window.getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden') {
                    idx++;
                    el.setAttribute('data-hermes-id', 'h' + idx);
                    result.push({
                        id: 'h' + idx,
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.placeholder || '').trim().substring(0, 40),
                        rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}
                    });
                }
            }
        });
        return result;
    })()
    """)
    
    print(f"✅ 注入了 {len(result)} 个标签")
    for item in result[:20]:
        print(f"  [{item['id']}] {item['tag']} | {item['text'][:30]} | {item['rect']['x']},{item['rect']['y']}")
    
    browser.close()
    p.stop()
    return result

def click_hermes_id(hermes_id):
    p, browser = get_browser()
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    
    pos = page.evaluate(f"""
    (function() {{
        var el = document.querySelector('[data-hermes-id="{hermes_id}"]');
        if (!el) return null;
        var r = el.getBoundingClientRect();
        return {{ x: r.x + r.width/2, y: r.y + r.height/2 }};
    }})()
    """)
    
    if not pos:
        print(f"❌ 元素 {hermes_id} 未找到")
        return
    
    page.mouse.click(pos['x'], pos['y'])
    print(f"✅ 点击 [{hermes_id}] 坐标: {pos['x']},{pos['y']}")
    time.sleep(0.5)
    print(f"   当前URL: {page.url}")
    browser.close()
    p.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 dom_label.py [inject|click <hermes-id>|navigate <url>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "inject":
        inject_labels()
    elif cmd == "click" and len(sys.argv) >= 3:
        click_hermes_id(sys.argv[2])
    elif cmd == "navigate" and len(sys.argv) >= 3:
        p, browser = get_browser()
        ctx = browser.contexts[0]
        page = ctx.pages[0]
        page.goto(sys.argv[2], wait_until="domcontentloaded")
        print(f"✅ 打开: {page.url}")
        browser.close()
        p.stop()
    else:
        print("未知命令")
