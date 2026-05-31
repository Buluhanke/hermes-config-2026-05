# ProjGuard: Safety Monitoring for Computer-Use Agents via Low-Dimensional Projections

**来源**：arXiv 2605.13631, submitted May 13 2026
**作者**：Kebin Contreras, Carlos Hinojosa, Jorge Bacca, Bernard Ghanem (KAUST)
**发现日期**：2026-06-01 07:15（通过 arXiv API 搜索 `computer use agent safety` 发现）

## 核心贡献

行为轨迹监控（Behavioral Trajectory Monitoring）替代逐输入大模型分析：

```
传统方法：每个输入 → 大模型分析 → 成本高覆盖有限
ProjGuard: 累计交互历史 → 轻量标量风险信号 → 在线评估漂移
```

### 三层架构
1. **低维投影**：从 agent 的逐步交互历史中提取轻量风险信号
2. **在线评估**：判断执行是否开始向不安全区域漂移（提前预警）
3. **按需纠正**：预警触发时选择性激活辅助 VLM 提出修正步骤

### 关键数据

| 指标 | 无监控 | ProjGuard |
|------|--------|-----------|
| Unsafe Rate (OS-Harm) | 16% | **3%** |
| Task Completion (OS-Harm) | 59% | **65%** |
| Unsafe Rate (RiosWorld) | - | **4%** |
| Task Completion (RiosWorld) | - | **64%** |

## 对 Hermes 的直接参考价值

### 已验证的分层安全策略

ProjGuard 的核心设计 = Hermes 现有架构的学术验证：

| Hermes 组件 | ProjGuard 对应 | 匹配度 |
|-------------|---------------|--------|
| scene_classification（始终在线监控） | Behavioral trajectory monitoring | ✅ 一致 |
| 否定检测 + CRITICAL_KEYWORDS（快速风险信号） | Low-dimensional risk signal | ✅ 一致 |
| 按需内容分析（仅 alert 时激活） | On-demand VLM correction | ✅ 一致 |

### 可借鉴改进

1. **风险信号的量化**：当前否定检测是二元（threat/no-threat），ProjGuard 展示标量风险信号更敏感
2. **纠正的量化触发阈值**：ProjGuard 的 alert 阈值可作为 handler 切换内容分析模式的参考
3. **跨场景迁移**：OS-Harm → RiosWorld 迁移验证了方法通用性，对 Hermes 多场景（browser/wechat/desktop）有参考价值

## 方法论差异

| 维度 | ProjGuard | Hermes handler |
|------|-----------|----------------|
| 监控粒度 | 历史轨迹累积 | 单帧独立 |
| 风险信号 | 标量连续值 | 二元（否定检测） |
| 纠正触发 | 阈值驱动 | 场景类型驱动 |
| 纠正执行 | 辅助 VLM | 同一 VLM 的 content analysis |
| 延迟开销 | 轻量（标量） | 中（~3s scene + ~7s content） |

ProjGuard 的优势在于历史轨迹提供了趋势预测能力，handler 的单帧独立分析无法预测漂移趋势。未来 Direction C 可探索在 handler 中维护短期轨迹状态指标。
