# AI 站点免 OCR 读取屏幕内容方案（2026-06-02 实测）

## 问的问题
> "我们电脑配置免费不要OCR能直接读取屏幕内容吗"

## 背景约束
- 不使用 OCR（光学字符识别）
- 使用 Mac Mini 24GB 配置
- 追求免费、本地化方案

---

## 三大免 OCR 机制（来源：ChatGLM 2026-06-02）

### 机制1：辅助功能 API（UI 自动化）
操作系统知道它正在渲染什么文本/元素。屏幕阅读器使用这一机制，从 DOM/可访问性树读取，而非从像素读取。

**优点**：免费、内置、不需要 OCR、准确读取文本  
**缺点**：不是面向普通用户的直接"复制粘贴"工具，而是用于自动化或无障碍用途

**工具**：
- Windows：`PowerShell + UIAutomation`，或 Windows 讲述人
- macOS：`Accessibility API`（Hermes 正在使用的方案）

### 机制2：剪贴板 / API
如果应用程序提供 API 或标准文本选择，可以直接复制它。

**适用场景**：PDF、视频字幕、游戏 UI 等无法直接选中的内容

### 机制3：源代码 / 结构树抓取
对于网页：直接读取 HTML（DOM）  
对于应用程序：读取内存或 UI 框架树（如 MSAA/UIA）

**工具**：
- 网页：浏览器开发者工具、F12、扩展程序（如 SimpleAllowCopy）
- Windows 应用：`Inspect.exe`（Windows SDK）或 AutoHotkey 中的 UIA 函数

---

## 各站实测结果

| 站点 | 是否免 OCR 可行 | 方案 | 回复质量 |
|------|--------------|------|---------|
| **DeepSeek** | ✅ | DOM `.ds-markdown` selector | "自主、感知、执行" |
| **ChatGLM** | ✅ | textarea + direct value + innerText | 三种机制完整分析 |
| **豆包** | ✅ | textarea + direct value | 有历史残留 |
| **Gemini** | ❌ | webview 跨域限制 | - |
| **ChatGPT** | ⚠️ | ProseMirror 受限 | 旧回答残留 |
| **Grok** | ❌ | Cloudflare 拦截 | - |

---

## Hermes CDP 方案总结

**读取（免 OCR）**：
1. `Runtime.evaluate` + DOM selector（最快，最干净）
2. `Accessibility.getFullAXTree`（Shadow DOM 会阻挡）
3. 截图 + Vision 模型（备选）

**输入（免逐字打字）**：
- `ta.value = 'text'` + `dispatchEvent(new Event('input', {bubbles:true}))`（推荐）
- 发送：`Input.dispatchKeyEvent(key='Enter')`（穿透，不依赖按钮）

**完成信号**：
- `document.body.innerText.length` 单调增长停止

---

## 关键教训

- **直接 value 注入**比逐字打字快 10 倍（用户明确反馈"模拟人工打字速度太慢"）
- **Enter 穿透**比按钮点击更稳定（Shadow DOM 无法 .click()）
- **bodyLen 增长**是判断 AI 是否还在输出的最可靠信号
- **新标签页**比旧标签页更容易读取 AX 树（新鲜 tab 无 Shadow DOM 阻挡）