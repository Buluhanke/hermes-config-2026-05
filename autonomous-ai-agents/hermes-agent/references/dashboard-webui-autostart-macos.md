# Dashboard / Web UI Auto-start via launchd

## The Two Processes

| Process | Port | launchd managed? |
|---------|------|----------------|
| Vite dev server (`npm run dev`) | 5173 | No — 需要单独建 plist |
| Dashboard backend (`hermes dashboard`) | 9119 | No — 建议用 dev server 方式（见下） |

## 正确方案：Dev Server Auto-start

### Step 1. 创建 wrapper script

launchd 的 PATH 不包含用户 PATH，必须用绝对路径调用 npm/node。

```bash
# ~/.hermes/scripts/hermes-web-start.sh
#!/bin/bash
cd /Users/mac/.hermes/hermes-agent/web
exec /Users/mac/.hermes/node/bin/npm run dev
```

```bash
chmod +x ~/.hermes/scripts/hermes-web-start.sh
```

> 注意：用 `exec` 让脚本替换自身进程，避免产生多余的 bash 父进程。

### Step 2. 创建 launchd plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.web</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/mac/.hermes/scripts/hermes-web-start.sh</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/mac/.hermes/node/bin:/Users/mac/.hermes/hermes-agent/venv/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/mac/.hermes/logs/web.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/mac/.hermes/logs/web.error.log</string>
</dict>
</plist>
```

路径根据实际情况替换（`/Users/mac` → 用户 home 目录）。

### Step 3. 加载

```bash
launchctl unload ~/Library/LaunchAgents/ai.hermes.web.plist   # 先卸
launchctl load ~/Library/LaunchAgents/ai.hermes.web.plist     # 再装
sleep 8
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/  # 应返回 200
```

## Dashboard Backend (port 9119) launchd plist

Dashboard 后端也需要通过 launchd 管理自启，**必须加 `--tui` 参数**，否则 Dashboard 的 CHAT 页面（嵌入式 PTY 聊天）不工作，刷新后所有会话窗口消失。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hermes.dashboard</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/mac/.hermes/hermes-agent/venv/bin/hermes</string>
        <string>dashboard</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>9119</string>
        <string>--no-open</string>
        <string>--tui</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HERMES_HOME</key>
        <string>/Users/mac/.hermes</string>
        <key>HERMES_WEB_DIST</key>
        <string>/Users/mac/.hermes/hermes-agent/hermes_cli/web_dist</string>
        <key>PATH</key>
        <string>/Users/mac/.npm-global/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pkg/env/active/bin:/opt/pmk/env/global/bin:/Users/mac/.local/bin</string>
        <key>HTTP_PROXY</key>
        <string>http://127.0.0.1:7897</string>
        <key>HTTPS_PROXY</key>
        <string>http://127.0.0.1:7897</string>
        <key>ALL_PROXY</key>
        <string>http://127.0.0.1:7897</string>
        <key>NO_PROXY</key>
        <string>localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,api.deepseek.com,v2.aicodee.com,open.bigmodel.cn</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/mac/.hermes/logs/dashboard.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/mac/.hermes/logs/dashboard.error.log</string>
</dict>
</plist>
```

**关键参数：**
- `--tui`：启用 CHAT 页面的嵌入式 PTY 功能。没有这个参数，`window.__HERMES_DASHBOARD_EMBEDDED_CHAT__` 为 `false`，CHAT 页面刷新后无输入窗口。
- `--no-open`：禁止启动时自动打开浏览器。
- `--host 127.0.0.1`：只监听本地。

**⚠️ `HERMES_WEB_DIST` 环境变量必须设置：**
如果不设置，`hermes dashboard` 会在启动时检查 npm 并尝试构建 web UI（调用 `_build_web_ui`）。launchd 环境里 npm 的 PATH 可能找不到，导致 dashboard 进程启动后立即崩溃并循环重启。

症状：`launchctl list` 显示 exit status `-1`，日志里大量 `address already in use` 是因为上一个崩溃进程还没完全退出端口就又被抢注。

设置 `HERMES_WEB_DIST` 后，dashboard 直接使用预构建的 `web_dist` 目录，完全跳过 npm 检查。

