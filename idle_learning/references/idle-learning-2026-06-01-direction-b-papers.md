# 2026-06-01 方向B论文发现 — GUI Understanding / Comprehension Layer

**来源**：OSU-NLP-Group GUI-Agents-Paper-List YAML 扫描（raw.githubusercontent.com, 537 papers）

## Top 10 新发现（按价值排序）

### 1. ⭐ UILoop — UI-in-the-Loop 范式（ACL 2026, ZJU）
- arXiv 2604.06995, Apr 8, Findings of ACL 2026
- **核心**：将 GUI 推理重构为 Screen → UI Elements → Action 循环范式
- **UI Comprehension-Bench**：26K 样本，三任务（localization, semantic function, usage）
- **对 Hermes**：screen_watcher pipeline（截图→场景分类→auto_execute）与此架构一致

### 2. ⭐ UI-Zoomer — 不确定性驱动自适应缩放（ZJU-REAL）
- arXiv 2604.14113, Apr 15
- **核心**：置信度感知门控 + 方差分解自适应裁剪，training-free
- **效果**：4.2-13.4% 提升（三个基准）
- **对 Hermes**：可直接集成到 handler "other" 场景第二层分析
- 代码：github.com/ZJU-REAL/UI-Zoomer

### 3. ⭐ MolmoWeb — 纯视觉 Web Agent SOTA（AI2/UW）
- arXiv 2604.08516, Apr 9
- **4B/8B screenshot-only**，无 DOM/a11y，SOTA WebVoyager，超越 GPT-4o
- **对 Hermes**：验证纯视觉路线是行业认可方向，小模型可超越大闭源

### 4. ⭐ Visual Confused Deputy — 双通道 Guardrail（vLLM/McGill/AMD/Red Hat）
- arXiv 2603.14707, Mar 16
- **核心**：感知失败=安全问题。双通道 guardrail：视觉目标 + 文本推理分别检查
- 与 AVR 路由同团队（vllm-project/semantic-router）
- **对 Hermes**：handler 场景分类+内容分析的学术验证

### 5. Same Outcomes, Different Journeys（Stockholm/Spotify）
- arXiv 2604.07929, Apr 9
- **核心**：agent 成功率匹配人类，但策略完全不同（search-centric vs content-centric）
- **对 Hermes**：auto_execute RPA 动作需从人类行为模式学习

### 6. PIRA-Bench — 主动意图推荐（CUHK/Huawei）
- arXiv 2603.08013, Mar 9
- **核心**：从连续视觉流推断用户意图（非等待命令），PIRF memory-aware baseline
- **对 Hermes**：screen_watcher 连续截图监控正是 "continuous visual streams" 范式

### 7. AndroTMem — 锚点状态记忆
- arXiv 2603.18429, Mar 19, 多机构
- **核心**：因果链接状态锚点记忆，12 agent 提升 5%-30.16%
- **对 Hermes**：screen_watcher 多帧追踪可借鉴 Anchored State Memory

### 8. Rethinking Token Pruning（Sichuan/ANU）
- arXiv 2603.26041, Mar 27
- **核心**：背景区域含状态过渡线索；随机剪枝保持空间结构；近期截图高权
- **对 Hermes**：历史截图 token 效率优化

### 9. GUIDE: Resolving Domain Bias via Video Retrieval（SJTU/BIGAI）
- arXiv 2603.26266, Mar 27
- **核心**：training-free，检索教程视频→注入 GUI agent 作为 grounding 注释
- **对 Hermes**：跨领域知识注入方向

### 10. OS-Themis — 可扩展 Critic 框架（USTC/Shanghai AI Lab）
- arXiv 2603.19191, Mar 19
- **核心**：轨迹分解为可验证里程碑 + 证据链审计
- OmniGUIRewardBench 跨平台 GUI 奖励基准

## 扫描方法

```
browser_navigate raw.githubusercontent.com/OSU-NLP-Group/GUI-Agents-Paper-List/main/papers.yaml
browser_console(expression='document.body.innerText.slice(0, 30000)')  # 分片提取
过滤关键字：Desktop + (understanding / comprehension / grounding / benchmark)
排除：healthcare / remote sensing / agriculture
对比已有知识库，标记新发现
```

**优势**：537 papers, 124 Desktop, 含 tldr 摘要可快速筛选，比 arXiv 搜索更快更广
**坑**：新论文有 1-3 周滞后
