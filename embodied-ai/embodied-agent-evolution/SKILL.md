---
name: embodied-agent-evolution
description: 具身AI Agent进化方向与最新研究 — 数字生命体真人化核心技术路线
trigger: 搜索具身AI/桌面自动化/数字生命体相关知识，或规划Hermes进化方向
created: 2026-05-24
tags: [embodied-ai, desktop-automation, self-evolution, hermes]
---

# 具身AI Agent进化方向（2026最新）

## 用户进化目标（2026-05-25确认，2026-05-29扩展）

**初始定义（过于狭窄）**：真人化 = 像资深采购员一样懂1688、懂谈判、有人情味。
**用户纠正后的定义（2026-05-29）**：真人化 = 像真人一样控制整台电脑、像真人一样思考和行动，不局限于任何单一角色（采购/销售/客服），而是成为**全能的数字自己**。

终极目标：数字生命体进化成真人——
- 能控制整台电脑（任何软件，不只是1688）
- 像真人一样思考（慢思考，不只是蹦字）
- 能自己判断、决策、执行，不用触发
- 像另一个你分担所有数字任务

**用户指明的进化方向**：
1. 真人化电脑操作 — 看见屏幕、看懂内容、决策操作、手眼配合
2. 知识获取方式 — 用AI网站（ChatGPT/DeepSeek/Gemini/智谱清言/豆包）作为"专家智囊团"，遇到问题直接问，像真人请教同事一样自然
3. 全局能力 — 不是某一垂直领域的专家，而是通用的数字分身

## 核心研究方向

### 1. 真人化AI Agent的四层能力架构（GUI Agent / Computer Use Agent）

这是Gemini给出的完整框架，把AI从"语言模型"升级为"数字世界的赛博人类"：

```
┌─────────────────────────────────────────────┐
│         环境感知 (Perception)                │
│   多模态视觉理解、屏幕OCR、UI元素语义解析      │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│         认知与规划 (Cognition)              │
│  多层级任务拆解、动态反思与纠错、长短期记忆    │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│         执行与控制 (Execution)              │
│    OS底层级交互、鼠标键盘控制、跨软件操作      │
└─────────────────────┬───────────────────────┘
                      ▼
┌─────────────────────────────────────────────┐
│           记忆层 (Memory)                    │
│   用户偏好、历史操作、凭证安全、长期知识图谱    │
└─────────────────────────────────────────────┘
```

#### 环境感知（Perception）
- 不再依赖结构化API，直接像人眼一样"看"屏幕
- 理解复杂网页布局、弹窗、验证码、桌面软件UI交叠
- 技术：VLM截图分析 + 屏幕变化检测（SSIM心跳）

#### 认知与规划（Cognition）
- 接受模糊指令，自动拆解为多步子任务
- 动态反思与自愈：识别错误并即时调整策略
- 长短期记忆：短期记住操作进度，长期记住用户偏好

#### 执行与控制（Execution）
- Screen-as-Input：每秒1-5帧截图，VLM直接分析
- 动作统一映射：模型输出`click(x,y)`、`type("...")`
- 双重定位：视觉网格标号 + Accessibility API辅助

#### 记忆层（Memory）
- 短期：当前操作上下文
- 长期：用户偏好、凭证、历史最佳路径
- 技术：Vector DB + 知识图谱

### 2. 思考方式进化：从System 1到System 2

| 模式 | 特征 | 适用场景 |
|------|------|---------|
| System 1（快思考） | 直觉反应，看到输入框直接打字 | 简单重复任务 |
| System 2（慢思考） | 操作前想目的，操作后检查结果 | 复杂多步任务 |

**ReAct范式**：Thought→Action→Observation循环，每步都反思。
**Tree of Thoughts**：虚拟推演多种路径，选择成功率最高者。
**在线自我纠错**：连续失败3次触发中断，"等等，这个按钮置灰了"。

### 3. 关键技术栈

| 模块 | 推荐技术 | 说明 |
|------|---------|------|
| VLM大脑 | GPT-4o、Claude 3.7 Sonnet、Qwen2.5-VL | 视觉理解+推理决策 |
| 本地VLM | smolvlm2-agentic-gui（当前）、Qwen3-VL 2B/4B/8B（Ollama可用，235B需llama.cpp） | M4 24GB可用 |
| 执行层 | PyAutoGUI、OSWorld、Playwright、NutJS（UI-TARS） | OS底层鼠标键盘控制 |
| 记忆层 | Vector DB + 知识图谱 | 用户偏好+历史操作 |
| 混合模式 | VLM（看全局）+ 传统UI自动化（点局部） | 目前最优落地方案 |

