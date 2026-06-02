# Chrome CDP + AI网站对话 — 2026-06-02 实测

## 结论

**读 AI 对话内容：此路不通，直接调 API**

现代 AI 聊天网站（DeepSeek/豆包/Grok/ChatGPT 等）使用 custom elements + closed shadowRoot + 虚拟化列表（virtual scrolling），所有已知方法都无法穿透：

| 方法 | 结果 |
|------|------|
| `DOM.querySelector` + `innerText` | 空 |
| 递归遍历 `shadowRoot.childNodes` | 空 |
| `innerText` 获取整个 body | 空 |
| Accessibility Tree `getFullAXTree` | 只有外层容器，无实际对话内容 |
| Network 拦截 response | DeepSeek 等站返回 0 响应体 |

**可用范围（不依赖回复读取）**：
- AX Tree 读侧边栏历史对话列表 ✅
- 填入输入框 + 发送 ✅
- 读页面标题/URL/导航结构 ✅
- CDP 连接稳定性 ✅

## 正确方案：直接调厂商 API

```python
# DeepSeek
from openai import OpenAI
client = OpenAI(api_key="sk-...", base_url="https://api.deepseek.com")
r = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":"..."}])
print(r.choices[0].message.content)

# 豆包：https://www.volcengine.com/product/doubao
# ChatGLM：https://open.bigmodel.cn/
```

## 关键 CDP 命令（2026-06-02 实测）

```python
import asyncio, websockets, json, urllib.request

async def cdp_send(ws, method, params=None, msg_id=1):
    msg = {"id": msg_id, "method": method}
    if params: msg["params"] = params
    await ws.send(json.dumps(msg))
    resp = await ws.recv()
    return json.loads(resp)

async def main():
    TAB_ID = "9500172557FFD5EE04AFFC54B7BE4E99"
    WS_URL = f"ws://localhost:9333/devtools/page/{TAB_ID}"
    
    async with websockets.connect(WS_URL, max_size=20*1024*1024) as ws:
        # 等待页面加载
        await asyncio.sleep(3)
        
        # AX树：读285节点（DeepSeek）
        ax = await cdp_send(ws, "Accessibility.getFullAXTree", {"depth": 25})
        nodes = ax["result"]["nodes"]
        
        # 输入文字
        await cdp_send(ws, "Runtime.evaluate", {
            "expression": """
            (function(){
                const ta = document.querySelector('textarea');
                ta.focus(); ta.value = '请用3句话说清楚你是谁';
                ta.dispatchEvent(new Event('input', {bubbles:true}));
                return 'OK: ' + ta.value;
            })()
            """,
            "returnByValue": True
        }, msg_id=2)
        
        # 发送（Enter键）
        await cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.querySelector('textarea')?.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,bubbles:true}))",
            "returnByValue": True
        }, msg_id=3)
        
        # 等8秒AI回复
        await asyncio.sleep(8)
        
        # 再读AX树 —— 回复内容仍然读不到（Shadow DOM隔离）
        ax2 = await cdp_send(ws, "Accessibility.getFullAXTree", {"depth": 30})
```

## Chrome CDP 协议关键细节

- **消息格式**：不用 `{"jsonrpc": "2.0", ...}` — 去掉 jsonrpc 字段
- **Tab ID 获取**：`curl http://localhost:9333/json` 返回完整 32 字符 id
- **WebSocket URL**：`ws://localhost:9333/devtools/page/<tab_id>`
- **depth 参数**：建议 25-30，过浅漏节点，过深响应慢

## 端口对应

| 端口 | Chrome 实例 |
|------|------------|
| 9333 | `chrome-debug` profile（独立，无登录态） |
| 9222 | 用户日常 Chrome（需加 `--remote-debugging-port=9222` 开启） |