# ZJU-REAL/Awesome-GUI-Agents（2026-06-07 发现）

**来源**：`https://github.com/ZJU-REAL/Awesome-GUI-Agents`
**维护方**：浙江大学 ZJU-REAL 团队（228 commits，423 stars）
**定位**：最全面的 GUI Agents 学术资源库

## 四模块框架

按功能分为四个模块：

| 模块 | 核心问题 | 代表工作 |
|------|---------|---------|
| **Perception** | 如何"看见"屏幕 | smolvlm2, qwen3-vl, UI-TARS |
| **Exploration** | 如何探索环境 | UI-Voyager, AndroTMem |
| **Planning** | 如何规划行动 | UI-Copilot, GUI-Libra |
| **Interaction** | 如何执行操作 | Agent-S, computer-use agents |

## 重点论文（2026年新发布）

### 自进化方向
- **UI-Voyager (2026-03-26)** — 通过"失败经验"自进化
  - 核心：Agent 失败 → 积累失败经验 → 用失败经验重新训练/规划
  - 与 Hermes idle_learning 的"从错误中学习"理念高度契合
  - arXiv: UI-Voyager（需进一步查阅具体方法）

### 长程记忆
- **AndroTMem (2026-03-21)** — 轨迹到锚定记忆
  - 将交互轨迹转化为结构化记忆，支撑长时任务
  - 对 Hermes 跨 session 记忆能力有参考价值

### RL 训练
- **UI-Copilot (2026-04-16)** — Tool-Integrated Policy Optimization
  - R1-style reasoning + tool integration，解决长程 GUI 任务规划问题
- **LiteGUI (2026-05-11)** — RL 蒸馏紧凑 GUI Agent
  - 目标：用强化学习把大模型知识蒸馏到小模型，适合 M4 24GB 场景

### Token 压缩
- **AQuaUI (2026-05-22)** — 自适应四叉树视觉 Token 压缩
  - 自适应减少 GUI Agent 观察的 token 数量，加速 VLM 推理
  - 与 Hermes 现有截图降采样策略互补（可能提升 qwen3-vl:2b 响应速度）

## Benchmark 列表（按模块）

### GUI Grounding Benchmarks
- ScreenSpot-V2（当前主流）
- OSWorld（最难）
- AndroidWorld
- WinSpot（Windows专项）

### GUI Navigation Benchmarks
- WebArena
- MobileWorldBench
- Mind2Web 2

## 对 Hermes 的启发

1. **四模块覆盖完整**：Hermes 现有能力已覆盖 Perception(smolvlm2) + Exploration(screen_watcher) + Interaction(computer_use)，缺 Planning 模块的主动推理
2. **UI-Voyager 自进化机制**：值得借鉴到 Hermes idle_learning，实现"失败→学习→改进"闭环
3. **AQuaUI Token 压缩**：可研究用于优化 screen_trigger_handler 截图降采样，降低 qwen3-vl:2b 的响应延迟

## 已知限制
- 资源库本身是论文集合，非可直接运行的代码
- 部分论文需要 arXiv 访问（github.com 已恢复，可访问）
