---
name: self-evolving-agents-2026
description: 2026 自演化 agent 技术库 OEO/HSI/Metan/AGP 与 Hermes 进化启示。
version: "1.0"
author: Nous Research
license: MIT
group: 研究
metadata:
  hermes:
    tags: [self-evolving, agi, agent, oeo, hsi]
    related_skills:
      - hermes-evolution
      - evidence-loop
      - mempalace
      - deep-research
triggers:
  - "自演化"
  - "agent 进化"
  - "skill 改写"
  - "自动优化"
l1: 研究
l2: 自演化
---

## When to Use

**Use when any task asks for agent self-evolution research, skill improvement pipelines, or automated performance optimization** — the first decision is always: pick the right evolution technique (OEO, HSI, Metan, AGP, etc.) based on optimizer capability, then run the A/B test pipeline to validate before keeping changes.

---

# Self-Evolving Agents 2026 — 实战结论库

## 核心原则：Capability-Adaptive Responsibility（能力自适应分工）
- 框架持有外部契约（目标 / 权限 / 预算 / 评估边界），任务级"怎么改进"的元策略可下放到优化器——但仅当优化器足够强。
- 弱优化器无法用 Open-Ended Optimization（OEO）接口，此时固定管线（如 SkillOpt）反而更好。
- 处方（prescribed pipeline）改变的是"改进路径"而非"最终行为"：OEO 在 8 个配对设置里最大编辑更大、修订更churny，但 pass/fail 一致率 ≥0.78。

## 六种已验证技术（均带数字）

### 1. Open-Ended Optimization (OEO) — arXiv 2608.09629
- 固定目标/权限/预算/评估，让 frontier 优化器在线组合改进过程（无固定模板/编辑语言/停止规则）。
- GPT-5.5 OEO vs SkillOpt+GEPA（14 组 head-to-head）：12 胜 1 平 1 负（+0.21pp），仅用 SkillOpt 34.3% 的 token 预算。
- 边界：中档优化器下 SkillOpt 反超；弱优化器无法用 OEO。

### 2. Hierarchical Self-Improvement (HSI) — arXiv 2608.08466
- 单个 FROZEN LLM 在 3 层演化自身 harness（task harness H / evolver 改写 H / meta-evolver 改写 evolver，外层锚冻结）。
- 任务执行时 thinking-off，改写时 thinking-on（隔离 harness 演化贡献）。
- DeepSeek-V4-Flash 上 BALROG：+39.3 BabyAI / +33.0 Crafter / +25.0 TextWorld / +15.0 MiniHack（raw %）；held-out BabaIsAI 0.98-1.00。
- 受两限约束：feedback-fidelity bound（稀疏奖励无信号）+ backbone-capability bound（harness 改不动模型上限）。

### 3. Metan — arXiv 2608.24735
- 递归自改进：固定一个元操作 Ω，反复作用在自己产物上（读下方轨迹+代码，写下层 pre-process+callable helpers）。深度由收敛决定，非固定 → 元深度 >2.5（旧系统封顶 ~2）。
- 8 个 benchmark 家族全胜；ARC-AGI-2 达 0.331（唯一非零）。72% 增益来自传递的 context 字符串，15% 来自 callable code 传递。

### 4. Mem2Evolve — ACL 2026
- 双记忆共演化：Asset Memory（工具/专家 agent）+ Experience Memory（蒸馏经验）。前向"reuse first, create on demand"，后向留存资产+蒸馏经验。
- +18.53% over 标准 LLM，+11.80% over 仅经验，+6.46% over 仅资产（6 类任务 / 8 benchmark）。稳定跨任务演化。

### 5. Autogenesis Protocol (AGP) — arXiv 2604.15034
- 两层协议解耦 WHAT 演化（RSPL：prompt/agent/tool/env/memory 作 versioned 资源）与 HOW（SEPL：propose-assess-commit 闭环算子，可审计 lineage+rollback）。
- 实例化 AGS 多 agent 系统，在 GPQA/AIME/GAIA/HLE/LeetCode 上一致提升。明确引用 "EvoAgentX 与 Hermes Agent NousResearch (2025)" 为自演化 agent。

### 6. Prime Agent — arXiv 2608.23552
- 开源自改进 RLM harness，长程 coding-agent 评估。持久 IPython REPL 遵循 Recursive LM；Continual Harness 跨轨迹保留 histories/memories/skills/prompts/subagent specs。Agents View 检视 daemon-backed sessions。

