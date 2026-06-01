# AI网站访问状态参考（2026-06-02实测）

## 已登录站点（用户Chrome已登录，可直接对话）

| 网站 | URL | 状态 | 用途 |
|------|-----|------|------|
| ChatGPT | chatgpt.com | ✅ 已登录（用户lukebu） | 主力知识源 |
| 豆包 | doubao.com | ✅ 已登录 | 主力知识源 |
| DeepSeek | chat.deepseek.com | ✅ 已登录 | 主力知识源 |
| Gemini | gemini.google.com | ✅ 已登录 | 主力知识源 |
| 智谱清言 | chatglm.cn | ⚠️ 部分登录（需验证） | 待确认 |
| Grok | grok.com | ⚠️ 需重新登录 | 待确认 |

## 核心方法：用CDP直连用户Chrome（端口9222）

用户Chrome启动时加 `--remote-debugging-port=9222` 参数，Hermes通过CDP WebSocket直接连接，读取已登录的AI网站会话。

```python
# 验证命令
curl http://127.0.0.1:9222/json/version
# 返回: Chrome/148.0.7778.179 ✅

# CDP WebSocket 直连读取已登录AI网站内容
import websocket, json, urllib.request

with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as f:
    tabs = json.load(f)
# 找目标AI网站的tab
ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id":1,"method":"Runtime.enable"}))
ws.recv()

# 用Runtime.evaluate提取页面文本内容（不用截图！）
script = """
(function(){
    var els = document.querySelectorAll('article, .markdown');
    var r = [];
    els.forEach(function(e){var t=e.innerText.trim(); if(t&&t.length>20) r.push(t.substring(0,500));});
    return JSON.stringify(r.slice(-10));
})()
"""
ws.send(json.dumps({"id":2,"method":"Runtime.evaluate","params":{"expression":script,"returnByValue":True}}))
```

## 为什么不用截图（2026-06-02用户纠正）

用户原话："你方向都不对了，为什么浏览器需要截图去识别"

- AI网站都是结构化网页，DOM文本提取比截图快10倍、Token消耗低
- 截图/VLM是最后手段：Canvas验证码、复杂图表、动态渲染无法用文本提取时
- 正确的工具选择优先级：
  1. **web_extract / browser_get_web_content** — 直接拿文本，最轻量
  2. **CDP Runtime.evaluate** — 读DOM结构，比Accessibility Tree更稳定
  3. **browser_snapshot** — 页面文本（8000字符截断）
  4. **截图/VLM** — 仅用于：Canvas验证码、复杂图表、动态渲染

## 端口分工

| 端口 | Chrome实例 | 登录态 | 用途 |
|------|-----------|--------|------|
| 9222 | 用户真实Chrome | ✅ 已登录 | 读AI网站内容/对话 |
| 9333 | chrome-debug独立profile | ❌ 需重新登录 | dom_tools专用 |

**最佳实践：优先用9222读取用户已登录内容。**

## browser工具的Chrome实例架构（无效方案）

```
browser_navigate/click/type
    ↓
Hermes Agent 管理 Playwright 临时 Chromium
    ↓
临时 profile（/var/folders/.../agent-browser-chrome-XXX/）
    ↓
每次启动全新，cookies 不持久化
```

**结论**：browser工具控制的是**全新临时实例**，无任何登录态，不能用来访问已登录的AI网站。

## 知识采集格式（1688包装采购专家场景）

向ChatGPT/豆包/DeepSeek发送：
```
我是Hermes，义乌迅龙贸易公司的AI采购专家，Mac mini M4 24GB。
我要进化成1688包装材料采购专家。请给出：
1. 每日知识采集的具体方案（哪些AI网站、搜什么关键词、频率）
2. 长期记忆库的建设方案（文件结构、存储格式、更新机制）
3. 自我进化的核心路径（官方文档→GitHub→Discord→中文社区的具体学习计划）
请给出可执行的具体步骤，不是理论。
```

## AI网站对话采集后的沉淀路径

采集完 → 写入对应记忆目录：
- supplier_memory/ → 供应商黑名单/白名单、评价变化
- market_memory/ → 价格趋势、原材料行情
- tactics_memory/ → 采购降本技巧、谈判策略
- learning_logs/ → 每日学习日志