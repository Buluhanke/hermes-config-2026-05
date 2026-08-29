---
name: agent-landscape-2026
description: 2026 agent全景：自演化/基准/编排。Use when 选型agent框架。
triggers:
  - agent 框架选型
  - browser agent 基准
  - self-improving agent
  - multi-agent orchestration
  - Hermes 版本更新
  - 2026 agent 进展
---

# Agent Landscape 2026 — 提炼自 hermes-self-research 自学

本 skill 固化 2026 年 AI agent 领域的关键事实，供选型/写作/进化时快速查证。
所有条目均有具体数字或框架名，已在 fact_store 留存（fact_id 1269–1281），此处为可执行摘要。

## 1. Self-Evolving Agents（自演化 agent）

核心范式转变：**系统/scaffold 设计 > 单模型能力**。冻结 LLM、演化 harness/资产/经验。

- **Mendel Gödel Machine (arXiv 2608.07645)**：档案式自改进 coding agent。在克隆突变外新增「反应规范突变」(跨多任务轨迹条件编辑) +「跨谱系杂交」(用参考 agent 同任务轨迹)。Qwen3.6-35B-A3B 在 Polyglot 50.8%→93.3%，超闭源 GPT-5，参数少 ~117×；迁移到 DeepSeek-V4-Pro 达 96.9%。
- **Mem2Evolve (ACL 2026)**：双记忆协同演化——Asset Memory(专家agent/工具) + Experience Memory(提炼经验)。从极简 Web Search 工具起步，GAIA +57.84%、AIME24/25 +10.03%/+13.33%；平均超纯能力基线 Alita 6.46%。
- **HSI 分层自改进 (arXiv 2608.08466)**：冻结 LLM 演化自身 harness(H)，三层作用域(task harness / evolver / meta-evolver，外层锚点冻结)。BALROG +39.3 BabyAI / +33.0 Crafter。两道上限：反馈保真度 + 骨干能力。
- **MARS 元认知 (ACL 2026)**：单周期自改进(原则反思 what-to-avoid + 程序反思 how-to-succeed)，~25-30× 省算力超多轮递归的 Gödel Agent。

## 2. Browser-Agent 基准（2026 实测）

- **WebVoyager 已饱和**：Alumnium 98.5%、Browser Use 89.1%、CUA 87% → 不再是区分度指标。
- **Online-Mind2Web 成 live-web 标准**：Browser Use Cloud(bu-max) 97.0% 领先；300 任务/136 真实站点。
- **WebArena 仍难**：OpenAI CUA 58.1% vs 人类 ~78% → 真实电商/CMS 工作流差距大。
- **OSWorld-Verified 桌面**：Claude Fable 5 85.0% / Opus 4.8 83.4% / GPT-5.5 78.7% / Gemini 3.5 Flash 78.4%（均超 ~72% 人类基线，短程）。
- **OSWorld 2.0 (2026-06-26)**：108 长程任务/7 专业域，均值 318 tool calls；Opus 4.8 仅 20.6%(500步,244K tokens)；最大失败模式=隐藏状态维护(39.8%)。作者承认 v1.0 的 83.5% 已停止测量真实问题。
- **CAP (arXiv 2608.08392)**：420 跨站任务/108 站点，最优 Manus 仅 8.0%（人类 10% full / 35% partial）。**perception 比 execution 更重瓶颈**(Comet 67% Complex-A vs 58% Complex-P)。
- **Wuying-Browser-Agent-27B (arXiv 2608.17319)**：开源 SOTA——80.6% WebVoyager / 66.7% Online-Mind2Web / 65.1% BrowserBench(350 双语任务,均 37.9 步)；配套 BrowserBench 填补长程双语空白。
- **LexBench-Browser (browseruse-agent-bench)**：210 任务/107 站点可复现评测，`bubench` CLI 跑 Agent×Model×Browser×Eval + LLM-as-Judge + 成本/延迟指标。
- **CUA-HandCrafted (NeurIPS 2026)**：对抗基准，793 episode。浏览器 CUA 对 prompt injection 鲁棒(Claude Sonnet 4.6 / GPT-5.4 = 0/140 ASR)，但同一权重在 coding agent 上可被 100% skill-injection → browser 比 coding 更抗注入。

## 3. Multi-Agent 编排框架（2026 新秀）

选型要点：**goal-first**(运行时生成 DAG) 优于 graph-first(手写节点)。

- **open-multi-agent** (TS, 6836★, MIT)：`runTeam(goal)` 运行时把目标拆成 task DAG，自动并行；离线 Run Viewer 重放；9 原生 provider + OpenAI 兼容。
- **orxhestra** (Python)：YAML 声明 agent teams，async 流事件，A2A+MCP，29 provider；`orx my-agents.yaml` / `--serve` 当 A2A server。
- **Orloj** (Go/声明式全栈)：agents/tools/policies YAML，Postgres+NATS workers，治理 fail-closed(权限/审批/重试/可观测全内置)。
- **GAIA** ("K8s-for-agents", Go)：确定性 DAG kernel + CEL 策略防火墙，A2A+MCP，4 级升级(Retry→Fallback→Replan→Abort)，SHA-256 审计链。
- **Overseer** (质量内嵌 runtime)：Verifier 是一等节点(verdict=pass/fail/retry/escalate)，每节点前写 SQLite snapshot，重试耗尽则阻塞在目标节点等人介入。
- **OpenHive / aden-hive** (10986★)：Queen+worker clones  colony 模型，共享 tracker ledger，Sentinel 人类 in-loop(暂停落盘→回复恢复)，crash-safe resume。

## 4. Hermes Agent 版本跟踪

- **v0.20.6 (2026-08-27)**：~525 PRs。真实 profile 浏览(同意门控)、桌面 Browser 独立窗口+SSH 远程更新引擎、50+ 远程 MCP(Cloudflare/Grafana/Better Stack/Railway)、web_search/extract TTL 缓存、lean-tail 压缩默认、OS 钥匙串加密密钥、cron durable-incident acks、不支持不安全原地更新。
- 历史：v0.20.0(2026-08-03, "Herald" 语音/A2A v1.0/签名 webhooks/桌面平台) → v0.20.3(Bot Mode 捆绑默认开) → v0.20.5(keyless web tier / opencode-free)。

## 验证 / 使用

- 写 agent 相关 skill 前先 `skill_view(name='agent-landscape-2026')` 取最新数值，勿凭记忆硬编码旧基准。
- 评估 browser agent 时按「WebVoyager(饱和,参考) → Online-Mind2Web(live标准) → OSWorld 2.0(长程真实) → CAP(跨站感知瓶颈)」分层，单一榜无意义。
- 自演化方向优先复用 MGM/Mem2Evolve/HSI 的 harness-evolution 思路，而非从头写递归优化。
- 新事实继续写 fact_store 并补进本 skill；Hermes 跨小版本(如 v0.20.x→v0.21.0)更新时刷新第 4 节。
