# Agent Reach 和 ClawRouter 研究报告

**研究时间**：2026-05-28
**研究目的**：评估是否需要集成到 Hermes 架构

---

## Agent Reach

### 核心定位
开源安装框架，提供在线搜索和内容阅读能力的 CLI 工具链。

### 核心能力
**Channels（内容来源）**：
- Web（Jina Reader）
- YouTube
- GitHub
- RSS
- Exa Search
- V2EX
- Bilibili

**CLI Tools**：
- `twitter search "query" -n 10` — Twitter 搜索
- `bili hot` — Bilibili 热门
- `bili search "query"` — Bilibili 搜索
- `rdt search "query"` — Reddit 搜索
- `gh search repos "query"` — GitHub 仓库搜索
- `curl -s "https://r.jina.ai/URL"` — 网页内容提取

### 安装方式
```bash
pipx install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

**配置位置**：`~/.agent-reach/`（避免污染工作目录）

### 与 Hermes 对比
| 维度 | Hermes | Agent Reach |
|------|--------|-------------|
| 核心机制 | Skills + MCP Tools | CLI Tools via mcporter |
| 平台覆盖 | 浏览器、1688、桌面 | Twitter、Reddit、YouTube、Bilibili、GitHub、RSS |
| 安装方式 | `hermes skills install` | pipx install |
| 认证需求 | 无 | 部分 channels 需要 Cookies |
| 成熟度 | 高 | 高（工具成熟） |

### 优缺点
**优点**：
- 工具成熟稳定（twitter-cli、bili-cli 等）
- 支持更多平台（Twitter、Reddit、LinkedIn）
- 配置独立于 skills

**缺点**：
- 需要 pipx 安装（不同于 skills）
- 配置方式不同（~/.agent-reach/）
- 部分 channels 需要认证（Cookies）

### 决策逻辑
**安装条件**：
- ✅ 需要访问 Twitter、Reddit、LinkedIn、YouTube、Bilibili 等平台
- ✅ 需要批量内容抓取（RSS、Exa Search）

**不安装条件**：
- ❌ 只需要 1688 sourcing
- ❌ 只需要 web_search（即使付费）
- ❌ 不需要 social/video 平台

**结论**：当前不需要安装。Hermes 的 skills + MCP 工具已覆盖大部分场景，Agent Reach 的平台覆盖是额外价值，但非必需。

---

## ClawRouter

### 核心定位
Agent-native LLM router，提供智能路由、USDC 支付、无 API keys。

### 核心能力
**核心特性**：
- ✅ 无 API keys（钱包签名认证）
- ✅ 无信用卡（USDC 微支付，通过 x402）
- ✅ 本地路由 <1ms
- ✅ 15 维度智能路由
- ✅ 55+ 模型支持

**模型支持**：
- OpenAI、Anthropic、Google、xAI、DeepSeek
- **10 个 NVIDIA 模型永久免费**：
  - gpt-oss-120b
  - deepseek-v4-pro
  - qwen3-next-80b-a3b-thinking
  - qwen3-coder-480b
  - glm-4.7
  - llama-4-maverick
  - nemotron-3-nano-omni-30b-a3b-reasoning
  - （其他 3 个模型）

**路由策略**：
- `/model free` — 100% 免费模型
- `/model auto` — 74-100%（默认，智能选择）
- `/model eco` — 95-100%（经济模式）
- `/model premium` — 0%（仅付费模型）

**成本优势**：
- 平均成本：$2.05/M tokens
- Claude Opus：$25/M tokens
- **节省比例：92%**

### 安装方式
**Plugin 方式**：
```bash
pip install hermes-plugin-clawrouter
```

**配置**：
- `CLAWROUTER_API_KEY` 环境变量
- `CLAWROUTER_BASE_URL`: `https://clawrouter.com/v1`

### 与 Hermes 对比
| 维度 | Hermes 当前架构 | ClawRouter |
|------|----------------|------------|
| 模型选择 | 手动配置 custom providers | 自动智能路由 |
| 认证方式 | API keys | 钱包签名 |
| 支付方式 | 信用卡 | USDC 微支付 |
| 成本 | 依赖 provider 价格 | 平均 $2.05/M（节省 92%） |
| 路由速度 | - | <1ms 本地路由 |
| 免费模型 | 依赖 provider 提供免费额度 | 10 个 NVIDIA 模型永久免费 |

### 优缺点
**优点**：
- 智能路由（自动选择最优模型）
- USDC 微支付（无需信用卡）
- 92% 成本节省
- 10 个免费模型
- 本地路由（<1ms）

**缺点**：
- 需要安装 plugin
- 需要配置 API key
- USDC 支付需要钱包

### 决策逻辑
**安装条件**：
- ✅ 想要智能路由（自动选择模型）
- ✅ 想要 USDC 微支付
- ✅ 想要成本优化（92% 节省）
- ✅ 需要 agent-native 架构

**不安装条件**：
- ❌ 当前路由策略已满足需求
- ❌ 不需要 USDC 支付
- ❌ 不需要成本优化

**结论**：强烈建议安装。成本节省（92%）和智能路由是显著优势，USDC 微支付更适合 agent-native 场景。

---

## 总结与建议

### Agent Reach
**建议**：暂时不安装
**理由**：当前 Hermes 架构已覆盖大部分场景，Agent Reach 的平台覆盖是额外价值但非必需。

### ClawRouter
**建议**：立即安装
**理由**：
1. **成本优势显著**：92% 节省，平均 $2.05/M vs $25/M
2. **智能路由**：自动选择最优模型，减少人工配置
3. **USDC 微支付**：无需信用卡，适合 agent-native 架构
4. **10 个免费模型**：gpt-oss-120b、deepseek-v4-pro 等都是大模型

### 实施步骤
1. 安装 plugin：`pip install hermes-plugin-clawrouter`
2. 配置环境变量：`export CLAWROUTER_API_KEY=xxx`
3. 测试路由：`curl -X POST https://clawrouter.com/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"auto","messages":[{"role":"user","content":"Hello"}]}'`
4. 在 Hermes 中配置：修改 `config.yaml` 的 `custom_providers`

---

## 参考资料
- Agent Reach GitHub: https://github.com/Panniantong/agent-reach
- ClawRouter GitHub: https://github.com/BlockRunAI/ClawRouter
- Hermes 官方文档: https://hermes-agent.nousresearch.com/docs/zh-Hans/skills
