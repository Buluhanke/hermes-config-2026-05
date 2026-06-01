# webpro255/awesome-ai-agent-attacks — AI Agent Security Timeline (2024-2026)

**来源**：https://github.com/webpro255/awesome-ai-agent-attacks
**发现日期**：2026-06-02
**仓库最后更新**：2026-04-28
**状态**：未覆盖新发现（7 条事件不在 learning_log 中）

---

## 未覆盖事件

| # | 日期 | 事件 | CVE/Impact |
|---|------|------|-----------|
| 1 | 2026-04-24 | LangChain SSRF (langchain-openai + text-splitters) — TOCTOU in URL validation | CVE-2026-41488 (CVSS 3.1), CVE-2026-41481 (CVSS 6.5) |
| 2 | 2026-04-23 | HexagonalRodent — NK APT (Lazarus) uses Cursor/ChatGPT for developer attacks | 2,726 systems infected, $12M crypto stolen |
| 3 | 2026-04-22 | Bitwarden CLI npm trojanized via Checkmarx KICS supply chain cascade | 334 pulls, full credential harvesting |
| 4 | 2026-04-22 | Xinference PyPI compromised (3 consecutive malicious versions) | 600K+ download AI inference framework |
| 5 | 2026-04-21 | LMDeploy SSRF exploited **12.5h after public disclosure** | CVE-2026-33626 (CVSS 7.5) |
| 6 | 2026-04-21 | CanisterSprawl — self-propagating npm worm via Namastex Labs/pgserve | 16 malicious versions, ICP-canister C2 |
| 7 | 2026-04-21 | CSA survey: 65% enterprises had AI agent incidents | 418 orgs, 82% found unknown agents |

## 方向 C 巡检建议

- 后续轮次检查该仓库 README 中 "Last updated:" 字段是否有变化
- LMDeploy 的 13h exploit window 说明 AI 基础设施补丁窗口极短
- CanisterSprawl 的 npm→PyPI 跨生态传播映射 agent 供应链风险
