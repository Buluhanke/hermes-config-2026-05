# OpenClaw Security Crisis — 2026-06-03 新发现

## 来源
- NeuralCoreTech: `Agentic AI Security in 2026: OpenClaw, MCP Vulnerabilities & Enterprise Hardening Guide` (April 10, 2026)
- Reco.ai: `OpenClaw: The AI Agent Security Crisis Unfolding Right Now` (February 12, 2026)

## 核心数据
- **138 CVEs** associated with OpenClaw (as of April 2026)
- **CVE-2026-25253** (CVSS 8.8): Token Theft RCE — Control UI gatewayUrl parameter injection → WebSocket token exfiltration → full RCE
- **ClawJacked** (CVSS 8.8): Browser-to-Localhost Takeover — browser SOP doesn't block ws://127.0.0.1, combined with no localhost rate limiting → brute-force gateway password from any malicious webpage

## OpenClaw 三层架构（与 Hermes 对照）
```
Channel Layer → Brain Layer → Body Layer
(输入标准化)  (LLM推理)     (工具执行)
```
- Gateway: ws://127.0.0.1:18789，默认绑定 localhost
- **关键漏洞假设**：Gateway 认为 localhost 流量天然可信（浏览器场景下此假设错误）

## 7-Stage Agentic Loop（与 Hermes delegate_task 对照）
1. Channel Normalization
2. Routing & Session Serialization
3. Context Assembly — **最关键安全节点**，被污染则全链路受影响
4. Model Inference
5. ReAct Loop (while True: call tool → context.add result → continue)
6. On-Demand Skill Loading — **SKILL.md 注入风险**
7. Memory & Persistence — **MEMORY.md/SOUL.md 被污染则跨 session 持久化**

## Hermes 架构映射
| OpenClaw 组件 | Hermes 对应 | 风险 |
|---|---|---|
| Gateway (ws://127.0.0.1:18789) | Ollama API (http://127.0.0.1:11434) | Ollama 默认无认证，Hermes 同理 |
| SKILL.md skill loading | hermes-agent skill 加载 | malicious skill 注入风险 |
| MEMORY.md/SOUL.md persistence | Hermes memory 持久化 | memory poison → cross-session 持久化 |
| ReAct loop tool calls | delegate_task / terminal() | subagent 自汇报不验证（已知脆弱性） |
| Control UI (gatewayUrl injection) | Hermes gateway MCP 接口 | Host header 处理需验证 |

## Hermes 风险矩阵
| 维度 | 说明 |
|---|---|
| Direct risk | LOW — Hermes 不使用 OpenClaw，不暴露 18789 端口 |
| Indirect risk | MED — Ollama 默认无认证（与 OpenClaw Gateway 相同架构问题），delegate_task subagent 自汇报不验证（已知脆弱性已有记录） |
| Action | 已有 delegate_task 安全记录；本次补充 OpenClaw Gateway 架构类比，增强记忆 |

## ClawHub Skills Supply Chain（与 Hermes skills 体系类比）
- 发布门槛：仅需 SKILL.md + 1 周旧 GitHub 账号，无代码签名/沙箱/安全审计
- Snyk "ToxicSkills" audit + Trend Micro (February 6, 2026) 确认恶意 skills 在 marketplace 流通
- Hermes skill 体系无 marketplace，无外部导入渠道，当前风险 LOW

## MCP 注入攻击（已在之前 references 覆盖）
- 工具投毒（Schema-Level Injection）
- 资源放大循环（隐形成本通胀）
- TIP: Tree-based Injection Payloads
- 跨工具劫持
- 远程 MCP 认证失败
- 验证成功率：95% (arXiv, April 2026)

## 关键洞察
OpenClaw 的三类漏洞（Token Theft / Browser-to-Localhost / Skills Supply Chain）构成"初始访问→持久化→横向移动"完整杀伤链，与 OWASP Agentic Top 10 的 INITIAL_ACCESS / SUPPLY_CHAIN / LATERAL_MOVEMENT 直接对应。

Hermes 的 Ollama API 无认证配置与 OpenClaw Gateway 默认 localhost 信任模型相同，需关注 Ollama 网络绑定配置。
