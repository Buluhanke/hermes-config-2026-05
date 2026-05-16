# 替代桌面自动化工具对比

> 评估外部工具集成到 Hermes RPA 的可行性，供后续参考。

## 评估框架

每次评估替代桌面自动化工具时，按以下维度检查：

1. **硬件要求** — 用户 Mac mini M4 24GB，需要 >=32GB 的本地模型方案不推荐
2. **CLI/API 接口** — 是否有 CLI 或 SDK 可供 Hermes 调用
3. **方案差异** — 视觉驱动 vs 结构化驱动（AXUI/DOM）
4. **回退/补充价值** — 是否解决现有方案的盲区
5. **集成成本** — 安装、配置、维护工作量

## Mano-P（Mininglamp AI）

| 维度 | 详情 |
|------|------|
| 方案 | 纯视觉（VLM 看全屏截图 → 推理 → 点坐标） |
| 本地要求 | Apple M4 + 32GB RAM（用户只有 24GB） |
| 云端模式 | mano.mininglamp.com（需 API Key） |
| 安装 | `brew tap Mininglamp-AI/tap && brew install mano-cua` |
| CLI | `mano-cua run "task" --local` 或直接调云端 |
| 评估结论 | 本地跑不动，云端可集成但不如 Hermes RPA 直接 |
| 决策理由 | 24GB 内存不够本地推理，云端模式需要额外 API 费用 |

## UI-TARS Desktop / Agent TARS（ByteDance）

| 维度 | 详情 |
|------|------|
| 方案 | Agent: 纯视觉（VLM 全屏截图→推理→操作） |
| 用户态 | CLI: `npx @agent-tars/cli@latest` 或 `npm install -g @agent-tars/cli` |
| 本地要求 | 视觉模型需 GPU，桌面应用版需 Node.js >= 22 |
| Node.js 版本 | 用户已安装（`node --version` 可确认） |
| 评估结论 | 同样是视觉 Agent，与 Hermes RPA 定位重叠 |
| 决策理由 | 32k star 生态大，但纯视觉方案在 24GB 机器上效率不如 AXUI+OCR |

## 通用原则

### 什么时候应该考虑集成

- ✅ 外部工具提供 Hermes RPA 完全不具备的能力（如某种特殊的反爬 bypass）
- ✅ 外部工具 CLI 接口清晰，可以简单包装为 skill 子命令
- ✅ 硬件要求匹配用户机器（M4 24GB 能跑）

### 什么时候不应该花时间

- ❌ 本质是相同的"看屏幕→操控电脑"路线，只是实现方式不同
- ❌ 本地要求超过 24GB 内存
- ❌ 需要额外的云 API 订阅费
- ❌ 安装复杂或依赖过多

### 关于 "集成" 的正确理解

用户说"能不能整合到 Hermes"通常是指：
1. 有没有 CLI 可以调（而不是 GUI 应用）
2. 能不能通过 Hermes skill 形式暴露能力
3. 能不能替代或补充现有 RPA 流程

**不需要**把别人的整个代码库搬到 Hermes 里 — 包装 CLI 调用就够了。
