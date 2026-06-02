# MobileGUI-RL: Advancing Mobile GUI Agent through Reinforcement Learning (2507.05720)

**来源**: arXiv, ZJU/JD/orbit, EMNLP 2025
**arXiv**: https://arxiv.org/abs/2507.05720

## 核心贡献
- **问题**: 现有 GUI agent 主要在离线环境用预采集轨迹训练，无法适应动态开放世界
- **方案**: 在线强化学习框架，在真实移动环境中持续训练
- **训练 pipeline**: GRPO (Group Relative Policy Optimization) 用于在线 RL

## 关键发现
- 在线 RL 显著提升任务成功率和效率
- 对比离线 SFT：在线 RL 在 AITZ、VGA 数据集上均超越
- 开源训练代码和模型

## 对 Hermes 的价值
- 方向 B: 在线 RL + GRPO 是 screen_trigger_handler 未来优化方向
- 方向 D: auto_execute 可借鉴 test-time scaling (GTA1) 思想
