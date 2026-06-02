# 反应堆循环 (reactor) — 进化一: Sense → Think → Act

## 场景
需要一个 24h 守护进程: 监控 tab 状态, 智能决策下一步动作.
传统轮询是"瞎等", 反应堆是"有意识的等"。

## 三层职责

### 1. Sense (感知层) — 廉价高频
每次循环调一次, 抓:
- URL 是否变化 (e.g. 进入 /a/chat/s/xxx)
- 是否有可输入框 (textarea/contenteditable 数量)
- body 文本长度 (AI 回复是否到位)
- 关键 DOM 标记 (生成中 / 已完成 / 错误)

**示例**:
```python
sense = {
    "url": "https://chat.deepseek.com/",
    "ta": 1,           # textarea 数量
    "bodyLen": 427,    # body 文本长度
    "generating": False  # 通过 DOM class 推断
}
```

### 2. Think (认知层) — LLM 决策
把 Sense 输出喂给 LLM (默认 MiniMax), 让它给出行动列表:
```python
think = llm_decide(sense, history)
# → ["DETECT: 找到输入框", "READY: 可输入", "WAIT: 等用户发问"]
```

决策类型:
- **DETECT**: 发现关键元素 (输入框/按钮/生成指示器)
- **READY**: 状态就绪可以输入
- **WAIT**: 需要等待 (AI 生成中/网络请求中)
- **ACT**: 决定具体动作 (输入/发送/读回复/截屏)
- **ERROR**: 异常, 转修复流

### 3. Act (执行层) — CDP 物理动作
Think 决定后, 用 CDP 原子操作执行:
- `Input.dispatchKeyEvent` (输入/Enter)
- `DOM.focus` + JS 注入
- `Accessibility.getFullAXTree` (读回复)
- `Network.enable` + 拦截 (天眼)
- `Page.captureScreenshot` (视觉确认)

## 循环节奏
```python
while running and elapsed < max_seconds:
    sense = sense_layer(tab)
    think = think_layer(sense, history)
    if think.has("ACT"):
        act_layer(think)
    history.append((sense, think))
    await asyncio.sleep(period)  # 0.5~3s
```

## 最小可跑 (实测通过)
```bash
python3 /Users/aimac/.hermes/scripts/hermes_reactor.py deepseek 15
```

输出:
```
🌀 反应堆启动 (15秒)
[周期01] 0.0s
  📡 Sense: url=https://chat.deepseek.com/ ta=1 bodyLen=427
  🧠 Think: ['DETECT: 找到输入框']
...
🛑 反应堆停止 (运行8个周期)
```

## 演化路径 (已规划)
| 进化 | 内容 | 状态 |
|------|------|------|
| 进化一 (基础) | Sense/Think/Act 三层框架 | ✅ 跑通 |
| 进化二 (语义) | 视觉点选关键词/坐标 | ✅ 跑通 |
| 进化三 (流式) | Sense 加 Network 拦截, 实时拿 patch | ⏳ 待做 |
| 进化四 (自愈) | Think 加错误检测 + 自动降级/重试 | ⏳ 待做 |

## 进化三关键: 流式双工
让 Sense 跑一个**长连接监听** (Network天眼), 不等 FINISHED, 增量解析 patch 协议:

```python
async def sense_stream(tab):
    """天眼: 实时拿 patch, 不轮询 bodyLen"""
    eyes = await eyes_start(tab.ws)
    fragments = []
    async for event in eyes.events:
        if "Network.responseReceived" in event["method"]:
            url = event["params"]["response"]["url"]
            if "completion" in url:
                body = await eyes.wait_body(event["requestId"])
                for line in body.split("\n"):
                    if line.startswith("data: "):
                        chunk = parse_patch(line[6:])
                        fragments.append(chunk)
                        yield chunk  # 流式 yield
    return fragments
```

Think 层拿到流式 yield 后, 实时判定"还在生成"/"已结束"/"出错"。

## 进化四关键: 自我修复
Think 层加 self-healing 分支:
```python
if sense.get("error_count", 0) > 3:
    return ["RECOVERY: 重新打开 tab", "RECOVERY: 重新登录"]
if "Shadow DOM" in last_error:
    return ["FALLBACK: 改用 Network 拦截"]
if think.contains("CHAR_DUP"):
    return ["FIX: 强制 keyDown.text='' 然后重试"]
```

## 关键文件
- `scripts/hermes_reactor.py` — 155行, 当前实现
- `scripts/hermes_vision_click.py` — 162行, 进化二配套
- `references/network_sniffer.py` — 天眼 Network 拦截 (见 SKILL.md 进阶部分)
