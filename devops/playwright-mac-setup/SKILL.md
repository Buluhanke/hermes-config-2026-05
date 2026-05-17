---
name: playwright-mac-setup
title: Playwright Setup on macOS
description: Guide to install and configure Playwright browsers on macOS, handle caching, and troubleshoot download timeouts.
version: 1.0.0
---
## Purpose
Automate the installation and provisioning of Playwright browsers for macOS environments, addressing common issues such as long download times, timeouts, and missing cache directories.

## Prerequisites
- Python 3.9+
- pip
- Adequate disk space (~200 MB per browser)

## Steps
1. Install Playwright Python package.
   ```bash
   pip install playwright
   ```
2. Install browsers. Use the long‑running installer and set a custom cache path if needed.
   ```bash
   playwright install chromium --browser-dir ~/.cache/ms-playwright
   ```
   * Optionally, add `--timeout=0` to disable the 30 s default timeout.
3. Verify installation.
   ```bash
   playwright show-browser-list
   ```
4. Troubleshooting
   | Symptom | Fix |
   |---------|-----|
   | Download times out after 30 s | Set `PUPPETEER_DOWNLOAD_HOST=direct` and retry, or use a mirror. |
   | Cache not found after install | Ensure `~/.cache/ms-playwright` exists and has correct permissions. |
   | Browser launches headless by default | Run `-‑headless=false` or set `headless: false` in the launch options.

---

## 已知陷阱（2026-05-10 新增）

### Camoufox postinstall 的 npx 不继承代理

`@askjo/camoufox-browser` 包的 postinstall 脚本会调用 `npx camoufox-js fetch` 从 GitHub 下载浏览器二进制。**关键问题**：npm/pnpm 的 `npx` 子进程**不继承**父进程的 `HTTP_PROXY`/`GLOBAL_AGENT`/`NODE_OPTIONS` 环境变量，导致下载直接超时——即使代理已在运行。

**现象**：
- `pnpm install` 卡在 postinstall（超时）
- `pnpm approve-builds` 也超时（同样卡在 npx 调用）
- 代理实际在运行（7897端口），但下载仍然失败

**已验证有效的解法**：补丁 postinstall.js，强制设置 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`：

```bash
# 找到 postinstall.js
POSTINSTALL=$(find ~/.hermes/hermes-agent/node_modules/@askjo/camofox-browser -name "postinstall.js" 2>/dev/null | head -1)
echo "文件: $POSTINSTALL"

# 备份
cp "$POSTINSTALL" "$POSTINSTALL.bak"

# 关键补丁：把 "delete childEnv.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD;" 替换为
# childEnv.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
# 这让 postinstall 跳过网络下载，直接读缓存
sed -i '' 's/delete childEnv.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD;/childEnv.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";/' "$POSTINSTALL"

# 再跑一次（不走 postinstall，直接 rebuild）
cd ~/.hermes/hermes-agent && pnpm rebuild @askjo/camofox-browser
```

**验证**：输出 "Camoufox binaries up to date!" "Current version: v135.0.1-beta.24" = 成功。

**为什么有效**：缓存里已有 607MB 的 camoufox 二进制（`~/Library/Caches/camoufox/version.json` 可证），设 `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` 后 postinstall 直接跳过下载读取缓存，无需任何网络。

**pnpm 替代 npm**：hermes-agent 的 node_modules 用 pnpm 安装比 npm ci 快（全局缓存复用），遇到 postinstall 超时用上述补丁解决。

**相关工具链**：Camoufox → Playwright → browser automation。是 `agent-browser` / `browser-use` / `hermes-rpa` 的底层浏览器引擎。

## References
- [Playwright Installation Docs](https://playwright.dev/docs/intro)
- Session-specific reference: `references/macos-playwright-issue.md` (generated during this session).