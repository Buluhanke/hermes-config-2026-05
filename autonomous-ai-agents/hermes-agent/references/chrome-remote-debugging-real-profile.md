# Chrome Remote Debugging with Real Browser Profile

## Goal

Connect Hermes Playwright/browser automation to the user's **real Chrome** — with all logged-in sessions (豆包, ChatGPT, 1688, etc.) — instead of Playwright's isolated browser.

## The Problem

Chrome won't allow remote debugging with its default profile path:
```
DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.
```

## Solution: Symlink Trick

Chrome 对 `--user-data-dir` 有安全限制，不允许指向它自己正在使用的默认 profile（`~/Library/Application Support/Google/Chrome`）。用 symlink 绕过：

```bash
# 1. 创建空的远程调试 profile 目录
mkdir -p ~/chrome-remote-profile

# 2. 软链真实 Chrome 的 Default profile（不是整个 Chrome 目录！）
ln -sf ~/Library/Application\ Support/Google/Chrome/Default ~/chrome-remote-profile/Default

# 3. 杀掉所有 Chrome（必须完全退出）
pkill -9 -f "Google Chrome" 2>/dev/null; pkill -9 -f GoogleUpdater 2>/dev/null; sleep 2

# 4. 用远程调试端口启动 Chrome（后台运行）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="$HOME/chrome-remote-profile" \
  2>/tmp/chrome_err.log &

# 5. 等待启动完成
sleep 8

# 6. 验证端口已开
lsof -i :9222  # 应显示 Chrome 进程在监听

# 7. 验证 WebSocket 可用
curl -s http://localhost:9222/json/version | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('Browser:', d['Browser'])
print('WebSocket:', d['webSocketDebuggerUrl'][:60])
"

# 8. 查看所有已打开的 tab
curl -s http://localhost:9222/json | python3 -c "
import sys,json; pages=json.load(sys.stdin)
for p in pages:
    print(f'  [{p[\"id\"][:8]}] {p.get(\"title\",\"?\")[:40]}')
"
```

## 为什么 symlink 能 work

- `--user-data-dir` 必须指向**不同于 Chrome 默认使用的路径**
- 直接用 `~/Library/Application Support/Google/Chrome` 会被拒绝
- 用 `~/chrome-remote-profile`（自定义路径）满足"非默认目录"要求
- symlink 让 Chrome 以为它在用一个独立目录，实际上读写的是真实 profile

## 验证 Playwright 能连上

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "ws://localhost:9222/devtools/browser/<browser_id>"
    )
    # 现在可以访问所有已登录的 cookies/sessions
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()
    print(page.url)
```

## 重启后需要重跑

系统重启后 Chrome 进程会被终止，远程调试端口不会自动恢复。每次重启后需要重新执行步骤 3-4（步骤 1-2 的目录和 symlink 只需创建一次）。

## 错误排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `PORT CLOSED` | Chrome 没启动或启动失败 | 检查 `/tmp/chrome_err.log` |
| `DevTools remote debugging requires a non-default data directory` | 没加 `--user-data-dir` 或路径不对 | 确认用的是 `~/chrome-remote-profile` |
| symlink 后端口仍不开 | Chrome 仍在后台运行 | `pkill -9 -f "Google Chrome"` 彻底杀掉 |
| WebSocket 连接被拒绝 | browser_id 不对 | 从 `curl http://localhost:9222/json/version` 取正确的 ws URL |
