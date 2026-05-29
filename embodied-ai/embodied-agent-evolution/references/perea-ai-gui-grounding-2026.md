# GUI Grounding Models 2026 — Perea.AI SOTA 报告

**来源**：https://www.perea.ai/research/gui-grounding-models-2026
**日期**：2026年5月
**类型**：学术/行业研究报告

## 核心结论

> "The grounder is where the open-source stack has overtaken closed-source baselines, and where the next year of agent reliability gains will come from."

Planner（GPT-4o/Claude 3.7/Gemini 2.5 Pro）已成熟，Grounder（视觉 grounding）是瓶颈所在，开源栈已追上甚至超越闭源前沿。

## 三层架构（每个computer-use agent都有）

```
Planner（规划器）→ Reason about goals →  frontier models (GPT-4o, Claude 3.7, Gemini 2.5 Pro)
Grounder（接地器）→ Convert action to screen coordinate →  **the bottleneck**
Executor（执行器）→ Ship pixel-level click/keystroke to OS
```

## Benchmark 核心数据

### Grounding Accuracy

| MODEL | PARAMS | SCREENSPOT-V2 | SCREENSPOT-PRO | OSWORLD-G | UI-VISION | VENUSBENCH-GD |
|-------|--------|---------------|---------------|-----------|-----------|---------------|
| Qwen3-VL-30B-A3B (general) | 30B | — | 53.7% | 69.3% | 61.2% | 52.4% |
| Step-GUI-8B | 8B | — | 62.6% | — | — | — |
| MAI-UI-8B (Microsoft) | 8B | — | 65.8% | 60.1% | 40.7% | 65.2% |
| **MAI-UI-32B** | **32B** | **96.5%** | **67.9%** | **67.6%** | **47.1%** | **—** |
| GTA1-7B | 7B | — | 50.03% | 56.22% | — | — |
| GTA1-72B | 72B | — | 46.34% | 50.53% | — | — |
| Jedi-7B (xlang-ai) | 7B | — | 30.10% | 51.41% | — | — |
| UI-TARS-7B (closed) | 7B | — | 29.53% | 44.50% | — | — |
| UI-TARS-72B (closed) | 72B | — | 37.12% | 55.67% | — | — |
| OS-Atlas-7B | 7B | **81.0%** | — | — | — | — |
| UGround-V1-7B (Qwen2-VL) | 7B | **86.3%** | — | — | — | — |
| UGround-V1-72B (Qwen2-VL) | 72B | **89.4%** | — | — | — | — |
| ShowUI | 2B | 75.1% | — | — | — | — |
| Aguvis-7B | 7B | 83.0% | — | — | — | — |
| **UI-Venus-1.0-72B** | 72B | 95.3% | 61.9% | 62.2% | 36.8% | 70.2% |
| UI-Venus-1.5-2B | 2B | — | 57.7% | 59.4% | 44.8% | 67.3% |
| UI-Venus-1.5-8B | 8B | — | 68.4% | 69.7% | 46.5% | 72.3% |
| **UI-Venus-1.5-30B-A3B** | 30B-MoE | **96.2%** | **69.6%** | **70.6%** | **54.7%** | **75.0%** |
| MEGA-GUI (Gemini-2.5) | system | — | **73.18%** | **68.63%** | — | — |

### Online Navigation Accuracy

| MODEL | PARAMS | ANDROIDWORLD | ANDROIDLAB | VENUSBENCH-MOBILE | WEBVOYAGER |
|-------|--------|-------------|-----------|-----------------|-----------|
| GPT-4o (general) | — | — | 31.2% | — | 55.5% |
| Claude-3.7 (general) | — | — | — | — | 84.1% |
| Gemini-2.5-Pro | — | 69.7% | — | — | — |
| Seed1.8 (ByteDance) | — | 70.7% | — | — | — |
| MAI-UI-32B | 32B | 73.3% | — | — | — |
| Holo2-30B-A3B | 30B | 71.6% | — | — | 83.0% |
| **OpenAI-CUA (closed)** | — | — | — | — | **87.0%** |
| Aria-UI (Dec 2024) | 3.9B | 44.8% | — | — | — |
| UGround (Oct 2024) | 7B | 33→44% | — | — | — |
| UI-Venus-1.0-72B | 72B | 65.9% | 49.3% | 15.4% | — |
| UI-Venus-1.5-8B | 8B | 73.7% | 55.1%/68.1% | 16.1% | 70.8% |
| **UI-Venus-1.5-30B-A3B** | 30B | **77.6%** | 52.9%/68.1% | 21.5% | 76.0% |

## 五个架构选择

1. **Pure-vision vs AXTree**：纯视觉已胜出（screenshot in, coordinate out），AXTree因平台依赖被淘汰
2. **RFT（强化微调）**：UI-Venus-1.0基于Qwen2.5-VL + 350K grounding样本 + GRPO reward model
3. **四阶段训练**（UI-Venus-1.5）：Mid-Training(10B tokens) → Offline-RL → Online-RL(full-trajectory) → Model Merge(TIES)
4. **多阶段ROI分解**（MEGA-GUI）：Gemini 2.5 Pro做ROI选择 + specialized grounding agents，系统级73.18% ScreenSpot-Pro
5. **MoE架构**（Aria-UI 3.9B / UI-Venus-1.5-30B-A3B）：A3B=3B active per token，解释高效性

## 关键数字

- **AndroidWorld进展**：44.8%（2024-12 Aria-UI）→ 77.6%（2026-02 UI-Venus-1.5），一年内+32.8%
- **OSWorld进展**：单位数（2024）→ >50%（Jedi训练模型，2025-2026）
- **WebVoyager**：OpenAI CUA 87.0%仍最强，Holo2-30B 83.0%次之
- **ScreenSpot-Pro更难**：OS-Atlas+ScreenSeeker才48.1%，MEGA-GUI系统才73.18%（满分100%）