# Chrome CDP 调试连接：用户浏览器 vs Mirror Chrome（Failure 70 详述）

## 核心发现

**`chrome-devtools-mcp` 连接的是 `chrome-profile-mirror`（Hermes 自己的 Chrome），不是用户真实的 Chrome。**

两个 Chrome 进程独立运行，cookies/登录态完全不共享：
- `chrome-profile-mirror` → 9222 端口，Hermes 控制，无用户登录态
- 用户默认 profile → 独立进程，无调试端口

## 诊断命令

```bash
# 查看哪个 Chrome 在监听 9222
lsof -i :9222
ps -p <PID> -o args=

# 如果看到 --user-data-dir=/Users/aimac/.hermes/chrome-profile-mirror
# 说明是 mirror Chrome，不是用户真实 Chrome

# 查看所有 Chrome 进程
ps aux | grep -E "Chrome" | grep -v "Helper|crashpad|Renderer"
```

## 解决方案

### 方案A（推荐）：pasky/chrome-cdp-skill
- 3.1k stars，专门解决"不重启 Chrome 接管用户浏览器"
- 原理：通过 Unix socket 发现已有 Chrome 实例
- 安装：`npx skills add https://github.com/pasky/chrome-cdp-skill --skill chrome-cdp`
- 前提：Chrome 里开启 `chrome://inspect/#remote-debugging`
- 优点：**不需要重启 Chrome，不需要重新登录**

### 方案B：重启 Chrome 加调试端口
- 用户先关闭 Chrome
- 命令：`open -a "Google Chrome" --args --remote-debugging-port=9222`
- 注意：**必须先关掉所有 Chrome 实例**，否则新开的是 mirror profile
- **破坏性**：会丢失当前 tab 状态

### 方案C：Chrome 扩展 + chrome.debugger API
- 扩展装一次永久生效
- 通过 `chrome.debugger` API attach 到任何 tab
- 需要用户在 Chrome 里安装扩展并授权

## 教训

1. **绝对禁止** `pkill/killall "Google Chrome"` — 会同时杀用户真实 Chrome
2. 9222 端口绑定的是**最后一次启动时带 `--remote-debugging-port` 的实例**
3. `curl http://127.0.0.1:9222/json/list` 列出的 tab 不代表用户真实浏览器状态
4. **先搜索现成方案**（pasky/chrome-cdp-skill 3.1k stars），再考虑自己写脚本

## 关键搜索词

```
chrome cdp attach existing browser session without restart
pasky chrome-cdp-skill
Chrome DevTools MCP attach to running Chrome
playwright attach --cdp existing browser
```
