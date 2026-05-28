# smolvlm2-agentic-gui 模型变体与基准

## Ollama 可用变体

| Tag | 量化 | 大小 | 说明 |
|-----|------|------|------|
| `:latest` | Q4_K_M | ~1.85 GB | 默认，速度/质量最佳平衡 |
| `:q8_0` | Q8_0 | ~1.9 GB | 更高精度，仅大 ~50MB |
| `:fp16` | F16 | ~3.6 GB | 全精度，M4 24GB 可运行 |

## 基准分数

- **ScreenSpot-v2**: 61.71% (GUI元素定位基准)
- **来源**: ahmadwaqar/smolvlm2-agentic-gui Ollama 模型页面

## 本地实测响应时间 (M4, 24GB)

| 日期 | 场景 | 响应时间 | 识别质量 |
|------|------|---------|---------|
| 2026-05-28 | 桌面浏览器+ChatGPT+Android模拟器 | 10.3s | 准确，无幻觉 |
| 2026-05-28 | 移动端购物页面 | 11.1s | 准确，合理操作建议 |
| 2026-05-28 | 桌面+状态栏 | 5.2s | 准确 |
| 2026-05-29 | Chrome弹窗+键盘+图标 | 10.5s | 准确，无幻觉 |

## 能力

- GUI元素定位（从截图中识别按钮/输入框/图标）
- 多步骤GUI任务规划与执行
- 生成精确的点击、输入、滚动、拖拽坐标（归一化 [0,1]）
- 桌面、移动端、Web界面通用

## 训练架构

1. Phase 1: smolagents/aguvis-stage-1 — UI元素定位
2. Phase 2: smolagents/aguvis-stage-2 — 多步骤任务规划

## 相关信息

- Ollama模型页: https://ollama.com/ahmadwaqar/smolvlm2-agentic-gui
- 原始模型: smolagents/SmolVLM2-2.2B-Instruct-Agentic-GUI
- 许可证: Apache 2.0
