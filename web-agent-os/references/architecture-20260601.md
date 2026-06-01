# 浏览器架构确认记录（2026-06-01）

## 结论：当前架构已达最优

```
MiniMax M2.7
    ↓
Hermes Browser (CDP engine)  ← config.yaml: engine=cdp, cdp_url=http://127.0.0.1:9222
    ↓
Chrome CDP (port 9222)       ← Chrome/148.0.7778.179，用户真实Chrome（已登录）
    ↓
Accessibility Tree           ← 1688首页: 307个可交互元素，ref_id可用
    ↓
真实浏览器
```

## 端口分工（重要）

| 端口 | Chrome实例 | 登录态 | 用途 |
|------|-----------|--------|------|
| **9222** | 用户日常Chrome | ✅ 全部已登录 | 生产主力：1688/AI网站/电商 |
| 9333 | chrome-debug独立profile | ❌ 干净实例 | 测试/隔离场景 |

## 验证命令

```bash
# 确认Chrome在跑
curl -s http://127.0.0.1:9222/json/version
# → Chrome/148.0.7778.179

# 列出标签页
curl -s http://127.0.0.1:9222/json/list
# → [{"id":"...","url":"https://chatgpt.com/",...}]

# 验证Hermes Browser模块连通性
browser_navigate("https://www.1688.com")
# → 307个可交互元素，@eN ref_id可用
```

## Hermes Browser (CDP engine) vs MCP chrome bridge

MCP chrome bridge 失败：
```
mcp_chrome_get_windows_and_tabs → "Failed to connect to MCP server"
```

但 Hermes Browser 模块正常（直连 9222，不走 MCP bridge）：
```
browser_navigate("https://www.1688.com") → ✅ 完整Accessibility Tree
```

**结论**：不要等 MCP bridge修，CDP engine 已经覆盖所有 browser_* 工具能力。

## WebAct 结论

未找到官方发布包（名字可能不同或内部项目）。不需要：Hermes原生CDP已经是最优方案。

## 何时用 Vision

Accessibility Tree 已经能处理大多数页面。只有以下情况才截图：
- Canvas图形验证码
- 复杂图表/可视化
- 动态渲染无法用文本提取时
- 游戏页面

## 架构优先级（已确认）

```
1. web_extract / browser_get_web_content  → 文本提取，最快
2. CDP DOM.getDocument (通过 browser_snapshot) → 结构化DOM
3. Accessibility Tree (ref_id) → 点击/输入操作
4. 截图 + Vision → 只在必要时
```
