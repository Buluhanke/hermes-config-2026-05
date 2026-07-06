# macOS 浏览器调试能力对比 (2026-07-08 实测)

## Safari — 有内置调试器

- **开启方式**: 菜单栏 → **开发** → **显示网页检查器**
- **适用**: 任意 Safari 标签页，无论是否由 Hermes 启动
- **能力**: 直接读 DOM、修改 Elements、调试 JavaScript、查看 Network
- **无需重启**: 开发菜单开箱即用

```
菜单栏 → 开发 → 显示网页检查器
```

## Chrome — 无内置调试窗口

- **Chrome 官方不提供图形化远程调试 UI**（对比 Safari 的 Web Inspector）
- **唯一方式**: 启动时加 `--remote-debugging-port=9222`，通过外部工具连接
- **外部工具**: Chrome DevTools (浏览器访问 `http://localhost:9222`)、Puppeteer、Selenium、chrome-devtools-mcp
- **限制**: 需要**重启 Chrome** 才能加调试端口（不支持热启动加参数）

```bash
# Chrome 启动命令（需重启）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/path/to/profile \
  --no-first-run --no-default-browser-check \
  "https://target-site.com"
```

## Hermes Chrome 控制通道现状 (2026-07-08 实测)

| 通道 | 目标 Chrome | 状态 | 能否读网页 DOM |
|---|---|---|---|
| CDP :9222 | `chrome-profile-mirror` (Hermes 自己的) | ✅ 端口在线 | ✅ 可以（但内容是 about:blank） |
| CDP :9222 | 用户主 Chrome (profile "K") | ❌ 没开端口 | ❌ 不通 |
| cua-driver AX 树 | 用户屏幕上的任意 Chrome 窗口 | ✅ 可操作界面元素 | ❌ 读不到网页内容 |

## 用户主 Chrome 如何开启调试

**必须手动操作**（Hermes 无法远程为已运行的 Chrome 热添加调试端口）:

1. **完全退出 Chrome**（Cmd+Q）
2. **Terminal 执行**（或在 Chrome 快捷方式里改）:
   ```bash
   open -na "Google Chrome" --args \
     --remote-debugging-port=9222 \
     --remote-allow-origins=* \
     --user-data-dir="$HOME/Library/Application Support/Google/Chrome"
   ```
3. 这样启动的 Chrome 和用户正常使用的 Chrome 是**同一个 profile**（共享 cookies/登录态）

## 一句话结论

> **Safari**: 开发菜单 → 直接调试任意页面  
> **Chrome**: 必须重启 + 加参数，无内置调试 UI  
> **Hermes CDP**: 只控制 mirror profile，不控制用户主 Chrome  
> **cua-driver**: 能操作用户 Chrome 的界面元素，但读不到网页 DOM

## 触发词

- "Chrome 有没有调试 / Chrome 开发者工具 / Chrome 怎么调试网页 / Chrome 9222 看不到页面"
- "用户 Chrome 怎么控制 / Chrome 和 Safari 调试区别"
- "Hermes 的 9222 是谁的 Chrome"
