# Microsoft Agent Governance Toolkit（2026-06-01 发现）

> 来源：github.com/microsoft/agent-governance-toolkit（3.5k stars, 1,806 commits）
> 许可：MIT
> 版本：v4.0.0（consolidated packages），最后提交 43 分钟前（2026-06-01 02:15）

## 概览

Microsoft 官方 Agent 治理框架，覆盖 OWASP Agentic Top 10。解决 Agent 部署后的三个核心问题：
1. **This action allowed?** — Agent 有 send_email 和 query_database 权限，不应能 drop_table
2. **Which agent did this?** — 多 Agent 共享同一个 API key 时，如何追溯具体哪个 Agent 出问题
3. **Can you prove what happened?** — 审计和合规需要防篡改决策记录

**核心哲学**：Prompt-level safety 是"请遵守规则"的礼貌请求。AGT 在确定性应用代码层拦截，做到"不可能违规"而非"不太可能违规"。

## 架构

```
Agent ──► Policy Engine ──► Identity ──► Audit Log
            (YAML/OPA/Cedar)  (SPIFFE/DID/mTLS)  (Tamper-evident)
                 │                                      │
                 ├── Allowed ──► Tool executes           │
                 └── Denied  ──► GovernanceDenied        │
                                                        ▼
                                                 Decision Record
```

## 包结构

| 包名 | 功能 | 对 Hermes 价值 |
|------|------|---------------|
| Agent OS | Policy engine, agent lifecycle | ACTION_WHITELIST 可直接映射 |
| Agent Mesh | Agent discovery, routing | 多 Agent 场景 |
| Agent Runtime | 4 特权环沙箱 | → Silent/Logged/Confirmed/Blocked 分级 |
| Agent SRE | Kill switch, SLO monitoring | auto_execute 安全熔断 |
| Agent Compliance | OWASP 验证, policy linting | `agt verify` CLI |
| Agent Marketplace | Plugin governance | MCP Security Gateway |
| Agent Lightning | RL training governance | 未来 RL 训练场景 |
| Agent Hypervisor | Execution audit, delta engine | tamper-evident 日志 |

## CLI 工具

```bash
agt doctor                    # 检查安装状态
agt verify                    # OWASP compliance 检查
agt verify --evidence ./agt-evidence.json --strict  # CI 模式
agt red-team scan ./prompts/ --min-grade B          # prompt injection 审计
agt lint-policy policies/                            # 策略文件验证
```

## 安装

```bash
pip install agent-governance-toolkit[full]
```

## 核心 API

```python
from agentmesh.governance import govern

safe_tool = govern(my_tool, policy="policy.yaml")
# 每次调用都被检查、记录、执行

# policy.yaml
apiVersion: governance.toolkit/v1
name: production-policy
default_action: allow
rules:
  - name: block-destructive
    condition: "action.type in ['drop', 'delete', 'truncate']"
    action: deny
  - name: require-approval-for-send
    condition: "action.type == 'send_email'"
    action: require_approval
    approvers: ["security-team"]
```

## 特权环模型（Agent Runtime）

与 Hermes action 分级的直接映射：

| 环 | 名称 | 操作类型 | Hermes 映射 |
|----|------|---------|-----------|
| Ring 0 | Silent | 只读（读取、感知、分析） | wininfo, ocr, scene classification |
| Ring 1 | Logged | 文件修改（日志、状态写入） | dry-run logging |
| Ring 2 | Confirmed | Shell/网络/跨应用 | click, type, send (需确认) |
| Ring 3 | Blocked | 凭据/系统修改 | destructive ops (拒绝) |

## MCP Security Gateway

- Tool poisoning detection — 检测被篡改的 MCP tool
- Drift monitoring — 监控 tool 行为漂移
- Typosquatting scanning — 扫描域名/命令名混淆
- Hidden instruction scanning — 检测隐藏指令注入

## 对 Hermes auto_execute 的启发

1. **策略引擎架构**：Hermes ACTION_WHITELIST 可升级为 YAML 策略文件（从硬编码 map 到可加载策略）
2. **4 特权环**：直接指导 DRY_RUN=False 过渡方案中的动作分级
3. **Tamper-evident 日志**：auto_execute 执行记录需要防篡改
4. **确定性代码层**：重申"prompt 层安全不可靠，代码层拦截才是真安全"
5. **MCP Security Gateway**：未来 auto_execute 使用 MCP 时需集成
6. **CLI 工具链**：`agt lint-policy` 模式可用于验证 ACTION_WHITELIST 配置正确性

## 限制

- 库较重（多语言 SDK, 4.0.0 版本 1,806 commits），不适合 Hermes 直接安装
- Azure 集成（可选）依赖 AZURE_CLIENT_ID/TENANT_ID
- 设计面向企业生产环境，对 Hermes 单机场景较重
- 重点关注**架构设计模式**而非直接采用

## 参考链接

- GitHub: https://github.com/microsoft/agent-governance-toolkit
- OWASP Agentic Top 10: https://genai.owasp.org/
- SPDIFFE: https://spiffe.io/
