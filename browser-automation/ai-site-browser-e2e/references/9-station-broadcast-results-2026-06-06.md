# 9 站 broadcast 实战 — 2026-06-06 multi_ask_v3 验证

## 触发条件
- 用户问"X 是哪个 / X 怎么选 / 哪个最好"类对比问题 → 跑多站 cross-validate
- 需要 N≥4 站共识答案时

## 9 站实际登录态 (2026-06-06 实测)
| 站 | URL 匹配关键字 | 登录态验证 |
|---|---|---|
| Gemini | `gemini.google.com` | ✅ "Conversation with Gemini", cookies 751 字符 |
| 豆包 | `doubao.com/chat` | ✅ "用户320735" + 历史对话列表, localStorage 7 user-key |
| ChatGLM | `chatglm.cn` | ✅ "GLM-5.1" + 模型选择条, localStorage 4 user-key, cookies 1414 |
| DeepSeek | `chat.deepseek.com` | ✅ "罗" + 快速/专家/识图模式, localStorage 2 user-key, cookies 209 |
| ChatGPT | `chatgpt.com` | ✅ "新聊天" + 完整历史列表, localStorage 8 user-key, cookies 2739 |
| Grok | `grok.com` | ✅ "新建聊天" + 历史记录, localStorage 3 user-key, cookies 1068 |
| 元宝 | `yuanbao.tencent.com` | ❌ **未登录** - body 明确显示 "未登录" + 登录按钮, 单独报告, 不与成功混说 |
| 文心一言 | `yiyan.baidu.com` | ❓ tab URL 实际是 `qianwen.com` (被千问占), navigate_timeout |
| 千问 | `qianwen.com` | ✅ "Qwen1929" 用户名, cookies 1328 |

## 4 维证据验证 SOP (跑前必做, 跑后必验)
**按 skill `browser-webpage-100score` 红线, 不能只看 title**

```python
import json, urllib.request, asyncio, websockets

tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
ws_map = {t['url']: t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page'}

async def probe(ws_url):
    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
            "params": {"expression": "document.body ? document.body.innerText.slice(0,300) : 'NO_BODY'",
                       "returnByValue": True}}))
        body = json.loads(await ws.recv()).get('result', {}).get('result', {}).get('value', '')
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate",
            "params": {"expression": """(() => {
                const ls = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    if (/user|uid|token|email|account|profile/i.test(k)) ls[k] = localStorage.getItem(k).slice(0, 60);
                }
                return {lsUserKeys: Object.keys(ls).length, lsSample: ls,
                        cookiesLen: document.cookie.length,
                        cookiesSample: document.cookie.slice(0, 100),
                        hasLoginBtn: !!document.querySelector('button[class*="login"], a[class*="login"]'),
                        title: document.title};
            })()""", "returnByValue": True}}))
        info = json.loads(await ws.recv()).get('result', {}).get('result', {}).get('value', {})
        return body, info
```

**判定标准**:
- body < 50 字符 → 没渲染, 重 navigate
- localStorage 0 user-key + cookies < 100 字符 + 有登录按钮 → **未登录, 跳过该站, 单独报告**
- 历史对话列表存在 (body 含"昨天/今天/最近") → 强证据已登录

## 7 站真回复共识 (2026-06-06 "hermes 最强免费聚合搜索"实测)
- **SearXNG** (4 站: 豆包/ChatGLM/Grok + 隐含 Gemini): 自建元聚合 20+ 引擎, 永久免费, 无 API Key
- **session_search** (DeepSeek 推): Hermes Agent v0.15.0 自带, 20ms 提速 4500x, FTS5 全文索引
- **Tavily + DuckDuckGo 双引擎** (千问 Qwen3.7 推): 1000 次/月高精度 + 无限兜底

## ChatGPT 0 字符坑 (2026-06-06 实测未解决)
- multi_ask_v3 ProseMirror + Enter 路径, ChatGPT 没触发 send
- body 0 字符, AX tree 0 字符, 天眼 SSE 0 包
- 根因未查清, 可能是 ChatGPT 当前 A/B 测试的 ProseMirror 模式不接受 `Input.dispatchKeyEvent` 的 Enter
- 下次: 试 `browser_click` 发送按钮, 或改用 `Input.insertText` on ProseMirror (cdp step 1 for ChatGPT)

## 假阳性判定 (按 skill 红线)
| 假阳性类型 | 怎么识别 |
|---|---|
| 抓的是历史对话标题 (豆包/Grok) | AX 抓到内容含"Mac mini M4 24GB: 5 Key AI Agent Shortfalls" 这种**历史对话标题** (跟本次问题无关) |
| 抓的是思考过程 (ChatGLM "GLM-5.1" 推理) | 含 `*等等*` `*让我再核实*` 这种 reasoning 标记, **不是最终答案** |
| 长度 < 50 字符 (豆包 41 字符假阳性) | 极可能是占位符/历史标题 |
| 抓的是页面 footer (备案号/用户协议) | 含 "京公网安备 11010802041394 号" 这种备案信息 |

**真回复判定**: 长度 ≥ 200 + 不含历史对话标题 + 不含页面备案号 + 不含内部 reasoning 标记

## multi_ask_v3 实测成功率 (2026-06-06)
- 5/6 站真回复: Gemini/豆包/ChatGLM/DeepSeek/Grok
- 1/6 站失败: ChatGPT (0 字符)
- 1 站跳过: 元宝 (未登录)
- 1 站单独跑通: 千问 (走 browser_navigate + Enter 路径)

**比 skill 文档"还没一次成功"有突破**, 但 ChatGPT 仍是 0/6 失败坑

## 关键 CDP 坑 (2026-06-06 实测, 已 patch 到主 SKILL.md)
- **page tab.webSocketDebuggerUrl 是 tab 专属 WS, 无需 attachToTarget**: 主 SKILL.md 4-line skeleton 原版用 attach 反而报错
- **Tongyi 千问 (qianwen.com) 必须 Enter 发送, 不能 browser_click 按钮**: 按钮 click "成功" 但无回复, 详见 SKILL.md "Tongyi Qianwen" 章节
- **multi_ask_v3 SITES 字典只有 6 站**: 千问/元宝/文心需要走单独路径
