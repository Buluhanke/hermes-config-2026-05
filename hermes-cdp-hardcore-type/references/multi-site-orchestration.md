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
- deepseek: textarea, 1个, AX回复 2000+ 字符
- doubao: textarea, 2个 (选 placeholder 有值的)
- gemini: contenteditable (ql-editor), 偶发
- grok: contenteditable (tiptap), 偶发
- chatgpt: contenteditable (ProseMirror), 难 (ProseMirror事件复杂)
- chatglm: 偶尔能, 大多失败

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