### 7. AutoAgent — arXiv 2603.09716 (github vicFigure/AutoAgent)
- 自演化多 agent 框架，三耦合组件：evolving cognition（prompt 级结构化认知：工具/自身能力/同伴专长/任务知识）、on-the-fly 上下文决策、Elastic Memory Orchestrator（原始记录 + 压缩摘要 +  episodic 抽象，降 token 开销）。
- 闭环认知演化：从轨迹反馈对齐意图与结果，更新认知而无需重训。GAIA/HLE/ALFWorld 上优于 static + memory-augmented baseline。

### 8. MANTA — arXiv 2607.28527 (Multi-Agent Network Topology Adaptation)
- 通信拓扑在推理时自演化（非离线优化）：Topology Planner 从经验初始化 → Trace Auditor 标过程风险 → 有界结构突变（改角色/链路/顺序/可见性/验证路径）。
- Cross-run playbook 蒸馏拓扑经验。5 benchmark avg 74.0（+5.8pt 超最强 baseline），PlanCraft 最佳。无权重更新。
- 启示：拓扑是独立自演化层——有效适应常是"重连通信/加验证器"而非"加 agent 数量"。

### 9. TPGO + GRAO — ACL 2026 Findings 1534 (Textual Parameter Graph Optimization)
- MAS 建模为文本参数图（agent/tool/workflow = 模块化节点，交互 = 边），"文本梯度"（执行轨迹的 NL 反馈）驱动。
- 核心 GRAO（Group Relative Agent Optimization）元学习：从历史优化成败（持久 Optimization Experience Memory）学"如何优化自己"，提出更有效更新。GAIA + MCP-Universe 增益。

### 10. MEGA — arXiv 2608.10504 (Self-Evolving Agent Optimization Infrastructure via Wisdom Graph)
- 三层基础设施：① 行为聚类 + 经验 A/B 验证从会话蒸馏可复用 wisdom → 持久资产；② 拆为原子 PCR (Primary-Context-Resultant) 单元入类型化 Wisdom Graph，演绎/溯因/归纳推理，组合检索揭开 embedding 相似度够不到的桥接知识；③ 多 agent 协同优化，受控评估将增益归因到具体策略变更。
- 证据回流自演化"策展策略"与"跨 run 优化轨迹"。

## 对 Hermes 进化循环的启示
1. **能力自适应**：Hermes 当前模型(hy3-free/tencent)若作优化器偏弱 → 进化循环应保留固定 skill 改写模板（类 SkillOpt），不要盲目上 OEO。
2. **双层演化**：HSI 的三层（harness/evolver/meta-evolver）对应 Hermes 的 skill/技能改写逻辑/元改写守卫——外层守卫（cron watchdog、内存守卫）必须冻结不可自改。
3. **双记忆**：Mem2Evolve 的 Asset+Experience 对应 Hermes 的 skill_store + fact_store + session_search：经验蒸馏进 fact，资产（可复用工具）进 skill。
4. **版本化+审计**：AGP 的 versioned resources + 可回滚 lineage 是 Hermes skill 改写应补的——每次 skill 改写留 diff + 可回滚。
5. **反馈保真度**：HSI 表明稀疏奖励下演化失效——Hermes 进化需用真实工具实测回报（evidence-loop skill），非模型自评。

## A/B 测试流程（2026 迭代）

### 问题
自演化 agent 的 skill 改写容易产生大量变体，但无法确定哪个变体更好。模型做出的判断（如「这个改写看起来更好」）不等于真实工具实测回报——HSI 已证明稀疏奖励/模型自评会导致演化失效。

### 解决：分三阶段 A/B 测试

#### 阶段 1：生成变体（由弱优化器做，固定管线）
- 针对同一 skill，生成 3 个变体（v1 原版，v2 改写版，v3 改写版）
- 每个变体在 `evidence-loop` 中记录：原始行为、改写后行为、工具实测数据
- 所有变体在同一测试集上运行（不并行，避免环境差异）

#### 阶段 2：工具实测（真实调用，非模型自评）
- 为每个变体跑 5 个固定测试用例（用例见 `references/ab_test_cases.md`）
- 记录：通过率、平均步骤数、平均工具调用数、失败原因分类
- 输出标准化 JSON：`{ variant, test_cases: [{name, pass, steps, errors}], metrics: {}}`

