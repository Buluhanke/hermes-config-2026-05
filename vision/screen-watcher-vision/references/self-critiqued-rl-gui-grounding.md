# Self-Critiqued RL for Trustworthy GUI Grounding (arXiv 2510.27266)

**论文**："Enhancing Trustworthy GUI Grounding via Self-Critiqued Reinforcement Learning"
**作者**：Shaojie Zhang, Pei Fu, Ruoceng Zhang et al.
**arXiv**: 2510.27266 (Oct 2025, cs.CV)

## 核心贡献

自批评机制（Self-Critique）：模型在输出坐标前先进行自我批评，拒绝低置信度的坐标预测。将 GUI grounding 从单向坐标生成改为**生成→自批评→接受/拒绝**的三步循环。

## 关键发现

- **自批评门控**：模型同时输出坐标 + 置信度评分，低分坐标被拒绝而不是直接使用
- **强化学习增强**：正确坐标得到正奖励，被拒绝但实际正确的坐标得到额外惩罚 → 自批评精度可训练提升
- **效果**：在 ScreenSpot 基线上超越单步坐标生成的基线方法，错误定位显著减少

## 对 Hermes 的价值

当前的 **handler 否定检测**（前12字符"没有/无/未/不"匹配）和 **CRITICAL_KEYWORDS** 是规则启发式的基础版 self-critique：

| 当前 (heuristic) | → 提升 (self-critique) |
|------|------|
| 关键词匹配 → [urgent/silent] | Model logprob → accept/reject action |
| 前12字符否定检测 | 语义级置信度评分 |
| 单一阈值 | 自适应门控（可训练） |
| 仅作用于 answer 文本 | 同时作用于坐标 + 文本 |

自批评可直接应用于 **auto_execute 的 SafeGround 不确定性量化**（DRY_RUN=False 条件⑤）：
- 不引入额外模型（用 qwen3-vl:2b 自身的 logprob 做置信度）
- 不需要训练数据（zero-shot 自批评 prompt）
- 与 SafeGround 的 selective prediction 互补

## Coordinate Confidence 示例 prompt

```python
self_critique_prompt = """You identified UI element "{element}" at coordinates [{x}, {y}].
On a scale of 0-1, how confident are you that this coordinate is exactly correct?
Consider: (1) Is the element clearly visible? (2) Is the coordinate in the center?
Reply with ONLY a number between 0 and 1:"""
```

## 来源

- arXiv: https://arxiv.org/abs/2510.27266
- 2026-06-01 方向D idle_learning 发现（arXiv 搜索 query: "GUI agent action grounding coordinate mapping execution"）
