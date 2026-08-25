---
name: osascript-chrome-js
description: "AppleScript JS驱动已登录Chrome CDP备选。Use when CDP连不上但要操作真实Chrome"
version: 1.0.0
triggers:
- drive logged-in Chrome / operate GitHub settings / fill web form no CDP
- AppleScript Chrome / osascript execute javascript
- computer_use typing not landing / browser_requires_setup
---

# Osascript Browser Control — 第三条登录态浏览器操作路

## 何时用（决策顺序）
L1 前台 AX 树（computer_use capture）只能读不能可靠写；cua_browser_state 需要 owned DevTools endpoint（会拒 `browser_requires_setup`）；computer_use 的 CGEvent 击键经常 `delivered 0 of N` 送不进地址栏。此时第三条路：**AppleScript 直接在真实登录态页面里执行 JS**。零调试端口、零截图、能读能写。

## 核心模式

```bash
# 读页面文字
osascript -e 'tell application "Google Chrome" to tell active tab of window id <ID> to execute javascript "document.body.innerText.slice(0,2500)"'

# 导航（比模拟 cmd+L 击键可靠一万倍）：用 set URL 或 location.href=
osascript -e 'tell application "Google Chrome" to set URL of active tab of window id <ID> to "https://github.com/settings/security"'
```

## 定位目标 tab
遍历 windows/tabs 按 URL 匹配拿 window id。注意 `index of t` 在部分 macOS 版本报 -1700 错，用外层计数器变量代替。

## 复杂 JS 一律走文件中转
内联复杂 JS 会撞两堵墙：osascript 转义地狱、terminal 工具的 oversized-payload 拦截。正确姿势：
```bash
cat > /tmp/task.js <<'EOF'
(function(){ /* 任意复杂逻辑 */ })()
EOF
osascript -e 'tell application "Google Chrome" to tell active tab of window id <ID> to execute javascript (read POSIX file "/tmp/task.js" as «class utf8»)'
```

## 实战坑（2026-08-23 GitHub 设置页验证）
1. **"You signed in with another tab or window" 是假错误**——点击表单按钮后常闪现，多数时候操作已生效，reload 或直接访问目标 URL 确认即可，别当成失败重试。
2. 无 submit 按钮的表单（如 GitHub 的 Preferred 2FA method）：`select.value='xxx'` → dispatch change event → `form.submit()`。
3. 提取数据先 dump `document.body.innerText` 摸清结构，再定向 querySelector（用 `closest('form').action` 定位表单归属）。
4. 登录墙无解药：被重定向到 `/login` 说明该 Chrome profile 登录态过期，让用户手动登录一次后继续——不代填密码。
5. 验证结果永远回读页面状态（select.value / flash message），不信 oscript 返回值本身。

## 实证战果（2026-08-23）
GitHub（Buluhanke）settings 页：读取 recovery codes 全文并提取 16 个码、把首选 2FA 从 Authenticator App 改为 Passkey（webauthn_preferred）并提交成功。全程无 CDP、无截图、无新实例。
