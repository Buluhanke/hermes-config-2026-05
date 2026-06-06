# 物理外挂键盘破解（AppleScript Bypass）
**日期**: 2026-06-03  
**验证**: Gemini ✅ 成功，Grok ❌ 失败

---

## 原理

当 `Input.dispatchKeyEvent` 的 `nativeVirtualKeyCode: Int32` 字段缺失时，Angular zone.js / Next.js React 的事件链在框架层断裂，事件被静默丢弃。

`computer_use` 的 AppleScript 路径：
```
AppleScript keystroke → Mac OS 硬件事件 → Chrome 渲染器 → 原生事件处理器
→ InputManager → WebKit 编辑器 → 框架事件（zone.js/React）
```
绕过了 CDP 协议的 Int32 字段限制。

---

## Gemini 破解步骤（✅ 成功）

```python
# 1. 激活标签页
browser_cdp(method="Target.activateTarget", params={"targetId": "A29DBE7C..."})

# 2. focus Quill 编辑器
browser_cdp(method="Runtime.evaluate",
    params={"expression": "document.querySelector('.ql-editor')?.focus()",
            "returnByValue": True},
    target_id="A29DBE7C...")

# 3. 写入剪贴板
terminal(command='echo -n "Mac屏幕OCR本地免费方案有哪些？" | pbcopy')

# 4. 物理粘贴 + 回车（via computer_use AppleScript）
computer_use(action="key", keys="cmd+v")   # 粘贴
computer_use(action="key", keys="return") # 发送
```

**验证结果**: Gemini 收到完整 18 字符问题，生成 1800+ 字符回复（Live Text、快技指令、Pearl OCR、Screenpipe、PaddleOCR 等方案）。

---

## Grok 破解尝试（❌ 失败）

**同样步骤**在 Grok 上失败。根因：

| 特征 | Grok | Gemini |
|------|------|--------|
| textarea 真实高度 | 16px，y=0（CSS隐藏） | 正常 |
| React fiber | 无 `__reactProps` | N/A |
| form.submit() 结果 | 返回 "submitted" 但静默失败 | N/A |
| 失败机制 | DOM value 写入了但 React state 未更新 | zone.js 事件链断裂 |

Grok 的 textarea 是 plain HTML，`nativeInputValueSetter` 设置 value 后不触发 React onChange，所以 Grok 的状态机认为 textarea 为空，submit 按钮始终 disabled。

**物理按键只写入 DOM，不写入 React 状态**——这与 Gemini 的 zone.js 问题本质不同。

---

## 适用条件

物理外挂有效的网站特征：
- Quill / Angular zone.js 编辑器（`Input.dispatchKeyEvent` 失效）
- 前端框架通过 `nativeVirtualKeyCode` 做事件来源验证

物理外挂无效的网站特征：
- plain HTML textarea + React controlled input（Grok）
- textarea DOM value 变化不触发 React onChange（需要 `__reactProps.$onChange` 合成事件）

---

## 决策树

```
CDP Input.dispatchKeyEvent / insertText 失败？
  ↓ 是
网站是 Quill/Angular zone.js 编辑器？
  ↓ 是 → 用 computer_use（Cmd+V + Return）✅
  ↓ 否
网站是 plain HTML textarea + React？
  ↓ 是 → 需要 React fiber 注入或进入 iframe 内部 ❌
  ↓ 否
  → 尝试其他 input 策略
```
