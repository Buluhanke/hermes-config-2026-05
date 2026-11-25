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

## 5. Hermes Agent v0.23.x（2026-11，重大更新）

- **v0.23.0 "The Hearth Release" (11-05)**：自 v0.22.0 ~10080 commits / ~1950 PRs / 666贡献者 / ~850 issues closed。核心：①**单 gateway 拥有所有会话**——CLI/TUI/Desktop/editor/bots/cron 全部 attach 到同一个 gateway，同一 chat 不再重复/丢消息；②**Webapp** 把整个 Desktop 工作区开在浏览器标签（`webapp.enabled` 默认关）；③终端内联图片(kitty/Ghostty/iTerm2/VSCode)；④`/rewind` 对话回退+fork；⑤插件自动更新，catalog 600→1050+；⑥内置 skill 58→44（Word/PPT/Excel 合并为 `microsoft-office`）；⑦`hermes curator lock` 锁手工 skill。默认模型 GLM-5.3（1M 上下文）。
- **破坏性变更**：旧 `browser_*` 工具(agent-browser/browser_exec/browser_exec…)全删，浏览器自动化只剩 `browser_exec`；`hermes mcp serve`→`hermes mcp-serve`；Desktop 需 macOS 13+/64位 Windows。写自动化 skill 时勿再引用旧工具名。
- **v0.23.2 (11-16)**：~1989 PRs，durable subagents(跨 gateway 重启存活)、`hermes fallback check`、CVE-2026-130164(env 文件 allowlist)安全修复。
- **v0.23.3 (11-19/20)**：~370 PRs，prompt-cache lifecycle controller(长工具运行预热/闲置压缩)、GPT-6.2 Astra+Sol 上 OpenRouter/Nous Portal、可配置 skill 索引描述宽度(`skills.index_desc_limit`)。
- **Hermes Enterprise (11-18, Nous×Microsoft)**：进 Microsoft Teams/Microsoft Store/Azure Container Apps Sandboxes；Collective Wisdom 把员工成功做法沉淀为可共享 skill；日处理近 2 万亿 token，OpenRouter 公共 agent 排名 #1。

## 6. WebMCP 追踪（用户重点要求持续关注）

- **2026-11-19**：Web Machine Learning Community Group 发布 Draft Community Group Report（**非 W3C 标准**，无标准轨道）。
- **API 已稳定为命令式 `document.modelContext.registerTool()`**；`navigator.modelContext` 于 5-27 废弃迁移到 Document，旧 `provideContext()`/`clearContext()` 3-05 删除；**声明式 API 10-08 从规范移除**（当前只用 Imperative API）。特征检测用 `'modelContext' in document`。
- Chrome 演进：origin trial Chrome 149→162；Chrome 153+ 支持 abort() 注销工具而不中断 in-flight 执行；Chrome 155 弃用 executeTool 的 JSON 字符串入参（改对象）；Chrome 156 成 stable(10-20)，157 于 11-03。
- **替代 CDP 判断**：站点覆盖率仍极低，主要是 origin trial + `chrome://flags/#enable-webmcp-testing`；无头环境支持有限。**结论：尚不能替代 browser_exec/CDP，继续按「观察、未到切换点」跟踪**，等站点覆盖与无头支持成熟再评估。

## 7. Browser-Agent 新基准（2026-11 增补）

- **WebArena-Pro**（arXiv 2611.17955）：300 任务/20 自托管应用/6 域，多模态(音/视频为一等观测)。50 步预算最强 Codex+GPT-6.1 Sol 与 Claude Code+Opus 5.5 并列 **62.3%**，OpenCode+Kimi 3.1 Pro 60.7%；通用 agent 最强仅 30.3%。仍 38% 任务无成功记录。
- **BU Bench V2.1**：200 真实 web 任务，judge `gpt-5.6-luna` xhigh，含 9-25 CAPTCHA/Reuters 修订；BrowserCode runner。
- **ClawBench V2**（Findings EMNLP 2026）：281 任务/163 live 站点/15 类。**Hermes harness 官方榜**：claude-opus-4-7 54.6% intercepted / 44.6% lenient / 24.6% strict；gpt-5.5 45.4%；glm-5.1 48.5%。两次同模型复现 ±2pp。
- **WARC-Bench**（ICLR 2026）：438 GUI 子任务(WAR 归档)，最强 CUA 64.8%；7B SFT 48.8%→RLVR 52.8%，72B RLVR 达 84.31%。
- **Odysseys2**：100 live-web 任务(≤60min)，GPT-6 Astra 47/100，Opus 5.5 仅 18，5 个模型为 0——长程 live-web 仍是硬骨头。
- **Stagehand evals**：claude-fable-5-2(claude code) 92.0%/378s/$1.242 居首。

