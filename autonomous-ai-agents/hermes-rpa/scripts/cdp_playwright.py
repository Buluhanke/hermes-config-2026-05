#!/usr/bin/env python3
"""
CDP Playwright 工具 — 连接到用户本地 Chrome (127.0.0.1:9222)
通过 CDP 复用用户登录态，操作任何已登录的网站。

用法: 由 Hermes agent 在 execute_code 或 terminal 中调用

典型工作流:
  1. browser = connect_cdp()
  2. page = browser.contexts[0].new_page()
  3. page.goto('目标URL')
  4. page.click(), page.fill(), page.evaluate()...
  5. browser.close()
"""

from playwright.sync_api import sync_playwright
import json, sys


def connect_cdp(port=9222, host='127.0.0.1'):
    """连接到本地已在运行的 Chrome CDP 实例"""
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(f'http://{host}:{port}')
    return p, browser


def list_pages(browser) -> list[dict]:
    """列出当前所有标签页"""
    from playwright.sync_api import Browser
    pages = []
    for ctx in browser.contexts:
        for p in ctx.pages:
            pages.append({
                'id': p.url[-8:],
                'title': p.title()[:50],
                'url': p.url[:80]
            })
    return pages


def screenshot(page, path='/tmp/hermes_rpa_screenshot.png'):
    """截图并返回路径"""
    page.screenshot(path=path, full_page=False)
    return path


def get_page_text(page, max_len=2000):
    """获取页面可见文本"""
    text = page.evaluate('document.body.innerText')
    if len(text) > max_len:
        text = text[:max_len] + '\n... [截断]'
    return text


def scroll(page, direction='down', amount=500):
    """滚动页面"""
    if direction == 'down':
        page.evaluate(f'window.scrollBy(0, {amount})')
    else:
        page.evaluate(f'window.scrollBy(0, -{amount})')
    return True


def click_by_text(page, text, exact=False):
    """通过文本内容点击元素"""
    try:
        if exact:
            page.get_by_text(text, exact=True).first.click()
        else:
            page.get_by_role("link", name=text).first.click()
        return True
    except Exception as e:
        try:
            page.locator(f'text={text}').first.click()
            return True
        except:
            raise Exception(f'找不到包含 "{text}" 的元素')


def fill_input(page, placeholder_or_label, value):
    """填入输入框"""
    try:
        page.get_by_placeholder(placeholder_or_label).fill(value)
    except:
        page.locator(f'input[placeholder*="{placeholder_or_label}"]').fill(value)
    return True


def wait_and_click(page, selector, timeout=5000):
    """等待元素出现后点击"""
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)
    return True


# --- CLI 入口: python3 cdp_playwright.py <action> [args...] ---
if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'

    p, browser = connect_cdp()

    if action == 'status':
        info = browser.contexts[0].pages if browser.contexts else []
        print(f'✅ Chrome CDP 已连接 | {len(info)} 个标签页')

    elif action == 'pages':
        for pg in list_pages(browser):
            print(f'[{pg["id"]}] {pg["title"]} | {pg["url"]}')

    elif action == 'goto':
        url = sys.argv[2]
        page = browser.contexts[0].new_page() if browser.contexts else browser.new_page()
        page.goto(url, timeout=30000)
        print(f'导航至: {url}')
        print(f'标题: {page.title()}')
        text = get_page_text(page, 800)
        print(f'内容:\n{text}')

    elif action == 'screenshot':
        page = browser.contexts[0].pages[-1] if browser.contexts and browser.contexts[0].pages else browser.new_page()
        path = screenshot(page, sys.argv[2] if len(sys.argv) > 2 else '/tmp/hermes_rpa_screenshot.png')
        print(f'截图: {path}')

    elif action == 'eval':
        js = sys.argv[2]
        page = browser.contexts[0].pages[-1] if browser.contexts and browser.contexts[0].pages else browser.new_page()
        result = page.evaluate(js)
        print(json.dumps(result, ensure_ascii=False, default=str))

    browser.close()
    p.stop()
