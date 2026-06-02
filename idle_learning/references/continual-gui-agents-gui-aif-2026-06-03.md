# Continual GUI Agents (GUI-AiF) — 2026-06-03 新发现

## 基本信息
- **论文**：Continual GUI Agents
- **arXiv**：2601.20732
- **作者**：Ziwei Liu, Borui Kang, Hangjie Yuan, Zixiang Zhao, Wei Li, Yifan Zhu, Tao Feng（NTU等）
- **提交**：2026-01-28，Last revised 2026-03-25（v4）
- **环境**：Desktop / GUI Agents
- **Code**：可用

## 核心问题
数字环境（数据分布）持续变化，新GUI数据不断到来（新领域/新分辨率），导致在静态环境训练的agent性能退化。现有方法在GUI分布漂移时无法保持稳定的grounding（交互点和区域的多样性导致）。

## 方法：GUI-AiF
GUI-Anchoring in Flux，强化微调框架，两种新奖励：
- **APR-iF**（Anchoring Point Reward in Flux）：对齐漂移交互点
- **ARR-iF**（Anchoring Region Reward in Flux）：对齐漂移交互区域
- 解决现有奖励策略过度适应静态grounding线索（固定坐标/元素尺度）的问题

## 关键发现
- 首个GUI持续学习框架
- 揭示了RL微调对持续GUI Agents的潜力
- GUI-AiF在所有baseline上取得SOTA

## Hermes映射
- 方向B：GUI grounding持续学习新范式，GUI分布漂移应对策略
- 方向D：screen_watcher面临新UI/新应用时的泛化问题，未来可考虑增量fine-tune方向
