# TencentDB Agent Memory 架构参考

来源：[Tencent/TencentDB-Agent-Memory](https://github.com/Tencent/TencentDB-Agent-Memory)，MIT License，Tencent 开源。

## 核心问题

长程 Agent Session 的 token 爆炸：
- SWE-bench 单 Session 连续执行 50 个任务，OpenClaw 消耗 3474M token
- 暴力摘要不可逆，丢失证据，溯源困难

## 解决方案：分层记忆 + 符号化

### 分层架构（L0→L3）

| 层级 | 内容 | Token 密度 |
|------|------|-----------|
| **L0** | 原始对话日志、工具调用结果 | 最高（完整原文） |
| **L1** | 结构化原子事实（JSONL） | 中 |
| **L2** | 场景块（Scenario） | 低 |
| **L3** | 用户画像（Persona） | 最低 |

### 符号化压缩（Mermaid 画布）

工具日志 → 提取关系 → 生成 Mermaid 任务图谱（几百 token）→ 上下文注入。

```
繁杂冗长的过程日志(几十万Token) --> 卸载完整原文到外部文件系统
                               --> 提取关系生成 Mermaid 符号图谱(带 node_id)
                               --> 轻量级注入 Agent 上下文(几百Token)
Mermaid 图谱 -. 按 node_id 回溯 .-> 外部文件系统(原始日志)
```

### 关键指标

- WideSearch：Token 消耗 -61.38%，通过率相对 +51.52%
- SWE-bench：Token 消耗 -33.09%，通过率相对 +9.93%
- PersonaMem 准确率：48% → 76%（+59%）

### 溯源机制

每条高层信息都有到 L0 原文的映射链路：
`L3 Persona → L2 Scenario → L1 Atom → L0 Conversation/refs`

低层保留证据，高层保留结构。压缩不是黑洞，是分层索引。

## Hermes 可借鉴的点

1. **Mermaid 任务画布**：在 Hermes Loop 的 Planning 阶段，可以生成轻量级 Mermaid 图谱注入上下文，而非注入完整日志
2. **分层卸载**：工具调用日志 → L1 JSONL → 高层符号，按需回溯
3. **node_id 溯源**：每个压缩节点带原始引用 ID，随时可查
4. **渐进式披露**：平时只看高层，遇错时再下钻

## 待落地实现

- [ ] find-url：Python 读 Chrome/Edge 书签+历史（来自 web-access 研究）
- [ ] 站点经验积累：site_memory/<domain>.json（来自 web-access 研究）
- [ ] CDP URL 参数问题排查（来自 web-access 研究）
