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

---

## 候选替代：Qwen3-VL（2026-05-29 发现）

### 概述
Qwen3-VL 是 Alibaba Qwen 最新旗舰视觉语言模型（2026年），在 Ollama 上完整可用。
**官方声明**：可直接操作电脑/手机界面，OSWorld 全球顶级表现。

### Ollama可用变体与大小

| 变体 | 大小 | M4 24GB适配 | 备注 |
|------|------|-----------|------|
| qwen3-vl:2b | 1.9GB | ✅ | 同smolvlm2大小，实测可用 |
| qwen3-vl:4b | 3.3GB | ✅ | 推荐测试 |
| qwen3-vl:8b | 6.1GB | ✅ | 更高能力 |

### 本地实测（M4 24GB, 2026-05-29）

**qwen3-vl:2b 测试结果**：
- ✅ 500px JPEG截图：19.3s总响应（8.8s加载 + 0.6s图像编码 + 8.5s推理）
- ✅ 正确识别虚拟键盘 UI，区分背景与非UI元素
- ❌ 1024px+图像处理超时（需小尺寸输入）
- Warm模型（keep_alive=-1）：预计 ~10.5s

| 维度 | smolvlm2-agentic-gui | qwen3-vl:2b |
|------|------|------|
| 大小 | 1.85GB (Q4_K_M) | 1.9GB (Q4) |
| 架构 | SmolVLM2 finetuned | Qwen3-VL |
| GUI专项 | ✅ (agentic-gui) | ✅ (官方支持) |
| 响应速度(warm) | 5-11s | ~10.5s |
| 上下文 | 4K | **256K** |
| OSWorld | 未公开 | ✅ Top全球 |

### 结论
qwen3-vl:2b 体积、速度与 smolvlm2 相当，但架构更新、GUI agent 能力官方支持、上下文大64倍。推荐后续测试 qwen3-vl:4b（3.3GB）。
