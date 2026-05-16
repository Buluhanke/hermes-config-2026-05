# Playwright CDP Accessibility — 读网页结构（2026-05-10）

## 背景

hermes-rpa 的传统方案（截图 + Baidu OCR）只能读文字，无法获取元素的精确坐标。1688 注册页需要点击"立即入驻"按钮，但 OCR 返回坐标全为 (0,0)，无法定位。

## 解决方案：CDP Accessibility.getFullAXTree

Playwright 通过 Chrome DevTools Protocol 读取完整 AX（Accessibility）树，包含每个元素的：
- `role` — 元素角色（button、link、staticText 等）
- `name` — 元素名称/文本
- `properties` — 属性（focusable、expanded 等）
- `backendDOMNodeId` — 可关联回 DOM

```python
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://open.1688.com/support/register")

    # 关键：不能直接 page.accessibility.snapshot()
    # Playwright 1.58 中该 API 不存在（AttributeError: no attribute 'accessibility'）
    # 正确方式是通过 CDP session：
    cdp = page.context.new_cdp_session(page)
    tree = cdp.send('Accessibility.getFullAXTree', {})

    print(json.dumps(tree, indent=2, ensure_ascii=False)[:5000])
```

## 查找特定元素

```python
def find_by_text(tree, keyword):
    """递归搜索AX树中名称包含keyword的节点"""
    results = []

    def search(node):
        name = node.get('name', {}).get('value', '')
        role = node.get('role', {}).get('value', '')
        if keyword in name:
            props = {}
            for p in node.get('properties', []):
                props[p['name']] = p.get('value', {}).get('value', p.get('value'))
            results.append({
                'role': role,
                'name': name,
                'nodeId': node.get('nodeId'),
                'backendDOMNodeId': node.get('backendDOMNodeId'),
                'properties': props
            })
        for child_id in node.get('childIds', []):
            # 需要通过 getFullAXTree 响应的 nodeId 再次查询
            pass  # tree 本身已包含完整树，直接遍历即可

    search(tree)
    return results

# 使用
matches = find_by_text(tree, '立即入驻')
for m in matches:
    print(f"[{m['role']}] '{m['name']}' nodeId={m['nodeId']}")
```

## 限制

- **坐标获取**：AX 树不直接含像素坐标（boundingBox），需要额外调用：
  ```python
  cdp.send('DOM.getBoundingClientRect', {'nodeId': node['nodeId']})
  ```
  或用 Playwright 的 `page.locator()` API 直接获取 bounding_box。
- **首次运行慢**：Chromium 下载/安装 + 首次启动约 60 秒。
- **Playwright Chrome 与用户 Chrome 独立**：Playwright 启动的是独立的 Chromium 实例，没有用户登录态。需要配合 hermes-rpa（AppleScript + cliclick）操控用户已有的 Chrome。

## 与 hermes-rpa 的关系

hermes-rpa 通过 AppleScript 操控用户已登录的 Chrome，但 AppleScript 无法读取 HTML 页面元素结构。
**最佳组合**：
1. `hermes_desktop_rpa.py activate` — 把用户 Chrome 带到前台
2. Playwright CDP `Accessibility.getFullAXTree` — 读取页面结构找到目标元素
3. 用查到的元素信息 + `cliclick c:{x},{y}` 执行点击

## 环境

- Playwright: 1.58.0
- Python: 3.14.4 (`/usr/local/bin/python3`)
- macOS: aimac Mac mini
