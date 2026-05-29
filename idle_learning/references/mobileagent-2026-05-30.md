# MobileAgent — Qwen3-VL Native GUI Agent

## 基本信息

- **GitHub**: https://github.com/X-PLUG/MobileAgent
- **Base Model**: Qwen3-VL (2B/4B/8B/32B)
- **License**: 需确认（GitHub blocked，无法直接访问）
- **Status**: 2026-05-30 发现，开源可用

## 核心能力

1. **Native GUI Agent** — 基于 Qwen3-VL 原生视觉能力，非 Grounding 辅助
2. **多平台支持** — desktop/mobile/browser 自动化
3. **20+ GUI benchmarks SOTA** — 包括 grounding/tool calling/long-horizon memory
4. **架构**：vision→action→verify 循环，与 ScreenAgent 规划一致

## 关键特性

- **Grounding**: 视觉元素定位
- **Tool calling**: 工具调用
- **Long-horizon memory**: 长时记忆
- **多模态理解**: 基于 Qwen3-VL 的原生视觉-语言对齐

## 与 Hermes 现有方案的对比

| 能力 | hermes-rpa (cliclick) | MobileAgent (Qwen3-VL) |
|------|----------------------|------------------------|
| 视觉理解 | smolvlm2 (外接) | 原生内置 (Qwen3-VL) |
| 执行精度 | 像素坐标 | 视觉 grounding |
| benchmark | 无官方数据 | 20+ SOTA |
| 部署难度 | 低（CLI工具） | 需跑 Qwen3-VL |
| M4 24G 可行性 | ✅ | ⚠️ Qwen3-VL 8B+ 需要较大内存 |

## M4 24G 适配分析

- **qwen3-vl:2b (1.76GB)** — M4 24G 可运行，但 46.6s 响应（需缩图）不适合实时 agent loop
- **MobileAgent 如用 2B variant** — 可能可行，需测试实际响应速度
- **核心瓶颈**：Qwen3-VL 图像处理在 M4 上慢，agentic loop 需要多轮调用，成本高

## 潜在价值

1. **执行层升级**：如能跑通，比 hermes-rpa 的 pixel-based 点击更精确
2. **benchmark 验证**：有 20+ 基准 SOTA，数据可信
3. **架构参考**：vision→action→verify 循环设计值得借鉴

## 待验证项

- [ ] MobileAgent GitHub 实际内容（github.blocked，无法直接访问）
- [ ] qwen3-vl:2b 作为 MobileAgent base 的实际 agent loop 响应时间
- [ ] 是否可在 M4 24G 上完成简单 GUI 任务（打开应用、点击按钮）

## 参考链接

- GitHub: https://github.com/X-PLUG/MobileAgent
- Qwen3-VL: https://qwen.ai/blog?id=99f0335c4ad9ff6153e517418d48535ab6d8afef