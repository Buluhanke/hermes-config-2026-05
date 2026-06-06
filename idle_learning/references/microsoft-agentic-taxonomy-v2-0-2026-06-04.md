# Microsoft AI Red Team: Taxonomy of Failure Modes in Agentic AI Systems v2.0

**来源**: Microsoft Security Blog, June 4, 2026
**URL**: https://www.microsoft.com/en-us/security/blog/2026/06/04/updating-taxonomy-failure-modes-agentic-ai-systems-year-red-teaming-taught-us/
**PDF**: https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/security/Taxonomy-of-Failure-Modes-in-Agentic-AI-Systems-v2-0.pdf

## 概述

微软 AI 红队基于 12 个月实战红队经验，将 agentic AI 失败模式分类从 v1.0 的 27 项扩展到 v2.0 的 34 项，新增 7 大失败模式。

## 新增 7 大失败模式

### 1. Agentic Supply Chain Compromise
- **攻击面**: agent 行为可通过**自然语言**而非恶意代码被影响
- **Hermes 映射**: SKILL.md loading — 恶意 skill 可通过自然语言指令操控 agent
- **风险**: HIGH（与 Hermes delegate_task 架构直接相关）

### 2. Goal Hijacking
- **攻击面**: 对抗性指令伪装成合法任务完成，暗中重定向 agent 终端目标
- **Hermes 映射**: prompt injection → task 重定向
- **风险**: MEDIUM

### 3. Inter-Agent Trust Escalation
- **攻击面**: 多 agent 间信任关系被恶意利用
- **Hermes 映射**: **delegate_task subagent 自汇报不验证** — 父 agent 信任 subagent 的 self-report summary
- **风险**: **HIGH**（直接架构映射）

### 4. Computer-Use Agent Visual Attack
- **攻击面**: UI overlay / 伪造按钮 / 视觉欺骗
- **Hermes 映射**: screen_watcher + CUA 执行层
- **风险**: MEDIUM

### 5. Session Context Contamination
- **攻击面**: 会话上下文被污染，影响后续决策
- **Hermes 映射**: memory/SOUL.md 被污染 → 跨 session 持久化
- **风险**: MEDIUM

### 6. Zero-Click Human-in-the-Loop Bypass
- **攻击面**: 无需用户点击，仅通过视觉层操控即可 bypass human-in-the-loop 确认
- **Hermes 映射**: DRY_RUN=False 后暴露此攻击面
- **风险**: MEDIUM（当前 DRY_RUN=True 不暴露）

### 7. MCP/Plugin Abuse
- **攻击面**: MCP 协议和插件系统被滥用
- **Hermes 映射**: Hermes 使用 skills 而非 MCP，但 skills loading 有类似脆弱性
- **风险**: LOW

## Mitigation Families（5 个缓解族）

微软建议在 v2.0 中引入 5 个缓解策略族（具体细节见 PDF 全文）。

## Hermes 行动项

- [ ] DRY_RUN=False 前加入 intent validation 层
- [ ] delegate_task 加入 subagent 执行日志跟踪（非 self-report 验证）
- [ ] SKILL.md loading 加入 integrity check
- [ ] 持续跟踪此 taxonomy 更新
