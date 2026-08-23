---
name: pacore-delegate-pattern
version: 0.1
description: "PaCoRe-inspired parallel reasoning pattern for Hermes. Use when user wants deep analysis, systematic reasoning, or beating a large model with a small one. Core insight: not thinking longer, but multiple thoughts in parallel then synthesize. Trigger: 深度分析/系统性思考/复杂推理/如何用小模型赢大模型"
triggers:
  - "深度分析"
  - "系统性思考"
  - "复杂推理"
  - "小模型赢大模型"
  - "test-time compute"
  - "多角度分析"
trigger_type: deep_reasoning
tags: [reasoning, parallel, test-time-compute, method, pacore]
created: 2026-07-25
来源: ACL 2026 PaCoRe Paper
---

# PaCoRe-Inspired Parallel Reasoning Pattern

## 核心洞察

**不是让模型思考更久，而是让多个思考并行再汇总。**

PaCoRe (ACL 2026): 8B 模型通过并行推理 + 消息压缩，在 HMMT 2025 达到 94.5% 超越 GPT-5 (93.2%)，有效 TTC ≈ 2M tokens。

## Hermes 的 PaCoRe 实现

Hermes 的 `delegate_task` 天然就是 PaCoRe 在 Agent 层的实现：

```
用户问题 → delegate_task 广播 N 个子任务 → 并行推理 → 综合汇总
```

## SOP

### 步骤 1: 任务分解

将问题拆为 3-5 个独立方向/视角。

```
示例问题: "分析 Mac mini M4 的购买价值"
→ 子任务 A: 硬件规格 vs 价格（性价比视角）
→ 子任务 B: 使用场景适配（用户需求视角）
→ 子任务 C: 市场竞品对比（竞争格局视角）
→ 子任务 D: 长期持有成本（TCO 视角）
```

### 步骤 2: 并行委托 (delegate_task tasks=[...])

```python
delegate_task(
  tasks=[
    {"goal": "从硬件规格vs价格角度分析Mac mini M4购买价值，给出具体数字", "context": full_question},
    {"goal": "从使用场景适配角度分析Mac mini M4是否值得买", "context": full_question},
    {"goal": "从市场竞品对比角度分析Mac mini M4的竞争位置", "context": full_question},
  ]
)
```

### 步骤 3: 综合 (Synthesize)

收到的多个子任务结果 → 按维度合并 → 提炼共同结论 → 输出最终答案。

## 何时用

✅ 复杂推理/多维度分析任务
✅ 小模型要达到大模型质量
✅ 需要系统性思考而非快速问答

❌ 简单事实查询（不需要多角度）
❌ 需要快速回复的简单任务

## 验证

PaCoRe-8B 在 HMMT 2025 (数学竞赛) 达 94.5% vs GPT-5 93.2%，方法：并行探索 × 多轮迭代 × 消息压缩。

## 关联知识

- fact_id=659: PaCoRe 核心洞察（见 fact_store）
- fact_id=625: MLPs are Hebbian Memories（知识存储理论）
