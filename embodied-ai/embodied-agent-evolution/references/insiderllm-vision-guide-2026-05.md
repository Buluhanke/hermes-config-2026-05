# InsiderLLM Vision Models Guide（2026-05-30 获取）

## 来源
- URL: https://insiderllm.com/guides/vision-models-locally/
- 获取方式: browser_navigate + 页面内容读取
- 触发原因: ddgs 搜索发现 + github blocked 时用浏览器直接访问

## 核心内容（2026-05 更新版）

### Quick Answer
- **24GB+ GPU**: Qwen 3.6-27B dense（~17GB VRAM，Apache 2.0）是新SOTA本地视觉模型，vision内建于基座
- **18GB+ VRAM 最快路径**: `ollama run gemma4:26b`（Fast multimodal MoE）
- **8GB GPU**: `ollama run qwen2.5vl:7b`（Qwen 3.6 Ollama 暂不支持）

### VRAM Tier Table（完整）
| VRAM | Best Pick | Ollama Command | Why |
|------|---------|----------------|-----|
| 4GB | Gemma 3 4B (int4) | `ollama run gemma3:4b` | 2.6GB |
| 4GB | SmolVLM2 2.2B | — (HF) | ~2GB |
| 8GB | Qwen 2.5-VL 7B (Q4) | `ollama run qwen2.5vl:7b` | 8GB fallback |
| 10-12GB | Phi-4-reasoning-vision 15B | — (llama.cpp) | Math/science |
| 16-22GB | Qwen 3.6-35B-A3B MoE | — (llama.cpp + --cpu-moe) | 35B via offload |
| ~18GB | Gemma 4 26B-A4B | `ollama run gemma4:26b` | Fast MoE |
| ~20GB | Gemma 4 31B dense | `ollama run gemma4:31b` | MMMU Pro 76.9% |
| 24GB+ | Qwen 3.6-27B dense | — (llama.cpp/LM Studio) | **SOTA** |
| Any OCR | PaddleOCR-VL 0.9B | `pip install` | 92.6% doc acc |

### 关键技术洞察
1. **Qwen 3.6 vision 内建于基座** — 无独立VL track，27B/35B-A3B 均原生多模态
2. **Gemma 4 是 Ollama 最快多模态路径** — 18GB+ VRAM 直接跑
3. **Qwen 3.6 Ollama 暂不支持** — 需 llama.cpp 或 LM Studio；`qwen3-vl:8b` 是 3-VL 系列，不是 3.6
4. **M4 Mac 24GB**: qwen3-vl:2b（1.9GB）/4b（3.3GB）/8b（6.1GB）Ollama 可用；gemma4:e2b（7.2GB）/e4b（9.6GB）

### What's New（May 2026）
- Qwen 3.6 dropped the separate VL track — vision baked in base models
- Gemma 4 26B-A4B 是 fast multimodal pick（3.8B active params/token）
- Phi-4-reasoning-vision 可从照片解数学题
- PaddleOCR-VL 使专用文档 OCR 近免费

### 原文精选
> "A lot changed in early 2026. Qwen3-VL replaced Qwen2.5-VL as the vision model to beat. Phi-4-reasoning-vision can actually solve math problems from photographs now. PaddleOCR-VL made dedicated document OCR nearly free to run."