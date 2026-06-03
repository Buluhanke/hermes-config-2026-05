# Doubao (豆包) CDP 发送突破 — 2026-06-03 实测

## 根因
ByteDance `sync-input-engine-infra-interactive` (Semi Design + React 18) 维护独立于 React 的内部状态。`ta.value=` + `dispatchEvent` 方式被 Semi Design 的 debounce 拦截，发送按钮始终 disabled。

## ✅ 成功方案（2026-06-03 验证）

### 步骤 1：`Input.insertText` 灌入问题
```python
# 1. 先聚焦 textarea
await cdp.send("Runtime.evaluate", {
    "expression": "document.querySelector('textarea').focus()"
})
# 2. 用 insertText 填入完整问题（触发 keydown→char→keyup 事件链）
await cdp.send("Input.insertText", {"text": question})
# 3. 验证 textarea 有内容
r = await cdp.send("Runtime.evaluate", {
    "expression": "document.querySelector('textarea').value.length"
})
# 期望: question 字符数（如 76）
```

**为什么 insertText 有效**：insertText 产生真实的 keydown/keyup/char DOM 事件链，React 的 `__reactFiber$***` 能监听到，触发 Semi Design 内部的 `handleChange` → 状态更新。

### 步骤 2：点击发送按钮
```python
# 豆包的发送按钮不是 <button>，是 <div class="send-btn-wrapper">
# 坐标点击（最稳定的兜底方式）
await cdp.send("Input.dispatchMouseEvent", {
    "type": "mousePressed",
    "x": 1472, "y": 820,
    "button": "left", "clickCount": 1
})
await cdp.send("Input.dispatchMouseEvent", {
    "type": "mouseReleased",
    "x": 1472, "y": 820,
    "button": "left", "clickCount": 1
})
```

## ✅ 成功断言（必须全部满足）

| 信号 | 预期值 | 含义 |
|------|--------|------|
| `ta.value` → 0 | 0 | 文本已发送（被清空） |
| URL 跳转 | `/chat/38428871089839106` | 新对话创建（≠ `/chat/`） |
| `body.innerText` 增长 | 610 → 3158+ | 回复生成中 |
| 等待时间 | 30-60s | xAI 流式生成需时间 |

**DO NOT abort early**：DeepSeek 的流式响应在 `body.innerText` 里可能只显示对话标题 30-60 秒，之后 SSE stream 才完成。保持轮询直到 `bodyLen` 稳定 10 秒。

## ❌ 已验证失效的方案

1. `ta.value = 'text'` + `dispatchEvent(input/change)` — Semi Design 拦截
2. `__reactProps.onChange()` 调用 — `event.target` undefined 导致崩溃
3. `Input.dispatchKeyEvent` Enter — 按钮未激活时不触发发送
4. `click()` 直接点按钮 — 按钮找到但发送未生效（React 状态未更新）

## 输入框选择器

豆包有 2 个 textarea（第 2 个是隐藏的搜索框），必须选对：
```javascript
// ✅ 正确：选可见的、非只读的、有 placeholder 的
document.querySelectorAll('textarea').forEach(ta => {
    if (!ta.readOnly && ta.offsetParent !== null && ta.placeholder) {
        ta.focus();
    }
})

// ❌ 错误：直接 querySelector('textarea') 可能选到搜索框
```

## 相关文件
- `/tmp/doubao_deepseek_automation_notes.md` — 豆包/DeepSeek 早期技术笔记
- `/tmp/hermes_bot_chatgpt_20260603.txt` — ChatGPT 回复存档（同类问题参考）
