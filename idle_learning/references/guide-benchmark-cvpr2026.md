# GUIDE Benchmark (CVPR 2026)

**Paper**: GUIDE: A Benchmark for Understanding and Assisting Users in Open-Ended GUI Tasks
**arXiv**: 2603.25864
**Code**: https://guide-bench.github.io/

## 核心架构

三层递进任务：
1. **Behavioral State Detection** — 9类行为状态分类（最难，最强模型44.6%）
2. **Intent Prediction** — 4选项MCQ（较易，最强71.39%）
3. **Assistance Prediction** — 二分类（是否需要帮助）+ 4类辅助类型

## 数据集

- 67.5小时真实用户屏幕录制
- 120名新手用户，10个软件应用
- WhisperX语音转录 + Gemini-2.5-Pro自动标注 + 人工审核
- 96.1%行为标签一致率

## 九类行为状态Taxonomy

**Planning**: goal setting, task planning
**Execution**: executing actions, exploring and deciding  
**Problem-solving**: confusion/help-seeking, debugging/correcting, frustration
**Evaluation**: checking progress, refining work

对齐 Norman's Seven Stages of Action 和 Bloom's Taxonomy。

## 关键实验结果

### 三大任务准确率

| Model | Behavior Detection | Intent Prediction | Assistance Need |
|-------|------------------|-------------------|-----------------|
| Claude-4.5-Sonnet | **44.61%** | 71.39% | 39.49% |
| Gemini-2.5-Pro | 42.44% | 67.80% | **69.82%** |
| GPT-4o | 36.32% | 61.19% | 49.69% |
| Qwen3-VL-8B | 37.97% | 62.70% | 52.83% |
| InternVL3-8B | 22.57% | 46.11% | 34.94% |

### 上下文增强效果（Assistance Need Detection）

| Model | No Context | +Behavior State | +Behavior+Intent | Gain |
|-------|-----------|----------------|------------------|------|
| GPT-4o-mini | 46.05% | 78.92% | 82.26% | +36.21pp |
| GPT-4o | 49.69% | 87.79% | 87.91% | +38.22pp |
| Gemini-2.5-Pro | 69.82% | 84.73% | 82.38% | +14.91pp |

## 核心发现

1. **行为检测是最大瓶颈**：最强模型Claude仅44.6%，错误模式是把"沮丧/调试"误认为"执行动作"（错过用户遇到困难的信号）
2. **结构化上下文带来巨大提升**：提供行为状态后GPT-4o assistance F1从47.73跃升至90.19（+42pp）
3. **开源小模型几乎不可用**：InternVL3 assistance need recall接近零，把所有需要帮助的情况误判为不需要
4. **模型规模不等于用户理解力**：Qwen3-VL-8B assistance 52.83%，远低于GPT-4o-mini的46%→82%上下文提升

## 对Hermes auto_execute的启示

1. **当前smolvlm2的scene classification**（browser/wechat/calculator）对应 GUIDE 的 behavioral state detection，但只有9类
2. **auto_execute需要捕捉用户困难信号**：用户遇到困难时的微妙行为（频繁撤销、鼠标轨迹犹豫）比最终动作更重要
3. **分层上下文架构值得借鉴**：behavioral state → intent → assistance 三层递进，auto_execute可以从单层动作扩展为三层决策
4. **当前DRY_RUN=False时的风险**：如果模型无法正确判断用户是否需要帮助，可能在用户不需要时打扰，或在需要时忽略

## 局限

- 32帧采样可能错过快速动作
- think-aloud依赖用户表达能力
- 仅评估离线推理，在线实时辅助未验证
- 120 clips数据集规模有限
