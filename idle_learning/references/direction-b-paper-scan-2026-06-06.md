# 方向 B 深度分析 — GUI Grounding 论文与模型扫描

**日期**: 2026-06-06 22:30
**范围**: GUI Grounding 最新模型 + 基准测试 + 本地部署可行性

## 1. 核心发现：GUI Grounding 2026 模型全景

### 1.1 开源 GUI Grounding 模型

| 模型 | 机构 | 规模 | 亮点 | 本地部署 |
|------|------|------|------|----------|
| **UI-Venus 1.5** | inclusionAI | ? | SOTA on ScreenSpot-Pro, VenusBench-GD, OSWorld-G | ❓ |
| **GUI-G2-3B** | ZJU-REAL (ICLR 2026) | 3B | Semi-online RL for GUI | ❓ |
| **GUI-G2-7B** | ZJU-REAL (ICLR 2026) | 7B | Semi-online RL for GUI | ❓ |
| **Aria-UI** | ? (ACL 2025) | ? | Pure-vision GUI grounding | ❓ |
| **Mano-P** | Mininglamp-AI | ? | #1 on OSWorld (specialized, 58.2%) | **✅ M4 Mac mini** |
| **UI-Atlas** | ? | ? | Multi-platform grounding | ❓ |

### 1.2 关键基准测试

- **OSWorld**: LLM/VLM agents 真实电脑环境任务，人类成功率 72.36%，最佳模型仅 12.24%
  - 主要困难：**GUI grounding** 和 **操作知识**
- **ScreenSpot-Pro**: GUI grounding 标准基准
- **VenusBench-GD**: UI-Venus 提出的 grounding 基准
- **OSWorld-G**: OSWorld 的 grounding 专项基准
- **AndroidWorld / AndroidLab**: 移动端 grounding 基准

### 1.3 四篇新论文（2026-03-30 arXiv）
标题: "Four New Research Papers Advance GUI Grounding for AI Agents"
- 四篇论文同时提出了不同的 GUI grounding 方法
- 核心方向：从纯视觉方法 → 区域感知方法 → 强化学习优化

## 2. Mano-P — M4 Mac 本地部署方案

**关键发现**: Mano-P 是第一个明确标注"Runs locally on Apple M4 Mac mini/MacBook — no data leaves your device"的 GUI grounding 模型。

### 2.1 Mano-P 优势
- **OSWorld specialized 排行榜 #1**（58.2%）
- **M4 Mac 本地运行** — 这正是 Hermes 的硬件环境
- **数据本地处理** — 隐私友好

### 2.2 适合 Hermes 的原因
1. 硬件匹配：M4 Mac mini 24GB RAM 足够运行
2. 隐私：无数据离开设备
3. 本地化：不依赖外部 API（vs 百度 OCR）
4. 可集成：可以作为 ScreenParser YOLO 的替代或补充

## 3. UI-Venus 1.5 — SOTA 基准

- **ScreenSpot-Pro**: 当前最佳 grounding 基准
- **VenusBench-GD**: 专门评估 grounding 能力的基准
- **OSWorld-G**: OSWorld 的 grounding 子集
- **VenusBench-Mobile**: 移动端 grounding 基准

## 4. Hermes 当前方案 vs 业界方案

| 维度 | Hermes 当前 | UI-Venus 1.5 | Mano-P | 差距 |
|------|------------|-------------|--------|------|
| Grounding | qwen3-vl:2b 分类 | 原生 bbox 输出 | 原生 bbox 输出 | ❌ Hermes 无 bbox |
| 准确率 | 未知（unknown 84%）| SOTA | SOTA（OSWorld）| ❌ 未知 vs SOTA |
| 本地部署 | ✅ Ollama + qwen3-vl | ❓ | ✅ M4 本地 | ✅ 平手 |
| 延迟 | ~1-2s (qwen3-vl:2b) | ❓ | ❓ | ✅ qwen3-vl 较快 |
| 集成度 | handler + RPA | 独立 | 独立 | ❌ Hermes 耦合度低 |

## 5. 优先级改进建议

### 短期（无需新模型）
1. **prompt 工程**: 改进 qwen3-vl 的分类 prompt，减少 unknown 率
2. **YOLO 阈值调整**: 调低 active 阈值从 >5 到 >3
3. **增加场景类别**: chrome/firefox/vscode/finder/terminal

### 中期（集成新模型）
1. **引入 UI-Venus 1.5**: SOTA grounding，如果能本地部署
2. **引入 Mano-P**: 已确认 M4 Mac 本地运行，OSWorld #1
3. **双模型方案**: ScreenParser YOLO 预分类 + UI-Venus/Mano-P 精细化 grounding

### 长期（架构升级）
1. **Grounding 作为第一公民**: handler 返回 `{scene, elements: [{text, bbox}]}` 而非仅场景分类
2. **多平台支持**: Android/iOS  grounding 基准对齐
3. **RL 微调**: 借鉴 GUI-G2 的 semi-online RL 方法
