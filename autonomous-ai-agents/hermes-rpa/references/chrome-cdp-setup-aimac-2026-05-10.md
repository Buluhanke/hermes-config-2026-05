# Chrome CDP 调试实例配置（aimac Mac mini）

## 目标
让 Hermes browser 工具复用 Chrome 的登录态，不再每次重新登录。

## 架构

```
Hermes (browser_tool) 
    → connect_over_cdp("http://127.0.0.1:9333")
    → 独立 Chrome 实例 (profile: ~/.hermes/chrome-debug)
    → 持久的 cookies/登录态
```

独立于用户日常使用的 Chrome（`~/Library/Application Support/Google/Chrome`）。

## 当前配置（2026-05-10）

- Chrome 调试实例端口：**9333**
- Profile 目录：`~/.hermes/chrome-debug`
- 持久化方式：`~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist`
- Hermes 配置：`config.yaml browser.cdp_url: 'http://127.0.0.1:9333'`

## 启动/停止

```bash
# 手动启动（临时）
screen -dmS chrome-debug "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run --no-default-browser-check

# 停止
screen -S chrome-debug -X quit

# launchd 持久化（系统启动自动运行）
launchctl load ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist
launchctl unload ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist
```

## launchd plist 内容

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aimac.hermes-chrome-debug</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Google Chrome.app/Contents/MacOS/Google Chrome</string>
        <string>--remote-debugging-port=9333</string>
        <string>--user-data-dir=/Users/aimac/.hermes/chrome-debug</string>
        <string>--no-first-run</string>
        <string>--no-default-browser-check</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

## 验证

```bash
# 端口监听确认
lsof -i :9333 | grep LISTEN

# CDP 端点确认
curl -s http://127.0.0.1:9333/json/version

# Hermes 是否使用 CDP（观察 browser_navigate 输出的 stealth_features）
# 应该有 "cdp_override"，不是 "agent_browser" 或空
```

## 第一次使用（建立登录态）

`~/.hermes/chrome-debug` 是全新 profile，网站未登录。**只需做一次**：

1. Chrome 调试实例运行中
2. 在 screen session 中查看：`screen -r chrome-debug`
3. 在 Chrome 窗口手动登录 1688/ChatGPT
4. Cookies 写入 `~/.hermes/chrome-debug`
5. 之后 Hermes 操作用这个 profile，登录态自动保持

## 故障排查

### 端口不监听
- 检查 Chrome 进程：`pgrep -a Chrome`
- 很可能用了默认 profile 被单例锁。改用独立 profile dir（见上方命令）
- 确认目录存在且可写：`mkdir -p ~/.hermes/chrome-debug`

### Hermes 重启后 CDP 不生效
- 确认 `config.yaml` 里 `browser.cdp_url: 'http://127.0.0.1:9333'` 存在
- 执行 `hermes gateway restart`

### 登录态丢失（每次都要重新登录）
- 检查 `~/.hermes/chrome-debug/Default/Cookies` 文件是否存在
- 可能是 profile 被清空，需要重新登录一次
