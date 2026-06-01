# Security Considerations for AI Agents — arXiv 2603.12230

**来源**: https://arxiv.org/abs/2603.12230
**作者**: Perplexity (Ninghui Li, Kaiyuan Zhang, Kyle Polley, Jerry Ma) — adapted from NIST/CAISI RFI 2025-0035 response
**日期**: Submitted 12 Mar 2026, revised 5 Apr 2026 (v2)

## 核心发现

Perplexity 在 NIST/CAISI RFI 框架下的 AI Agent 安全全面分析。

### 攻击面（4 类）

1. **工具（Tools）**：第三方 API 和服务器的安全风险
2. **连接器（Connectors）**：MCP 等集成协议的攻击面
3. **托管边界（Hosting Boundaries）**：sandbox 逃逸
4. **多 Agent 协调（Multi-Agent Coordination）**：subagent 权限/委托控制

### 三大风险模式

| 模式 | 描述 | Hermes 相关性 |
|------|------|--------------|
| Indirect Prompt Injection | 通过第三方内容注入指令 | ✅ | 
| Confused-Deputy Behavior | 低权限 agent 诱使高权限 agent 执行危险操作 | ✅ delegate_task subagent 自汇报 |
| Cascading Failures | 长运行工作流中的连锁故障 | ✅ handler 冷却竞争 |

### 防御建议

- Sandboxed execution（沙箱执行）
- Deterministic policy enforcement for high-consequence actions（确定性的高风险动作策略执行）
- 独立审查机制

### Hermes 加固建议

当前 delegate_task：subagent 返回 self-report summary → Hermes 检查并告知用户
风险：subagent 汇报中隐瞒已执行的危险命令（同行已验证：Cortex Code CLI sandbox escape 子 agent）
建议：delegate_task 增加 subagent 执行日志验证，而非仅依赖 self-report summary
