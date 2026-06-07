# cua_extract.py 已知不工作 — 2026-06-07 端到端翻车实录

> **TL;DR**：`scripts/cua_extract.py` 在默认配置的 Chrome 上不能用。
> 跑 `python cua_extract.py "URL"` → `❌ empty_content` 或 `osascript error: ... AppleScript 执行 JavaScript 的功能已关闭`。
>
> 修复方向见 SKILL.md "⚠️ cua_extract.py 已知不工作" 段。本文件是**原始翻车证据**。

## 翻车现场

### 跑的命令

```bash
~/.hermes/hermes-agent/venv/bin/python \
  ~/.hermes/skills/cua-bridge/scripts/cua_extract.py \
  "https://hermes-agent.nousresearch.com/" \
  --max-chars 800
```

### 输出

```
📦 引擎: cua-driver ✅ | DiskCache ✅

🌐 [?]
   https://hermes-agent.nousresearch.com/
   ❌ empty_content
```

`empty_content` 的代码位置：`scripts/cua_extract.py` line 181：
```python
if not content or len(content) < 50:
    return {"url": url, "error": "empty_content", ...}
```

意思是 `get_text_or_article(pid)` 返回空字符串或 < 50 字符。

## Bug #1：`cua-driver call page` CLI 缺 window_id

### 复现

直接调 CLI 子进程：

```bash
echo '{"action":"execute_javascript","pid":59692,"javascript":"document.title"}' \
  | ~/.local/bin/cua-driver call page
```

### 报错

```
Missing required parameter: window_id
```

### 矛盾点

跑 `~/.local/bin/cua-driver describe page` 看 schema：

```json
"required": ["action"],   ← 只要 action
"window_id": { "type": "integer" }   ← optional
```

JSON schema 明明说 window_id 可选，daemon 实际报缺。

### 根因推测

CLI 包装层（`scripts/cua_extract.py` 的 `cua_call` 函数）通过 stdin 把整个 kwargs dict 一次性 JSON 传：

```python
result = subprocess.run(
    [CUA_DRIVER, "call", tool_name],
    input=json.dumps(kwargs),     # ← 整个 dict 一次进
    ...
)
```

daemon 这一层可能有独立于 schema 的"如果 action 是 execute_javascript 必须有 window_id"的硬编码验证。

### 绕过

**不通过 CLI 子进程**，直接用 MCP 工具 `mcp__cua_driver_page` ——MCP 走 daemon 的内部通道，不经过 CLI 包装层。

但 MCP 工具又撞上 Bug #2。

## Bug #2：Chrome 关闭了 AppleScript JS 执行

### 复现

绕过 Bug #1 用 `mcp__cua_driver_page`:

```
action=execute_javascript, pid=59692, window_id=648, javascript="document.title"
```

### 报错

```
osascript error: /tmp/db97f13d45415150.applescript:311:365: execution error:
"Google Chrome"遇到一个错误: 通过 AppleScript 执行 JavaScript 的功能已关闭。
要开启此功能，请在菜单栏中依次转到"查看">"开发者">"允许 Apple 事件中的 JavaScript"。
```

### 根因

**Chrome 自己的开关**（不是 cua-driver 的问题）。

Chrome macOS 出于安全默认禁止 AppleScript 路径执行 JS。需要在 Chrome 菜单里手动开：

```
View > Developer > Allow JavaScript from Apple Events
```

### 影响

- **OFF by default** ——99% 的用户撞上
- **每次 Chrome 升级/重装可能回退**
- **不可通过代码开**（需要用户 UI 操作）

## 决策：这条路还值不值得走？

### 不值得（v1.1.0 决策）

| 维度 | 评估 |
|------|------|
| 95% 抓页场景 | Trafilatura 已覆盖（轻量、零配置、5s 出结果）|
| 剩下 5% JS 渲染 | `browser_navigate` + DOM 提取更直接（走 CDP，不撞 AppleScript）|
| cua_extract.py 撞的坑 | 两个 bug 叠在一起，每次 Chrome 重启可能回退 |
| 维护成本 | 高（依赖 Chrome 版本、用户配置、cua-driver 0.x 接口稳定性）|

**结论**：保留 `cua_extract.py` 作为 "需要 AppleScript JS 开关 + 复杂 SPA" 的备选，但**降级链里把它放最后**，首选 `fetch_url.py` (Trafilatura) 和 `browser_navigate`。

## 修复路线（如果将来要重做）

### 路线 A：CDP 路径（推荐）

让 `cua_extract.py` 改用 Chrome DevTools Protocol 抓页面：

1. `launch_app` 启动 Chrome 时传 `--remote-debugging-port=9333`
2. 走 CDP `Runtime.evaluate` 而非 AppleScript
3. 走 CDP `Page.navigate` 而非 `launch_app urls=`
4. **完全不依赖 AppleScript JS 开关**

**预估工作量**：2-3 小时（重写 `find_or_launch_browser` + `get_text_or_article`）

### 路线 B：彻底放弃 cua_extract

直接删 `scripts/cua_extract.py`，让 search.py 全文用 Trafilatura + `browser_navigate` 兜底。

**预估工作量**：30 分钟（删除 + 改 search.py 注释）

### 路线 C：写 Chrome 启动包装脚本

写一个 `scripts/launch_chrome_debug.sh` 帮用户启动带 CDP 端口的 Chrome，cua_extract.py 检测到有 CDP 端口就走 CDP 路径，否则报 "请先跑 launch_chrome_debug.sh"。

**预估工作量**：1 小时

## 配套：什么场景还在用 cua-driver？

**抓页场景基本不用了**（Trafilatura + CDP 覆盖）。

**真正发挥价值的是 GUI 操作场景**（不抢焦点的后台自动化）：

- 定时帮用户点某个 macOS app 的按钮
- 帮用户在 Chrome 里填表单（避开反爬）
- 监控某个 app 的状态变化

这些场景 `mcp__cua_driver_*` 工具集直接调就行，**不需要走 cua_extract.py 包装层**。
