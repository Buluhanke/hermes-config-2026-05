# ICLR 2026 GUI Grounding Papers — 新发现 (2026-06-02)

来源：raw.githubusercontent.com/ZJU-REAL/Awesome-GUI-Agents/main/ICLR2026/Paperlist.md（browser_navigate + CDP JS 提取）

## 1. CNRL — Label-free GUI Grounding via Confidence-guided Negative RL

- **架构**：Label-free training, 仅用负样本学习
- **结果**：CNRL-7B 92.1% ScreenSpot-V2（超越 UI-TARS-72B 90.3%），33.8% ScreenSpot-Pro
- **关键洞察**：学习"避免什么"比从不确定的正样本学习更有效
- **Hermes 相关度**：场景分类中降低 false positive 有参考价值

## 2. ManiCoG — Manipulation-based Chain of GUI Grounding

- **方法**：Coarse-to-fine focus + candidate selection，训练无关（plug-and-play）
- **结果**：TianXi-Action-7B 51.9% → 57.8% ScreenSpot-Pro
- **Hermes 相关度**：无训练改进方法可直接应用（不依赖模型重新训练）

## 3. UI-Ins — Multi-Perspective Instruction as Reasoning

- **架构**：SFT + RL 两阶段，将指令视为动态分析路径
- **结果**：UI-Ins-32B 87.3% UI-I2E-Bench；UI-Ins-7B 66.1% AndroidWorld
- **Hermes 相关度**：指令多样性 → 更鲁棒的 scene understanding

## 4. GUI-R1 — R1-Style Vision-Language Action Model for GUI Agents

- **架构**：统一动作空间规则建模 + 强化微调（RFT）
- **仅 3K 数据 vs OS-Atlas 13M（0.02%）**
- **跨平台**：Windows, Linux, MacOS, Android, Web
- **Hermes 相关度**：强化微调范式 vs 传统 SFT，3K 数据的高效性可参考

## 5. GUI-AIMA-3B — Aligning Intrinsic Multi-Modal Attention

- **架构**：Attention-only, coordinate-free SFT 框架
- **仅 85K 截图训练**
- **结果**：~44.9 ScreenSpot-Pro, 90.8 ScreenSpot-v2（3B 模型 SOTA）
- **Hermes 相关度**：3B 模型尺寸适合 M4 本地部署，无需坐标回归

## 6. GUI-Spotlight — Adaptive Iterative Focus Refinement

- **方法**：动态调用多个专用工具迭代缩小关注区域
- **Hermes 相关度**：多工具协作范式 → screen_watcher 多模型 routing 参考

## 7. Generalist Scanner + Specialist Locator — Coarse-to-Fine Framework

- **方法**：通用扫描器（粗定位）+ 专用定位器（精确定位）协同
- **Hermes 相关度**：两阶段架构 → screen_watcher YOLO 预分类 + VLM 精分类的验证

## 8. EAM — Executable Agentic Memory (arXiv 2605.12294, May 12, 2026)

- **方法**：结构化知识图谱将 GUI 规划从自由生成 → 检索执行
- **关键技术**：State-aware DFS + action group mining，轻量 Q 函数引导 MCTS
- **结果**：+19.6% over UI-TARS-7B on AndroidWorld，6x token cost reduction vs GPT-4o
- **延迟**：平均 2.8s
- **Hermes 相关度**：结构化记忆 → 可应用于 screen_trigger handler 减少重复 VLM 分析
