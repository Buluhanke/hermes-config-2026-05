# macOS GUI-Automation Stack — 2026-06-07 完整决策矩阵

本文档是 `macos-computer-use` skill "ecosystem" 小节的参考资料。
当你不确定该用 cua-driver MCP、Peekaboo CLI、还是别的工具时，查这个表。

## 三个桌面控制路径

来源：[OpenClaw Peekaboo bridge docs](https://docs.openclaw.ai/platforms/mac/peekaboo)
原文："OpenClaw has three desktop-control paths, and they intentionally stay separate"

### Path A — cua-driver MCP（TryCua）

- **项目**：[trycua/cua](https://github.com/trycua/cua) — `cua-driver` 是其 Rust 端口
- **形态**：MCP server（stdio），Hermes 通过 `mcp_cua_driver_*` 工具调用
- **核心特性**：
  - **后台运行**（不抢用户光标、键盘焦点、Space）
  - 跨平台：macOS / Windows / Linux (pre-release)
  - pid/window/element-index 工作流
  - 跨 harness：Claude Code / Cursor / Codex / OpenClaw / 自定义客户端
- **安装**：`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"`
- **权限**：需要 Accessibility + Screen Recording
- **维护方**：TryCua（独立项目，OpenClaw 生态之外）

### Path B — Peekaboo v3（OpenClaw / Peter Steinberger）

- **项目**：[openclaw/Peekaboo](https://github.com/openclaw/Peekaboo)
- **形态**：macOS CLI（`peekaboo` 命令）+ 可选 MCP server
- **核心特性**：
  - **需要前台窗口**（会抢用户焦点）
  - 5/9/2026 发布 v3.0.0，当日连更 3 次（v3.0.0-beta 1/2/3）
  - 当前最新 v3.1.2（5/11 构建）
  - v3 比 v2 强的地方：v2 只能截图，v3 能像人一样操作 Mac（"Playwright but for the OS"）
  - Action-first 自动化（AX 树 → 直接点元素，合成输入兜底）
  - 通过 PeekabooBridge 借用 OpenClaw.app 的 TCC 权限
- **安装**：`brew install steipete/tap/peekaboo`
- **权限**：需要 Screen Recording + Accessibility + Event Synthesizing
- **维护方**：Peter Steinberger @steipete（**已加入 OpenAI**——项目长期维护存疑）

### Path C — OpenClaw Codex Computer Use

- **形态**：Codex app-server + Codex computer-use MCP server
- **使用场景**：Codex-mode agent 依赖 Codex 的原生 computer-use 插件
- **集成**：OpenClaw 不代理这些操作通过 PeekabooBridge

## 三个路径的关系（官方图）

```
┌─────────────────────────────────────┐
│  Codex Computer Use  (Path C)       │
│  (Codex-mode only)                   │
└──────────────┬──────────────────────┘
               │
               │  OpenClaw.app 桥接
               ↓
┌─────────────────────────────────────┐
│  PeekabooBridge  (Path B 主机)      │
│  - Peekaboo.app (full UX)          │
│  - Claude.app (if installed)        │
│  - OpenClaw.app (thin broker)       │
└──────────────┬──────────────────────┘
               │
               │  peekaboo CLI 客户端
               ↓
┌─────────────────────────────────────┐
│  Peekaboo v3 CLI                    │
│  暴露 AX 树、SOM 索引、操作原语     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  cua-driver MCP (Path A)            │
│  独立于 OpenClaw / Peekaboo         │
│  Hermes 通过 mcp__ 工具直连         │
└─────────────────────────────────────┘
```

**关键事实**：cua-driver MCP **不走** PeekabooBridge，是**完全独立**的另一条路。

## 决策矩阵（什么场景用哪个）

| 任务 | 首选 | 理由 |
|------|------|------|
| 后台点 Safari 按钮 | **cua-driver MCP** | `mcp_cua_driver_click` 元素索引，不抢焦点 |
| 后台键盘输入 | **cua-driver MCP** | `mcp_cua_driver_type_text` 不抢焦点 |
| 跨 Space 操作 | **cua-driver MCP** | 不需要切 Space |
| 抓 Dock 菜单 | Peekaboo | `peekaboo list` Dock 表面，cua-driver 不暴露 |
| 抓 Menu Bar 图标 | Peekaboo | `peekaboo click` 菜单栏，cua-driver 不暴露 |
| 处理系统弹窗 | Peekaboo | `peekaboo click` 弹窗按钮，更可靠 |
| 自动化 Finder | **cua-driver MCP** | 通用 AX 树操作够用 |
| 拖拽文件 | **cua-driver MCP** | `mcp_cua_driver_drag` 元素索引 |
| 用户在前台用电脑时跑自动化 | **cua-driver MCP** | 唯一不抢焦点的方案 |
| Windows / Linux | **cua-driver MCP** | Peekaboo macOS only |
| 在 Codex-mode agent 里 | OpenClaw Codex Computer Use (Path C) | Codex 自己的插件 |

## 实测：本机环境

| 工具 | 状态 | 权限 | 来源 |
|------|------|------|------|
| CuaDriver.app + `cua-driver mcp` | ✅ 装好且在跑 | ✅ Screen Recording + Accessibility + Event Synth | TryCua upstream |
| Peekaboo v3.1.2 | ✅ 装好 | ✅ Screen Recording + Accessibility + Event Synth | `steipete/tap` |
| OpenClaw.app | ❌ 没装 | — | — |

**结论**：本机两个互补工具**都已齐全**。cua-driver 是日常主力（不抢焦点），Peekaboo 是 menu bar / Dock 的补充。

## 何时**不**该装新东西

❌ **不要因为看到 "Peter 发了 Peekaboo v3" 新闻就重装**——已经装好 1 个月了。
❌ **不要装 OpenClaw.app**——CuaDriver 已经满足 95% 的需求，加 OpenClaw.app 反而引入更多桥接层。
❌ **不要因为 "X 不稳" 就重装 cua-driver**——它是 OpenClaw 生态**之外**的独立项目，不会受 Peter 加入 OpenAI 的影响。

## 排除清单（本机已实测）

| 工具/服务 | 排除原因 | 时间 |
|----------|---------|------|
| Peekaboo 替代品（Crawl4AI 等）| 本任务不需要截图/视觉理解 | 2026-06-07 |
| 自建 OpenClaw.app | CuaDriver 已覆盖 | 2026-06-07 |

## 相关 skill 维护记录

- `macos-computer-use` v1.1.0：本文档是其补充资料
- `tool-stack-evolution` v1.0.0：本文档是其"先盘点当下再决定装新"方法论的应用
