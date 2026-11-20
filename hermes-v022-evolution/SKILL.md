---
name: hermes-v022-evolution
description: "Hermes v0.22.5 新特性速查。Use when 升级或配 MCP。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Hermes, v0.22.5, connectors, mcp, best-practices, evolution]
    category: autonomous-ai-agents
---

# Hermes Agent v0.22.5 进化速查

## When to Use

升级 Hermes、配置 connectors/MCP、选模型、或排障 Hermes v0.22.x 时加载。

## 版本基线
- 当前稳定版 v0.22.5 (2026-10-22)，~81 PRs 自 v0.22.4。
- 主干 v0.22.0 Threshold Release (2026-10-14)：connectors、local models、stable channels、plugin catalog 600+。

## 关键新能力
- **Connectors**：Hermes 通过 Nous tool gateway 操作 Linear/Notion 等 hosted apps，浏览器一次登录即可；无 Nous 账号也能用（首次自动建 connectors-only 身份）。
- **Local models 一键**：本地跑 open model，无账号无 API key；自动装 llama.cpp（CPU/CUDA/Metal/Vulkan/ROCm），按 GPU/RAM 评分选最高质量 build。
- **Plugin catalog 600+**：每条 pin 到 reviewed commit，Desktop/CLI 安装；`hermes plugins install <name>`。
- **Password manager 登录网站**：浏览器 agent 可用 1Password/Bitwarden/Hermes 加密 vault 登录，模型永远看不到密码；无保存时 CLI/TUI/Desktop 弹出掩码提示保存；OTP 自动填充。
- **Claude 5.5 / GPT-6 / Gemini 4** 模型波：Fable 5.1、Opus 5.5、Sonnet 5.5、Haiku 5.5、GPT-6 Astra/Sol/Luna、GPT-6.1 Sol、Gemini 4 Argon。
- **model_overrides**：自定义任意模型的 context window / 定价，无需等 release。
- **hermes mcp serve → mcp-serve plugin**：Hermes 作为 MCP server，`hermes plugins install mcp-serve`；`hermes mcp serve` 现打印新拼写。`--tools` 暴露 web/browser/vision/skills/TTS（terminal/file 永不暴露）。
- **Pluggable delegation backends**：子 agent 按 model map 或 profile 路由，会话可切换。
- **OpenClaw migration**：`hermes import-agent` + setup 提供 importer。
- **Usage-window plan support**：plan gauges、limit cards、model-switch recovery。

## MCP 新特性 (v0.22)
- Trust tier：`trust: full` (默认) / `untrusted`（写操作需审批）；unrecognized → untrusted（fail-closed）。
- `tool_costs` / `spend_limit` / `cost_unit`：按工具计费，审批提示显示成本与累计。
- OAuth 2.1 + PKCE（`auth: oauth`）；lazy connect + schema cache；events client（webhook）。
- `protocol: auto/stateless/legacy` 协商。

## 最佳实践 (官方 Tips)
- AGENTS.md 放项目约定；SOUL.md 放人格；.cursorrules 兼容。
- Memory 存事实，Skills 存流程；5+ 步重复任务 → 创建 skill。
- `/compress` 前 `/usage`；delegate_task 并行研究；execute_code 批量操作。
- 模型切换重置 prompt cache；长会话频繁切换不如新开会话。
- 审批 “always” 谨慎；deny 规则防 honest-but-wrong agent。
- 容器 backend 跳过危险命令检查（容器即边界）。
- Checkpoints opt-in：`checkpoints.enabled: true` + `/rollback`。

## 已知限制 / 排障
- `hermes update` 拉新代码后需重启 gateway（kill -HUP pgrep hermes_cli.main gateway）。
- git 二进制架构不匹配时 plugin install 失败（Bad CPU type in executable）→ 需装 arm64 git 或用 HTTPS 直连。
- keras skill 有 update_available 但本地有编辑 → `hermes skills update keras --force` 会覆盖本地定制，慎用。
- `hermes skills check` MCP catalog 错误（'str' object has no attribute 'get'）通常是 config.yaml 某 MCP server 配成字符串而非字典。

## 进化决策记录 (2026-10-24 夜间)
- 评估：keras update（跳过，保护本地编辑）；mcp-serve plugin（git 架构问题失败）。
- 落实：创建本 skill 记录 v0.22.5 特性与最佳实践（零依赖，自包含）。
- 下一步：装 arm64 git 后重试 mcp-serve；考虑 decision-questionnaire / setup-wizard-generator 官方 optional skill。
