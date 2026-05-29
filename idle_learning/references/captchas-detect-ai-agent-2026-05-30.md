# CAPTCHAs 检测 AI Agent 研究（2026-05-30）

## 来源

- **论文**：Roundtable Research（roundtable.ai），CogCAPTCHA30
- **链接**：https://research.roundtable.ai/captchas-detect-ai/
- **日期**：2026-05-27

## 核心结论

**行为检测 vs 输出检测**

前沿模型（Claude/GPT/Gemini）在**任务输出**上与人类等价，但在**行为过程**上差异显著。
小模型（Qwen/Centaur）反而更接近人类的过程特征。

```
输出等价 ≠ 过程等价
Cohen's d (output): high similarity
AUC (process): low similarity for frontier models
```

## 检测维度

CogCAPTCHA30 测量四个维度的过程特征：
1. **决策**（decision-making）
2. **记忆**（memory）
3. **感知**（perception）
4. **推理**（reasoning）

## 关键图表结论

- Figure 4: State-of-the-art frontier models (Claude, GPT, Gemini) have **less similar human process features** compared to smaller models (Qwen, Centaur)
- Figure 5: Direct process-level fine-tuning (P-SFT) makes AI more humanlike, but this advantage is reduced when some features are excluded and **completely disappears when asked to cross-task generalize**

## 对 Hermes auto_execute 的影响

### 当前状态（DRY_RUN=True）
- 不执行真实动作，不受影响
- dry-run 只记录不实际操作，无行为特征暴露

### 未来切换到 DRY_RUN=False 时
- Hermes 的 auto_execute 会产生可检测的行为模式：
  - 鼠标移动轨迹（直线 vs 人手曲线）
  - 点击时间间隔（过于均匀）
  - 键盘输入节奏（无自然停顿）
  - 屏幕变化检测后的响应延迟（规律性强）

### Anti-CAPTCHA 对策思路
1. **轨迹扰动**：cliclick 操作前加随机微小移动，模拟人手自然抖动
2. **延迟随机化**：sleep 时间加 ±30% 随机波动
3. **mouseMoved 前置**：CGEventTap 要求前面有 mouseMoved 才接受事件
4. **过程级伪装**：不只是伪装输出，而是伪装行为模式

### 防御持久性
- 检测器基于当前 agent 行为模式优化
- 未来 agent 升级后检测器也会升级
- **过程级扰动**比输出伪装更难被检测，是更持久的防御路线

## 相关 HN 讨论

HN 今日热门 #10：[27pts] CAPTCHAs can still detect AI agents
https://news.ycombinator.com/item?id=xxx（需从 HN 获取实际 ID）