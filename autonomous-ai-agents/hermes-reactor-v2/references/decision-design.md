# 核心设计决策 — 反应堆 v2/v3

记录每个决策的"为什么"，便于未来回顾和新人 onboarding。

---

## 决策 1: 用 bodyLen 增长替代 stopBtn 作为"AI 正在输出"信号

### 选项对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| stopBtn 元素存在 | 语义清晰 | Shadow DOM 屏蔽，JS 拿不到 |
| Network 请求 pending | 准确 | 需要开启 CDP Network 域 |
| bodyLen 单调增长 | 通用、简单 | 需要记录上一周期值 |

### 最终选择
**bodyLen 增长**

### 理由
现代 AI 站（DeepSeek/豆包/ChatGPT）全部用 Shadow DOM 渲染 stopBtn。bodyLen 是最通用的信号：
- AI 输出文本 → bodyLen 增长
- AI 停止 → bodyLen 不增长
- 任何前端框架（React/Vue/Vanilla）通用

---

## 决策 2: 18 周期（36s）作为"真卡住"阈值

### 最终选择
**18 周期（36s）**

### 理由
DeepSeek R1 深度思考模式在 20-40s 之间。18 周期覆盖最坏情况，同时不会让用户等待超过 40s。

三重条件防止误判：
```python
if loading or body_len_growing: return False  # AI 在输出，不算卡
if self.state["stuck_cycles"] >= 18: return True  # 36s 阈值
if self.state["last_body_len"] == 0: return False  # 会话从没输出过 = 死了
```

---

## 决策 3: 状态锁 cooldown 防止重复触发

### 问题
每 2 秒一个循环，上一轮点击"发送"，下一轮又点 → 死循环。

### 解决方案
状态机：WAITING 状态只允许"等 AI 输出"，即使看到发送按钮也不点。

```python
ACTION_LOCK_COOLDOWN = {
    "CLICK_SEND": 5,      # 发送后 5s 不再发
    "TYPE_MESSAGE": 2,    # 输入后 2s 不重复
    "RECREATE_TAB": 10,   # 重建后 10s 冷却
}
```

---

## 决策 4: Enter 兜底发送

### 问题
某些 AI 站（DeepSeek）没有可见的"发送"按钮，只有 textarea。

### 解决方案
1. 找按钮（严格匹配 `t === '发送'`，按宽度排序选最小）
2. 找不到 → `focus_textarea()` + `dispatch_key("Enter")`
3. Enter 后加 2s sleep，防止重复发送

---

## 决策 5: RECREATE_TAB 用活 tab 的 ws 做 Page.navigate

### 问题
直接关闭目标 tab 后，原 ws.send() 抛出 ConnectionClosedError。

### 解决方案
用**任意活 tab 的 ws** 发 Page.navigate，避免直接关闭主 ws。

---

## 决策 6: body > 200 作为短回复完成的阈值

### 问题
body=700-800（"三个词回答"类短回复）被误判"卡住"触发 RECREATE_TAB。

### 解决方案
阈值从 800 降到 200：
```python
BODY_COMPLETE_THRESHOLD = 200
if no_growth_cycles >= 6:
    if body_len <= BODY_COMPLETE_THRESHOLD:
        action = "RECREATE_TAB"  # 真死了
    else:
        action = "COMPLETED"     # AI 短回复完成
```

---

## 决策 7: LLM Think 层降级策略

### 问题
MiniMax API 429 额度耗尽时，LLM Think 层无法调用。

### 解决方案
```python
def think_llm(self, state):
    try:
        return call_minimax(state)  # 可能 429
    except Exception:
        return think_rules(state)  # 规则兜底
```

任何异常降级规则引擎，确保反应堆不卡死。