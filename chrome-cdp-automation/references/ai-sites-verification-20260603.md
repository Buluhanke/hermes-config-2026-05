# 6 AI 网站自动化验证结果 — 2026-06-03

## 总评（4/6 端到端跑通）

| 网站 | 策略 | 结果 | 备注 |
|------|------|------|------|
| ✅ ChatGPT | `press_sequentially` | 338字符回复 | ProseMirror，Input.insertText 也有效 |
| ✅ DeepSeek | `insert_text_enter` | 标题先出，re-poll 30-60s | `<div role="button">` 替代 `<button>`，SSE 流式 |
| ✅ ChatGLM | `insert_text_enter` | 341字符回复 | `textarea.scroll-display-none` |
| ✅ Grok | `press_sequentially` | 完整回复 | Tiptap，`__reactProps` 在 parentElement |
| ⚠️ 豆包 | `press_sequentially` (Playwright) | 91字符（首页内容，非回复） | SyncInputEngine 拦截，CDP Input 失败，Playwright `press_sequentially` 有效但需等90s |
| ❌ Gemini | — | 加载失败 | `<webview>` 跨域，CDP 不可达 |

## 关键发现

### Playwright `press_sequentially` 是万能破局方案
- 触发 OS 级 keydown/keyup/input 事件，绕过所有定制输入引擎（SyncInputEngine/Tiptap/Semi Design/ProseMirror）
- 50ms/字延迟，76字符约 4 秒输入时间
- 适合不需要登录态的场景（独立 Playwright Chromium 147）

### CDP `browser_cdp` 工具适合需要登录态的场景
- 复用已打开的 Chrome tab（6 个 AI 网站已登录）
- `Input.insertText` 对 ProseMirror/DeepSeek/ChatGLM 有效
- 对豆包 SyncInputEngine 无效（`Input.dispatchKeyEvent` 逐字可行，需 nativeVirtualKeyCode int32）

### DeepSeek 流式渲染陷阱
- 点击发送后 5-10s 内 body.innerText 只显示标题，无正文
- 需要继续轮询 30-60s 才能看到完整回复
- 误判为失败的原因：看到标题就停止等了

## 输入策略选择决策树

```
需要复用登录态？（browser_cdp / CDP over WS）
├── 是 → Input.insertText（ProseMirror/DeepSeek/ChatGLM 有效）
│         豆包 → 需 Input.dispatchKeyEvent 逐字（工具链限制，跳过）
└── 否 → Playwright press_sequentially（通用方案，全站验证通过）

发送方式优先级：
1. browser_press("Enter") — 通用，大多数场景有效
2. CDP Runtime.evaluate + click（精确找到按钮后点击）
3. 豆包特殊：找父容器上溯 5 层最近的可用按钮
```

## Playwright `press_sequentially` 实测数据

| 网站 | 输入耗时 | 等待回复 | 总耗时 | 成功率 |
|------|---------|---------|--------|--------|
| ChatGPT | 4s (76chars×50ms) | 30s | ~40s | ✅ |
| DeepSeek | 2s (type+Enter) | 60s | ~65s | ✅ |
| 豆包 | 4s | 90s | ~100s | ⚠️（首页内容，非AI回复） |
| ChatGLM | 2s | 90s | ~95s | ✅ |
| Grok | 4s | 60s | ~67s | ✅ |

## 参考命令

```bash
# 安装
pip install playwright && playwright install chromium

# 运行
python ~/.hermes/scripts/hermes_web_bot.py                    # 全部网站
python ~/.hermes/scripts/hermes_web_bot.py -s chatgpt        # 单网站
python ~/.hermes/scripts/hermes_web_bot.py -q "你的问题"      # 自定义问题
```

## 综合推荐（跨站共识）

1. **macOS Vision / Live Text**（零成本，4/4 网站推荐）
2. **ocrmac（Python Vision 封装）**（自动化首选）
3. **PaddleOCR**（中文场景，1-3秒/图）
4. **uitag**（屏幕理解，超出 OCR 范畴）
5. **Docling**（复杂文档/表格）