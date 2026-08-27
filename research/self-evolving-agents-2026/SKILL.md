---
name: self-evolving-agents-2026
description: 2026 自演化 agent 技术库 OEO/HSI/Metan/AGP 与 Hermes 进化启示。
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

## 验证步骤
- 每次进化循环后：用真实工具调用（非模型自评）验证 skill 是否真可用。
- 保留外层守卫冻结 ≠ 被改写；内存守卫 free_bytes 等变量必须带 $。
- 增量写盘防中途被杀（1688 工作流同铁律）。

## 坑
- 弱优化器 + OEO 接口 = 死锁（无法产出有用更新）。先测优化器能力再选模式。
- harness 演化无法突破 frozen backbone 上限（NLE 任务零增益）。别指望演化解决模型硬伤。
- 处方管线改变路径 > 改变结果；过度 churny 的改写可能破坏可用 skill——保留 last-known-good。

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
