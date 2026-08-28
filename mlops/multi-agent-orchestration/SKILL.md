---
name: multi-agent-orchestration
description: 多agent编排选型与落地。Use when 搭多agent系统或选编排模式。
version: 1
author: hermes-self-research
license: MIT
triggers:
  - 多agent编排
  - 多智能体架构
  - orchestrator pattern
  - multi-agent production
  - 选编排框架
hermes:
  tags: [multi-agent, orchestration, production, patterns]
  related_skills: [self-evolving-agents-2026, dispatching-parallel-agents]
---

## When to Use
- 设计、评审或搭建多 agent 系统架构时
- 需要在 6 种编排模式中做选型（含失败模式与 guardrail）
- 排查多 agent 生产事故（上下文溢出、cascade failure、成本失控）
- 在确定性工作流（YAML/DAG）vs LLM 动态规划之间做架构决策
- 选多 agent 框架（LangGraph/CrewAI/AutoGen/Orloj/Conductor 等）

# Multi-Agent Orchestration — 生产级指南

# Multi-Agent Orchestration — 生产级指南

## 核心判断（先读）
- **能用单 agent 解决就别上多 agent**。Princeton NLP：同工具同上下文下，单 agent 在 64% 的任务上≥多 agent 系统；多 agent 仅 +2.1pp 精度但 ~2x 成本。多 agent 只在「子角色确实不同 / 需并行 / 需独立 critic」时划算。
- **topology（拓扑）比模型选择更决定成败**。但 40% 多 agent 试点在投产 6 个月内失败——根因多是选错模式或不知它怎么崩。
- Gartner：2024Q1→2025Q2 多 agent 咨询量 +1,445%；企业平均已跑 12 个 agent，两年后 +67%。

## 6 种编排模式（beam.ai 2026 实证）
| 模式 | 形状 | 用在 | 怎么崩 |
|---|---|---|---|
| Orchestrator-worker | 1 规划者拆子任务派专家 | 子任务设计期已知、要单一问责点 | orchestrator 上下文溢出（≥4 工人累积全上下文） |
| Sequential pipeline | 固定线性链，输出→输入 | 文档处理/合同生成/审核（明确线性依赖） | 早步出错毒化后续；4-agent 链协调开销 ~950ms vs 处理 500ms，3-agent 耗 29k token vs 单 agent 10k |
| Fan-out/fan-in | 多 agent 并发 + 聚合（投票/加权/LLM 合成） | ≥4 个独立任务、要砍 75% wall-clock | 聚合器需处理矛盾输出 |
| Multi-agent debate | 共享对话多轮挑战/精炼（maker-checker） | 合规/QA/需多专家视角 | 用 cheap maker + capable checker 拿 40-60% 降本 |
| Dynamic handoff | 无中央协调，agent 间按运行时上下文互转 | 客服路由（账单→实为技术问题） | handoff 可能死循环，需 guardrail |
| Adaptive planning | manager 动态建/改/执行计划 | 开放问题/事件响应（步骤涌现） | 计划漂移，需回退机制 |

**选型决策树**：
- 子任务设计期已知？→ Orchestrator-worker
- 固定线性步骤？→ Sequential pipeline
- ≥4 个独立并行任务？→ Fan-out/fan-in
- 要质量校验？→ Multi-agent debate（maker-checker）
- 路由不可预知？→ Dynamic handoff
- 开放问题/计划需涌现？→ Adaptive planning

## 生产 5 支柱（seodatapulse 2026）
1. **Roles** — 每 agent 单一职责 + 自有工具集 + 自有上下文
2. **Tools** — 标准化工具接口（MCP）
3. **Memory** — 分层记忆； episodic 检索别只靠向量相似（语义相似≠任务相关，账单系统已变则旧方案错）
4. **Guardrails + HITL** — 不可逆转/高风险动作（发钱/删数据/合并代码）前必设 human gate
5. **Observability + Evals** — 不能只靠 log；要 tracing 显示每个 agent/tool/token/handoff；建回归测试集 + LLM-as-judge 门禁

**成本铁律**：按 completed-task 计成本，不是 per-token。一个便宜模型失败触发 3 次重试，比 1 次 frontier 调用更贵。先优化端到端成功率，再压单价。

## 确定性工作流 = 投产收敛形态（Orkes Conductor 实证）
- 生产级 agentic 系统收敛为：**LLM 负责推理，工作流负责执行**。推理只在需要判断力处；重启集群等确定性路径必须是每次一致的工作流。
- Orkes Conductor（Conductor OSS）：agent plan 先编译成 **AST 白名单 + schema 校验** 的 DAG，非法 plan 整体失败走 fallback，绝不半执行；每步持久化，crash/3天审批后从原位恢复。可跑 十亿级/月 工作流。
- Microsoft Conductor：YAML 声明 + Jinja2 确定性路由（路由层零 token 消耗），per-agent model override，3 种 context 模式（accumulate/last_only/explicit），human gate 内置步骤。MIT。
- Orloj：agents-as-code YAML，DAG 编排 + 治理（policy/role/tool-permission fail-closed），lease 任务所有权 + idempotent replay + dead-letter。Apache 2.0。
- 结论：**已知结构的流程用确定性编排**（可预测/可审计/省成本），只有探索性任务才让 LLM 动态规划。

## 框架选型（2026 实测）
| 框架 | 阵营 | 状态化 | 适合 | License |
|---|---|---|---|---|
| LangGraph | code-first | 是 | 有状态生产多 agent 图 | MIT |
| CrewAI | code-first | 是 | 角色编队快速原型（<3月） | MIT |
| OpenAI Agents SDK | vendor | 是 | GPT-led handoffs+guardrails | OpenAI |
| Anthropic Claude Agent SDK | vendor | 是 | Claude-led planner-worker | Anthropic |
| Microsoft AutoGen | code-first | 是 | 研究/group chat/debate | MIT |
| AWS Multi-Agent Orchestrator | cloud | 是 | Bedrock 客服路由 | Apache 2.0 |
| n8n | no-code | 是 | 业务自动化 AI 节点 | fair-code |
| Orloj | YAML runtime | 是 | 治理+可观测生产编排 | Apache 2.0 |

> LangChain 单独用不是 2026 意义的编排器；要编排请用 LangGraph。

## 通信控制（hidden-profile 场景）
- Consilience（arXiv 2608.20564）：用紧凑状态（不确定性/分歧/证据增益/冗余/过早共识）选干预（challenge/clarify/seek-evidence/route）+ 说话者；轮级 conformal 校准保证单步 regret 有界。HiddenBench 12 模型：规则控制器 0.83 vs round-robin 0.26，11/12 超 full-information 基线。
- 启示：**结构化通信控制比单纯增加信息可用度更有价值**。

## Verification（落地后自检）
- [ ] 画出实际 topology，确认不是「为用多 agent 而多 agent」
- [ ] 每个模式标注了失败模式与对应 guardrail
- [ ] 高风险动作前 human gate 已接
- [ ] tracing 能回放完整 agent/tool/handoff 链
- [ ] 已知结构流程走了确定性编排（YAML/DAG）而非 LLM 动态规划
- [ ] 成本按 completed-task 核算，非 per-token
