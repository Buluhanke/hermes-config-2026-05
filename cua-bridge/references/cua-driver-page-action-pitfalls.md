# cua-driver `page` action 双重坑（2026-06-07 实地验证）

跑 `cua-driver call page action=execute_javascript` 抓浏览器页面会撞两个独立坑，**叠加触发**才让人误以为"是网络问题"。

## 坑 1：CLI 子命令要求 `window_id` 必传（daemon 严于 schema）

`cua-driver describe page` 的 schema 标 `window_id` **非 required**，但 `cua-driver call page` 实际跑时：

```
Missing required parameter: window_id
```

**根因**：CLI 包装层把 stdin JSON 直接 forward 给 daemon，daemon 的 runtime 验证比 schema description 严（schema 是文档态，daemon 是 enforcement 态）。

**绕过**（按推荐度）：
1. **不要走 CLI 子命令**——直接用 `mcp__cua_driver_page` MCP 工具
2. **必须走 CLI 时**：先 `cua-driver call list_windows pid=<pid>` 拿 window_id，再传

**修复方向**：本机实测发现 MCP 工具也是同样的 daemon 验证（详见坑 2），所以**走 CLI 不走 CLI 都不能解决——这条路整体废弃**。

## 坑 2：Chrome 默认关闭 AppleScript JS 执行

绕开坑 1 用 MCP 工具 `mcp__cua_driver_page` 后报：

```
osascript error: 'Google Chrome'遇到一个错误:
通过 AppleScript 执行 JavaScript 的功能已关闭。
要开启此功能，请在菜单栏中依次转到'查看'>'开发者'>'允许 Apple 事件中的 JavaScript'。
```

**关键事实**：
- 这是 **Chrome 自身的开关**（不是 cua-driver 的问题）
- **OFF by default** ——每次 Chrome 升级/重装可能回退
- cua-driver 调 `page.*` action 走 AppleScript → 必须开
- 路径：Chrome 菜单 → View → Developer → **Allow JavaScript from Apple Events**

## 真实可行方案

| 方案 | 适用 | 配置成本 |
|------|------|----------|
| **playwright_extract.py**（本 skill v2.0.0 提供）| JS 渲染页 | `playwright install chromium` 5-10 分钟 |
| **fetch_url.py --js**（本 skill 接入）| Trafilatura 不够时自动升级 | 同上 |
| **fetch_url.py**（Trafilatura 主路）| 95% 静态页 | 零配置 |
| **browser_navigate + DOM**（CDP）| 真 Chrome + 拿 cookies | 抢焦点 |

**cua-driver 调 `page.*` 在 macOS 默认 Chrome 上基本不能用**——除非用户先手动开 AppleScript JS 开关（且每次升级要重开）。v2.0.0 已弃用此路径。

## 抓页降级链（修正后）

```
抓 URL 内容
 ├─ fetch_url.py (Trafilatura)        ← 静态页面主路（5s，零配置）
 ├─ fetch_url.py --js                 ← Trafilatura 不够时自动升 Playwright
 ├─ playwright_extract.py             ← JS 渲染场景（独立调）
 └─ curl + html2text                  ← 终极兜底
```

cua-driver 在抓页场景 **不出现**——它只做 GUI 操作（launch/click/hotkey/type），这是它最稳的部分。

## 历史踩坑时间线

- **2026-06-07 09:08** v1.0.0 写出 cua_extract.py，未跑通
- **2026-06-07 10:00** 端到端验证翻车：empty_content
- **2026-06-07 10:30** 定位坑 1（window_id）
- **2026-06-07 11:00** 定位坑 2（AppleScript JS）—— 决定整体弃用
- **2026-06-07 11:30** v2.0.0 重构：cua-driver 回到 GUI，Playwright 接抓页
