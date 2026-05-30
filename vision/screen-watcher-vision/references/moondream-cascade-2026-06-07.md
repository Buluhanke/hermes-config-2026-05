# moondream Cascade 场景分类架构（2026-06-07 发现）

## 背景问题
qwen3-vl:2b 当前承担所有视觉分析（场景分类 ~24s），是实时监控链路的主要延迟瓶颈。

## moondream 作为快速初筛器

**候选模型**：`moondream:1.8b-v2-q4_K_M`
- 大小：~1GB（Q4_K_M 量化）
- Ollama：直接可用
- 理论速度：M4 上 ~30+ tok/s（纯 decode，不含图像编码）
- 同 smolvlm2 量级，轻量视觉理解

## Cascade 架构设计

```
帧截图
  ↓
[moondream 快速初筛] → <5s → 场景明朗 → 直接触发对应动作
  ↓ （信心不足时）
[qwen3-vl:2b 详细分析] → ~24s → 精确判断
```

**判断逻辑**：
- moondream 返回高置信度（某个场景 > 0.8）→ 直接使用，跳过 qwen3-vl:2b
- moondream 返回模糊/多类别相似 → 调用 qwen3-vl:2b 详细分析
- 目标是降低 80%+ 场景的平均响应时间从 24s 到 <5s

## 局限
- moondream 非 GUI 专用模型，场景分类准确率可能低于 smolvlm2-agentic-gui
- cascade 引入决策复杂度（何时信任 moondream vs 何时升级）
- 需实测验证 moondream 分类准确率 vs qwen3-vl:2b

## 测试计划（网络恢复后）
1. `ollama pull moondream:1.8b-v2-q4_K_M`
2. 对比同一批截图的 moondream vs qwen3-vl:2b 分类结果
3. 测量 moondream 单帧响应时间
4. 评估 cascade 决策准确率

## 状态
- 当前不适用（smolvlm2 已退役，qwen3-vl:2b 是唯一可用模型）
- 等网络恢复后验证 moondream 可用性
