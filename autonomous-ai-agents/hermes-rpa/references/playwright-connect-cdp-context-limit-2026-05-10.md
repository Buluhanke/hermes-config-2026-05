# Playwright connect_over_cdp 上下文限制（2026-05-10）

## 问题

在 aimac 上尝试用 Playwright `connect_over_cdp()` 连接已有 Chrome 调试实例：

```python
from playwright.sync_api import sync_playwright
browser = p.chromium.connect_over_cdp("http://127.0.0.1:9333")
```

报错：
```
playwright._impl._errors.Error: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported.
```

## 分析

- WebSocket 连接成功（`ws://127.0.0.1:9333/devtools/browser/...` 建立）
- Chrome 本身支持 CDP 调试端口
- Playwright 尝试调用 `Browser.setDownloadBehavior` 时被拒绝
- 这是 Chrome 调试协议的安全限制：**通过 CDP 连接时，Playwright 不能管理 context**（创建/关闭 context）

## 结论

**不能用 `playwright.connect_over_cdp()` 往已有 Chrome 上挂载 Playwright session。**

可行方案：
1. **Hermes browser 工具**（`browser_navigate` 等）→ 内部走 `connect_over_cdp`，但工具层面不暴露 context 管理操作
2. **直接用 CDP HTTP API** → `http://127.0.0.1:9333/json/new` 新建 target，然后 WebSocket 直连操作该 target
3. **hermes-rpa 截图+OCR** → 完全不依赖 Playwright，AppleScript + cliclick + Baidu OCR

## 验证命令

```bash
# Chrome 调试端口正常监听
lsof -i :9333 | grep Google

# HTTP API 可用（但返回空列表因为没有 page target）
curl -s http://127.0.0.1:9333/json

# 版本信息正常
curl -s http://127.0.0.1:9333/json/version
```
