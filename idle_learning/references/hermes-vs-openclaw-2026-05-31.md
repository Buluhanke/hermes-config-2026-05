# Hermes vs OpenClaw 竞品分析（2026-05-31）

**来源**：dev.to WanjohiChristopher（2026-05-23），HN 热点

## 核心数据对比

| 维度 | Hermes Agent | OpenClaw |
|------|-------------|----------|
| GitHub stars | 163k | 374k |
| 发起方 | Nous Research | openclaw org（OpenAI/GitHub/NVIDIA/Vercel 赞助） |
| 语言 | Python | TypeScript（Node 22.19+） |
| 核心差异 | **自进化闭环**：self-improving skills + agent-curated memory | **Live Canvas**：可视化工作区 + 跨平台原生 APP |
| 渠道覆盖 | Telegram/Discord/Slack/WhatsApp/Signal/Email/CLI | 22+（含 iMessage/微信/QQ/Matrix/Feishu 等） |
| Skills 标准 | agentskills.io + Honcho | ClawHub registry |
| 工具 | MCP-native，40+ 内置，RPC subagents | Browser/canvas/nodes/cron/sessions |
| 托管 | Local/Docker/SSH/Singularity/Modal/Daytona/Vercel | Local Gateway 控制面 + macOS/iOS/Android APP |
| 理想用户 | 想要跨 session 自学习的开发者 | 想要多设备多渠道开箱即用助手的用户 |

## 关键洞察

1. **Hermes 自进化能力是核心差异**：记忆变成反馈闭环而非静态存储。每天使用后 agent 变聪明。
2. **OpenClaw 生态更完整**：22+ channels，多平台原生 APP，大厂背书，社区更大。
3. **Hermes 在 OpenRouter 排名 #1**（2026-05-10）：说明在真实使用量上已经超过 OpenClaw。
4. **OpenClaw 正在尝试迁移用户**：文章暗示 OpenClaw 在引导用户从 Hermes 迁移到 OpenClaw。

## 对 Hermes 义乌贸易的实际意义

- Hermes 的 self-improving skills 对**高频重复任务**（如 1688 找品、比价、监控）有天然优势
- OpenClaw 的微信/QQ 支持对国内用户更有吸引力，但 Hermes 通过 Telegram/飞书等也可覆盖
- Hermes 的 MCP-native 架构 vs OpenClaw 的 ClawHub — Hermes 更轻量，适合树莓派级别的 Mac Mini M4

## HN 关联热点

- OpenRouter Series B $113M（275pts）：AI model routing 成为基础设施赛道，Hermes 如果支持 OpenRouter 调度可受益
