---
name: hermes-vision-agent
description: "视觉感知 + 桌面/浏览器控制。Phase 2 核心：看→想→做→验证闭环。"
---

# hermes-vision-agent

## 当前架构（2026-06-01）

**VLM不再必要。** 浏览器用DOM+LLM，桌面用AX树+OCR，VLM是可选补充。

```
浏览器:
  browser_snapshot (DOM, 8ms) → LLM理解 → browser_click/type 执行

桌面:
  Apple Vision OCR (60-240ms) 或 AX树 → LLM判断 → human_click 执行

验证:
  browser_snapshot 对比 或 SSIM (5ms) 或 LLM第二次分析
```

## 浏览器自动化（主力方案）

**不需要截图，不需要VLM，不需要Ollama。**

**ReAct工作循环实测（2026-06-01）：**
- Playwright启动Chrome：0.1s（`channel='chrome'`）
- DeepSeek响应：0.8s
- 表单填写+提交：1步完成
- 1688搜索：遇到滑块验证码（ddddocr可用，待集成）

**进化框架**：任务池(cron 09:00) → 自我优化(cron 02:00) → 结果存日志 → 自我修复 → 汇报

**脚本**：`~/.hermes/scripts/hermes_react_loop.py`

```python
# 安装
pip3 install playwright
playwright install chromium

# 用系统Chrome（推荐），避免Playwright自带浏览器版本冲突
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel='chrome')
    page = browser.new_page()
    page.goto(url, wait_until='domcontentloaded')
    
    # 获取页面信息
    title = page.title()
    inputs = page.evaluate('() => Array.from(document.querySelectorAll("input")).map(i => i.name)')
    
    # 操作
    page.fill('input[name="custname"]', '值')
    page.click('button')
```

### Playwright版本冲突处理

macOS上容易出现多个Playwright版本（1.58.0/1.59.1/1.60.0）：
- 用 `channel='chrome'` 绕过版本问题，直接接系统Chrome
- 不要用 `playwright install chromium` 装浏览器，用系统Chrome更稳定
- 验证：`playwright install --list` 看哪个版本驱动匹配哪个浏览器

### ReAct循环脚本

参考脚本：`~/.hermes/scripts/hermes_react_loop.py`

```
感知(DOM) → 理解(DeepSeek 0.8s) → 执行(playwright) → 验证
```

## 桌面应用控制

| 工具 | 适用场景 | 状态 |
|------|---------|------|
| PyAutoGUI | 基础鼠标键盘 | ✅ hermes venv |
| je_auto_control | AX树定位+精确点击 | ✅ Homebrew Python |
| Apple Vision OCR | 屏幕文字识别(60ms) | ✅ Homebrew Python |
| PaddleOCR | 中文高精度OCR | ✅ hermes venv |

## 搜索能力

| 工具 | 状态 | 说明 |
|------|------|------|
| ddgs | ✅ | DuckDuckGo搜索，pip install ddgs |
| hermes web_search | ✅ | 内置搜索 |
| SearXNG (Docker) | ❌ | Docker已停，不恢复 |

## 已停用的依赖

- **Ollama 本地VLM** — ❌ 退出，不需要本地备用模型。浏览器DOM+LLM足够
- **Docker (Colima)** — ❌ 彻底停用。hindsight→holographic，searxng→ddgs
- **cua_driver** — ❌ 未装，Playwright+PygAutoGUI替代
- **browser-use** — ❌ 框架太重，用Playwright直连

## 已知限制

- Chrome GPU合成层 → 截图全失败 → 用browser_snapshot (DOM) 替代
- 文件对话框 → 需要人工介入
- Gemini API视觉 → 网络墙不可靠
