---
name: cc-haha-architecture
description: "cc-haha 架构精髓 — 分层解耦、Python Bridge、9层安全关卡、Project Memory树形结构、Plugin热重载。来源：NanmiCoder/cc-haha (11.2k stars, 基于Claude Code泄露源码)"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  source: https://github.com/NanmiCoder/cc-haha
  stars: 11.2k
  commits: 794
---

# cc-haha 架构精髓

cc-haha 是基于 2026-03-31 从 Anthropic npm registry 泄露的 Claude Code 源码修复而来的跨平台桌面端 Claude Code 工作台（TypeScript + Tauri 2 + React）。

核心价值：从泄露源码中提取了「分层解耦 + 替换底层」的实现思路，可借鉴到 Hermes 的 computer use 和具身智能架构中。

## 一、分层解耦（最重要）

cc-haha 保留了原始 MCP 工具定义和安全机制不变，只替换底层执行层：

```
Layer 1 — MCP 工具接口层（24个工具schema）← 不改
Layer 2 — 安全关卡（9层）← 不改
Layer 3 — 会话上下文 + 全局锁 + 截图缓存 ← 不改
Layer 4 — CLI 集成（权限对话框 + 状态读写）← 不改
Layer 5 — Python Bridge（进程通信层）← 替换为
Layer 6 — Python 运行时（pyautogui + mss + pyobjc）← 替换为
```

**核心思路**：不改原始接口和安全机制，只换底层实现。这样在 Anthropic 更新工具定义时，可以同步更新而不需要重新实现所有逻辑。

**对 Hermes 的启发**：
- Hermes 的 computer use 也可以这样分层
- skill 协议不变，只换执行层实现
- 安全关卡可以复用 cc-haha 的设计

## 二、Python Bridge 机制

TypeScript (Bun) → JSON RPC → Python (venv) 架构：

```typescript
// executor.ts
callPythonHelper('click', payload) → execFile → mac_helper.py → pyautogui
```

**启动引导流程**：
1. 检查 venv 是否存在 → 不存在则创建
2. 检查 pip 是否可用 → 不可用则运行 ensurepip
3. 检查 requirements.txt 依赖 → 缺失则安装
4. 启动 mac_helper.py 主循环

**依赖清单**：
| 库 | 用途 |
|---|---|
| mss | 高性能屏幕截图 |
| Pillow | JPEG 编码 |
| pyautogui | 鼠标点击、键盘输入 |
| pyobjc-core | macOS 桥接 |
| pyobjc-framework-Cocoa | NSWorkspace、NSPasteboard |
| pyobjc-framework-Quartz | CGDisplay、CGWindow |

**对 Hermes 的启发**：
- Hermes 的 computer use 可以用 Python subprocess 做执行层
- TS/Python 通信走 JSON RPC，简洁高效
- venv 隔离避免依赖冲突

## 三、9层安全关卡体系

| 关卡 | 名称 | 检查内容 | Hermes现状 |
|---|---|---|---|
| 1 | Kill Switch | `getChicagoEnabled()` → 永远 `return true` | 无 |
| 2 | TCC 权限 | Accessibility + Screen Recording | `mcp_cua_check_permissions` |
| 3 | 全局互斥锁 | `~/.claude/computer-use.lock` 文件锁 | 无 |
| 4 | 白名单应用隐藏 | 隐藏非白名单应用窗口 | 无 |
| 5 | 前台应用检查 | 当前前台必须在已授权应用 | 无 |
| 6 | 权限等级检查 | read < click < full 三级 | 无 |
| 7 | 剪贴板防护 | click-tier 应用前台时清空剪贴板 | 无 |
| 8 | 像素验证 | 对比上次截图与当前屏幕像素 | 无 |
| 9 | 系统快捷键拦截 | 阻止 ⌘Q、⌘Tab 等 | 无 |

**三级权限模型**：
| Tier | 允许的操作 | 禁止的操作 |
|---|---|---|
| `read` | 截图查看 | 任何输入 |
| `click` | 左键点击、滚动 | 右键、拖拽、键盘 |
| `full` | 全部操作 | 无 |

**对 Hermes 的启发**：可以借鉴这套关卡体系，建立 Hermes computer use 的安全模型。

## 四、应用分类系统

191 个 Bundle ID 分类：

| 类别 | 数量 | 权限等级 | 代表应用 |
|---|---|---|---|
| 浏览器 | 55 | read | Safari, Chrome, Firefox, Arc |
| 终端 | 102 | click | Terminal, iTerm2, VS Code, Xcode |
| 交易 | 34 | read | Webull, Fidelity, Binance, Kraken |
| 完全禁止 | — | 拒绝 | Netflix, Spotify, Apple Music, Kindle |

**对 Hermes 的启发**：Hermes 的 computer use 可以建立类似的应用白名单，对不同应用分配不同权限级别。

## 五、Project Memory 树形结构

v0.2.7 从散列列表升级为项目树导航：

- 记忆路径恢复优先级：`cwd` → session元数据 → 真实文件系统
- 支持中文路径、空格路径
- 设置页面改为树形导航
- 移除手动创建记忆文件的方式

**对 Hermes 的启发**：供应商记忆系统也可以用树形结构组织，比散列表更易用。

## 六、Plugin/Skills 热重载

cc-haha 的 stop/start plugin 后自动刷新：
- slash commands
- skills
- CLI 设置
- 当前 session plugin 命令

**不需要重启进程**，这是非常实用的功能。

**对 Hermes 的启发**：Hermes 目前不支持热重载，改完 skill 需要重启 gateway。这个功能值得借鉴。

## 七、会话按项目分组

- 按 `project root` 分组会话
- worktree session 合并到源项目
- 排序、隐藏、置顶等偏好持久化到 `~/.claude/cc-haha`

**对 Hermes 的启发**：多会话管理可以借鉴这个设计，按项目组织而不是平铺。

## 参考资料

- 官方文档：https://hermes-agent.nousresearch.com/docs
- GitHub：https://github.com/NousResearch/hermes-agent
- Discord：Nous Research Discord
- cc-haha：https://github.com/NanmiCoder/cc-haha
- cc-haha Computer Use 架构：https://github.com/NanmiCoder/cc-haha/blob/main/docs/features/computer-use-architecture.md