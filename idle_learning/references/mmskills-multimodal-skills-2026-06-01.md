# MMSkills: Towards Multimodal Skills for General Visual Agents

**Paper**: arXiv 2605.13527, May 13, 2026 (v2 May 14)  
**Authors**: Kangning Zhang, Shuai Shao, Qingyao Li, Jianghao Lin, Lingyue Fu, Shijian Wang, Wenxiang Jiao, Yuan Lu, Weiwen Liu, Weinan Zhang, Yong Yu  
**Project page**: https://deepexperience.github.io/MMSkills  

## Relevance to Hermes

**最高优先级** — 第一份从学术角度系统定义和验证"多模态技能"概念的工作。直接验证 Hermes Skills 的方向正确，同时指出 Hermes Skills 当前缺失的视觉维度。

## Core Contribution

"Reusable skills have become a core substrate for improving agent capabilities, yet most existing skill packages encode reusable behavior primarily as textual prompts, executable code, or learned routines. For visual agents, however, procedural knowledge is inherently multimodal."

## MMSkill 结构

每个 MMSkill 是一个紧凑的、状态条件化的包：

| 组件 | 说明 | Hermes 对应 |
|------|------|-----------|
| Textual procedure | 文本过程描述 | Hermes SKILL.md ✅ |
| Runtime state cards | 运行时的关键 UI 状态截图 + 关键元素标注 | ❌ 缺失 |
| Multi-view keyframes | 多视角关键帧（动作序列的可视化记录） | ❌ 缺失 |

## 轨迹→技能生成 Pipeline

```
Public trajectories → Workflow Grouping → Procedure Induction → Visual Grounding → Meta-Skill Auditing → MMSkills
```

## Branch-Loaded 技能执行

1. 从 MMSkill 包中选择相关 state cards 和 keyframes
2. 在临时分支中检查这些视觉信息
3. 与实时环境对齐
4. 蒸馏为结构化指导给主 agent

## 对 Hermes 的具体价值

### 当前问题
- Hermes Skills 是纯文本的（SKILL.md + 引用文件）
- 缺乏"这个技能在什么视觉状态下应该触发"的识别信息
- screen_watcher handler 中场景分类是硬编码的，不能从 skills 自动推断触发条件

### 未来方向
1. **Skill 触发条件可视化**：每个 Hermes Skill 应附加 state cards（目标应用截图 + 关键 UI 元素标注）
2. **自动从 dry-run 日志生成技能**：`AUTO-EXEC-DRY` 日志中积累的场景+动作对可作为 MMSkills 的输入数据
3. **Branch-loaded 执行**：screen_watcher 发现某个场景后，加载对应技能的状态卡片，对齐后决定是否执行

## Key Insight

"External multimodal procedural knowledge complements model-internal priors." — 外部多模态过程知识补充模型内部先验知识。这意味着 Skills 不应只作为 prompt 存在，而是可自主运行的视觉-文本混合包。

## 来源
- Paper: https://arxiv.org/abs/2605.13527
- 发现时间: 2026-06-01 方向B idle_learning
