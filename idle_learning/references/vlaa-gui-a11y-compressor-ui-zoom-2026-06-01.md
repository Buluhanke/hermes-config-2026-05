# Direction C 最新论文：VLAA-GUI + A11y-Compressor + UI-Zoomer + GUI-Perturbed

**发现日期**：2026-06-01 03:27 (idle_learning方向C巡检)
**来源**：OSU-NLP-Group/GUI-Agents-Paper-List (804 stars, 537 papers)

---

## ⭐ VLAA-GUI (arXiv, Apr 23 2026) — Know When to Stop, Recover, and Search

**标题**：VLAA-GUI: Knowing When to Stop, Recover, and Search, A Modular Framework for GUI Automation

**作者**：Qijun Han, Haoqin Tu, Zijun Wang et al. (UCSC, CMU, UNC, Salesforce, UC Berkeley)

**核心贡献**：
- 模块化框架解决 GUI agent 的**三大失败模式**：
  1. 过早终止 (Premature task termination)
  2. 无产出循环 (Unproductive action loops)
  3. 卡死 (Deadlock)
- 三层决策：**Stop**（判断任务是否完成）→ **Recover**（回滚/纠正）→ **Search**（探索替代路径）

**Benchmark 成绩**：
- OSWorld: **77.5%** — 至今最高之一
- WindowsAgentArena: **61.0%**
- 多 LLM backbone 兼容（不绑定特定模型）

**对 Hermes 的价值**：
- 否定检测 = 基础版 Recover；可借鉴 VLAA-GUI 的完整三层框架
- Stop 阶段 → 判断任务是否真正完成（当前 handler 缺失此阶段）
- Recover 阶段 → 回滚到已知好状态（当前缺少回滚机制）
- Search 阶段 → 探索替代路径替代重复无用动作
- 与 RoTS-32B (ICML 2026 Spotlight) 的 GUI-RobustEval 方法论互补

---

## ⭐ A11y-Compressor (arXiv, May 1 2026) — Observation Compression

**标题**：A11y-Compressor: A Framework for Enhancing the Efficiency of GUI Agent Observations

**作者**：Michito Takeshita et al. (Hosei University)

**核心贡献**：
- 将线性化 accessibility tree 观测重构成紧凑结构化表示
- 压缩至原始 token 的 **22%** （78% 缩减）
- OSWorld 任务成功率平均提升 **+5.1pp**

**对 Hermes 的价值**：
- 当前 handler 纯视觉（无 a11y tree），但若未来引入 AX tree 作为辅助信号，此压缩方案适用
- 通用原则：observation compression 降低 token 成本且不损失（甚至提升）性能
- 间接验证了 handler 的 400px resize 策略（降维→性能提升）

---

## ⭐ UI-Zoomer (arXiv, Apr 15 2026) — Training-free Uncertainty Zoom

**标题**：UI-Zoomer: Uncertainty-Driven Adaptive Zoom-In for GUI Grounding

**作者**：Fei Tang, Bofan Chen et al. (ZJU)

**核心贡献**：
- 将 zoom-in 的触发时机和缩放尺度建模为**预测不确定性量化问题**
- Confidence-aware gate：仅当需要时激活 zoom-in
- Uncertainty-driven module：通过方差分解选取每实例的 crop 尺寸
- **Training-free**，兼容多种模型架构

**Benchmark 成绩**：
- GUI grounding 提升 **4.2-13.4%** （三个基准）
- ScreenSpot-Pro 跨 VLM 均有改进

**对 Hermes 的价值**：
- 与 AutoFocus (arXiv 2605.02630) 不确定性感知方法互补
- 对 handler：在 other/unknown 场景做 second-pass zoom-in 时可直接集成
- Training-free → 无需训练即可集成到 handler 流程中

---

## ⭐ GUI-Perturbed (arXiv, Apr 15 2026) — Grounding Robustness

**标题**：GUI-Perturbed: Domain Randomization Reveals Systematic Brittleness in GUI Grounding Models

**作者**：Yangyue Wang et al. (Fig AI, Manifold Research)

**核心贡献**：
- 控制变量扰动框架：独立变化视觉场景和指令以探测 grounding 鲁棒性
- 模型在标准基准报告 >85%，**空间推理时下跌 27-56 分**
- 暴露了系统性脆弱性而非真正 grounding 能力

**对 Hermes 的价值**：
- 对 auto_execute：坐标 grounding 在不同分辨率/布局下需要鲁棒性验证
- 提示：handler 的场景分类需要在不同屏幕分辨率、窗口布局下测试稳定性
- 空间推理下跌风险 → DRY_RUN=False 前需在多布局下验证人机确认率

---

## 综合对 Hermes 的价值排序

| 论文 | 优先级 | 直接用途 | 集成复杂度 |
|------|--------|---------|-----------|
| VLAA-GUI | P0 | handler Verify 阶段三层框架 | 中（代码重构 handler 逻辑） |
| A11y-Compressor | P1 | 未来引入 AX 辅助信号时的前置步骤 | 低（仅参考） |
| UI-Zoomer | P1 | other/unknown 场景集成 | 低（training-free, 直接调用） |
| GUI-Perturbed | P2 | DRY_RUN=False 前鲁棒性验证 | 低（仅测试方法论） |

**来源链接**：
- OSU-NLP-Group/GUI-Agents-Paper-List: https://github.com/OSU-NLP-Group/GUI-Agents-Paper-List (Web 版: osu-nlp-group.github.io/GUI-Agents-Paper-List)
