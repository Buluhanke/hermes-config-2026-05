# ZonUI-3B — WACV 2026 轻量级 GUI Grounding VLM

> 发现日期：2026-05-29
> 来源：[WACV 2026] ZonUI-3B: Competitive GUI Grounding with a 3B VLM Trained on a Single Consumer GPU

## 基本信息

- **参数**：3B（基于 Qwen2.5VL 架构）
- **训练**：RTX 4090 单卡，仅 24K 样本
- **许可证**：Apache-2.0
- **定位**：跨平台 GUI grounding（移动/网页/桌面）
- **亮点**：分辨率感知（Resolution-Aware），在资源受限环境下达到竞争性精度

## 资源链接

- HuggingFace: https://huggingface.co/zonghanHZH/ZonUI-3B
- GitHub: https://github.com/Han1018/ZonUI-3B
- Paper: https://arxiv.org/abs/2506.23491
- PDF: https://openaccess.thecvf.com/content/WACV2026/papers/Hsieh_ZonUI-3B_Competitive_GUI_Grounding_with_a_3B_VLM_Trained_on_WACV_2026_paper.pdf

## 与当前模型的对比

| 特性 | ZonUI-3B | smolvlm2-agentic-gui |
|------|----------|---------------------|
| 参数 | 3B | 1.8B / 2.2B |
| GUI专项 | 是 | 是 |
| Ollama可用 | 否（需Transformers） | 是 |
| 对话能力 | 有（基于Qwen2.5VL） | 有限 |
| 推理框架 | PyTorch + Transformers | llama.cpp + Ollama |
| GGUF | 无 | 有 |

## 部署方式（M4 24GB）

需通过 Transformers + PyTorch 推理（非 Ollama）：

```python
from transformers import AutoProcessor, AutoModelForImageTextToText

processor = AutoProcessor.from_pretrained("zonghanHZH/ZonUI-3B")
model = AutoModelForImageTextToText.from_pretrained("zonghanHZH/ZonUI-3B")
```

**潜在优化路径**：
1. 用 llama.cpp 的 convert 工具将 safetensors 转为 GGUF
2. 导入 Ollama（需 mmproj 支持，与 Vocaela-500M 相同限制）
3. 或直接用 Transformers 推理（M4 24GB 可运行）

## 备注

- 无 GGUF 发布，无法直接 `ollama pull`
- 与 Vocaela-500M（500M, 85.8% ScreenSpotV2）相比：ZonUI-3B 更大但支持对话+推理
- 是 Vocaela 的互补方案：Vocaela 适合纯动作，ZonUI-3B 适合理解+对话
