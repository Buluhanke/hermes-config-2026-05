# cua-bridge 实战场景速查

## 场景 1：抓 SPA（单页应用）

**症状**：Trafilatura 抓出来内容是空的或不完整，因为页面是 JS 渲染的。

**解法**：
```bash
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/skills/cua-bridge/scripts/cua_extract.py "https://app.example.com"
```

**原理**：用 cua-driver 调起 Chrome → 导航 → 等 `readyState=complete` → 抓 `article/main/role=main` 的 innerText。

## 场景 2：抓需要登录的页面

**症状**：fetch_url 没 cookie，看到的是登录页。

**解法**：
- 直接 `cua_extract.py URL`（用本机 Chrome，已登录）

**前置**：用户已经在 Chrome 里登录过该网站。

## 场景 3：定时 GUI 任务（不抢焦点）

**症状**：每天 9 点帮用户点一下"刷新数据"按钮。

**解法**：写 cron 任务调 cua-driver：
```bash
#!/bin/bash
~/.local/bin/cua-driver call get_window_state --pid <chrome_pid> --window_id <wid>
~/.local/bin/cua-driver call click --pid <chrome_pid> --element_index <button_idx>
```

**为什么不用 Playwright**：Playwright headless 抢焦点 + 看不见。
**为什么不用 osascript**：抢焦点，违反 no-foreground 原则。

## 场景 4：反爬严格的站点

**症状**：fetch_url 拿到 403，curl 被 Cloudflare 拦。

**解法**：用 cua_extract.py（真实 Chrome + 真实 User-Agent + 真实 TLS 指纹）。

**注**：不保证 100% 过 Cloudflare，但比 curl 强很多。

## 场景 5：测试桌面 app

**症状**：需要测试一个原生 macOS app 的 UI。

**解法**：用 `mcp__cua_driver_*` 工具集（`get_window_state`、`click`、`type_text`）。

参考：官方 skill pack `MACOS.md` 里有完整章节。

## 场景 6：跨平台 GUI 测试

**症状**：同一段自动化代码在 macOS、Windows、Linux 都要跑。

**解法**：用 cua-driver（唯一跨 3 平台的 GUI 自动化）。
- macOS：AX 树（`get_window_state` → element_index）
- Windows：UIA 树
- Linux：AT-SPI（pre-release）

**注**：官方 skill pack 的 `WINDOWS.md` 和 `LINUX.md` 有专门章节。