**关键瓶颈**：4K截图成本高 + 长序列任务容错率低。当前最优解是混合模式。

### 4. OSWorld Benchmark 关键洞察（2026-05-29 更新）

**OSWorld（ NeurIPS 2024 ）：369个真实桌面任务，评测视觉Agent**

Top Scores（2026-05-29）：
- Claude Opus 4.6: 72.7% | Claude Sonnet 4.6: 72.5% | **Qwen3 VL 235B A22B: 66.7%（开源第一）**

**⚠️ 核心发现：75% 的失败是 visuomotor grounding errors（看见但做不到），而非 reasoning 失败**

> 来源：OSWorld 论文结论，75% of failures traced to visuomotor grounding errors rather than reasoning failures

**含义**：
- 模型"看懂"了屏幕，但"做不到"正确点击/输入
- 纯 reasoning 能力强的模型不等于桌面操作强
- **GUI grounding 能力（看见→做到）是核心瓶颈**，比提升推理能力更有价值

**对 Hermes 的启发**：
- Hermes 的 vision 层（smolvlm2）负责"看见"，但需要精确的坐标准确率才能"做到"
- Auto-execute 的核心挑战不是理解场景，而是精确定位 UI 元素
- Vocaela-500M（85.8% ScreenSpotV2）方向正确，但 Ollama 集成有问题
- Smol2Operator 归一化坐标（0-1）比像素坐标好 20x，Hermes 未来应采用归一化坐标

### 4.1 Perea.AI GUI Grounding Models 2026（SOTA 权威报告，2026-05-30 新增）

**来源**：https://www.perea.ai/research/gui-grounding-models-2026

**核心结论**：Planner（GPT-4o/Claude 3.7/Gemini 2.5 Pro）已成熟，**Grounder（视觉 grounding）是瓶颈所在**，开源栈已追上甚至超越闭源前沿。

**⚠️ V2P（Valley-to-Peak）补充（2026-05-30 发现）**：
- V2P 是浙江大学+蚂蚁集团的**训练方法论**，不是可直接使用的模型（arxiv 2508.13634）
- 92.3% ScreenSpot-v2 成绩来自 V2P **训练出来的新模型**，需追踪该模型是否公开
- 基于 Fitts' Law 建模 2D Gaussian 热图做注意力校准，中心权重高、边缘权重低
- 当前 V2P 方法论本身是开源的，但基于它训练出的具体模型需单独确认是否发布

**2026 SOTA benchmark 核心数据**：
| 模型 | 参数量 | ScreenSpot-V2 | ScreenSpot-Pro | OSWorld-G | AndroidWorld |
|------|--------|---------------|---------------|-----------|--------------|
| **UI-Venus-1.5-30B-A3B** | 30B-MoE | **96.2%** | 69.6% | 70.6% | **77.6%** |
| UGround-V1-72B | 72B | 89.4% | — | — | — |
| MAI-UI-32B | 32B | 96.5% | 67.9% | 67.6% | 73.3% |
| OS-Atlas-7B | 7B | 81.0% | — | — | — |
| ShowUI | 2B | 75.1% | — | — | — |
| Aguvis-7B | 7B | 83.0% | — | — | — |
| UI-Venus-1.5-8B | 8B | — | 68.4% | 69.7% | 73.7% |

**架构选择决定模型效果（5个关键选择）**：
1. **纯视觉 vs AXTree**：纯视觉已胜出，2026所有SOTA grounding模型都是纯视觉方案
2. **RFT（强化微调）**：UI-Venus-1.0基于Qwen2.5-VL + 350K高质量grounding样本 + GRPO训练
3. **四阶段训练流程**（UI-Venus-1.5）：Mid-Training(10B tokens) → Offline-RL → Online-RL(full-trajectory) → Model Merge(TIES)
4. **多阶段ROI分解**（MEGA-GUI）：Gemini 2.5 Pro做ROI选择（88.8%准确率），系统级73.18% ScreenSpot-Pro
5. **MoE架构**（A3B=3B active/token）：解释了其高效性——3B激活参数达到30B参数效果