#### 阶段 3：决策与回滚
- 按「通过率 + 平均步骤数」双维度评分
- 若 v2/v3 优于 v1：保留变体，写入 `skill_audit.json`（含 diff + 日期）
- 若 v2/v3 劣于 v1：回滚到 v1，记录失败原因到 `lesson_store`
- 保留 last-known-good（总是保留原版备份，`cp -r skill skill_backup_$(date +%F)`）

### 测试用例（固定 5 条，不扩展）
| 编号 | 用例 | 验证内容 |
|---|---|---|
| T1 | 相同输入，重复 3 次 | 输出一致性 |
| T2 | 边界输入（空、超长、特殊字符） | 无崩溃 |
| T3 | 组合输入（多条件叠加） | 不误判 |
| T4 | 长程任务（>10 步） | 不丢状态 |
| T5 | 错误注入（模拟失败） | 恢复机制生效 |

### 坑
- 变体太多会变成评估噪声：固定 3 个变体、上限 5 条测试用例
- 不同时间运行的变体环境可能不同：统一快照日期记录
- 模型自评代替不了工具实测：任何 A/B 决策必须基于工具调用输出，不能依靠「感觉更好」

## 浏览器智能体基准版图（自演化 agent 的评估参照，2026-08 增补）
自演化 agent 的"能力可被测"依赖这些长程/安全/跨站基准：
- **Wuying-Browser-Agent-27B**（arXiv 2608.17319）：开源 SOTA，WebVoyager 80.6% / Online-Mind2Web 66.7% / BrowserBench 65.1%；RUIC-SFT（恢复轨迹）+ DAO-GRPO（分歧感知在线 RL）。
- **BrowserBench**（同上）：350 双语长程任务（中191/英159），avg 37.9 步，254 网站，判官↔人类 96.4% 一致。填补短基准暴露不了的长程失败。
- **CAP-Bench**（COLM 2026）：跨站 108 网站 420 任务，最强 agent 仅 8.0% SR，感知交互为主瓶颈。
- **ST-WebAgentBench**（ICLR 2026）：安全基准 375 任务/3057 策略实例，CuP 指标显完成率 <2/3 过策略过滤，70% 违规在用户同意+严格执行。
- **WebForge**（arXiv 2604.15034）：934 静态自包含任务，7 维难度控制，Gemini-3-Pro 75.9%（去视觉→59.2%）。
- **WebOne/WebLearner**（ECCV 2026）：教程跟随泛化，按网站切分 1342 任务/970 教程，56.9% SR，GRPO > SFT。

## 启示（评估侧）
- 自演化 agent 的评估不应只看最终 pass rate：长程（BrowserBench）、安全（ST CuP）、跨站（CAP）是三个独立维度，任一塌陷都不算真强。
- Hermes 进化循环验证时同理：用真实工具实测 + 长程任务 + 策略约束，比单点成功更可信（呼应 evidence-loop）。

## 2026-08-30 自学成果补充（fact_store #1269-#1281）

### 模型/系统突破
- **NVIDIA AVO**：100% ARC-AGI-3（Claude Opus 5 30%→100%），系统设计 > 模型能力。
- **Mendel Gödel Machine**：Qwen3.6-35B Polyglot 50.8%→93.3%（~117× 少参数超 GPT-5）。
- **MARS**：单周期元认知自我改进，~25-30× 省算力超 Gödel Agent。
- **Mem2Evolve**（已收录）：双记忆协同演化，GAIA +57.84%。
- **HSI**（已收录）：冻结 LLM 演化自身 harness，BALROG +39.3 BabyAI。

### 浏览器智能体基准
- **OSWorld 2.0**：108 长程任务均值 318 tool calls，Opus 4.8 仅 20.6%（500 步）。
- **CAP benchmark**（已收录）：420 跨站任务最优 Manus 仅 8.0%，perception 是比 execution 更重瓶颈。
- **CUA-HandCrafted**：浏览器 CUA 对 prompt injection 鲁棒（0/140 ASR），但 coding agent 可被 100% skill-injection。
- **LexBench-Browser**：210 任务/107 站点可复现 browser-agent 评测框架（bubench）。
- **2026 浏览器 agent 榜**：WebVoyager 饱和（98.5%）、Online-Mind2Web 成 live-web 标准（97.0%）、OSWorld-Verified 桌面 Claude Fable5 85%。

