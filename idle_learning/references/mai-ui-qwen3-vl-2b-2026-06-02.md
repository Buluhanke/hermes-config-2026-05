# MAI-UI (Qwen3-VL-2B-MAI-UI-NOESIS-NF4)

**来源**: ddgs 搜索 `qwen3-vl GUI grounding benchmark 2026` (2026-06-02)
**类型**: Qwen3-VL-2B fine-tune, NF4 量化, Ollama 可直接部署

## Benchmark 成绩

| Benchmark | 成绩 | 对比 |
|-----------|------|------|
| ScreenSpot-Pro | **73.5%** | 超越 Gemini-3-Pro / Seed1.8 |
| MMBench GUI L2 | **91.3%** | |
| OSWorld-G | **70.9%** | |
| UI-Vision | **49.2%** | |

## 关键信息

- **模型名**: `AMAImedia/Qwen3-VL-2B-MAI-UI-NOESIS-NF4` (HuggingFace)
- **量化**: NF4 (4-bit)，GGUF 格式，Ollama 直接兼容
- **定位**: 端侧 GUI grounding 专用 fine-tune
- **与 qwen3-vl:2b 对比**: 同是 2B 级别，但 MAI-UI 是专用调优，qwen3-vl:2b 是通用模型

## Hermes 产线映射

- **当前部署**: qwen3-vl:2b (1.76GB, 通用型)
- **MAI-UI 潜力**: 2B 专用型，ScreenSpot-Pro 73.5% 显著高于通用 qwen3-vl:2b
- **评估结论**: NF4 量化后体积接近 qwen3-vl:2b，ScreenSpot-Pro 精度提升明显，值得产线验证

## 参考来源

- HuggingFace: https://huggingface.co/AMAImedia/Qwen3-VL-2B-MAI-UI-NOESIS-NF4
- 原型: Qwen3-VL-2B (Qwen3-VL 系列)