**⚠️ PATH 必须包含 npm 的完整路径：**
launchd 的默认 PATH 仅包含 `/usr/bin:/bin:/usr/sbin:/sbin`，不包含 Homebrew 或 npm global 安装的路径（`/usr/local/bin`、`~/.npm-global/bin`）。必须在 plist 的 `EnvironmentVariables` 里显式写完整 PATH。

**验证是否生效：**
```bash
# 检查进程是否带了 --tui
ps -p $(pgrep -f 'hermes dashboard') -o args=

# 检查 EMBEDDED_CHAT 标志
curl -s http://127.0.0.1:9119/ | grep EMBEDDED_CHAT
# 应返回 window.__HERMES_DASHBOARD_EMBEDDED_CHAT__=true
```

**修改 plist 后重载（正确顺序）：**
```bash
# 先杀掉现有 dashboard 进程（否则端口被占无法启动）
launchctl unload ~/Library/LaunchAgents/ai.hermes.dashboard.plist
kill $(ps aux | grep 'hermes dashboard' | grep -v grep | awk '{print $2}') 2>/dev/null
sleep 2
launchctl load -w ~/Library/LaunchAgents/ai.hermes.dashboard.plist
sleep 5
lsof -nP -iTCP:9119 -sTCP:LISTEN  # 应显示 dashboard 进程监听 9119
```

## 常见失败模式

### 症状：dashboard 进程在跑但端口 9119 无监听，日志刷屏 "address already in use"

**原因：** dashboard 进程崩溃后立即被 launchd 重启（`KeepAlive: true`），但进程没有干净退出导致端口仍被 TIME_WAIT 占用。新进程启动时 bind 失败也立即退出，再次被拉起，形成 crash loop。

**排查步骤：**
```bash
# 1. 确认 crash loop
launchctl list | grep dashboard
# status 列显示 -1 且 PID 每次变 = crash loop

# 2. 看错误日志
tail -5 ~/.hermes/logs/dashboard.error.log
# 会看到 "address already in use" 或 "npm is not available" 或其他根因

# 3. 确认根因
grep -c "address already in use" ~/.hermes/logs/dashboard.error.log
# 大量重复 → npm 检查失败 → 崩溃重启循环

# 4. 修复：加 HERMES_WEB_DIST + 完整 PATH（见上方 plist 配置）
```

### `npm: command not found` 或 `env: node: No such file or directory`

**原因：** launchd 的 PATH 只包含 `/usr/bin:/bin:/usr/sbin:/sbin`，不包含用户安装的 node。

**解决：** 必须在 plist 的 `EnvironmentVariables` 里显式写完整 PATH（包含 `/Users/mac/.npm-global/bin` 和 `/usr/local/bin`）。

### CHAT 页面刷新后会话窗口消失

**原因：** Dashboard 后端 launchd plist 缺少 `--tui` 参数，或 `HERMES_WEB_DIST` 未设置导致 dashboard 崩溃退出。

**解决：** 在 plist 的 `ProgramArguments` 中添加 `<string>--tui</string>`，设置 `HERMES_WEB_DIST`，然后重载。

### 换行符问题

plist 是 XML，换行符必须是 `\n`（Unix style），不能用 Windows `\r\n`。

### Vite dev server 找不到 dashboard 后端的 session token

**原因：** Vite dev server（5173）依赖 Python dashboard 后端（9119）在每次页面加载时注入 `window.__HERMES_SESSION_TOKEN__` 和 `window.__HERMES_DASHBOARD_EMBEDDED_CHAT__`。如果 dashboard 后端没跑，Vite 无法注入这些变量。

**症状：** 5173 页面能显示但 CHAT 入口消失，或者所有操作返回 500。

**解决：** 确保 dashboard 后端（9119）在 Vite 之前启动，并检查 `vite.config.ts` 的 `BACKEND` 变量是否指向正确的 dashboard URL。

### 验证日志

```bash
cat ~/.hermes/logs/web.error.log
cat ~/.hermes/logs/web.log
cat ~/.hermes/logs/dashboard.error.log
cat ~/.hermes/logs/dashboard.log
```

## 生产构建 vs Dev Server

| 方式 | 优点 | 缺点 |
|------|------|------|
| `npm run dev`（dev server） | 实时 HMR，热更新 | 需要 node/npm 长期运行 |
| `npm run build` + `hermes dashboard` | 单一进程，gateway 自带 | 构建步骤，首次配置复杂 |

Dev server 方案够用，如果追求简洁再切生产构建。
