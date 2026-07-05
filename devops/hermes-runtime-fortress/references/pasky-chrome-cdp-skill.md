# pasky/chrome-cdp-skill — 接管用户真实 Chrome 的现成方案

## 概述

- **Stars**: 3.1k
- **官网**: https://github.com/pasky/chrome-cdp-skill
- **解决问题**: 不重启 Chrome、不重新登录，直接接管用户已有 Chrome 的 CDP 会话
- **原理**: 通过 Unix socket 发现已运行的 Chrome 实例

## 核心能力

```
chrome-cdp list          # 列出用户 Chrome 所有 tab
chrome-cdp snap          # 截图保存到 /tmp/screenshot.png
chrome-cdp snap --path /tmp/doc.png  # 指定截图路径
chrome-cdp eval "document.title"  # 执行 JS 获取页面标题
chrome-cdp click "#submit"       # 点击元素
```

## 安装

```bash
npx skills add https://github.com/pasky/chrome-cdp-skill --skill chrome-cdp
```

## 前提条件

1. **Chrome 开启远程调试**: 打开 `chrome://inspect/#remote-debugging`，开关打开
2. **Node.js 22+**: 使用内置 WebSocket
3. **不需要重启 Chrome**: 这是最大优点

## 重要发现

Chrome 调试端口（`chrome://inspect/#remote-debugging`）和命令行 `--remote-debugging-port=9222` 是**两套机制**：
- 命令行端口：需要重启 Chrome 才能开启
- `chrome://inspect/#remote-debugging` 开关：**不需要重启**，立即生效

## 工作流程

```
用户Chrome开着 → 用户手动开chrome://inspect/#remote-debugging → 开关打开
→ Hermes通过pasyky/chrome-cdp-skill连接 → 看到用户所有tab和登录态
```

## 替代方案对比

| 方案 | 需要重启Chrome | 需要重新登录 | 难度 |
|---|---|---|---|
| pasky/chrome-cdp-skill | ❌ 不需要 | ❌ 不需要 | 低 |
| chrome://inspect 开关 | ❌ 不需要 | ❌ 不需要 | 最低 |
| 重启+--remote-debugging-port | ✅ 需要 | ✅ 可能丢失 | 中 |
| Chrome扩展+chrome.debugger | ❌ 不需要 | ❌ 不需要 | 中 |

## 克隆备用（GitHub 可能访问不稳定时）

```bash
cd /tmp && git clone --depth=1 https://github.com/pasky/chrome-cdp-skill.git
```

## 关联

- `references/chrome-cdp-user-vs-mirror.md` — Chrome mirror vs 用户真实 Chrome 区分方法
- 4 层浏览器识别方法论中 L1 DOM-id 层依赖稳定 CDP 连接
