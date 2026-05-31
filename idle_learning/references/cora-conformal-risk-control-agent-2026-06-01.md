# CORA: Conformal Risk-Controlled Agents (arXiv 2604.09155)

**Published**: Apr 10, 2026 | **Authors**: Feng, Du, Wang, Ma, Niu, Matsuo, Feng, Yu (HKU, CUHK, UTokyo)
**Link**: https://arxiv.org/abs/2604.09155

## Architecture — Three Modules

### 1. Guardian (风险估计)
- 对每个候选动作估计 **action-conditional risk**（VLM 驱动）
- 输出：每个动作的安全风险分数
- **对 Hermes**: 映射为 qwen3-vl:2b 的场景分类置信度（logprob 几何平均）
  - 当前 handler 已输出场景类型 + 否定检测结果，可作为 Guardian 的输入特征

### 2. Conformal Risk Control (校准层)
- 用 **Conformal Prediction** 校准 execute/abstain 决策边界
- 核心特征：提供 **形式化统计保证**（formal guarantee），非 heuristic
- 用户可指定风险预算（user-specified risk budget）
- 不需要假设数据分布，适用于任意 VLM
- **对 Hermes**:
  - 当前否定检测是 heuristic（前12字符检测"没有/无/未/不"）
  - CORA 提供正式理论框架：conformal calibration 替代硬编码否定关键词
  - 834 条 dry-run 日志可用作 calibration 数据集

### 3. Diagnostician (干预推荐)
- 对 Guardian 标记的 rejected 动作做 **多模态推理**
- 推荐三种干预：**confirm / reflect / abort**
- **对 Hermes**:
  - confirm → 对应动作分级的 Confirmed（需用户确认）
  - reflect → 对应 Logged（记录但不执行）
  - abort → 对应 Blocked（直接拒绝）
  - 当前 handler 的否定检测 [silent]/[urgent] 标记可映射为这三级

### Goal-Lock (意图锚定)
- 锚定到已澄清、冻结的用户意图
- 抵抗视觉注入攻击（如敌对 UI 元素覆盖）
- **对 Hermes**: 当前 CRITICAL_KEYWORDS + 否定检测是 Goal-Lock 的文本级近似
  - 差异：CORA 的 Goal-Lock 在意图层面，handler 在关键字层面

## Benchmark: Phone-Harm
- 移动端安全违规数据集
- **step-level 有害行为标签**（非全任务标签）
- 可用于评估 Guardian 的每步风险估计精度

## CORA → Hermes Handler 映射

| CORA 模块 | Hermes 等价组件 | 差距 |
|-----------|----------------|------|
| Guardian | qwen3-vl:2b 场景分类 + logprob | 未显式提取 logprob 置信度 |
| Conformal Risk Control | 前12字符否定检测 | Heuristic → Formal guarantee |
| Diagnostician | [silent]/[urgent] 标记 | 需升格为 confirm/reflect/abort 三级 |
| Goal-Lock | CRITICAL_KEYWORDS + 否定词 | 文本级 → 语义级 |
| Phone-Harm | 834 dry-run 日志 | 可用作 calibration data |

## 集成路径（优先级排序）

### P0: logprob 置信度提取
在 get_scene_type() 中提取 top-1 token 的 logprob 概率值，作为 Guardian 分数。
```python
# 当前 API 调用后添加：
prob = response.get("probs", {}).get("top_logprobs", [{}])[0].get("prob", 0.5)
confidence = prob  # Guardian score
```

### P1: Conformal Calibration
用 834 条 dry-run 日志构建 calibration 集合：
- 随机抽取 500 条做 calibration
- 计算 execute/abstain 边界阈值 q_hat
- 替换当前硬编码否定关键词匹配

### P2: Diagnostician 分级
将 [silent]/[urgent] 二元标记升格为三级：
- confirm: 高置信否决 → 提示用户确认
- reflect: 中置信 → 记录日志但不停止
- abort: 低置信 → 直接阻止执行

### P3: Goal-Lock 语义化
从 CRITICAL_KEYWORDS 的关键词匹配，升级为 qwen3-vl:2b 对截图内容的语义级意图理解（需要定义什么构成"用户意图偏离"）。

## 关键论文引用
```
@misc{feng2026cora,
  title = {CORA: Conformal Risk-Controlled Agents for Safeguarded Mobile GUI Automation},
  author = {Yushi Feng and Junye Du and Qifan Wang and Zizhan Ma and Qian Niu and Yutaka Matsuo and Long Feng and Lequan Yu},
  year = {2026},
  eprint = {2604.09155},
  archivePrefix = {arXiv}
}
```