### 多 agent 编排框架（6 个新）
- open-multi-agent / orxhestra / Orloj / GAIA (Go) / Overseer / OpenHive。

### Hermes 自身
- **Hermes Agent v0.20.6**（2026-08-27，~525 PRs）：真实 profile 浏览、桌面 Browser 独立窗口+SSH 远程更新、50+ 远程 MCP、web_search/extract TTL 缓存、OS 钥匙串加密、cron durable-incident acks。
- **Wuying-Browser-Agent-27B**（已收录）：开源 SOTA，WebVoyager 80.6% / Online-Mind2Web 66.7% / BrowserBench 65.1%。

## 2026-11-22 自学成果补充（新论文，均带数字）

> 主题「自改进 harness / 记忆管理 / 经验复用」本轮积累 8+ 条，触发 skill 升华，已并入本库。fact_store 在 cron 上下文只读，故直接固化于此。

### 成本与经验复用（黑盒、不改模型）
- **TokenEconomizer**（UC Berkeley×MSR×MS Security，11-16，开源）：从仓库历史会话学习。三机制=micro-skills(仓库事实单行笔记)/tool pruning(每轮23工具16未用→裁剪)/failure-loop intervention。277 个 SWE-Bench 任务降本 **18.4-30.9%**，Pass@1 在 4/5 组合上升；第 6 个任务起累计成本低于默认。Web-Bench 降 16-21.2%。**启示：Hermes skill 的 few-shot 笔记+工具裁剪可直接借鉴**。
- **MEMCON**（UCLA/Wash/Northwestern，11-20）：记忆管理作可控过程，控制器按任务类型学「检索/改写重查/取成功轨迹/合并/删除/跳过」策略。ALFWorld **67.9%** vs G-Memory 59.7%，输入 token 45k→39k(-13%)；GAIA 22.4% vs 21.2%。**启示：记忆策略应随任务类型自适应，非全局固定 top-k**。

### Harness 自改写（运行时）
- **Self-Improving Harnesses 统一框架**（arXiv 2611.22299）：4 可编辑组件(context/state、agent control、action interface、verification&recovery) × 4 阶段循环(诊断失败→提代码补丁→验证候选→部署)。结论：模块化更新+验证门(gated modular evolution)优于整体重写(后者过拟合/跨模块崩)，SWE-bench Lite 验证且 token 成本更低；防御 prompt bloat/benchmark gaming/evaluator tampering。
- **Exo**（arXiv 2611.00463）：运行时自改进架构，受保护机制层存历史+管策略激活，harness 以可检视代码变更演化。开放世界游戏成本降 12-53%(standalone)/45-82%(transfer)；AppWorld/SREGym held-out 成本降 35-61%，AppWorld 均时 -13%。
- **AgentEvolver**（arXiv 2610.11613）：任务执行中演化，8 类实体(versioned lifecycle)。SWE-bench Pro Public 解出率 **82.08%**（超无演化基线）。
- **RSIFlow**（arXiv 2610.21791）：自适应工作流编排 + meta-agent 把结果蒸馏为组件 skill 并演化自身 harness。6 基准 SOTA 均值 **+3.42%**，12 个 benchmark-backbone 设置中 11 领先；Qwen3-8B 达 59.95%。
- **Predictive self-evolution / IDM**（arXiv 2610.13991）：可编辑 Improvement Dynamics Model 在昂贵评估前预测修改效果并指导修订。4 域全超 HyperAgents，Polyglot 中位 AUBC 0.306 vs 0.210，最高 +46%，预测知识可跨域迁移。

### 问题表征与形式化验证
- **Pro² Agent**（arXiv 2611.25357）：把自主研究主状态从 codebase 改为显式 **Problem State**(什么阻碍成功+哪些方案可能解决)，受控假设检验更新权重。完整 MLE-Bench 24h **70.7%**、48h **76.0%**(该榜最高)。**启示：卡住时先显式化「问题状态」而非盲改代码**。
- **AlphaProof Nexus**（Nature Comput Sci 11-19）：多 prover 子 agent 生成-验证 Lean 形式化证明，进化 agent 用共享 population+rating 协调，解决悬置 50+ 年难题。**启示：可验证领域用编译器/求解器做 verifier 消除幻觉**。
- **Salesforce「Self-Evolution Ladder」**：三级 Toolmaker(造缺失工具)→Learner(改进自身推理)→Architect(设计后继)；RSI=改进「改进能力本身」的速率。SFR-AutoR&D 3 天完成团队数周的 embedding 优化。建议治理：工具可演化、推理可改进、架构仅在人判定安全处改，价值观固定。

