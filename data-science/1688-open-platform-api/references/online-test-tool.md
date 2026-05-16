# 1688 Open Platform — Online Test Tool (在线测试工具)

Session: 2026-05-05. Discovered during 1688 API documentation exploration.

## Test Tool URL

The "在线测试工具" button on API doc pages opens a **new browser tab** with URL:

```
https://open.1688.com/api/apiTool.htm?ns=<namespace>&n=<api_name>&v=<version>
```

Example for `alibaba.category.attribute.get`:
```
https://open.1688.com/api/apiTool.htm?ns=com.alibaba.product&n=alibaba.category.attribute.get&v=1
```

## Page Structure

The test tool page contains 2 iframes:
1. **Main iframe** (same origin) — contains the page shell
2. **Console iframe** — `https://gw.open.1688.com/console/index.html?from=aop&lang=cn&namespace=...&api=...&version=...` — **this is where the actual form lives**

## Test Form Fields (inside the iframe)

| Input ID/Label | Type | Required | Description |
|----------------|------|----------|-------------|
| `#appkey` | text | Yes | ISV application key |
| `#signkey` | text | Yes | App secret (签名密钥) |
| Access Token | text | Yes | OAuth2 access token (获取 Token button generates it) |
| Refresh Token | text | No | Token refresh token |
| 会员ID | text | No | Member ID |
| 客户端超时 | number | No | Client timeout in ms (default: 5000) |
| * categoryID (Long) | text/number | Yes | Leaf category ID |
| * webSite (String) | text | Yes | `"1688"` or `"alibaba"` |
| scene (String) | text | No | Scene value (empty or "processing") |

## Test Form Buttons

| Button | Function |
|--------|----------|
| 调用API | Execute the test API call |
| 签名工具 | Open signature generation tool |
| 提交问题 | Submit support issue |
| 获取 Token | Generate OAuth2 access token |
| 刷新 Token | Refresh access token |
| 重置 | Reset the form |

## Playwright Automation

```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Step 1: Open the doc page
    page.goto("https://open.1688.com/api/apidocdetail.htm?aopApiCategory=category_new&id=com.alibaba.product%3Aalibaba.category.attribute.get-1")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Step 2: Click "在线测试工具" -- opens a new tab
    test_btn = page.locator("text=在线测试工具").first
    test_btn.click()
    time.sleep(2)
    
    # Step 3: Switch to the new tab
    pages = context.pages
    assert len(pages) > 1  # 在线测试工具 opens new tab
    test_tab = pages[1]  
    test_tab.wait_for_load_state("networkidle")
    time.sleep(3)
    
    # Step 4: Find the console iframe
    target_frame = None
    for f in test_tab.frames:
        if "gw.open.1688.com/console" in f.url:
            target_frame = f
            break
    
    if target_frame:
        # Step 5: Fill in the form
        target_frame.locator("#appkey").fill("your_app_key")
        target_frame.locator("#signkey").fill("your_app_secret")
        
        # Fill categoryID and webSite (may need to locate by label structure)
        # ...
        
        # Step 6: Click "调用API"
        target_frame.locator("button").filter(has_text="调用API").click()
        time.sleep(5)
        
        # Step 7: Read results
        result_text = target_frame.evaluate("document.body.innerText")
        print(result_text)
```

## Key Findings

1. **The form is in an iframe from a different origin** — always check `page.frames` to find it
2. **The test tool opens in a NEW TAB** — use `context.pages` to switch
3. **You must be logged into 1688** in the Playwright browser for this to work
4. **`page.content()` returns raw React HTML** — always use `page.evaluate("document.body.innerText")`
5. **Iframe has no `.screenshot()` method** — screenshot from main page instead
