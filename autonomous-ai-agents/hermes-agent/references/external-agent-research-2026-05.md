# 外部 Agent 工具研究笔记

本 session 评估了 4 个 GitHub 项目，结论供未来参考。

## gstack — https://github.com/garrytan/gstack
**85K stars** | AI 工程工作流 | MIT

Garry Tan（Y Combinator CEO）每天使用的开发框架。23 个专家角色（CEO 评审、eng manager、QA lead、安全审计、设计师等），给 Claude Code 用。

**包含技能**：`/office-hours`、`/plan-ceo-review`、`/review`、`/qa`、`/ship`、`/browse`（headless 浏览器）、`/cso`（OWASP+STRIDE 安全审计）等 40+。

**安装**：`~/.claude/skills/gstack/` + `bun install`

**限制**：需要 Claude Code desktop app 启动才能加载 skills。此 Mac 无头环境，`claude` CLI 报 Electron helper 缺失。skills 文件已就位，桌面环境就绪后自动生效。

**结论**：开发者工具，对当前 1688 找品任务无直接帮助。长期有价值。

---

## gbrain — https://github.com/garrytan/gbrain
**11K stars** | 知识图谱记忆 | MIT

AI Agent 记忆大脑，知识图谱 + 混合搜索。P@5 49.1%，Benchmarked 超过纯向量检索 +31.4 分。自连接实体关系（`attended`、`works_at`、`invested_in` 等）。

**安装**（已在本机完成）：
```bash
git clone https://github.com/garrytan/gbrain.git ~/gbrain
cd ~/gbrain && bun install
ln -sf ~/gbrain/src/cli.ts ~/.local/bin/gbrain
chmod +x ~/.local/bin/gbrain
cd ~/gbrain && bun run src/cli.ts skillpack install --all   # 39 skills
cd ~/gbrain && bun run src/cli.ts init                      # → ~/.gbrain/brain.pglite
```

**MCP 接入 Hermes**：`config.yaml` → `mcp_servers.gbrain.command: /Users/mac/.local/bin/gbrain`

**结论**：✅ 最有价值的外部工具，显著提升任何 Agent 的记忆能力。对 1688 找品长期有用（跨 session 追踪供应商历史）。

---

## OpenHarness — https://github.com/HKUDS/OpenHarness
轻量级 Agent 框架 | HKUDS | MIT

核心模块：Agent Loop（流式工具调用+重试+并行）、Harness Toolkit（43 工具，SKILL.md 按需加载）、Context & Memory（Auto-Compact）、Governance（多级权限+钩子）、Swarm Coordination。

`oh` CLI 启动，兼容 Claude Code/Codex/Cursor/nanobot。

**结论**：低优先级，和 Hermes 功能重叠，已在本机安装 `openharness-ai`（pip）。框架层面的研究价值，非直接使用价值。

---

## hermes-agent-self-evolution — https://github.com/NousResearch/hermes-agent-self-evolution
**2.4K stars** | 自我进化 | MIT

DSPy + GEPA（Genetic-Pareto Prompt Evolution）自动进化 Hermes skills、prompt、tool descriptions。ICLR 2026 Oral。`$2-10/次`，无 GPU 训练需求。

Phase 1 已实现：Skill 文件优化（DSPy + GEPA）。Phase 2-5（tool descriptions、system prompt、代码进化）规划中。

**安装**（已在本机完成）：
```bash
pip install -e ~/hermes-agent-self-evolution
```

**结论**：开发者工具，给自己优化 Hermes 技能用的。已有知识，备用。