### 横向对照（与库内早期技术）
- 硬件/模型冻结前提不变：本轮 Exo/HSI/TokenEconomizer 均不训模型权重，改进全在 harness/记忆/策略层——再次印证「系统/scaffold 设计 > 单模型能力」。
- 演化安全性共识：gated validation + 受保护机制层 + 回滚，是本轮 Exo/Self-Improving-Harnesses/AGP 的共同底座，Hermes 进化循环应保留冻结外层守卫。

## 2026-11-23 自学成果补充（fact_store cron 只读，直接固化于此）

### 头号发现：瓶颈是「评估分辨率」，不是「提案质量」
- **Resolution Hypothesis**（arXiv 2611.23068，7 种演化方法 × 6 模型 × >10M LLM calls）：agent 演化停滞不是因为提不出好 artifact，而是噪声评估分不出好坏——候选选择「与随机无异」，错误逐轮累积；方法间几个百分点的差距小于同一方法两次独立运行的波动，论文排名常靠运气。**行动：先投资评估可靠性（重复采样/统计门/held-out），再投资新提案生成器。**
- **TRUST**（2611.10787）：在线多重假设检验门控 RSI，HotpotQA/DROP/APPS + DeepSeek-V4-Flash/Qwen-3.8-Flash 上把「接受劣化更新」比例从贪心门 45.59% 压到 2.78%，最终分数还高于 SOTA 统计门。
- **SelfImprove-Bench**（2611.02797）：G0–G4 泛化阶梯证明 RSI 增益不稳定——18 个方法-任务对里 8 个在已见实例回放分数反低于历史；训练难度上的提升未必迁移到更难/其他任务。
- **Flex-RSI**（2611.08946，24 任务/18 模型/177 runs）：85% 的 run 有提升、中位 +10.4 分；闭源 94% runs +14.9 中位 vs 开源 76% +8.5；收益主要来自 agent 自建方案 + 改写 harness，简单单一答案任务 0 增益。

### 可落地的新方法（均带数字）
- **Elite**（2611.21056）：Explore-then-Integrate，不用下游任务评估也能自改进。SWE-bench Pro 60.0%→85.6%（DGM 86.7%/HGM 88.3%），零候选任务评估、演化时间比 DGM 快 8.8×；跨基准 73.3% Verified / 69.3% Polyglot。适合评估费用高的场景。
- **GUARD**（2611.23476）：无评分器 RSI，方向性 regret + Soft-HURT 非退化门，专治局部退化/技能遗忘/记忆膨胀，测试时单 pass 冻结 harness，还降部署 token。
- **SIM / Self-Improvement Memory**（2611.18856）：给 harness 优化器记「每次编辑的动机+预测/实测结果+评估上下文」，跨 benchmark/跨模型续训时 coding 平均 +2.36 分（p=0.003）。**对应 Hermes：skill 改写应留 diff + 理由 + 实测结果，而非只留最终版。**
- **Skill∞**（2610.35434）：meta-agent 按 meta-skill 优化任务 skill，同时用同一流程改写 meta-skill 自身；83 SkillsBench 任务 60.7% > 人工策展 56.4% > SkillEvolver 54.5%。meta-skill 与任务 skill 解耦、走原生 skill discovery——与 Hermes skill 架构同构。
- **MAPE**（2611.17068，github ash-ding/MAPE）：从最小种子演化整个记忆程序，LoCoMo/LongMemEval 比人工设计 +12% 绝对准确率、仅 35% serving 成本；两条可移植模式：①保留原始对话作可检索证据 ②按查询意图组合检索证据（移植到 5 个记忆系统全部涨点）。
- **ModHarness-RL**（2611.18533）：harness 变成可学习程序——State 类型块 + Compression/Steering 两个程序，RL 中从轨迹提候选、执行验证、在历史轨迹回放；1.5B–8B 上 CodeSearch/ALFWorld/BIRD SQL 多数设置超固定 harness。
- **AIDE²**（2609.26457）：8 天自主 RSI，100 节点轨迹 7 次接受改进，grade 0.703→0.778，迁移到 4 个 held-out 基准并追平/超过人工生产 agent；reward hacking 55%→32%（比人工 39% 还低），该行为从未被显式优化。

