# GUIDE Benchmark (CVPR 2026)

**Paper**: GUIDE: A Benchmark for Understanding and Assisting Users in Open-Ended GUI Tasks
**arXiv**: 2603.25864
**Code**: https://guide-bench.github.io/

## 核心架构

三层递进任务：
1. **Behavior State Detection** — 9类行为状态分类（最强模型44.6%）
2. **Intent Prediction** — 4选项MCQ（较强Claude 71.39%）
3. **Help Prediction** — (3-1) 二分类是否需要帮助 + (3-2) 4类帮助内容

## 数据集

- 67.5小时真实用户屏幕录制
- 54/120名新手用户，10个软件应用（5类）
  - Photo Editing: Photoshop, GIMP
  - Graphic Design: Figma, Canva
  - Presentation: PowerPoint, Google Slides
  - Video Editing: Premiere Pro, CapCut
  - Data Analysis: Google Sheets, Microsoft Excel
- WhisperX语音转录 + Gemini-2.5-Pro自动标注 + 人工审核
- 96.1%行为标签一致率

## 九类行为状态Taxonomy

**四大阶段 + 9状态**：

| 阶段 | 状态 | 描述 |
|------|------|------|
| **Planning** | Task Understanding and Preparation | 解释任务、收集资源、配置环境 |
| | Ideation and Planning | 高层次概念工作、头脑风暴 |
| | Seeking External Help | 识别知识缺口，转向外部资源 |
| **Execution** | Exploration and Decision-Making | 试验选项、理解效果、决定用哪个 |
| | Performing Actions | 自信操作软件，目标明确少犹豫 |
| **Problem-Solving** | Frustration | 遇到阻塞，表现困惑/烦躁 |
| | Debugging | 积极调查问题原因，形成并测试假设 |
| **Evaluation** | Waiting and Monitoring | 被动等待系统进程完成 |
| | Assessment | 有意暂停，审视评估工作质量 |

对齐 Norman's Seven Stages of Action 和 Bloom's Taxonomy。

## 完整实验结果表（8模型 × 4任务 × 3条件）

2026-05-31 从 guide-bench.github.io 直接提取。颜色标记：「–」= 无上下文（裸视频输入），「+Prev.」= 加前一段行为，「+Behavior」= 给出当前行为状态标签，「+Behv.+Intent」= 给出行为+意图完整上下文。

### (1) Behavior Detection（9类分类，%）

| Model | – | +Prev. |
|-------|---|--------|
| **Claude-4.5-Sonnet** | **44.61** | **45.63** |
| Gemini-2.5-Pro | 42.44 | 43.79 |
| Qwen3-VL-8B | 37.97 | 38.13 |
| Gemini-2.5-Flash | 36.91 | 38.19 |
| GPT-4o | 36.32 | 37.24 |
| InternVL3-8B | 22.57 | 24.90 |
| InternVideo2.5-8B | 21.57 | 27.02 |
| GPT-4o-mini | 17.65 | 17.07 |

### (2) Intent Prediction（4选MCQ，%）

| Model | – | +Behavior |
|-------|---|----------|
| **Claude-4.5-Sonnet** | **71.39** | **72.62** |
| Gemini-2.5-Pro | 67.80 | 70.16 |
| Gemini-2.5-Flash | 65.40 | 66.77 |
| Qwen3-VL-8B | 62.70 | 64.03 |
| GPT-4o | 61.19 | 62.58 |
| GPT-4o-mini | 60.76 | 62.19 |
| InternVL3-8B | 46.11 | 46.97 |
| InternVideo2.5-8B | 43.79 | 45.13 |

### (3-1) Help Need Detection（二分类，%）

| Model | – | +Behv. | +Behv.+Intent |
|-------|---|--------|--------------|
| **GPT-4o** | 49.69 | **87.79** | **87.91** |
| Gemini-2.5-Pro | **69.82** | 84.73 | 82.38 |
| GPT-4o-mini | 46.05 | 78.92 | 82.26 |
| Gemini-2.5-Flash | 53.64 | 76.33 | 78.07 |
| Qwen3-VL-8B | 52.83 | 70.39 | 77.36 |
| Claude-4.5-Sonnet | 39.49 | 58.56 | 59.43 |
| InternVL3-8B | 34.94 | 43.73 | 46.82 |
| InternVideo2.5-8B | 34.36 | 35.35 | 35.25 |

### (3-2) Help Content Prediction（4选MCQ，%）

