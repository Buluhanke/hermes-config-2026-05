# H Company Runner H — H-VLM GUI VLM 方法论（2026-06-01）

**来源**：hcompany.ai/blog — "Charting a New Route: The Tech Behind Runner H's State-of-the-Art Results"
**日期**：June 3, 2025（文章日期）

## 核心发现

### H-VLM (3B 参数)
- 专注 GUI 感知/理解/交互的专用 VLM
- ScreenSpot benchmark：**最强小模型**，超越 10x 更大通用模型
- 比 Anthropic Computer Use 快得多且更准确
- "Our model is much more accurate than the very large generalist models, while being orders of magnitude cheaper and faster to serve"

### Runner H 0.1 — WebVoyager 67%
| Agent | WebVoyager |
|-------|-----------|
| **Runner H 0.1** | **67%** |
| Emergence AgentE | 61% |
| Anthropic Computer Use | 52% |
| Original WebVoyager | — |

### H-LLM (2B 参数)
- 代码+function calling 超越 7B+ 模型
- HumanEval / MBPP / BFCL 等 benchmark 表现优异

## 对 Hermes 的启发

1. **专用 GUI 训练数据 > 模型大小** — 3B 专业 VLM 在 GUI 任务上打爆通用大模型
2. **qwen3-vl:2b 路线正确** — 2-3B 级别的通用 VLM 做场景分类已够用
3. **如需提升**：需要专门的 GUI scene classification 标注数据，不是换模型
4. **Dedicated data >> model scaling** — H Company 内部自训 VLM，非微调通用模型

## 关键引用

> "We trained and specialized our 3B parameters VLM to perceive, understand, and interact with graphical user interfaces, images, diagrams, and other visual information"
>
> "H-VLM is by far the strongest small model in localization"
