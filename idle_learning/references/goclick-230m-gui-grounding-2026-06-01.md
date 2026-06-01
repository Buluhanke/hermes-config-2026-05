# GoClick — 230M 轻量级 GUI Element Grounding VLM (Apr 2026)

> arXiv: 2604.23941 (Submitted Apr 27, 2026)
> 作者: Hongxin Li, Yuntao Chen, Zhaoxiang Zhang

## 概述

GoClick 是仅 230M 参数的轻量级 GUI 元素定位 VLM，专为资源受限设备（如手机）设计。核心发现：在小参数规模下，**encoder-decoder 架构优于 decoder-only 架构**，这与当前主流 decoder-only 趋势相悖。

## 关键技术

1. **Encoder-Decoder 架构选择**：实验证明在 230M 规模，encoder-decoder 比 decoder-only 更适合 GUI grounding（decoder-only 子最优）
2. **渐进式数据精炼管线 (Progressive Data Refinement)**：从 10.8M 原始数据集中通过 task type filtering + data ratio adjustment 提取 3.8M 高质量核心集
3. **设备-云端协作框架**：GoClick 端侧定位 + 云端规划器 → 精确元素定位 + 更高任务成功率

## 对 Hermes 的启示

- **230M 超轻量**：M4 CPU 可运行，无需 GPU。当前 qwen3-vl:2b (1.76GB) VLM 场景分类可被 GoClick 补充做精确 grounding
- **Encoder-Decoder > Decoder-only**：与我们当前 qwen3-vl:2b decoder-only 方案对比，GoClick 架构更适合 grounding 任务
- **设备-云端协作**：可映射到 Hermes 的 screen_watcher (端侧 YOLO 预分类) → handler (VLM 场景分类) → action mapping 三层架构
- **数据精炼方法论**：可指导我们 YOLO 训练数据的清理策略

## 劣势

- **纯 grounding 模型**：不包含场景理解/分类能力，需配合场景分类器使用
- **仅 230M**：能力上限低于 1B+ 模型，复杂场景可能失效
- **未提供 Ollama GGUF**：需从 HuggingFace 或自行转换

## 获取方式

- arXiv: 2604.23941
- PDF: https://arxiv.org/pdf/2604.23941
- 代码: 论文提及但未提供明确 GitHub 链接