### Hermes 本体与生态（影响自家技术栈）
- **v0.23.3**（11-19/20，v0.23.2 以来 370 PR）；**v0.23.0「Hearth」**（11-05，~1950 PR/850 issues/666 贡献者）：Webapp 从自有 gateway 在浏览器标签开整台工作区；**单 gateway 拥有所有会话**（CLI/TUI/Desktop/bot/cron 降级为客户端，解决重复写/丢消息）；终端内联图片；`/rewind` 回退分叉会话；多机同窗 Desktop；Group Chats 自路由；插件自动更新（catalog 600→1050+）；`hermes curator lock` 锁手工 skill；内置 skill 58→44；付费 MCP 可设 spend 上限；cron 共享 prompt cache/每次调用省 ~1570 tokens。**破坏性变更：旧 browser_* 工具全删，浏览器自动化只剩 `browser_exec`；`hermes mcp serve`→`hermes mcp-serve`；Desktop 需 macOS 13+。**
- **Hermes Enterprise**（11-18 与微软）：进 Microsoft Store/Teams/Azure Container Apps Sandboxes；Collective Wisdom 把成功做法沉淀为可共享 skill；Foundry autonomous agents 给每个 agent 独立 Entra 工作账号；OpenRouter 公共 agent 榜第一、日均近 2T tokens。
- **浏览器基准 2026-11 现状**：OSWorld-Verified 顶层 90.19%@100 步（Intelligence-Indeed）、无插件最强模型 85.96%（claude-fable-5）；OSWorld 2.0 v2.1（推荐版，108 长程/均值 318 tool calls）顶层 Claude Opus 5 max 44.33% binary/77.67% partial@500 步（论文时仅 20.6%）；WebVoyager 顶层 99.19%（browser-control/Fable 5 的 shell-native CDP harness）。**步数预算是一等混淆变量：同一模型仅因 step cap 从 9.1%→23.0%，引用分数必须带 release+step cap。**
- **WebArena-Pro**（2611.17955）：300 任务/20 自托管应用/6 域，音视频与文本视觉同为观测；最高 62.3%（Codex GPT-6.1 Sol & Claude Code Opus 5.5），OpenCode Kimi 3.1 Pro 60.7%，通用 agent 仅 30.3%。
- **成本对照**（Auto Browser，WebVoyager-mini 105 任务）：DeepSeek V4.1 Flash 82.8%、$0.026/任务（后续 92.7%）；Claude Sonnet 5.5 79.3%、$0.87/任务——33× 差价而准确率在噪声内。**低成本模型 + 好 harness 已够用，支持 Hermes 不锁模型策略。**
- **多 agent 编排 11 月新原语**：Vercel Board（实验性 headless 消息板，CLI/SDK，跨 harness，v0 安全 swarm + v0 software factory 已合并 >50% PR）；eve 1.0 GA（开源 harness + Workflow SDK 崩溃续跑 + Slack multiplayer）；Swarms v17 InterLink（6 类 comms channel、import 1.91s→0.28s、100 节点 fan-out 0.21s vs LangGraph 1.44s）；Chorus v0.24（product/dev/review/lead 四角色 + review 独立 session 锚，避免「换 agent 但同一脑袋」）；Microsoft Agent Framework Durable Task 扩展 GA。

### 对 Hermes 进化循环的更新启示
1. **评估优先于提案**：现有 A/B 流程（3 变体 × 5 用例）应补「重复运行取方差 + held-out 集」，因为方法间典型差距小于同方法两次运行波动（Resolution Hypothesis）。
2. **统计门替代贪心门**：skill 改写采纳参考 TRUST 多重检验（把劣化接受率压到 ~3%），而非单次分数高就保留。
3. **skill 留可迁移记忆**：每次改写记录 diff + 动机 + 预测/实测结果（SIM），跨模型/跨 benchmark 续训才有依据。
4. **不锁模型有实证**：Auto Browser 数据显示廉价模型 + 好 harness 即可逼近昂贵模型，呼应「不给模型自动绑定」的用户铁律。
5. **工具链迁移提醒**：本机若升级到 v0.23+，所有指向旧 `browser_*` 工具的 skill/cron 提示须改 `browser_exec`，否则自动化静默失效。