| Model | – | +Behv. | +Behv.+Intent |
|-------|---|--------|--------------|
| **Claude-4.5-Sonnet** | **55.00** | **62.17** | **82.79** |
| GPT-4o-mini | 31.32 | 42.86 | 79.84 |
| GPT-4o | 45.95 | 48.37 | 79.78 |
| Gemini-2.5-Pro | 52.74 | 57.03 | 79.69 |
| Gemini-2.5-Flash | 49.53 | 53.75 | 78.59 |
| InternVideo2.5-8B | 23.67 | 29.15 | 73.86 |
| InternVL3-8B | 27.03 | 32.20 | 72.97 |
| Qwen3-VL-8B | 46.06 | 50.63 | 80.11 |

## 结构化上下文带来的提升（最关键发现）

裸视频输入下所有模型严重不足（行为检测最佳仅44.6%，帮助内容检测最佳仅55.0%），但提供结构化上下文后跨越式提升：

| Task | 裸视频最佳 | +Full Context最佳 | 提升 |
|------|-----------|-----------------|------|
| Behavior Detection | 44.61% (Claude) | 45.63% (Claude +Prev.) | +1.02pp |
| Intent Prediction | 71.39% (Claude) | 72.62% (Claude +Behavior) | +1.23pp |
| Help Need Detection | 69.82% (Gemini-Pro) | 87.91% (GPT-4o +Behv+Intent) | **+38.22pp** |
| Help Content Prediction | 55.00% (Claude) | 82.79% (Claude +Behv+Intent) | **+27.79pp** |

**最大增益案例**：GPT-4o 帮助内容预测从45.95% → 79.78%（+33.83pp，行为+意图上下文）。

## 八模型相对表现总结

| 模型 | 裸视频 | +上下文 | 综合评价 |
|------|--------|---------|---------|
| Claude-4.5-Sonnet | 行为/意图/内容三项领先 | 帮助需求差（59.43%） | 最强裸理解，上下文增益弱 |
| Gemini-2.5-Pro | 帮助需求裸视频#1（69.82%） | 全面85%附近 | 稳定全面，自带基础理解 |
| GPT-4o | 中等 | 帮助需求87.91% #1 | 上下文增益最大，+38pp |
| Qwen3-VL-8B | 行为/意图中游 | 帮助内容80.11% | 开源最强，接近GPT-4o |
| Gemini-2.5-Flash | 中等 | 全面78%附近 | 性价比高，Flash级表现 |
| GPT-4o-mini | 行为极低（17.65%） | 帮助内容79.84% | 裸视频差但上下文强补齐 |
| InternVL3-8B | 全部垫底（22-34%） | 帮助需求46.82% | 几乎不可用 |
| InternVideo2.5-8B | 全部垫底（21-34%） | 帮助需求35.25% | 最差 |

## 核心发现

1. **行为检测是最大瓶颈**：最强模型Claude仅44.6%，错误模式是把"沮丧/调试"误认为"执行动作"（错过用户遇到困难的信号）
2. **结构化上下文带来巨大提升**：无需更好的模型，只需提供行为+意图标签即可将帮助预测从46%推至82%+
3. **开源小模型（InternVL3）几乎不可用**：assistance need recall接近零，把所有需要帮助的情况误判为不需要
4. **模型规模不等于用户理解力**：Qwen3-VL-8B 通过上下文补齐后帮助内容80.11%，逼近GPT-4o的79.78%（但GPT-4o minis更小却更强）
5. **Claude的"盲区"**：裸视频理解最强但上下文增益最小，提供行为标签后帮助需求仅从39.49%→59.43%

## 对Hermes auto_execute的启示（2026-05-31 更新）

1. **当前scene_type分类需升级**：目前 screen_trigger_handler 用 qwen3-vl:2b 做 scene_type（browser/calculator/wechat/desktop/unknown）过于粗糙。应向 GUIDE 的 9 类行为状态看齐（Frustration/Debugging/Exploration/Performing Actions 等）
2. **结构化上下文是核心催化剂**：auto_execute 不应直接判断"要不要执行动作"，而应先构建用户行为状态→意图→帮助需求的**三层上下文**，据此决策
3. **auto_execute 介入前增加帮助需求判断**：建议增加 needs_help binary 分类步骤，仅在用户明确需要帮助时才介入，避免打扰
4. **"Frustration"状态值得重点关注**：GUIDE 发现模型最容易把用户沮丧误判为正常执行。auto_execute 若能准确捕捉 frustration 信号（频繁撤销、鼠标轨迹犹豫、重复点击），比执行标准动作更有价值
5. **当前DRY_RUN=True安全**：日志仅468条记录，unknown占40%。升级分类器至GUIDE级可大幅提升分类精度和 auto_execute 判断质量

## 局限

- 32帧采样可能错过快速动作
- think-aloud依赖用户表达能力
- 仅评估离线推理，在线实时辅助未验证
- 120 clips数据集规模有限
- 仅桌面软件，未覆盖mobile/web app
