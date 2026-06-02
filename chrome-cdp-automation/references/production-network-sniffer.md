# Production Script: network_sniffer3.py

**位置**: `/tmp/network_sniffer3.py`（已验证 4 次成功，2026-06-02）
**建议**: 移到 `~/.hermes/scripts/network_sniffer3.py` 统一管理

## 核心能力
- WebSocket CDP 直连 DeepSeek tab
- 逐字 `hardcore_type` 输入（keyDown→char→keyUp，0.05s/字）
- 天眼监听 `Network.loadingFinished`，捕获 SSE 原始流
- 解析 DeepSeek patch 协议 `{"v": "x"}` 累加

## 验证记录
| 时间 | 问题 | 结果 |
|------|------|------|
| 18:37 | network_sniffer3.py 初代 | 6149字符原始流 |
| 22:52 | "1+1等于几" | ✅ 21字 |
| 22:55 | "什么是AI" | ✅ 完整长回答 |
| 22:59 | "用三个词形容Hermes" | ✅ 完整 |
| 23:07 | "解释量子计算" | ✅ 完整 |

## 关键代码片段（逐字输入）

```python
async def hardcore_type(eyes, text, delay=0.05):
    for ch in text:
        await eyes.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ""})
        await eyes.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
        await eyes.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        await asyncio.sleep(delay)
```

## DeepSeek patch 协议解析

```python
# 增量 patch
if "v" in data and isinstance(data["v"], str):
    all_text += data["v"]
# 累积式老格式
v = data.get("v", {})
if isinstance(v, dict):
    resp = v.get("response", {})
    for frag in resp.get("fragments", []):
        content = frag.get("content", "")
        if content and frag.get("type") in ("RESPONSE", "THINK"):
            if len(content) > len(all_text):
                all_text = content
```

## AI 回复完成信号
`document.body.innerText.length` 单调增长 → 停止增长 10s = 完成（不是 stopBtn）