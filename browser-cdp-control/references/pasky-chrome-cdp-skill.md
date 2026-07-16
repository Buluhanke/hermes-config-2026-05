# pasky/chrome-cdp-skill — 轻量级 CDP CLI（2026-07-06 实测）

## 核心价值

不重启 Chrome、不需要 `--remote-debugging-port` 参数，通过 Unix socket 自动发现用户已运行的 Chrome 实例，连接后可直接操作已有 tab 的 DOM/Screenshot/SendKeys。

## 安装

```bash
npx skills add https://github.com/pasky/chrome-cdp-skill --skill chrome-cdp
```

依赖：Node.js 22+（内置 WebSocket）

## 核心命令

```bash
# 1. 列出所有打开的页面
node skills/chrome-cdp/scripts/cdp.mjs list

# 2. 截图（默认 /tmp/screenshot.png）
node skills/chrome-cdp/scripts/cdp.mjs shot <targetId前缀>

# 3. 抓取页面快照
node skills/chrome-cdp/scripts/cdp.mjs snap <targetId前缀>
```

## 工作原理

通过 Chrome 的 SingletonSocket（`/var/folders/.../com.google.Chrome.../SingletonSocket`）自动发现运行中的 Chrome 实例，无需调试端口参数。

## 限制

- 需要用户在 Chrome 里开启 `chrome://inspect/#remote-debugging` 开关
- 第一次使用需要用户在 Chrome 里点"允许调试"的开关
- Node.js 22+ 环境

## 与 Hermes 现有方案对比

| 方案 | 需要重启 Chrome | 需要调试端口 | 接管已有 tab |
|------|----------------|-------------|-------------|
| pasky chrome-cdp-skill | ❌ 不需要 | ❌ 不需要 | ✅ 是 |
| Chrome DevTools MCP | ❌ 不需要 | ⚠️ 需要（但可自动发现） | ✅ 是 |
| Hermes browser CDP | ✅ 需要（mirror profile） | ✅ 需要 | ❌ mirror 隔离 |
| 手动开调试端口 | ✅ 需要 | ✅ 需要 | ✅ 是 |

## 关键场景

用户已在 Chrome 登录了企业微信文档 / 飞书 / Google Docs，不想重启浏览器丢失 session → 用 pasky 方案最合适。

## 触发词

"接管已有 Chrome" / "不重启 Chrome 操作浏览器" / "pasky" / "chrome-cdp-skill"
