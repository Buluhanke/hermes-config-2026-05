---
name: browser-fallback
description: 浏览器控制降级策略 — MCP chrome bridge失效时自动切换到browser工具
triggers:
  - MCP chrome连接失败
  - "Failed to connect to MCP server"
  - chrome_navigate报错
  - browser工具可用但MCP不可用
  - 需要读取已登录网站的DOM结构
  - Accessibility Tree返回空节点
  - React SPA内容读取（ChatGPT、豆包等）
---

# Browser Fallback（浏览器控制降级）

## 优先级（已确认 2026-06-01）

1. **Browser工具 CDP engine** (`browser_navigate/click/type/snapshot`) — 主要，完全可用
   - 直连 `http://127.0.0.1:9222`（用户真实Chrome）
   - 不走 MCP bridge，MCP失败不影响
2. **Playwright CDP** (`ws://localhost:9333`) — 备用，需要Chrome开启debug端口

## 降级触发

当 `browser_navigate` 报错（独立Chromium实例问题）时，尝试：
1. `computer_use` 控制用户真实Chrome（已登录态）
2. Playwright CDP 直连 `ws://localhost:9333`（需要chrome-debug Chrome在跑）

## 验证结果
- MCP chrome bridge: 报错 "Failed to connect to MCP server"
- browser工具: ✅ 正常，可打开网站、点击、输入、截图
- Playwright CDP备用: ws://localhost:9333 直连

## 已验证可用的AI对话网站
| 网站 | 状态 | 备注 |
|------|------|------|
| Gemini | ✅ 可访问 | 需要用户Chrome登录态 |
| 豆包 | ❌ 需登录 | 临时实例无cookies |
| ChatGLM | ❌ 需登录 | 临时实例无cookies |
| DeepSeek | ⚠️ 429限速 | 未登录 |
| ChatGPT | ⚠️ 403 | 未登录 |
| Grok | ✅ 可访问 | 未登录 |

## 架构结论（2026-06-01 确认）

用户Chrome（9222）已达最优，无需额外配置：
- `browser_navigate` → 307元素Accessibility Tree，@eN ref_id可用
- 1688/淘宝/京东/AI网站：直接操作，不需要截图/VLM
- 只有Canvas验证码/复杂图表才需要Vision

**browser工具临时实例**：无用户cookies，每次session重新创建，适合不需要登录的网页操作。

## ⚠️ 关键：DOM/Runtime.evaluate 优先于 Accessibility Tree / 截图

**适用场景**：React SPA（ChatGPT、豆包等）、动态渲染页面
**症状**：Accessibility Tree 返回空节点（0 nodes）、browser_snapshot 返回 0 elements

**正确工作流**：
```
1. curl http://127.0.0.1:9222/json/list → 找标签页ID
2. WebSocket 连上标签页 → Runtime.evaluate 执行 JS
3. JS 直接读 DOM 结构 → 返回结构化文本
4. 不需要截图、不需要 VLM
```

**为什么 Accessibility Tree 会空**：React SPA 的 DOM 是动态渲染的，Chrome accessibility 快照在页面未完全加载时为空。而 Runtime.evaluate 执行的是当前内存中的 DOM，任何时刻都准确。

**参考脚本**（Python）：
```python
import websocket, json, urllib.request

# 1. 找到目标标签页
with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as f:
    tabs = json.loads(f.read())
tab_id = [t for t in tabs if 'chatgpt' in t.get('url','') and t.get('type')=='page'][0]['id']

# 2. 连接并启用 Runtime
ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id":99,"method":"Runtime.enable"}))
ws.recv()

# 3. 用 JS 读取 DOM（例如读所有输入框）
ws.send(json.dumps({
    "id": 2,
    "method": "Runtime.evaluate",
    "params": {
        "expression": """
(function(){
    var els = document.querySelectorAll('textarea, input, [contenteditable]');
    var r = [];
    els.forEach(function(el){
        var rect = el.getBoundingClientRect();
        if(rect.width>0 && rect.height>0)
            r.push({tag:el.tagName, id:el.id, placeholder:el.placeholder||'', x:rect.x, y:rect.y, w:rect.width, h:rect.height});
    });
    return JSON.stringify(r);
})()
""",
        "returnByValue": True
    }
}))
result = json.loads(ws.recv())
print(result['result']['result']['value'])
ws.close()
```

## 配置验证（修改后需重启 Gateway）

修改 `~/.hermes/config.yaml`：
```yaml
browser:
  cdp_url: 'http://127.0.0.1:9222'
  engine: cdp
```

改完**必须重启 Gateway** 才能生效。快速重启：
```bash
# 找到 gateway PID
ps aux | grep "hermes_cli.main gateway"
# kill 掉再启动
kill <PID>
cd ~/.hermes/hermes-agent && nohup ./venv/bin/python -m hermes_cli.main gateway run > /tmp/hermes_gateway.log 2>&1 &
```

## 验证 CDP Chrome 连接

```bash
# 1. 确认 Chrome 在跑
curl -s http://127.0.0.1:9222/json/version

# 2. 查看当前标签页
curl -s http://127.0.0.1:9222/json/list

# 3. 若配置正确，browser_navigate 会自动用 CDP
```

`browser_navigate` 返回的成功 snapshot 里有元素结构和 ref ID 就说明 CDP 通了。

## 完整重启 Chrome 的步骤

当 Chrome 已经无联网调试端口启动时，需要完全退出后再启动：

```bash
# 1. 彻底杀死所有 Chrome 进程（包括子进程）
pkill -9 -f "Chrome"
sleep 3

# 2. 确认杀干净了
ps aux | grep -i "chrome" | grep -v grep | grep -v crashpad

# 3. 用调试端口 + Default profile 重新启动
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --no-first-run --no-default-browser-check --remote-allow-origins=*
```

⚠️ 注意：`pkill -f "Google Chrome"` 可能杀不干净子进程，改用 `pkill -9 -f "Chrome"` 更彻底。

## 已知问题：MCP Chrome Server 与内置 browser 工具的差异

| 维度 | MCP chrome tools | Built-in browser tools |
|------|-----------------|----------------------|
| 工具名 | `mcp_chrome_chrome_navigate/click/...` | `browser_navigate/click/type/...` |
| 依赖 | `mcp-chrome-stdio` 进程 + `stdio-config.json` | 直接读取 `config.yaml` 的 `cdp_url` |
| 状态 | ❌ `stdio-config.json` 缺失，初始化失败 | ✅ 配置正确即可用 |

**`stdio-config.json` 缺失**是最常见的 MCP chrome 失败原因。该文件位于 `/Users/aimac/.local/bin/stdio-config.json`，定义了 Chrome CDP URL。如果缺失，MCP chrome server 会报 "Failed to connect to MCP server"。

**解决方案**：直接使用 built-in browser 工具，无需 MCP chrome server。

## Chrome 启动参数（Mac）

```bash
# 用户已登录 Chrome（保留所有cookies和登录态）
/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --no-first-run --no-default-browser-check --remote-allow-origins=*
```

**注意**：`--user-data-dir` 必须指向用户的真实 profile（Default 或 Profile 1/2/3），不能用临时目录，否则没有登录态。

## 相关
- chrome-debug: Chrome debug配置
