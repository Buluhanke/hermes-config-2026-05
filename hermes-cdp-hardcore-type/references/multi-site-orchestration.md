# 多AI站点对比 (Multi-Site AI Compare)

## 场景
同一问题扔给 N 个 AI 站点, 收集所有回复做对比 (省手动切换/复制粘贴).

## 站点配置
```python
SITES = {
    "gemini":   {"match": ["gemini"],   "input_type": "contenteditable"},
    "doubao":   {"match": ["doubao"],   "input_type": "textarea"},
    "chatglm":  {"match": ["chatglm"],  "input_type": "textarea"},
    "deepseek": {"match": ["deepseek"], "input_type": "textarea"},
    "chatgpt":  {"match": ["chatgpt"],  "input_type": "contenteditable"},
    "grok":     {"match": ["grok"],     "input_type": "contenteditable"},
}
```
注意: ChatGPT/ChatGLM/Gemini/Grok 用 ProseMirror/tiptap/ql-editor, 是 contenteditable
而非 textarea. 自动聚焦逻辑必须两种都支持.

## Tab ID 失效对策
CDP HTTP `/json` 列出的 `webSocketDebuggerUrl` 对应的 tab id 每次启动会变.
**必须**: 每次脚本运行时重新调用 `http://localhost:9333/json` 拿当前 tabs,
按 `match` 字符串 (title 或 url 包含) 选最近的一个.

## 批量建 tab
用 `Target.createTarget` 一次性建多个 (依赖 background_page tab 的WS):
```python
async with websockets.connect(any_ws_url) as ws:
    for name, url in URLS:
        await send("Target.createTarget", {"url": url})
```

## 已知稳定的 6 站点
- **deepseek**: textarea, ✅ 完整跑通，回复 "自主、感知、执行"
- **doubao**: textarea, ✅ 能输入发送，新标签页有时无回复（旧标签历史残留）
- **chatglm**: textarea, ✅ 完整跑通，回复三种免OCR机制（辅助功能API/剪贴板+API/DOM抓取）
- **grok**: contenteditable (tiptap), ❌ Cloudflare 人机验证完全拦截
- **chatgpt**: contenteditable (ProseMirror), ⚠️ 输入框存在但 focus 受限，新问题发送失败
- **gemini**: contenteditable (ql-editor) 在 webview iframe 里, ❌ 跨域拿不到 textarea

## 快速输入：direct value 注入（推荐替代逐字输入）
```javascript
// 在 Runtime.evaluate 里执行，比逐字打字快 10 倍
ta.value = '问题内容';
ta.dispatchEvent(new Event('input', {bubbles:true}));
ta.dispatchEvent(new Event('change', {bubbles:true}));
```
适用：DeepSeek ✅、豆包 ✅、ChatGLM ✅
不适用：ChatGPT（ProseMirror 受控）、Gemini（webview 跨域）

## 进化二: 用 vision_click 解决"每站 selector 不同"
传统做法: 维护 6 套 selector, 站点改版全挂.
vision_click 做法: **关键词+坐标**, 站点改版也能用 (只要 UI 文字不变).

实战: DeepSeek "开启新对话" 按钮 `coord="130,90"` 一击必中, 不需要知道 class.
但关键词匹配会被侧边栏聊天列表干扰 (10+ 个 "新对话"), 优先用坐标兜底.

详见: `references/vision-click.md`

## 回复读取优先级
1. **天眼模式 (Network拦截)** - 拿服务器原始流, 最干净
2. **AX树 (Accessibility.getFullAXTree)** - 零OCR, 但 Shadow DOM读不到
3. **截图 + Vision模型** - 万能但慢

详见: hermes-cdp-hardcore-type 技能
