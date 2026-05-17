---
name: browser-testing-with-devtools
description: 浏览器测试与DevTools调试 — 用Chrome DevTools Protocol和Playwright进行浏览器自动化测试。
triggers:
  - "需要自动化测试Web应用"
  - "需要调试JavaScript"
  - "需要分析网络请求"
  - "需要截取屏幕或DOM快照"
  -
version: 1.0.0 "需要绕过反爬或登录验证"
---

# Browser Testing with DevTools

## Overview

浏览器测试是端到端验证的终极形式。DevTools Protocol和Playwright让浏览器自动化测试成为可能——从简单的点击测试到复杂的用户流程验证。

## When to Use

- 端到端测试（用户真实流程）
- 登录态保留的自动化操作
- 截图和视觉验证
- 网络请求分析和修改
- JavaScript调试
- 反爬虫绕过（合法用途）

## Process

### Phase 1: 环境准备

#### 1.1 Playwright安装
```bash
pip install playwright
playwright install chromium  # 或 firefox, webkit
```

#### 1.2 CDP连接已有Chrome
```python
# 连接已有的Chrome调试实例
browser = playwright.chromium.connect_over_cdp(
    "http://localhost:9333"
)
```

#### 1.3 Hermes Chrome配置
- 已有Chrome调试实例：端口9333，profile `~/.hermes/chrome-debug`
- CDP URL：`http://127.0.0.1:9333`

### Phase 2: 基础操作

#### 2.1 导航和点击
```python
page.goto("https://example.com")
page.click("#submit-button")
page.fill("input[name='username']", "user")
page.fill("input[name='password']", "pass")
page.click("button[type='submit']")
```

#### 2.2 等待元素
```python
# 等待元素出现
page.wait_for_selector("#result", state="visible", timeout=10000)

# 等待网络空闲
page.wait_for_load_state("networkidle")
```

#### 2.3 获取内容
```python
# 获取文本
text = page.inner_text(".result")

# 获取属性
href = page.get_attribute("a", "href")

# 获取HTML
html = page.inner_html(".container")
```

### Phase 3: CDP高级操作

#### 3.1 网络拦截
```python
def handle_route(route):
    if "analytics" in route.request.url:
        route.abort()  # 屏蔽分析请求
    else:
        route.continue_()

page.route("**/*", handle_route)
```

#### 3.2 执行JavaScript
```python
result = page.evaluate("""
    () => {
        return document.title;
    }
""")
```

#### 3.3 截取屏幕
```python
page.screenshot(path="screenshot.png", full_page=True)
```

### Phase 4: 调试技巧

#### 4.1 网络调试
```python
# 监听所有请求
page.on("request", lambda req: print(f"Request: {req.url}"))
page.on("response", lambda res: print(f"Response: {res.url} - {res.status}"))
```

#### 4.2 控制台日志
```python
# 获取控制台消息
page.on("console", lambda msg: print(f"Console: {msg.text}"))

# 注入console调试
page.evaluate("console.log('debug info')")
```

#### 4.3 错误捕获
```python
# 监听页面错误
page.on("pageerror", lambda err: print(f"Page error: {err}"))
```

### Phase 5: 最佳实践

#### 5.1 选择器优先级
1. `data-testid`（专用测试属性）
2. `role`和文本（语义化）
3. CSS类（稳定的话）
4. XPath（最后选择）

#### 5.2 等待策略
- 避免`sleep()`，使用等待条件
- 使用`networkidle`等待网络完成
- 使用`load`等待初始加载

#### 5.3 测试隔离
- 每个测试使用独立上下文
- 测试完成后清理状态
- 失败时截图保存

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "浏览器测试太慢" | 单元测试快但不能验证真实用户场景 | 分层测试，浏览器测试覆盖核心路径 |
| "手动测试就够了" | 手动测试不能回归 | 关键路径必须自动化 |
| "测试环境正常，生产不一定" | 说明环境差异是问题，不是跳过自动化的理由 | 缩小环境差异 |

## Red Flags

- 使用sleep()硬等待
- 使用不稳定的XPath
- 没有等待异步操作完成
- 测试之间没有隔离
- 失败后没有截图
- 选择器用易变的类名
- 隐藏元素被点击但期望生效

## Verification

验证清单：

- [ ] 测试使用专用选择器
- [ ] 没有硬编码sleep
- [ ] 等待条件明确
- [ ] 失败时截图
- [ ] 测试之间隔离
- [ ] 关键路径已覆盖
- [ ] CI中运行测试
