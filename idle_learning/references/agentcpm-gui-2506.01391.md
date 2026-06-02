# AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning (2506.01391)

**来源**: arXiv, EMNLP 2025 Demos
**arXiv**: https://arxiv.org/abs/2506.01391

## 核心贡献
- **8B 参数** GUI agent，端侧可运行
- **训练 pipeline**:
  1. Grounding-aware pre-training (增强感知)
  2. SFT on 高质量中英轨迹 (人类示教)
  3. GRPO 强化微调 (提升推理能力)
- 开源 GitHub: github.com/DemonDamon/gui-agent-research/tree/master/researches/AgentCPM-GUI

## 对 Hermes 的价值
- GRPO 训练策略在 GUI agent 中的实际应用
- 端侧 8B 模型是 M4 24GB 可探索的尺寸
- 方向 B: GRPO + SFT + RL 三阶段训练范式参考
