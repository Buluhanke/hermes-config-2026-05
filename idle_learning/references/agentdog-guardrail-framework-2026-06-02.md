# AgentDoG — 智能体安全诊断防护框架

- **论文**: arXiv 2601.18491 (v2, Apr 23, 2026), 40 页, 26 图
- **分类**: cs.AI, cs.CL, cs.CV, cs.LG
- **链接**: https://arxiv.org/abs/2601.18491
- **GitHub**: 所有模型和数据集已公开
- **发现时间**: 2026-06-02 06:36 ddgs 旋转查询

## 核心贡献

1. **三维风险分类体系** (正交):
   - 来源(where): 哪里出了问题
   - 失效模式(how): 怎么出的问题
   - 后果(what): 导致了什么

2. **ATBench** — 细粒度智能体安全基准测试集

3. **AgentDoG 防护框架**:
   - 对整个行为轨迹进行细粒度和上下文相关监控
   - 能诊断不安全行为 AND 看似安全但实际不合理行为的**根本原因**
   - 超越二元的 traceability + transparency
   - 支持 agent 协同

## 模型变体

| 变体 | 基座 | 参数量 |
|------|------|--------|
| AgentDoG-4B | Qwen | 4B |
| AgentDoG-7B | Qwen/Llama | 7B |
| AgentDoG-8B | Qwen/Llama | 8B |

- 4B 变体可能适合 M4 24GB 本地部署

## Hermes 架构相关性

| 维度 | 说明 | 等级 |
|------|------|------|
| **Direct risk** | 非直接——AgentDoG 是防护框架而非 Hermes 组件 | LOW |
| **Indirect risk** | Hermes 缺乏类似的 agent-level guardrail（现有仅为 scene classification） | MED |
| **Action** | 写入 reference 文件追踪；评估 AgentDoG-4B 作为 screen_trigger 后 guardrail 层的可行性 |

## 对比已知 guardrail

- **SafePred** (2602.01725): 预测式 guardrail，基于 world model 预测 action 安全——互补而非竞争
- **ProjGuard**: 项目级安全监控——互补
- **Parallax**: 认知-执行分离架构——互补
- **AgentDoG**: 诊断式（事后分析）× traceability——填补 Hermes "执行后如何审计"的空白

## 待评估

- [ ] AgentDoG-4B 能否在 M4 24GB 本地运行？
- [ ] 能否集成到 screen_trigger_handler 的执行后 audit 链路？
- [ ] 与 Hermes 的 scene classification 能否形成"执行前分类→执行后审计"双层防护？
