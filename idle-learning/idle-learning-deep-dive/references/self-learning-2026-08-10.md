# 2026-08-10 自学进化研究摘要

## Hermes v0.20.0 Herald (2026-08-03)

**核心能力：**
- 实时语音 streaming TTS + barge-in + 设备端唤醒词（本地运行不传音频）
- A2A v1.0 标准协议：可发现/驱动其他兼容 agent
- 出站 webhook（HMAC 签名）：推生命周期事件到 HTTP 端点
- 引用溯源 grounded citations：每条声明附可验证来源
- 桌面端→平台：artifacts 实时预览 + 插件 SDK + 多窗口 + 全局快捷键 quick-entry
- CLI：`!cmd` 快捷执行、`/init` 项目扫描、`/diff` 变更、`/context` 上下文分解
- 工具迭代上限 90→500
- **Federation P2P 心跳**：多设备任务中继，Raft-lite 共识，3 次失败判定死亡
- Buzz（Nostr/Block 消息）成捆绑平台

**数字**：3650 commits since v0.19.0，1400 PRs merged，650+ contributors

---

## MCP 2026-07-28 规范（最大版本更新）

**核心变化：**
1. **无状态 core**：去除 initialize/initialized 握手和 Mcp-Session-Id；每请求携带 `_meta`（协议版本+客户端能力+身份）
2. **server/discover**：唯一发现机制，代替握手
3. **MRTR (Multi Round-Trip Requests)**：替代 elicitation/sampling，server 返回 `resultType: "input_required"` + `requestState`，client 重试时附 `inputResponses`
4. **路由头**：Streamable HTTP 新增 `Mcp-Method` + `Mcp-Name`，网关可直接路由不解析 body
5. **缓存提示**：`tools/list` 等响应带 `ttlMs` + `cacheScope`，可安全缓存减少轮询
6. **Tasks 官方扩展**：`tasks/get` 轮询 + `tasks/update` 客户端输入，代替阻塞 `tasks/result`
7. **deprecated（12 个月过渡）**：Roots / Sampling / Logging
8. **OpenTelemetry**：W3C Trace Context 标准化，全链路可观测

**支持方**：Anthropic / Google / AWS / Cloudflare；400M 月 SDK 下载

---

## 多智能体编排研究前沿（2026.08）

### OrchestraBench (ACL 2026 Findings)
评估多 agent 系统可靠性，失败分三类：
- **工具调用故障**：完全可恢复（recovery=1.0），agent 手重算
- **模糊委托**：部分恢复（0.30）
- **语义故障**（context 污染/冲突输出/过早行动）：零恢复（0.0），且重试不修复只延长检测时间
- **级联半径**：随管道深度线性增长（depth 3→7: 0.9→4.7）
- **核心结论**：检测/归因 > 盲目重试；model-driven routing 零样本对抗 100% vs keyword routing 0%

### SyncPlan (ICLR 2026)
plan-execute-correct 框架：
- 中心化 LLM coordinator 单次规划生成 per-agent 动作链
- **显式同步原语**：`wait` 阻塞单个 agent 而非整个系统
- **Plan Staleness Detector**：轻量检测计划有效性，触发重规划而非定时重查
- Overcooked + Honor of Kings 新 SOTA，延迟 <0.05% 竞品

### InfraMind
基础设施感知的多智能体编排：
- infra-aware planner：根据负载选择拓扑（拥塞时简化图，空闲时丰富图）
- infra-aware executor：实时读队列深度/KV cache/延迟，动态选模型+推理深度
- budget-aware EDF scheduler：每模型队列按紧急程度重排序
- 全部三层联合 RL 训练
- **结果**：高负载下 99.9% SLO compliance，基线 <50%

### Orch-RM
编排级奖励模型：自监督从执行产物构造 win-lose 对 Bradly-Terry 训练，token 减少 10 倍，64 采样推理时扩展

---

## 记忆管理架构

| 层 | 存储 | 容量 | 注入方式 |
|----|------|------|----------|
| 高频 | MEMORY.md | ≤30KB | 每次 system prompt |
| 中频 | fact_store | 无硬限制 | 被检索才激活 |
| 低频 | sessions.db | — | 仅 session_search |

**膨胀根因**：MEMORY.md 每日日志堆砌（30KB+），state.db messages 删除未 VACUUM
**修复**：压缩 MEMORY.md + `sqlite3 state.db VACUUM`
**扩容备选**：MemPalace（57K stars）语义搜索
