# Microsoft RAMPART + Clarity — Open-Source Agent Safety Testing (May 2026)

**来源**：Microsoft Security Blog, May 20, 2026  
**URL**：https://www.microsoft.com/en-us/security/blog/2026/05/20/introducing-rampart-and-clarity-open-source-tools-to-bring-safety-into-agent-development-workflow/

## RAMPART

**定位**：开源 AI Agent 持续安全测试框架，基于 PyRIT  
**GitHub**：Microsoft RAMPART（开源）

### 核心特性

1. **pytest 接口** — 开发者自写自测，标准集成测试体验
2. **统计试验** — 支持 "80% runs must be safe" 等概率策略，匹配 LLM 概率性行为
3. **组合式评估器** — 检查工具调用/副作用/边界条件，布尔逻辑组合
4. **红队发现编码** — 红队发现 → 编码为永久回归测试，永不回退
5. **CI 可门控** — 每次变更自动运行
6. **可扩展威胁类别** — 增量添加新攻击模式（prompt injection, 数据投毒等）

### 与 PyRIT 的区别

| 维度 | PyRIT | RAMPART |
|------|-------|---------|
| 用户 | 安全研究员 | 工程团队 |
| 时机 | 系统构建后（黑盒） | 系统构建中（白盒） |
| 接口 | 面向发现 | pytest |
| 测试形式 | 一次性 | CI 回归测试 |

## Clarity

**定位**：结构化设计讨论平台，帮助团队在编码前验证假设

### 核心特性

1. **结构化对话** — 问题澄清 → 方案探索 → 失败分析 → 决策追踪
2. **.clarity-protocol/** — 产出的 markdown 文件，git 版本控制，PR review
3. **多角度 AI Thinkers** — 安全、人为因素、对抗场景、操作关注独立审查
4. **过期检测** — 当问题陈述变更时，通知关联方案/失败分析需重审
5. **桌面/Web/嵌入 Agent** 三种运行模式

## Hermes 映射

| 维度 | 评估 |
|------|------|
| Direct risk | LOW — Hermes 不使用 RAMPART |
| Indirect value | MED — RAMPART 的架构模式（pytest + 统计试验 + 组合评估器）可直接映射到 screen_trigger_handler 安全测试 |
| 行动 | 参考架构，暂不改造产线 |

**关键洞察**：RAMPART 的 "红队发现 → 永久回归测试" 模式与 Hermes 的 "screen_trigger_handler + 场景分类" 安全架构思路一致。如果未来产线需要正式安全测试框架，RAMPART 的 pytest 模式是自然选择。
