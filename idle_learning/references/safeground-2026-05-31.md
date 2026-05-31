# SafeGround: Know When to Trust GUI Grounding Models

**来源**：arXiv 2602.02419v2 (Feb 2026), UCSB AI Lab
**GitHub**：https://github.com/UCSB-AI/SAFEGROUND (10 stars, MIT license)
**Project Page**: https://safeground-ericlab.github.io/

## 核心思路

GUI grounding 模型总是输出坐标，即使不确定时也是如此 — 这是一个静默失败问题。
SafeGround 通过**不确定性校准（Uncertainty Calibration）** 解决何时信任/何时推迟执行：

1. **空间不确定性量化**：聚合多次随机 grounding 预测，形成 patch-level 概率分布
   - 分布越分散 → 模型越不确定 → 应该推迟执行
   - 分布越集中 → 模型越确定 → 可以信任执行
2. **校准阈值**：通过有限样本保证（finite-sample guarantees）校准出测试时的决策阈值
   - 统计上控制 FDR（False Discovery Rate）
3. **选择性预测 + 安全推迟**：不确定时 defer 而不是盲目执行

## 对 Hermes auto_execute 的意义

| SafeGround 概念 | Hermes 对应 |
|---|---|
| 不确定性量化 | 当前用 DRY_RUN=True 全量 defer |
| 校准阈值 | 确定性阈值：满足条件才执行 |
| 选择性预测 | 高确信度场景（browser/calculator）先执行 |
| 安全推迟 | 低确信度场景仍保持 dry-run |

## Benchmark 结果

- 在 ScreenSpot-Pro benchmark 上，SafeGround 对多个 GUI grounding 模型不一致行为输出区分优于现有 baseline
- 系统层面准确率提升最多 **+5.38pp**（相对于 Gemini-only 推理）
- 支持闭盒模型（无需访问模型内部，仅需多次采样输出）

## 对 Hermes 的启发

1. **决策层**：在 auto_execute 中引入置信度阈值，而非简单的黑白名单
2. **实现**：qwen3-vl:2b 多次分类采样 → 分布一致时才执行 action
3. **优先级**：先对高确定性场景（browser desktop）开放执行，其他保留 dry-run
4. **风险管理**：统计控制 FDR 的思路可以迁移到 action 执行的错误率要求上
