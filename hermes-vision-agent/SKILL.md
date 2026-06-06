---
name: hermes-vision-agent
description: "视觉感知 + 桌面/浏览器控制。Phase 2 核心：看→想→做→验证闭环。"
---

# hermes-vision-agent

## 当前架构（2026-06-01）

**VLM不再必要。** 浏览器用DOM+LLM，桌面用AX树+OCR，VLM是可选补充。

**优先级（用户指定，2026-06-02）：**
1. 浏览器自动化（Browser Use）
2. 电脑桌面控制（Computer Use）
3. 视觉感知闭环（看→懂→做→验证）
~~音频~~ ~~视频~~ ~~语音AI~~ — 不碰

```
浏览器:
  browser_snapshot (DOM, 8ms) → LLM理解 → browser_click/type 执行

桌面:
  Apple Vision OCR (60-240ms) 或 AX树 → LLM判断 → human_click 执行

验证:
  browser_snapshot 对比 或 SSIM (5ms) 或 LLM第二次分析
```

## 真实世界Browser Use / Computer Use SOTA数据

**当前SOTA（gentic.news 2026-04）：**
- OSWorld SOTA：Claude Sonnet 4.5 达 62.9%，**首个超人类基准(72.4%)**
- 最强开源：Kimi K2.6 达 73.1%
- 浏览器Agent：Surfer 2 WebVoyager 97.1%
- 代码Agent：Claude Opus 4.7 SWE-Bench Pro 64.3%
- 12个模型已在SWE-Bench Verified超越人类

详见 `references/browser-use-sota.md`

## 浏览器自动化（主力方案）

**不需要截图，不需要VLM，不需要Ollama。**

**ReAct工作循环实测（2026-06-01）：**
- Playwright启动Chrome：0.1s（`channel='chrome'`）
- DeepSeek响应：0.8s
- 表单填写+提交：1步完成
- 1688搜索：滑块验证码 → `slide-solver` skill 走 ddddocr 识别 + 仿人轨迹

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
| je_auto_control | AX树定位+精确点击 | ⚠️ 仅Homebrew Python，hermes venv无 |
| Apple Vision OCR | 屏幕文字识别(60ms) | ✅ Homebrew Python |
| PaddleOCR | 中文高精度OCR | ✅ hermes venv |
| **ddddocr** | **滑块/点选验证码识别 + 仿人轨迹** | ✅ **2026-06-04 已装**（85MB+66MB onnxruntime，详见 `slide-solver/` 子技能） |

### AI聊天网站状态
详见 `references/ai-chat-sites-status.md` — 各平台登录态限制和Bing搜索替代方案

## 搜索能力

| 工具 | 状态 | 说明 |
|------|------|------|
| ddgs | ✅ | DuckDuckGo搜索，pip install ddgs |
| hermes web_search | ✅ | 内置搜索 |
| SearXNG (Docker) | ❌ | Docker已停，不恢复 |

## 已停用的依赖

- **Ollama 本地VLM** — ❌ 退出，不需要本地备用模型。浏览器DOM+LLM足够
- **Docker (Colima)** — ❌ 彻底停用。hindsight→holographic，searxng→ddgs
- **browser-use** — ❌ 框架太重，用Playwright直连
- **cua_driver** — ⚠️ 已装运行中（`mcp_cua_driver_*` 工具链），闲置时空转 ~45% CPU，受 30 分钟空闲回收规则管理（见 `~/.hermes/scripts/idle_killer.sh`）

## 已知限制

- Chrome GPU合成层 → 截图全失败 → 用browser_snapshot (DOM) 替代
- 文件对话框 → 需要人工介入
- Gemini API视觉 → 网络墙不可靠

### AI聊天网站登录态限制（2026-06-01发现，2026-06-02更新）

**问题**：Playwright启动的是干净浏览器实例，没有用户Chrome的cookies和session。

豆包、ChatGLM、DeepSeek、ChatGPT等AI网站：
- 打开后显示"登录"按钮或需要手机验证
- AI对话功能不可用（显示转圈但无回复）

**Shadow DOM / 懒加载导致DOM查询失效（2026-06-02更新）**：
- ~~DeepSeek、ChatGLM、豆包等使用 Shadow DOM + 懒加载~~
- ~~`browser_snapshot` 读不到AI对话内容，即使登录态正常也不行~~
- ~~CDP `Runtime.evaluate` 对这些tab返回空text nodes~~
- **已解决**：Accessibility.getFullAXTree 对所有AI站点的Shadow DOM完全可用，返回285节点（DeepSeek），可读取对话历史链接/输入框/模式选择等所有内容

**computer_use capture返回0x0的原因（已澄清）**：
- 不是Chrome GPU问题，是活动标签是`about:blank`
- 切换到AI站点标签后，screencapture能完整捕获页面内容

**当前解法（按优先级）**：
1. **Accessibility.getFullAXTree（推荐）** — 直接读取浏览器Accessibility Tree，~50ms，无OCR，Chrome原生API
2. **CDP Runtime.evaluate + JS** — 直接执行JS读innerText/DOM
3. **screencapture + 视觉模型读取** — 切到AI站点标签 → 截屏 → 视觉模型分析（MiniMax不支持，需Claude/Gemini）
4. **CDP直接注入（无回复需求时）** — 向已登录站点的输入框写内容并发送

**不要做的事**：
- 不要花时间调 `browser_vision` — API key无效，短期内无法修复
- 不要依赖CDP `Page.captureScreenshot` — Chrome GPU合成层返回空（但Accessibility Tree不受影响）
- 不要用当前MiniMax模型分析截图 — 不支持图片输入（纯文字模型）