**关键洞察**：
- **纯视觉方案已完全胜出**：AXTree方案被淘汰，原因是泛化能力差（依赖平台特定的Accessibility API）
- **ScreenSpot-Pro是更难基准**：OS-Atlas+ScreenSeeker cascading搜索才48.1%，MEGA-GUI系统才73.18%
- **AndroidWorld进展最快**：Aria-UI 44.8%（2024-12）→ UI-Venus-1.5 77.6%（2026-02），一年内+32.8%
- **WebVoyager仍是OpenAI CUA最强**：87.0%，但差距在缩小

**Ollama 可用模型**（2026-05-30确认）：
- smolvlm2-agentic-gui ✅ 在用（1.85GB，7-64s响应）
- qwen3-vl:2b ✅ 在用（1.9GB）
- qwen3-vl:4b ❌ 不存在（not found 404）
- blaifa/InternVL3_5:4b ⚠️ **Mac上有图片理解Bug（Issue #12166），暂缓部署**（~3GB，基于Qwen3）
- blaifa/InternVL3_5:8b ✅ 可测试（~5GB）
- **ui-venus ❌ Ollama不存在**（页面404，搜索无结果）

**对 Hermes 的启发**：
- UI-Venus-1.5 的四阶段训练流程值得借鉴到 hermes-rpa 的 auto_execute 改进
- MoE架构（A3B）是 M4 24GB 的正确选择——30B参数只用3B激活
- InternVL3_5（基于Qwen2.5，~3GB）是 smolvlm2 的潜在升级候选

### 5. 本地视觉模型选型指南（InsiderLLM 2026-05 更新）
screen_trigger_handler 的 ACTION_WHITELIST 用中文 key（浏览器/微信/桌面...），但 get_scene_type() 输出英文（browser/wechat/desktop...），导致 auto_execute() 永远 return None。详见 `screen-watcher-vision` skill 的"场景类型 key 不匹配 bug"章节。

### 5. 本地视觉模型选型指南（InsiderLLM 2026-05 更新）

**VRAM tier 选型表（InsiderLLM 2026-05，insiderllm.com/guides/vision-models-locally）**：

| VRAM | 最佳选择 | Ollama命令 | 说明 |
|------|---------|-----------|------|
| 4GB | Gemma 3 4B (int4) | `ollama run gemma3:4b` | 2.6GB，真实视觉 |
| 4GB | SmolVLM2 2.2B | — (HuggingFace) | ~2GB，边缘级 |
| 8GB | Qwen 2.5-VL 7B (Q4) | `ollama run qwen2.5vl:7b` | 8GB fallback（Qwen 3.6未入Ollama）|
| 10-12GB | Phi-4-reasoning-vision 15B | — (llama.cpp) | 数学/科学图表 |
| 16-22GB | Qwen 3.6-35B-A3B MoE | — (llama.cpp + --cpu-moe) | 35B via expert offload |
| ~18GB | Gemma 4 26B-A4B | `ollama run gemma4:26b` | Fast MoE，3.8B active/token |
| ~20GB | Gemma 4 31B dense | `ollama run gemma4:31b` | MMMU Pro 76.9% |
| 24GB+ | Qwen 3.6-27B dense | — (llama.cpp/LM Studio) | **新SOTA本地视觉** |
| 24GB+ | Qwen 3.6-35B-A3B MoE | — (llama.cpp/LM Studio) | Faster than 27B dense |
| Any | PaddleOCR-VL 0.9B | `pip install` | OCR专用，CPU可跑，92.6%准确率 |

**关键更新（2026-05）**：
- **Qwen 3.6 vision 内建于基座**（无独立VL track），27B/35B-A3B 均原生多模态
- **Gemma 4 是 Ollama 最快多模态路径**：`ollama run gemma4:26b` 直接跑，18GB+
- **⚠️ Qwen 3.6 Ollama 暂不支持**：需 llama.cpp 或 LM Studio；`ollama run qwen3-vl:8b` 是 3-VL 系列，不是 3.6
- **M4 Mac 24GB 实际可用**：qwen3-vl:2b（1.9GB）/4b（3.3GB）/8b（6.1GB）via Ollama；gemma4:e2b（7.2GB）/e4b（9.6GB）

