# Fara1.5 & Three Generations of Desktop Automation (2026-06-01)

**来源**：Microsoft Research + Mininglamp Technology (Mano-P)

## Microsoft Fara1.5 CUA Model Family

**发布时间**：2026-05-21 | **论文**：microsoft.com/en-us/research/articles/fara1-5-computer-use-agent/

### 关键数据

| 指标 | Fara1.5-4B | Fara1.5-9B | Fara1.5-27B |
|------|-----------|-----------|------------|
| Online-Mind2Web | 57% | 63% | 72% |
| WebVoyager | — | 86.6% | — |
| 基座模型 | Qwen3.5-4B | Qwen3.5-9B | Qwen3.5-27B |

- Fara1.5-9B 的 Online-Mind2Web 63% 近乎 Fara-7B 的 2 倍
- Fara1.5-27B 72% 超越 Gemini 2.5 Computer Use 和 OpenAI operator
- 所有模型均为 computer-use agent (CUA)，专为浏览器交互设计

### Agent Loop 架构

```
Observe(3 screenshots + history) → Think(reasoning) → Act(single-step action)
```

**输入**：最近 3 张截图 + 完整对话历史（每个 step 保留最近 3 帧）
**动作类型**：
1. 鼠标/键盘操作（click, type, scroll, hotkey）
2. Web-specific actions（web search）
3. **Context management meta-actions**（memorize, ask_user, verify）

**Context management 价值**：让模型能在长时间任务中保持状态、向用户澄清歧义、在不可逆操作前请求确认

### FaraGen1.5 合成数据管线

三组件：
1. **Environments**：open-internet tasks（live web）+ gated-domain synthetic replicas（sandbox clones）
   - Copilot CLI + human iteration → 全功能沙盒站点克隆（Email/Calendar/Marketplace/ML-experiment）
2. **Solvers**：GPT-5.4 with custom tool calling → 生成轨迹
3. **Verifiers**：3 criteria — correctness（LLM-judge）+ efficiency + user interaction

**关键创新**：用 coding agent 生成训练环境（而非手动编写），大幅降低合成数据成本

### 训练方法

- 基座选择：Qwen3.5 "given its strong grounding and reasoning capabilities"
- Loss：cross-entropy on tokens of thoughts and actions
- 数据 mix：agentic trajectories + grounding + VQA + instruction following + safety
- 仅对最近 3 步的 action tokens 计算 loss（多帧上下文衰减）

---

## Three Generations of Desktop Automation Architecture

**来源**：Mininglamp Technology, dev.to, 2026-05-26

### Gen 1: Selector-Action (RPA)

```
Selector → Action → Selector → ...
```

**代表**：UiPath, Automation Anywhere, Blue Prism
**核心**：CSS selector / DOM path / accessibility attribute → hardcoded action
**失败模式**：
- DOM 耦合：30-40% 维护成本 = selector 修复
- 维护超线性增长：200+ 机器人需专门 "bot repair" 团队
- 跨应用边界：clipboard/watcher/pipe 脆弱管线
- 语义盲：无法区分 "Submit" vs "Cancel" 按钮

### Gen 2: Vision + LLM (Set-of-Marks) ← Hermes 当前位置

```
Screenshot + Labels → LLM Plan → Click x,y → ...
```

**核心**：截图 + 元素标签 → 大模型规划 → 坐标点击
**失败模式**：
- Open-loop：无 grounding 验证，无错误恢复
- 模型输出坐标后不验证动作是否生效
- 无法处理非确定性（动画延迟、弹窗、加载）

### Gen 3: VLA Unified Model ← 目标方向

```
Visual Encoding → Reason + Ground → Action Predict → Verify → Loop
```

**代表**：Mano-P 4B (Mininglamp), Fara1.5 (Microsoft)
**核心**：同一模型完成感知 + 推理 + 动作预测 + 验证（closed-loop）
**关键特性**：
- 统一梯度共享：visual features + language reasoning + action prediction 联合训练
- 三阶段训练：SFT → Offline RL (Advantage Learning) → Online RL
- Think-Act-Verify 循环：行动后重新截图验证结果，失败则 retry

### Mano-P 4B 详细架构

| 组件 | 描述 |
|------|------|
| Visual Encoding | ViT 生成空间特征图，保留元素细节 + 全局布局 |
| Language Reasoning | 自然语言 task → 多轮对话 + 推理 traces |
| Action Prediction | 结构化输出（click/type/scroll/hotkey），grounded in visual space |
| Verify | 执行后重新截图，评估预期结果是否达成 |

**GSPruning**（2-3x 吞吐）：
- Anchor tokens：窗口边界、工具栏等空间参考点，永不剪枝
- Semantic outlier detection：异常语义 token（通知徽章、错误信息）自动保护
- M5 Pro 达 ~80 tok/s

**Cider SDK**（1.4-2.2x 加速）：
- W8A8 / W4A8 activation quantization
- Apple Silicon UMA-aware memory allocator
- 数据永远不离开本地

### 何时用哪种

| 维度 | RPA (Gen 1) | GUI Agent (Gen 3) |
|------|------------|-------------------|
| 最佳场景 | 稳定、高量、单 App | 跨 App、UI 变动频繁、需推理 |
| 维护 | 线性→超线性 | 模型更新覆盖全部任务 |
| 速度 | 毫秒级 | 秒级（感知+推理） |
| 确定性 | 100% (work时) | 概率性（verify 补偿） |
| 成本 | 每个流程手写 | 一次模型部署 |

---

## 对 Hermes 的实践意义

### 架构定位
- **当前**：vision-agent-loop = Gen 2（open-loop，截图→VLM→action，无验证）
- **目标**：DRY_RUN=False = Gen 3（closed-loop perception-reasoning-action-verify）

### 立即可行的改进
1. **多帧输入**：借鉴 Fara1.5 的 3-frame context，screen_trigger_handler 传入最近 3 帧
2. **Context management actions**：在 ACTION_WHITELIST 增加 memorize/ask_user/verify
3. **GSPruning 轻量版**：prompt 级别实现 anchor token 定位（先找窗口边界再下钻）
4. **SafeGround 不确定性校准**：UCOM 分数替代二元 dry-run/all 决策

### 待网络恢复后
- 验证 Fara1.5-4B 的 Ollama 可用性（microsoft/fara 仓库）
- 验证 Mano-P 4B 的 Ollama 导入（Mininglamp-AI/Mano-P）
- 评估 Cider SDK + GSPruning 对 M4 24GB 的加速效果
