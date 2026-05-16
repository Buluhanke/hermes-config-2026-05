# macOS 权限问题排查

> Hermes RPA 依赖 macOS 权限链。以下权限任一缺失都会导致自动化失败。

## 权限矩阵

| 能力 | 所需权限 | 设置路径 | 相关工具 |
|------|---------|---------|---------|
| 截图整个屏幕 | 屏幕录制 | 系统设置 → 隐私 → 屏幕录制 | `screencapture`, PyAutoGUI screenshot |
| 截取特定窗口 | 屏幕录制 | 同上 | `screencapture -l <window_id>` |
| 控制键盘鼠标 | 辅助功能 | 系统设置 → 隐私 → 辅助功能 | PyAutoGUI click/type, System Events |
| AppleScript 控制应用 | 辅助功能 | 同上 | `osascript`, tell application |
| Chrome 执行 JS via AppleScript | Chrome 内部设置 | Chrome → 显示 → 开发者 → 允许 Apple 事件中的 JavaScript | `execute ... javascript` |
| Playwright CDP | 无（网络端口） | N/A | `connect_over_cdp()` |

## 如何检测缺失

### 屏幕录制缺失
```bash
screencapture -x /tmp/test.png
# → "could not create image from display"
screencapture -l 12345 -x /tmp/test.png
# → "could not create image from window"
```

### 辅助功能缺失
```bash
osascript -e 'tell application "System Events" to get name of every process'
# → 工作（System Events 基本命令不用权限）
osascript -e '
tell application "System Events"
    tell process "Google Chrome"
        click menu bar item "显示" of menu bar 1
    end tell
end tell'
# → "osascript"不允许辅助访问" (-1719)
```

### Chrome JS from Apple Events 缺失
```bash
osascript -e '
tell application "Google Chrome"
    execute active tab of window 1 javascript "document.title"
end tell'
# → "通过 AppleScript 执行 JavaScript 的功能已关闭" (12)
```

## Chrome 调试端口问题

### macOS 26 + Chrome 147 已知问题

`--remote-debugging-port=9222` 标志被 Chrome 进程接收（ps aux 可见），
但端口不绑定（lsof 无输出）。Chrome 界面正常启动，可以手动浏览。

**影响**：Playwright CDP (`connect_over_cdp`) 完全不可用。
**替代方案**：仅 AppleScript 路线。如果 AppleScript JS 执行也失败，则是硬阻塞。

### 典型症状
```bash
# Chrome 进程有 --remote-debugging-port=9222
ps aux | grep Chrome | grep remote-debugging
# → 进程存在

# 但端口不监听
lsof -i :9222
# → 无输出

# Playwright 连接失败
python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); p.chromium.connect_over_cdp('http://127.0.0.1:9222')"
# → connect ECONNREFUSED 127.0.0.1:9222
```

### 排查步骤
1. 确认 Chrome 版本：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version`
2. 确认 macOS 版本：`sw_vers -productVersion`
3. 检查端口可用：`lsof -i :9222`（应无输出表示空闲）
4. 尝试其他端口：`--remote-debugging-port=9333`
5. 尝试 `--remote-allow-origins=*`
6. 若以上均失败 → 标记为硬阻塞，告知用户此环境不支持 CDP

## 已知工作组合

### 完全不可用的环境（本机: aimac@Mac-mini 2026-05-09）
- macOS 26.4.1
- Chrome 147.0.7727.139
- `--remote-debugging-port=9222` ❌ 端口不绑定
- AppleScript JS execution ❌ 即使 Chrome 设置了也不能用（tcc 权限链问题）
- `screencapture` ❌ 无屏幕录制权限
- `System Events` click ❌ 无辅助功能权限
- **结论**：当前环境下无法自动读取浏览器页面内容。需用户手动操作或远程协助。

## 解决方案分级

| 级别 | 方案 | 对用户的要求 | 成功率 |
|------|------|------------|--------|
| A | 手动开启所有权限 | 每开一个新终端应用都要授权一次 | ⭐⭐⭐ |
| B | 用户手动截图/复制内容 | 配合度高，但效率低 | ⭐⭐⭐⭐⭐ |
| C | 用户重启 Chrome 带 debug port | 仅需一次 | ⭐⭐（本机无效） |
| D | 远程控制用户桌面（向日葵/TeamViewer） | 安装第三方软件 | ⭐⭐⭐⭐⭐ |
