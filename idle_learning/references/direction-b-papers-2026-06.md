# Direction B Papers — 看懂内容（理解层）
## 已发现的论文清单（截至 2026-06-01）

### CORA (arXiv 2604.09155, Apr 10 2026)
Conformal Risk-Controlled Agents — handler guardrail 形式化理论框架
- 三模块后-策略预-动作安全框架：Guardian(risk estimation) → Conformal Risk Control(calibrate) → Diagnostician(confirm/reflect/abort)
- **对 Hermes**: 当前否定检测(前12字符 heuristic) → conformal risk control(formal guarantee)
- Guardian = qwen3-vl:2b logprob（已产线运行），calibration 数据 = 834 dry-run 日志
- Goal-Lock 抵抗视觉注入 = CRITICAL_KEYWORDS + 否定检测的语义化升级

### AutoGUI-v2 (arXiv 2604.24441, Apr 27)
2,753 任务/6 OS 的 GUI 功能理解基准
- 开源模型(Qwen3-VL)在 functional grounding 领先，商业模型在 captioning 领先
- 验证 qwen3-vl:2b 选型正确

### OS-BLIND (arXiv 2604.10577, Apr 12)
良性指令→有害环境上下文攻击，>90% agent 成功率
- 安全对齐只在初始激活，执行中不再评估 → 验证 handler 每帧场景分类+全否定检测为正确设计

### EE-MCP (arXiv 2604.09815, Huawei)
自进化 MCP-GUI 混合策略，experience bank +10pp
- 验证 dry-run 日志积累可作为 self-evolution 的数据基础

### UI-Injection (arXiv 2604.07831, Apr 9)
语义级 UI 元素注入攻击，4.4x 攻击成功率提升
- screen_watcher 纯视觉输入易受攻击 → 需要 cross-modal 验证机制

### H-VLM (H Company Runner H, 3B)
Strongest small ScreenSpot model. Runner H 0.1 achieves 67% WebVoyager
- 专用 GUI VLM 在小模型（3B）上超越 10x 大模型。验证 qwen3-vl:2b 路线。

### GUIDE (CVPR 2026)
三层递进任务：行为检测（9类，44.6%最强）→ 意图预测（71.39%）→ 辅助需求检测（69.82%）
- **核心发现**：结构化上下文是关键催化剂——GPT-4o assistance从46%跃升至82%（+36pp）
- **对Hermes的启发**：auto_execute需要捕捉用户困难信号（confusion/frustration）

### UI-Zoomer (ZJU-REAL, arXiv 2604.14113)
training-free 自适应缩放 GUI grounding，置信度门控+方差分解，4.2-13.4% 提升

### MolmoWeb (AI2/UW, arXiv 2604.08516)
4B/8B screenshot-only web agent，无 DOM/a11y，SOTA WebVoyager 超越 GPT-4o。验证纯视觉路线。

### Visual Confused Deputy (vLLM/McGill/AMD, arXiv 2603.14707)
双通道 guardrail（视觉+文本分别检查）。handler 场景分类+内容分析的学术验证

### PIRA-Bench (CUHK/Huawei, arXiv 2603.08013)
连续视觉流→意图推断，screen_watcher 范式验证

### AndroTMem (arXiv 2603.18429)
因果链接状态锚点记忆，12 agent 提升 5-30%

### TRISHUL (arXiv 2502.08226, Feb 2025)
训练无关 (training-free) 的 GUI 理解框架
- HSP 多层次解析 + SEED 空间增强元素描述
- 纯视觉，不依赖 HTML/元数据（vs SoM 依赖 DOM）
- 可直接集成到 handler 做 other/unknown 场景的第二层细粒度分析

### AutoFocus (arXiv 2605.02630, May 4, 2026)
训练无关不确定性感知主动视觉搜索 GUI grounding
- token-level perplexity in coordinate generation = spatial uncertainty signal
- training-free 的不确定性量化，可直接在 handler 中用 perplexity 做置信度判断

### GUI-Cursor (ICML 2026, Microsoft Research/Edinburgh)
交互式光标搜索 grounding，Multi-step online RL with dense trajectory-based reward
- 验证 cursor-based 交互式搜索可行，humanize_click 方向正确

### GUI-G² (AAAI 2026, ZJU-REAL)
Gaussian Reward Modeling — 将点击点建模为高斯概率分布

### MobileWorldBench (arXiv 2512.14014, Dec 2025)
语义世界模型 for Mobile GUI，1.4M samples
- screen_watcher 可输出语义化 "state transition" 描述

### GUI-ReWalk (ByTeadance, IJCAI 2026)
推理增强 GUI 轨迹合成 — 随机探索→推理增强→多阶段轨迹合成

### LocateAnything-3B (NVIDIA, arXiv 2605.27365, May 26-27 2026)
Parallel Box Decoding (PBD) — 3B 参数，M4 24GB 可运行
- HuggingFace: nvidia/LocateAnything-3B
- ❌ GitHub 不存在，代码通过 HF + vLLM/Transformers 部署

### ScreenParse + ScreenVLM + ScreenParser (ICML 2026)
ScreenParse v2: 1,447,100 screenshots, 25,575,213 elements
- ScreenVLM: 316M params, 0.592 PageIoU
- ScreenParser: YOLO11-Large fine-tuned at 1280px, 55 UI classes
- CPU推理 93ms@320px (75x faster vs VLM)

### R5 Papers (2026-06-01)
- GUI-CIDER (2605.28534): Mid-training paradigm
- DocOS (2605.18048): 主动搜索文档处理长尾任务
- Macaron-A2UI (2605.24830, Tencent): Generative UI
- DynamicUI (2604.25380): 视频输入解决动态GUI
- GUI Grounding Sensitivity Benchmark (EACL 2026): 单prompt不鲁棒
- CutVerse (2605.19484): 媒体编辑基准36%

### ScreenSearch (arXiv 2605.16024, May 15 2026)
PUCT graph-bandit 用于大规模桌面探索
- 1M screenshots / 30K deduplicated states
- Novelty-Ambiguity Trade-off 验证有限场景分类方向正确

### TOCTOU Attacks on CUA (arXiv 2604.18860, Apr 20 2026)
Observation-to-action gap avg 6.51s → TOCTOU window
- PUSV防御: 3层 pre-execution UI state verification

### Apple FastVLM / ZonUI-3B / Mano-P / RoTS-32B
详见各自 reference 文件

### New (2026-06-01 discovery):

### uxCUA (arXiv 2604.26020, Apr 28)
Training CUAs to assess GUI usability
- 三步：优先交互流 → 拟人化交互 → 预测可用性评分
- 超越更大模型的可用性评估准确度
- **对 Hermes**: screen_watcher 场景分类+内容分析可扩展为可用性评估

### Same Outcomes, Different Journeys (arXiv 2604.07929, Apr 9, Stockholm/Spotify)
人类 vs GUI agent 行为 trace-level 比较
- **核心发现**: 结果对齐 ≠ 行为对齐
- 人类: content-centric, exploratory | Agent: search-centric, low-branching
- **对 Hermes**: 强化 humanize_click 方向必要性

### Code as Agent Harness (arXiv 2605.18747, May 18)
大规模综述，framing code as agent infrastructure
- 三层: harness 接口 → harness 机制 → 规模化
- 覆盖 GUI/OS automation, embodied agents
- **对 Hermes**: 直接验证 code-based agent 架构
