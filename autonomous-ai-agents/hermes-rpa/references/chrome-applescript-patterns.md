# AppleScript 控制 Chrome — 已验证可用模式

## 2026-05-09 实测结果

### ✅ 可用：让用户已登录的 Chrome 跳转到指定 URL

```python
import subprocess
from pathlib import Path

def open_chrome_url(url):
    script = f'''
    tell application "Google Chrome"
        activate
        open location "{url}"
    end tell
    '''
    Path('/tmp/goto.scpt').write_text(script)
    r = subprocess.run(['osascript', '/tmp/goto.scpt'], capture_output=True, text=True)
    return r.returncode == 0
```

原理：用 `open location` 让 Chrome 跳转到 URL，用户的登录态（Cookie/Session）全部保留。

**关键限制**：AppleScript 无法读取页面内部内容（输入框/按钮），只能读 URL 和标题。

### ✅ 可用：读 Chrome 当前 URL 和标题

```python
def get_chrome_url_and_title():
    script = '''
    tell application "Google Chrome"
        if (count of windows) > 0 then
            set u to URL of active tab of window 1
            set t to title of active tab of window 1
            return "URL: " & u & " | Title: " & t
        end if
    end tell
    '''
    # ... 执行并返回
```

### ❌ 失败：AppleScript 执行 JavaScript（Chrome 内部）

Chrome 需要开启「允许 Apple 事件中的 JavaScript」。即使开启后，从 Hermes 终端调用仍可能因 TCC 权限链问题失败。

```applescript
-- 这条需要 Chrome 开启设置，且可能仍报 -10006
tell application "Google Chrome"
    execute tab 1 of window 1 javascript "document.title"
end tell
```

### ❌ 失败：Playwright CDP 连接用户已有 Chrome

Chrome 必须带 `--remote-debugging-port=9222` 启动。但 Hermes 自动化启动的 Chrome 无法绑定调试端口（macOS 沙箱限制）。只能用户手动启动。

**已验证：用户手动在终端执行启动命令后，CDP 可连接。**

### ✅ 可用：Playwright 启动独立 Chromium 实例（不依赖调试端口）

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    chrome = p.chromium.launch(headless=False, args=['--disable-gpu'])
    page = chrome.new_page()
    page.goto('https://chatgpt.com/')
    # 找输入框
    inp = page.locator('textarea').first
    inp.fill('问题内容', force=True)
    page.keyboard.press('Enter')
```

⚠️ 独立实例 = 独立 profile = 无登录态。需要重新登录。

## 结论

| 需求 | 方案 |
|------|------|
| 操控用户已有的登录态 Chrome | AppleScript `open location`（仅跳转，无法读写页面内容）|
| 读 Chrome URL/标题 | AppleScript ✅ |
| 读写页面内容（填表单/点击/抓数据）| Playwright 新实例 或 CDP（需用户手动开调试端口）|
| 复现用户 Chrome 登录态 | Playwright + `storage_state` 导出 cookie |