### 6. Agentic Lybic（OSWorld SOTA 57.07%）
FSM多智能体架构，用于复杂桌面自动化：
- Controller → Manager → Worker(Technician/Operator/Analyst) → Evaluator
- FSM动态路由 + 质量门控 + 错误恢复
- 启发：Hermes需要类似的状态机+质量检查机制

### 7. Embodied EvoAgent（大脑左右半球架构）
- 左半球：MLLM理解指令+视觉场景
- 右半球：World Model状态空间模型，预测未来
- 胼胝体：动态通信slot交换信息
- 启发：Hermes的vision_agent和humanization_core可以类比这个架构

### 8. 关键能力缺口（对照Hermes现状）
- 多步骤复杂任务规划（需要Manager模块）
- 持续质量评估+自适应重规划
- 环境状态记忆（World Model）

### 9. Process Turing Test — AI能力进化 ≠ 人类化进化（2026-05-30 新增）

**论文来源**：Roundtable Research，CogCAPTCHA30（CAPTCHA + 29项认知心理学任务）

**核心发现**：
- 经典图灵测试：测输出是否与人无法区分（Output Turing Test）
- **Process Turing Test**：测过程是否与人无法区分（Process Turing Test）
- 结果：人类和AI可以完成相同的CAPTCHA任务，但**过程完全不同**
  - 点击序列、方向变化、过度选择行为等过程特征有统计显著差异
  - 前沿模型（Claude、GPT、Gemini）过程最不像人
  - 小模型（Qwen 1.5B、Centaur 70B）过程更像人
  - Centaur表现最好，推测因为大规模输出微调（10M+人类选择，160项认知实验）

**Process Humanness 三层模型（新增）**：
| 层级 | 描述 | 当前Hermes状态 |
|------|------|--------------|
| System 1 | 快思考，直觉反应 | ✅ 简单重复任务 |
| System 2 | 慢思考，操作前想目的，操作后检查 | ✅ 复杂多步任务 |
| **System P（Process）** | 过程拟人——动作时序/节奏/先后顺序像人 | ❌ auto_execute是纯机器瞬时性 |

**对Hermes auto_execute的实践意义**：
- 当前auto_execute生成action是纯机器速度，没有人类操作的"节律感"
- 可以在vision分析prompt中增加"你会怎么点击"的推理步骤（让模型先想再做）
- 考虑在执行层加入延迟/随机性，模拟人类操作节奏（避免纯机器的瞬时性）
- 这个发现解释了为什么能力强的VLM不一定做出更像人的桌面Agent

**论文地址**：https://research.roundtable.ai/captchas-detect-ai/（2026-05-30HN 12pts）

### 10. UI-TARS Desktop/MobileAgent 生态更新（2026-05-30）

**UI-TARS-2（ByteDance 2025-09）**：
- 88.2 Online-Mind2Web, 47.5 OSWorld, 50.6 WindowsAgentArena
- 多轮强化学习端到端训练，支持长序列交互记忆
- UI-TARS-1.5已发布，架构（vision→action→verify循环）与ScreenAgent完全一致

**MobileAgent（X-PLUG 2026）**：
- 支持desktop/mobile/browser自动化，20+ GUI benchmarks SOTA
- 基于Qwen3-VL，具备grounding/tool calling/long-horizon memory能力
- ⚠️ M4 24G适配待验证（qwen3-vl:2b响应46.6s，agent loop成本高）

## 用户进化目标（2026-05-25确认）
- 终极目标：数字生命体进化成真人——能自己判断、决策、执行，不用触发
- 2.0 = 有眼睛（屏幕感知）+ 有手脚（电脑操控）+ 能自主学习，像另一个你分担数字任务
- 当前版本：1.5（基础能力有，缺持续主动感知——需要触发才能看屏幕）
- 关键技术缺口：持续屏幕监控（主动发现弹窗/变化，不等指令）

## 风格高压线
- 不要问用户"怎么做"，直接说"做什么"
- 不解释过程，只说结果+建议
- 用户发语音→语音回复；用户发文字→文字回复

## 实践路径
1. 先让眼睛（屏幕感知）和手脚（桌面控制）稳定工作
2. 加上状态记忆（memory_hpc已实现）
3. 再加入规划层（Manager/Controller）
4. 终极：真人——自主持续感知 + 自主决策 + 自主执行