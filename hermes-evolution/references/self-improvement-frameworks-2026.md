# 2026 自改进 Agent 框架研究库（2026-08-26 自学沉淀）

全网自学抓到的 6 个 2026 自改进 SOTA。已写入 fact_store（IDs 1186–1192）。
浓缩在此供后续进化轮次引用，避免重复检索。

## 1. HSI — Hierarchical Self-Improvement
- 论文：arxiv.org/abs/2608.08466（代码 github.com/TailinZhou/hsi）
- 核心：单个**冻结 backbone** 也能端到端进化自身 harness（prompt/工具/记忆/验证逻辑）。
- 三层 scope：任务 harness H（执行）→ evolver（改写 H）→ meta-evolver（改写 evolver）；最外层 anchor 冻结防无限自指。
- thinking-on/off：任务执行时关 reasoning（锁死 per-step 能力天花板），改写时开 reasoning（最大化自改成功率）。
- 指标（BALROG, DeepSeek-V4-Flash 冻结）：+39.3 BabyAI / +33.0 Crafter / +25.0 TextWorld / +15.0 MiniHack（raw %Progress）；BabaIsAI 跨任务泛化 0.98/1.00。
- 两大瓶颈：**feedback-fidelity bound**（稀疏奖励无信号则无法选择）、**backbone capability bound**（harness 改不动模型天花板，NLE 上零提升）。
- Hermes 映射：L3 Skill写 = evolver，L4 Curator = meta-evolver，fact_store = archive。

## 2. OEO — Open-Ended Optimization
- 论文：arxiv.org/abs/2608.09629
- 核心：质疑预设优化 pipeline（SkillOpt / GEPA）。框架只持有 objective/permissions/budget/eval/governance 外部契约，把"如何改进"的 meta-policy 委托给足够强的 optimizer 在线自组。
- 指标：GPT-5.5 驱动 OEO 在 14 组对比中 12 胜 1 平 1 负（0.21pp 微负），仅用 SkillOpt 34.3% 交互 token 预算。
- 结论：**prescription 是 capability-dependent 脚手架**——frontier 模型可不用 pipeline，medium 模型仍需 SkillOpt，weak 模型连 OEO 接口都跑不动。
- Hermes 映射：skill 的 triggers/steps 是 prescription；弱模型保留详细步骤，强模型可下放。

## 3. MARS — Metacognitive Agent Reflective Self-improvement
- 论文：aclanthology.org/2026.acl-long.1329（代码 github.com/Paparare/MARS）
- 核心：单周期 self-improvement，元认知学习——principle-based reflection（抽象避错规则）+ procedural reflection（成功 step 策略）。
- 三阶段：Evaluation（失败分析）→ Failure Allocation（按 type-topic 分组聚错）→ Enhancement Generation（加权合入 base prompt）。
- 指标：6 基准超 Gödel Agent / MetaAgentSearch，计算开销远低于递归循环；GPQA 上 Self-Refine+hybrid 49.1%。
- Hermes 映射：每次任务后写 skill 即 MARS 式单周期升华。

## 4. MGM — Mendel Gödel Machine
- 论文：arxiv.org/abs/2608.07645
- 核心：archive-based 自改进 coding agent，三类自修改算子——clonal（单轨迹）/ reaction-norm（同 agent 跨多任务轨迹）/ cross-lineage hybridization（参考 agent 同任务轨迹）。
- 指标：加法 fitness landscape 下理论证更快收敛；SWE-bench 68.3%→78.3%；Polyglot 上 Qwen3.6-35B-A3B 50.8%→93.3%（超越 GPT-5，~117x 少参数）；evolved scaffold 迁移 DeepSeek-V4-Pro 达 96.9%。
- **关键缺口**：cross-lineage 杂交是当前 Hermes 缺的——只做单 trajectory 升华，应开始对比不同 skill 变体。

## 5. DGM-Hyperagents
- 论文：doi.org/10.48550/arxiv.2603.19461
- 核心：hyperagent 把 task agent 和 meta agent 统一进单一可编辑程序，meta 级修改机制本身也可编辑 → metacognitive self-modification。
- 指标：coding/论文评审/机器人奖励设计/奥数批改多域自我加速；meta 级改进跨域迁移并跨 run 累积。安全用 sandbox + human oversight。
- 结论：开放端 self-improvement 可推广到任意可计算任务，不限于 coding。

## 6. WebArena 2026（computer-use 基准）
- Leaderboard（2026-06）：WebTactix(DeepSeek v3.2) 74.3%（812/812）、OpAgent 71.6%、ColorBrowserAgent 次之、OpenAI Operator 仅 58.1%（Jan 2025）。
- 2026 评测共识：WebArena / WebVoyager 仅作 web baseline 已不够；OSWorld（真实桌面 OS）才是通用 computer-use 最近公开代理；BrowserGym 是复现基础设施非买家分数。
- 生产就绪看 recovery / permissioning / verification / intervention rate，而非首试导航成功率。
- Hermes 映射：computer_use 已对齐 OSWorld 路线（真实桌面控制），方向正确。

## 落地动作（本轮已执行）
- 把"单 trajectory 升华"升级为"archive 对比升华"：同主题积累 3+ fact 时对比多个 skill 变体再固化，而非逐条照抄（对应 MGM cross-lineage 杂交）。
