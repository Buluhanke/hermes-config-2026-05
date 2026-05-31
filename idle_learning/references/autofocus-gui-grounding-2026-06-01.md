# AutoFocus + GUI-Cursor + GUI-G² — GUI Grounding 最新进展 (2026-06-01)

## ⭐ AutoFocus: Uncertainty-Aware Active Visual Search for GUI Grounding

**来源**: arXiv:2605.02630, May 4, 2026
**关键词**: training-free, uncertainty-aware, active visual search, perplexity-based

### 核心思路

现有的 GUI grounding 在高分辨率界面上表现差（resolution gap）。现有的 zoom-in 策略依赖固定锚点/启发式网格/RL，缺乏自适应机制。

**AutoFocus 的解决方案**：直接用坐标生成过程中的 **token-level perplexity** 作为空间不确定性信号，不需要额外的训练。

### 技术流程

1. **多假设采样**：不单次预测坐标，而是采样多个坐标假设
2. **Anisotropic Gaussian 空间概率场**：将各轴的 perplexity 转换为各向异性的高斯概率分布，显式建模**方向性不确定性**（不同方向不确定性不同）
3. **Shape-Aware Zooming**：基于概率场生成全局和局部区域提议，平衡定位精度与上下文保留
4. **Visual Prompt 聚合**：通过结构化比较选出最一致的预测

### 关键特点

- **Training-free**：不需要微调任何模型，即用即装
- **Perplexity 作为不确定性信号**：VLM 在坐标生成时 high perplexity = 模型对位置不确定
- **跨 VLM 通用**：在通用 VLM 和 GUI 专用 VLM 上均有改进
- Benchmark: ScreenSpot-Pro 和 ScreenSpot-V2 上 consistent improvements

### 对 Hermes 的价值

| AutoFocus 概念 | Hermes handler 对应 |
|---|---|
| token-level perplexity → spatial uncertainty | handler 中 scene classification 的置信度判断 |
| 多假设采样 | 多次 VLM 分类采样 → 一致性判断 |
| Shape-Aware Zooming | 不确定时先截图局部区域再分析 |
| 视觉 prompt 聚合 | 结构化的场景多角度分析 |

**核心价值**：解决了 SafeGround 需要训练的问题 — AutoFocus 是 training-free 的不确定性量化方案。可直接集成到 handler。

### 相关链接

- arXiv: https://arxiv.org/abs/2605.02630
- Submitted: May 4, 2026

---

## ⭐ GUI-Cursor: Interactive Search for GUI Grounding

**来源**: arXiv:2509.21552v2, ICML 2026 (v2 updated May 25, 2026)
**作者**: Yu Zhao, Wei-Ning Chen et al. (Microsoft Research / University of Edinburgh)

### 核心思路

重构 GUI grounding 为**交互式光标搜索任务** — VLM 不是直接输出坐标，而是逐步移动光标靠近目标。

### 关键要素

1. **Rendered cursor as visual feedback**：每一步渲染的光标位置提供视觉参考，帮助模型对齐
2. **Multi-step online RL**：密集轨迹奖励函数，每一步的 cursor movement 都获得反馈
3. **Adaptive steps**：困难例子自动增加推理步数
4. **Spatial reasoning**：评估光标与目标的 spatial relations

### 效果

- 相同基座模型下超越强 baseline
- 训练数据更少
- OOD 空间推理更强

### 对 Hermes 的价值

验证了 **cursor-based 交互式搜索**的可行性。Hermes 的 humanize_click + hermes-rpa 已经有类似 cursor 位置反馈机制 — 方向正确。

---

## ⭐ GUI-G²: Gaussian Reward Modeling for GUI Grounding

**来源**: AAAI 2026, ZJU-REAL
**代码**: https://github.com/ZJU-REAL/GUI-G2

### 核心思路

将点击点建模为**平滑的高斯概率分布**而非离散的 hit-or-miss 目标。

### 技术

- 模拟人类点击行为的自然高斯分布模式
- 点击区域的连续概率分布 → 密集学习信号（比离散二元信号更丰富）
- 与 Valley-to-Peak (V2P, arXiv 2508.13634) 同方向 — 两者均用 Gaussian 建模替代二元分类

### 对 Hermes 的价值

验证了 Gaussian 建模在 GUI grounding 中的有效性。与 LITE/V2P 系列方法同方向，说明 **continuous probability modeling** 是 grounding 核心趋势。
