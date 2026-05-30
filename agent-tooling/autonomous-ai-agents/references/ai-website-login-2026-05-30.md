# AI网站登录与自动化 — 踩坑记录

## 核心教训（2026-05-30）

### 用户明确指令：不要停，直接执行
- 用户原话："以后这类问题不要停下来，当有多个选择的时候优先按你推荐做，而不是停下来等我，谨记"
- 多选项场景：直接执行推荐方案，不等确认
- 答应的事：当下落实，不放空炮

### Chrome实例隔离问题（关键！）
browser工具(MCP chrome bridge)连接的Chrome与用户日常Chrome是**两个完全独立的进程**：

| | browser工具Chrome | 用户日常Chrome |
|---|---|---|
| 路径 | `~/.hermes/chrome-debug` | `~/Library/Application Support/Google/Chrome/Default` |
| profile名 | chrome-debug | Default |
| 调试端口 | 9333 | 无 |
| 登录状态 | 各网站独立 | 各网站独立 |
| cookies | 不共享 | 不共享 |

**判断方法：**
```bash
ps aux | grep "Google Chrome" | grep -v Helper | grep "user-data-dir"
```
出现 `--user-data-dir=/Users/aimac/.hermes/chrome-debug` = browser工具Chrome
出现 `~/Library/Application Support/Google/Chrome` = 用户日常Chrome

### 批量打开URL的方法（browser console JS）
MCP断开时，可用browser console执行JS批量开标签：
```javascript
window.open('https://gemini.google.com/app', '_blank');
window.open('https://www.doubao.com/chat', '_blank');
window.open('https://chat.deepseek.com/', '_blank');
// 一次开完
```

### CDP端口 vs MCP bridge
- Chrome调试端口9333始终开着（Chrome进程本身）
- MCP chrome bridge是连接9333的中间服务，会断
- CDP raw WebSocket可能被origin限制拒绝（--remote-allow-origins）
- 即使MCP断了，底层Chrome进程和9333端口仍然健康

### 查看所有标签页
```bash
curl -s http://localhost:9333/json | python3 -c "import json,sys; [print(t['id'], t['title'], t['url']) for t in json.load(sys.stdin) if t.get('type')=='page']"
```

## 问题背景

用户要求在browser工具Chrome上自动化操作6个AI网站：
- https://gemini.google.com/app
- https://www.doubao.com/chat
- https://chatglm.cn/main/alltoolsdetail
- https://chat.deepseek.com/
- https://chatgpt.com/
- https://grok.com/z

## 各网站验证状态

| 网站 | 验证类型 | 解决方案 |
|------|---------|---------|
| 豆包 | 无需登录 | 直接可用 |
| Grok | Cloudflare/账号 | 用户手动登录一次 |
| Gemini | Google账号 | 用户手动登录(hanlukebu@gmail.com) |
| 智谱清言 | 滑动验证 | 用户手动操作（自动过不了） |
| DeepSeek | 手机号验证 | 用户手动操作或提供手机号 |
| ChatGPT | Cloudflare | 用户手动操作 |

## 解决路径

### 唯一可行方案：用户在browser工具Chrome里手动登录一次
1. 把browser工具Chrome窗口调到前台（osascript激活+设位置）
2. 用户逐个网站登录
3. 登录一次后cookies保存在chrome-debug profile，以后自动用

### MCP断开时的备选工具
1. **browser console JS** — 执行JS、操作DOM、批量开标签
2. **curl CDP端口** — 查看所有标签页状态
3. **AppleScript** — 激活Chrome、设URL（但看不到页面响应）
4. **computer_use** — 可操作Chrome但窗口需在当前Space可见

### 各网站自动化难点
- **Cloudflare**: browser工具IP被识别为数据中心流量，自动过不了
- **滑动验证**: 需要真人滑动，无法自动绕过
- **手机号验证**: 需要用户配合提供

## 真人化AI Agent路径
- 无账号网站（豆包等）: browser工具直接操作
- 有账号网站: 用户在browser工具Chrome手动登录一次 → cookies保存 → 后续自动化可用
