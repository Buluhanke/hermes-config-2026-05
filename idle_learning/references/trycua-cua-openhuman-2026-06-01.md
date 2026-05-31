# trycua/cua + OpenHuman — 开源计算机使用框架调研 (2026-06-01)

## trycua/cua (17.4k★, 3,460 commits, 1.1k forks, MIT)

GitHub: `github.com/trycua/cua` — 开源计算机使用基础设施。

### Cua Driver
- **核心**：Rust + Swift 实现的 macOS 后台桌面驱动（不抢焦点），与 Hermes `computer_use` 相同理念
- **架构**：CGEventTap + AX API（和 Hermes 一致），MCP-over-stdio 协议
- **工具输出格式**：人类可读文本而非结构化 JSON（"✅ Posted click to pid 6808"）
- **zoom 工具**：支持 `from_zoom=true` 自动坐标映射（Hermes 缺少此功能）
- **get_window_state**：对非标准 app（Blender/Electron/游戏）发出 ⚠️ 警告
- **安装**：`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"`
- CLI + MCP server 双模式，从 Claude Code / Cursor / Codex / OpenClaw 均可调用

### Cua Sandbox
- 统一 API 操作 Linux/macOS/Windows/Android 沙箱
- 云（cua.ai）和本地（QEMU）两种运行模式
- SDK: `pip install cua`，Python 3.11+

### CuaBot (Multi-Player Computer-Use)
- **全球首个**多 player computer-use（Feb 2026, ClawCon 发布）
- 同一屏幕上两个光标（agent + human）共存
- 人类可随时 takeover agent 动作
- `npx cuabot` 一键启动
- 内置 agent-browser 和 agent-device（iOS/Android）支持

### Lume — macOS 虚拟化
- 基于 Apple Virtualization.Framework
- `lume run macos-sequoia-vanilla:latest` 一键启动 macOS VM
- 可在本地跑完整的沙箱测试环境而不污染主桌面

### Cua VLM Router
- 统一 API key 访问所有 computer-use 模型
- 三级分类：Full CU / Browser-Only / Grounding-Only
- 与 AVR 三级路由概念完全一致，已验证生产可用

### Cua Bench
- 评测 agent 在 OSWorld / ScreenSpot / Windows Arena 上的表现
- 支持导出轨迹用于训练

### Blog 重要文章
- **Multi-Player Computer-Use**（Feb 2026）：cua.ai/blog
- **Human-In-The-Loop**（Aug 2025）：agent workflow checkpoint + 人工审批
- **Composite Agents**（Aug 2025, Agent Framework 0.4）：planner + executor 分离
- **Cua × HUD**（Aug 2025）：评测任意 computer-use agent

### 对 Hermes 的价值
- cua-driver 的 zoom→click 坐标映射链（`from_zoom=true`）可直接借鉴到 auto_execute
- Human-In-The-Loop = SafeGround defer-to-human 的生产实现
- Composite Agents = 验证 Hermes scene classifier → action executor 架构
- Lume 可用于本地跑测试沙箱，避免污染主桌面

---

## OpenHuman（May 2026, 韩 HN #1）

开源桌面 AI agent，位于：github.com/openhuman

### 五大核心能力
1. **Always-On 上下文引擎**：监控 active window / clipboard / filesystem events
2. **跨应用自动化 pipeline**：自然语言定义 workflow
3. **插件架构**：JS/TS + Python
4. **多 LLM 后端**：云（GPT/Claude/Gemini）+ 本地（Ollama/llama.cpp）
5. **长期记忆系统**：本地 DB，可导出删除

### 与 Hermes 对比
| 维度 | OpenHuman | Hermes |
|------|-----------|--------|
| 定位 | Proactive assistant | Agentic execution framework |
| 上下文引擎 | 类似 screen_watcher | screen_watcher + handler |
| LLM 路由 | 简单搬移 | AVR 三级路由（设计阶段） |
| 执行 | 应用 API 为主 | CGEventTap + cliclick |
| 架构 | 单体 | SOUL + Skills + Memory 三件套 |

### 对 Hermes 的价值
- OpenHuman 的 context engine 实现（active window + clipboard + filesystem 三重监控）可参考改进 screen_watcher 的场景配置
- OpenHuman 插件架构 = Hermes Skills 的同类设计