## 8. Multi-Agent 编排新框架（2026-11）

- **Swarms v17 "InterLink"**：comms channels(6 种：文件/queue/SQLite/HTTP/SMTP/AgentMail)、`PhasedFanOutWorkflow`(lead 规划跨数百 agent)；import 1.91s→0.28s；100 节点 fan-out 0.21s(LangGraph 1.44s)。`AgentRearrange` 两运算符编排 8-512 agent。
- **Vercel Board (11-18)**：headless 共享 message board 原语(harness agnostic)，channels+threads+labels+任务依赖；v0 software factory 用它后 50%+ PR 合并。\`npx skills add vercel/board\`。
- **eve 1.0 (Vercel, 11-17)**：开源生产级 agent 框架，Workflow SDK 崩溃后从最后完成步恢复，多人会话+agent-to-agent 内置。
- **Microsoft Agent Framework GA (11-19)**：C#/Python 正式可用，durable task extension。

## 9. 2026-11-22 自学新增自演化论文（详见 self-evolving-agents-2026 skill）

TokenEconomizer(会话经验降本 18.4-30.9%)、MEMCON(自适应记忆 ALFWorld 67.9%)、Exo(运行时 harness 自改降本 12-53%)、Pro²Agent(MLE-Bench 76%)、RSIFlow(SOTA+3.42%)、Predictive-IDM(+46%) 等，均已沉淀到 `self-evolving-agents-2026`。

## 10. 2026-11-26 自学新增（浏览器基准 / 编排 / 自改进）

### 浏览器 agent 与基准
- **Ramain**（ramain.ai 09-24）：严格「全项达成才通过」下 Online-Mind2Web 99.3、WebVoyager 99.2、WorkArena L3 89.4（GPT-5 仅 11.5）、WebArena-Verified Hard 84.2（Fable 5 71.3）。作者明确差距来自 harness（紧凑页面视图 + 精简历史），不是模型——再次印证 code-first/harness-first 路线。
- **knows**（2609.30604）：文档/表格/幻灯片产物流完整成功率 <3%；即使完成 >50% 其他步骤，视觉步骤一失败产物即不可用。Perplexity Comet Overall SF 64.7 领先，GPT-5.5 多模态 SF 46.7。
- **Fara1.5**（2606.20785，MIT 权重）：FaraGen1.5 三类 verifier（正确性/效率/关键点）+ Qwen3.5 4B/9B/27B；9B 达 OMW 63.4 / WebVoyager 86.6，27B OMW 72.3。
- **BrowseComp-V³**（SIGIR 2026，300 题）：GPT-5.2 仅 36.00% SR（Thinking 39.13），人类上限 68.03 SR——多模态深搜远未饱和。

### 多 agent 编排
- **Agensh**（microsoft/Agensh，1024 agent 自组织，无中央编排器）：ProgramBench 5 个最难任务平均通过率 19.31%（1 agent）→28.78%（128）；Pandoc 33.89%→55.06%（1024），GPT-6.1-sol 下 32 agent 就把 56.19% 推到 79.59%。
- **HTN-Orchestrate**（2610.22195）：Planner 管层级依赖、Orchestrator 调度叶节点，开源 DeepSeek-V4.1-Flash 达 BrowseComp 89.73%（超 Agent Team 2.45 分）、SUPERChem 73.44%、FSR 43.33%。
- **WorkflowArena**（2611.12856，145 任务/8 域）：把「模型自己写工作流」当独立能力；Claude+Claude Code 少委派但大组，GPT+Codex 频繁小单元委派；Opus 5.5 写的工作流能提升弱执行器。
- **SwarmBench**（EMNLP 2026 Findings）：GPT-5.4 为最强最均衡编排器（8 任务中 6 个最佳）；SwarmExp 用经验抽取+回放提升编排。

### Hermes 本体
- **v0.23.4** 已确认（11-23，229 PR / 1122 commits / 1316 文件）：`hermes gateway migrate --backends`、`hermes plugins config`、Desktop 审批卡、客户端身份广播、`skills.index_desc_limit`；完整 notes 随 v0.24.0 出。

## 验证 / 使用

- 写 agent 相关 skill 前 `skill_view(name='agent-landscape-2026')` 取最新数值，勿凭记忆硬编码旧基准。
- 评估 browser agent 时按「WebVoyager(饱和,参考) → Online-Mind2Web(live标准) → OSWorld 2.0(长程真实) → CAP(跨站感知瓶颈)」分层，单一榜无意义。
- 自演化方向优先复用 MGM/Mem2Evolve/HSI 的 harness-evolution 思路，而非从头写递归优化。
- 新事实继续写 fact_store 并补进本 skill；Hermes 跨小版本(如 v0.20.x→v0.21.0)更新时刷新第 4 节。
