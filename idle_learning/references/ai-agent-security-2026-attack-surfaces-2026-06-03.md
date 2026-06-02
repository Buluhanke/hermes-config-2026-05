# AI Agent Security 2026: Attack Surfaces in MCP, Function Calling, and Computer-Use Systems
**Source**: Programming Helper (Sarah Chen, May 5, 2026)
**URL**: https://www.programming-helper.com/tech/ai-agent-security-2026-attack-surfaces-mcp-function-calling

## 四大攻击面摘要

### 1. MCP Tool Poisoning (模型上下文协议工具污染)
- **机制**: 恶意 MCP 服务器在工具描述中注入后门指令，LLM 会在后续调用中不知不觉地执行有害操作
- **案例**: 当 LLM 询问时间时，响应中隐含重定向到钓鱼网站的指令
- **防御**: 在调用前验证工具描述的来源和完整性

### 2. Function Calling Injection (函数调用注入)
- **机制**: 通过提示词注入或对话历史污染，让 LLM 在本不该调用时调用危险函数
- **变体**: indirect injection（间接注入）— 通过第三方输入（如邮件内容）触发
- **高危场景**: `terminal()` / `bash` 类函数直接执行系统命令

### 3. Computer-Use Agent 屏幕操纵
- **机制**: 攻击者通过覆盖层、隐藏元素或视觉提示欺骗 agent 误操作
- **攻击链**: 显示假确认对话框 → agent 点击"允许" → 恶意操作执行
- **相关CVE**: CVE-2026-2256 (AI SDK 漏洞，3大云厂商受影响)

### 4. Multi-Agent Systems: Delegation Hazards (多智能体系统委托风险)
- **架构脆弱性**: 主 agent 询问子 agent 意见 → 子 agent 执行恶意操作 → 主 agent 不知情地向用户汇报"安全"
- **关键问题**: subagent 执行日志不返回父 agent，父 agent 仅基于汇报做决策
- **Hermes 映射**: `delegate_task` 的 self-report summary 模式存在此漏洞
- **防御**: 子 agent 应返回完整执行日志而非仅 summary

## FunctionCallValidator 模式（防御参考）

文章提到的函数调用验证模式（用于防止 Function Calling Injection）：

```
FunctionCallValidator {
  - 验证调用来源: 确认是用户意图还是注入
  - 参数沙箱: 参数不能包含可执行命令
  - 调用链追踪: 记录完整调用链供审计
  - 熔断机制: 异常模式自动阻断
}
```

这映射到 Hermes 的 `terminal()` 函数 — 应该：
1. 验证命令来源（用户输入 vs. agent 推理生成）
2. 参数白名单过滤
3. 执行日志完整记录

## 风险矩阵

| 维度 | 评估 | 说明 |
|------|------|------|
| Direct risk | MEDIUM | Hermes terminal() 对用户输入已有基本过滤 |
| Indirect risk | HIGH | delegate_task subagent 自汇报模式与 Multi-Agent Delegation Hazard 一致 |
| Action | 新增 reference + 考虑增强 subagent 日志返回 |  |

## 相关 CVE
- CVE-2026-2256: AI SDK 漏洞，影响 3 大云厂商
