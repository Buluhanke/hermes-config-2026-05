# SafePred: A Predictive Guardrail for Computer-Using Agents via World Models

- **来源**: arXiv 2602.01725, Feb 2026
- **作者**: Yurun Chen, Zeyi Liao, Ping Yin, Taotao Xie, Keting Yin, Shengyu Zhang
- **分类**: cs.CL / cs.AI / cs.LG

## 核心创新

**预测型Guardrail**替代主流反应式方案。反应式guardrail只能在当前观察空间约束行为，无法发现"今天清日志→下周审计不可追溯"这种延迟因果链。

## 架构

**risk-to-decision loop**：world model 预测短期+长期风险 → 在action扩散前prune高风险路径

两条能力线：
1. **风险预测**: safety policies → world model → semantic risk representation（同时覆盖短期和长期）
2. **决策优化**: step-level intervention + task-level re-planning（风险预测转译为可执行安全约束）

## 结果

- 97.6% safety performance
- 21.4% better task utility vs reactive baselines

## 对Hermes的意义

1. 当前ACTION_WHITELIST是最原始的反应式guardrail（检查action是否在白名单）
2. SafePred的world model预测+prune范式直接可迁移：handler的VLM分析结果可扩展为"风险等级"输出
3. **对DRY_RUN=False过渡**：guardrail演化路径：whitelist（二进制）→ SafePred（世界模型预测+修剪）→ production-ready
4. **与AVR路由互补**：AVR解决"哪个模型做"，SafePred解决"哪个动作安全"

## 关键词

predictive guardrail, world model, risk-to-decision loop, semantic risk representation, step-level intervention, task-level re-planning
