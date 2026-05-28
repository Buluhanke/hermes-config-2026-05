# UI-TARS Desktop 执行层调研（2026-05-29）

> 来源：ByteDance UI-TARS Desktop（bytedance/UI-TARS-desktop，35.6k stars）
> 相关：Agent TARS CLI v0.3.0, UI-TARS SDK

## 概览

UI-TARS（Task Automation and Reasoning System）是字节跳动开源的纯视觉桌面 Agent，Apache 2.0 协议。
**核心创新**：纯视觉感知（不解析 HTML/AX 树），输出统一动作空间，支持 planning-acting-reflection 三阶段循环。

## 仓库数据

| 指标 | 值 |
|------|-----|
| Stars | 35.6k |
| Forks | 3.6k |
| Commits | 1,109 |
| 最后提交 | 2 weeks ago (2026-05-15) |
| 协议 | Apache 2.0 |
| 主语言 | TypeScript (Electron) |

## 模型变体

| 模型 | 参数 | VRAM (FP16) | VRAM (Q4_K) | OSWorld |
|------|------|------------|-------------|---------|
| UI-TARS-2B | 2B | ~4GB | ~1GB | - |
| UI-TARS-7B | 7B | ~14GB | ~4GB | 24.6% |
| UI-TARS-1.5-7B | 7B | ~14GB | ~4GB | 27.5% |
| UI-TARS-1.5-72B | 72B | ~144GB | ~36GB | 42.5% |
| **UI-TARS 2** | 2-23B MoE | 532M ViT + 23B active | - | **47.5%** |

## 关键基准

| 基准 | UI-TARS 2 | Claude Computer Use | OpenAI Operator |
|------|-----------|-------------------|-----------------|
| OSWorld (50步) | **47.5%** | 22.0% | 38.1% |
| AndroidWorld | **73.3%** | ~35% | - |
| WebVoyager | 84.8% | 56% | **87%** |
| WindowsAgentArena | **50.6%** | - | - |
| SWE-Bench | **68.7%** | - | - |
| ScreenSpot-V2 | **94.2%** | - | - |
| ScreenSpotPro | 61.6% | - | - |

## 统一动作空间

```python
# Desktop operations
click(x, y)           # Single/double/right clicks at coordinates
type(text)            # Keyboard text input
hotkey(keys)          # Keyboard shortcuts (Ctrl+C, Alt+Tab)
scroll(direction, amount)  # Vertical/horizontal scrolling
drag(x1, y1, x2, y2)  # Drag-and-drop operations

# Mobile operations (Android/iOS)
long_press(x, y)      # Extended touch
swipe(direction)      # Touch gestures
open_app(name)        # Application launching
press_home()          # System navigation
press_back()          # Back button
```

## 架构：vision→action→verify 循环

```
① Screenshot Capture → ② Visual Encoding (675M ViT) →
③ Multimodal Fusion (M-RoPE) → ④ Action Prediction →
⑤ Execution (PyAutoGUI / NutJS) → ⑥ Feedback Loop (next screenshot)
```

## Agent TARS CLI v0.3.0（2025-11-05）

- 流式支持多个工具（shell 命令、多文件结构化展示）
- 运行时设置 + 工具调用和 deep thinking 的 timing 统计
- Event Stream Viewer — 数据流追踪和调试
- AIO agent Sandbox 支持

## 对 Hermes 的启示

1. **架构验证**：UI-TARS 30k+ stars 证明了 vision→action→verify 循环是桌面 agent 的正确方向
2. **坐标精度差距**：94.2% vs 61.71% (smolvlm2) — 坐标准确率是决定执行层成败的关键
3. **UI-TARS-2B Q4_K (~1GB)** 理论上可在 M4 24G 运行，后续可下载对比测试
4. **Agent TARS CLI** 的工具流式执行模式值得参考（工具调用 + 运行时统计）
5. **统一动作空间** 设计标准化 — Hermes 也可以对齐到相同的 click/type/hotkey/scroll/drag 命名

## Mac 硬件适配

| 模型 | 量化 | VRAM | M4 24G 可行性 |
|------|------|------|-------------|
| UI-TARS-2B | Q4_K | ~1GB | ✅ 可运行 |
| UI-TARS-7B | Q4_K | ~4GB | ✅ 可运行 |
| UI-TARS-7B | FP16 | ~14GB | ✅ 可运行 |
| UI-TARS-1.5-72B | Q4_K | ~36GB | ❌ 超上限 |
