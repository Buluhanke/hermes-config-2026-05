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
