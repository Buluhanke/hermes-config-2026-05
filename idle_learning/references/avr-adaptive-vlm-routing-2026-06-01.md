# AVR: Adaptive VLM Routing for Computer Use Agents (CVPR 2026)

**arXiv**: 2603.12823
**代码**: github.com/vllm-project/semantic-router
**会议**: CVPR 2026
**作者**: Xunzhuo Liu (vLLM Semantic Router), Bowei He (MBZUAI/McGill), Xue Liu, Andy Luo (AMD), Haichen Zhang (AMD), Huamin Chen (Red Hat)

## 核心思想

CUA 系统通常将所有动作路由到单一固定 VLM，但动作难度差异巨大（简单点击 vs 复杂UI定位）。AVR 插入轻量语义路由层，实现三级路由：

**三层管线**：难度评估器(120M嵌入,~2ms) → 小VLM置信度探测(logprob) → 记忆注入(few-shot) → 升级大VLM

## 关键设计

### 1. 多模态难度评估器
- 基于 120M 参数嵌入模型（类似 SigLIP-small 架构）
- 输入：截图 + 指令，输出：难度分数 d ∈ [0,1]
- 综合视觉复杂度（UI密度/目标显著性/布局复杂度）和语义复杂度（指令歧义度/推理步数）
- 推理开销极低（~2ms/帧），非管线瓶颈

### 2. Logprob 置信度探测
- 让小 VLM 执行推理，收集每个 token 的 log probability
- C(a) = exp(1/n Σ ln p(a_i)) — token 几何平均概率
- θ_high=0.85 → high confidence: 直接执行；θ_low=0.60 → low confidence: 直接升级大模型
- 0.60~0.85 → 注入记忆后重试

### 3. Warm Agent 记忆注入
- 动态经验库 M = {(s_j, a_j, r_j)}，FIFO 维持 1000 条
- top-3 相似经验以 few-shot 示例注入 prompt
- **不对称效应**: 小模型 +13pp（83→96%），大模型仅 +1pp（94→95%）
- 核心发现：小模型瓶颈不是能力不足，而是缺乏 GUI 先验经验

### 4. Guardrail（高风险动作）
- 涉及不可逆操作（删除/支付/发送）时附加 Visual Confused Deputy 验证
- 大模型错误率 3% → 加 guardrail 后降至 0.5%

## 关键数据

### ScreenSpot-Pro 准确率
| 模型 | 准确率 | 相对成本 |
|------|--------|---------|
| GPT-4o | 0.8% | 1.00× |
| OS-Atlas-7B | 18.9% | 0.05× |
| Qwen2.5-VL-14B | 28.3% | 0.12× |
| Qwen2.5-VL-72B | 43.6% | 0.80× |
| **AVR (7B+72B)** | **42.7%** | **0.22×** |

### OpenClaw 任务成功率
| 方法 | 成功率 | 平均成本 |
|------|--------|---------|
| Qwen2.5-VL-7B | 68.2% | $0.12 |
| Qwen2.5-VL-72B | 87.5% | $2.85 |
| RouteLLM (文本) | 76.8% | $0.89 |
| **AVR** | **85.7%** | **$0.63** |

AVR 成本降低 78% ($0.63 vs $2.85)，成功率仅低 1.8pp。

### 动作难度分布
- ~45% 简单（小模型直接处理）
- ~30% 中等（记忆注入后小模型可处理）
- ~25% 困难（需大模型+guardrail）

## 对 Hermes 的启发

### 1. Handler 架构升级
当前 2-tier（场景分类 → auto_execute routing）可升级为 AVR 式 3-tier：
- **Tier 1**: 场景分类 + logprob 置信度评估（qwen3-vl:2b 当前已做场景分类，可加 logprob）
- **Tier 2**: 中等置信场景注入历史成功分类作为 few-shot 示例
- **Tier 3**: 低置信场景升级到更强的分析策略

### 2. 记忆注入实战
- 维护成功分类的 (截图缩略图 hash, 场景类型) 缓存
- 当 qwen3-vl:2b 对分类结果置信度低时，注入最相似的历史示例
- 与 AVR 的 warm agent memory 一致

### 3. GPT-4o 的 0.8% 教训
GPT-4o 在 GUI grounding 上表现极差（0.8%），说明：
- 闭源模型在特定领域不一定优于开源模型
- 模型选择需基于任务评测而非品牌
- 路由不能按模型大小分层，需考虑 GUI 实际能力

### 4. Qwen3-VL 坐标约定（GitHub #1560）
从 AVR 中引用的关键 convention：
- [x, y] 在 1000×1000 相对坐标 canvas 上
- 像素映射：x_px = x/1000 × W, y_px = y/1000 × H
- 对 DRY_RUN=False 切换最关键
