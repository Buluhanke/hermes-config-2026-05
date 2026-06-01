# Direction B — 2026-06-02 论文扫描发现（OSU-NLP YAML + arXiv）

## 新增论文（未在之前 reference 中记录）

### macOSWorld (arXiv 2506.04135, Jun 2025)
**First interactive benchmark for GUI agents on macOS**
- 202 多语言任务，覆盖 30 个应用
- 包含专用安全子集
- **对 Hermes**: 验证 macOS-first 路线，可作未来 auto_execute 的评估框架

### ScreenSpot-Pro (arXiv 2504.07981, Apr 2025)
**High-resolution GUI grounding for professional computer use**
- 1,581 任务，23 个应用，5 个行业
- 挑战：高分辨率显示、小目标、复杂环境
- **对 Hermes**: 直接指导 nclick 坐标映射链设计

### CUAAudit (arXiv 2603.10577, Mar 2026)
**Meta-Evaluation of VLM as Auditors of CUA Agents**
- VLM 作为桌面 agent 任务成功裁判
- **对 Hermes**: 验证 qwen3-vl:2b 作为场景分类器路线

### SEA — Self-Evolution Agent (arXiv 2508.04037, Aug 2025)
**Automatic verifiable trajectory + step-wise RL**
- 自动可验证轨迹生成 + temporal compressed sensing
- **对 Hermes**: 映射到 self-evolution 路径

### Robustness of GUI Grounding (arXiv 2504.04716, Apr 2025)
- UGround 等在噪声/攻击下的鲁棒性评估
- **对 Hermes**: 需要评估 qwen3-vl:2b 截图质量鲁棒性

### DPO Local VLM (arXiv 2506.03095, Jun 2025)
- 轻量级本地 VLM 训练，LLM-as-Judge 信号
- **对 Hermes**: 验证 local-first 范式

### GuiRLVG (arXiv 2508.04389, Aug 2025)
- RL for GUI visual grounding + Adversarial KL Factor
- **对 Hermes**: RL fine-tuning 方法论

### ScaleCUA (arXiv 2509.15221, Sep 2025)
- 6 OS 开放数据集 + grounding mode
- **对 Hermes**: 数据管线设计参考

### IntentScore (arXiv 2604.05157, Apr 2026)
- Plan-aware reward model, 398K steps, 3 OS
- **对 Hermes**: auto_execute 轨迹验证器

### CaMeLs Can Use Computers Too (arXiv 2601.09923, Jan 2026)
- Dual-LLM: Single-Shot Planning + Branch Steering
- **对 Hermes**: 相似 handler 场景分类架构

### TinyClick (Interspeech 2025, 0.27B)
- 0.27B on-device Florence-2, ScreenSpot competitive
- **对 Hermes**: 超轻量 grounding, M4 CPU 可行
