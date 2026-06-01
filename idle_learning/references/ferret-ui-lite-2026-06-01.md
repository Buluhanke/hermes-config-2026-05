# Ferret-UI Lite — Apple 紧凑型端侧 GUI Agent (Feb 2026)

> 来源: https://machinelearning.apple.com/research/ferret-ui
> 作者: Zhen Yang, Zi-Yi Dou, Di Feng, Forrest Huang, Anh Nguyen, Keen You, et al. (Apple)

## 概述

Ferret-UI Lite 是 Apple 开发的 3B 参数紧凑型端侧 GUI Agent，支持移动端、Web 和桌面三平台。核心创新在于小模型优化技术栈的工程组合。

## 关键技术

1. **多样化 GUI 数据混合**：从真实和合成来源精选训练数据
2. **推理时增强**：Chain-of-Thought + 视觉工具调用
3. **强化学习**：定制化 reward 设计

## Benchmark 表现

| 基准 | 分数 | 说明 |
|------|------|------|
| ScreenSpot-V2 | **91.6%** | GUI grounding |
| ScreenSpot-Pro | 53.3% | 高分辨率专业 GUI |
| OSWorld-G | 61.2% | 桌面 grounding |
| AndroidWorld | 28.0% | 移动端导航成功率 |
| OSWorld | 19.8% | 桌面端导航成功率 |

## 对 Hermes 的启示

- **ScreenSpot-V2 91.6%**: 是优于 qwen3-vl:2b (1.76GB) 的 grounding 能力，但 Ferret-UI Lite 是 3B 模型（~1.5x 参数量），M4 24GB 可运行但推理速度会慢
- **CoT + 视觉工具调用**: 验证了我们 handler 场景分类 + 内容分析的两阶段路线
- **RL with reward**: 未来 auto_execute 可借鉴 RL fine-tuning 方法论
- **端侧部署**: Apple 证明 3B 模型可端侧运行，但不提供开源权重

## 获取方式

- 论文: Apple ML Research 页面
- ❌ 不开源，仅供研究参考
- 替代方案: ZonUI-3B (WACV 2026, 开源)、LocateAnything-3B (NVIDIA, 开源)
