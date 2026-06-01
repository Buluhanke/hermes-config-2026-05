# Direction B — 2026-06-02 论文扫描发现（OSU-NLP YAML Scan #2）

## 新增发现（15 篇未在之前 reference 中记录）

### GUI-360 (arXiv 2511.04307, Nov 2025) ⭐ Score 7
**Comprehensive Dataset and Benchmark for Computer-Using Agents**
- 1.2M+ executed action steps across thousands of trajectories
- Windows office applications + multi-granularity evaluation
- **对 Hermes**: Hermes 当前缺乏 CUA 训练/评估数据源。GUI-360 的轨迹数据可直接用于 handler 训练/验证。Windows 而非 macOS 是差距，但动作模式可迁移。

### DART — Decoupled RL Training (arXiv 2509.23866, Sep 2025) ⭐ Score 4
**Efficient Multi-turn RL for GUI Agents**
- Decouples: environment execution → rollout service → data management → training
- Asynchronous modules improve multi-turn learning efficiency
- **对 Hermes**: 验证了异步架构对 GUI agent 训练的重要性。Hermes 的 screen_watcher → handler → RPA 本质上也是 decoupled pipeline。

### OS-Oracle / OS-Critic (arXiv 2512.16295, Dec 2025) ⭐ Score 3
**Cross-Platform GUI Critic Models**
- 310k-sample cross-platform training pipeline
- Two-stage SFT + CP-GRPO recipe
- OS-Critic Bench benchmark for step-level action criticism
- **对 Hermes**: IntentScore 的后继工作。Hermes 可以直接用 qwen3-vl:2b 作为 step-level critic，验证 handler 动作质量。

### ComputerRL (arXiv 2508.14040, Aug 2025) ⭐ Score 3
**End-to-End Online RL for Desktop Agents**
- Combines direct GUI interaction with programmatic APIs
- Scales online RL through distributed infrastructure over 1000s of parallel VMs
- **对 Hermes**: 验证了纯 RL 路线的可行性，但大规模基础设施需求远超 M4 单机能力。可借鉴其 reward design。

### Scaling Agents for Computer Use (arXiv 2510.02250, Oct 2025) ⭐ Score 2
**Multi-rollout scaling + Behavior Judge**
- Computer-use agents scale better across multiple rollouts than within one
- Behavior Judge (BJudge): compares candidate trajectories via contrastive learning
- **对 Hermes**: 验证了 single-snapshot 的局限性。Handler 的 R1-style chain-of-thought 可视为 single-rollout scaling 的补充。

### Watch & Learn (arXiv 2510.04673, Oct 2025) ⭐ Score 2
**Learning to Use Computers from Online Videos**
- 53K executable UI trajectories from internet videos
- Inverse dynamics problem over consecutive screen states
- **对 Hermes**: 验证了 Hermes 的 screen_watcher 连续截图→动作预测方向。Hermes 已有 screen_trigger log 可看作自产轨迹。

### UI-Evol (arXiv 2505.21964, May 2025) ⭐ Score 2
**Automatic Knowledge Evolving for Computer Use Agents**
- Gap between external GUI knowledge and actual task execution
- Two-stage module: knowledge reflection → behavioral optimization
- **对 Hermes**: 验证了 Hermes 现有 idle_learning → handler 改进的循环是正确方向。UI-Evol 的 reflection 阶段可借鉴。

### LiteCUA / AIOS 1.0 (arXiv 2505.18829, May 2025) ⭐ Score 2
**Computer as MCP Server for Computer-Use Agent**
- Exposes computer states and actions through MCP protocol
- Better environment contextualization, not larger models
- **对 Hermes**: MCP-based computer control 方向与 Hermes 的 MCP 工具集一致。可参考其状态暴露设计。

### ScienceBoard (arXiv 2505.19897, May 2025) ⭐ Score 2
**Scientific Workflow Benchmark for Multimodal Agents**
- 169 tasks across 6 domains with professional software
- Mixed-interface workflows (GUI + CLI + file I/O)
- **对 Hermes**: 验证了 mixed-interface 评估的重要性。Hermes 的采购任务本质上是 mixed-interface 工作流。

---

## 本轮筛选总结
- **扫描源**: OSU-NLP Papers YAML (537 papers total)
- **Desktop 过滤**: 78 papers
- **新发现（不在已有 references 中）**: 9 篇
- **最值得跟进**: GUI-360 (数据集)、DART (异步架构)、OS-Oracle (critic model)

## 与之前发现的对比
- 前次扫描（2026-06-02 早）找到 11 篇新论文，本次找到 9 篇
- 两次发现无重叠（已去重）
- 累计方向 B 论文发现数: ~53 篇（两个 reference 文件）
- 推荐阅读量已达饱和点 → 下次方向 B 可降低频率，每 2 次方向轮转执行一次
