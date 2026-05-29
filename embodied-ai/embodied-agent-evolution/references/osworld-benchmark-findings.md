# OSWorld Benchmark Findings（2026-05-29）

## 核心统计（2026-05-29 空闲学习获取）

**OSWorld Leaderboard Top Scores（llm-stats.com, 2026-05-29）**：

| 排名 | 模型 | 分数 | 类型 |
|------|------|------|------|
| 1 | Claude Opus 4.6 | 72.7% | Proprietary |
| 2 | Claude Sonnet 4.6 | 72.5% | Proprietary |
| 3 | **Qwen3 VL 235B A22B Instruct** | **66.7%** | **开源第一** |
| 4 | Claude Opus 4.5 | 66.3% | Proprietary |
| 5 | GLM-5V-Turbo | 62.3% | Proprietary |
| 6 | Claude Sonnet 4.5 | 61.4% | Proprietary |
| 7 | Claude Haiku 4.5 | 50.7% | Proprietary |

> **Qwen3 VL 235B A22B 是开源模型第一名**，超越 Claude Opus 4.5。

## 关键洞察：失败原因分析

**75% 的 OSWorld 失败是 visuomotor grounding errors（视觉-运动 grounding 错误），而非 reasoning 失败**

来源：beancount.io bean-labs research log（2026-06-15）引用 OSWorld 论文结论：
> "75% of failures traced to visuomotor grounding errors rather than reasoning failures"

**含义**：
- 模型"看懂"了屏幕，但"做不到"正确点击/输入
- 纯 reasoning 能力强的模型（Claude Opus 4.6 reasoning 极强）不等于桌面操作强
- **GUI grounding 能力（看见→做到）是核心瓶颈**

这对 Hermes 的意义：
- Hermes 的 vision 层（smolvlm2）负责"看见"，但需要精确的坐标准确率才能"做到"
- Auto-execute 的核心挑战不是理解场景，而是精确定位 UI 元素
- 提升坐标准确率比提升推理能力对桌面操作更有价值

## Qwen3-VL 技术报告核心（arXiv 2511.21631, 2025-11-26）

**架构三大升级**：
1. **interleaved-MRoPE** — 更强时空建模（图像+视频）
2. **DeepStack** — 多级 ViT 特征融合，提升 vision-language 对齐
3. **text-based time alignment** — 视频时间对齐（从 T-RoPE 演进）

**模型系列**：
- Dense：2B / 4B / 8B / 32B（Ollama 可用：2b/4b/8b）
- MoE：30B-A3B / **235B-A22B**（OSWorld 66.7% 的功臣，需 llama.cpp/LM Studio）

**上下文**：256K token 原生支持（text + interleaved multimodal）

**定位**：image-grounded reasoning、agentic decision-making、multimodal code intelligence 的基础引擎

## 对 Hermes 的启示

1. **GUI grounding > 通用推理**：在桌面操作场景，精确的视觉定位比强大的推理能力更重要
2. **Qwen3-VL 2B/4B/8B 可直接通过 Ollama 使用**（M4 24G 可跑 2B/4B）
3. **Vocaela-500M（85.8% ScreenSpotV2）** 的方向是对的，但 Ollama 集成有问题（mmproj 不支持）
4. **Smol2Operator 归一化坐标**（0-1 范围）比像素坐标好 20x（41% vs 4%），Hermes 未来的 grounding 应采用归一化坐标

## 参考链接

- OSWorld Leaderboard：https://llm-stats.com/benchmarks/osworld
- Qwen3-VL Technical Report：https://arxiv.org/abs/2511.21631
- OSWorld 官方：https://os-world.github.io/