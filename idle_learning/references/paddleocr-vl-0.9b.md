# PaddleOCR-VL 0.9B — 文档 OCR 专家模型

**Status**: ⭐ 2026-05-31 发现, 2026-06-01 扩充 v1.5/v1.6 数据; 2026-06-01 验证 pip PaddleOCRVL API ✅
**厂商**: Baidu PaddlePaddle
**OmniDocBench v1.5**: **94.5%**

## 模型概况

- **参数**: 0.9B (LM: ERNIE-4.5-0.3B + NaViT dynamic resolution vision encoder)
- **任务**: 文档 OCR — 文本/表格/公式/图表/印章识别
- **语言**: 109 种语言 (含 CJK, Arabic, Hindi, Cyrillic, Latin)
- **架构**: NaViT dynamic resolution -> 2-layer MLP connector -> ERNIE-4.5-0.3B LLM

## Benchmark (OmniDocBench v1.5)

| 模型 | 参数 | 分数 |
|------|:---:|:----:|
| **PaddleOCR-VL v1.5** | **0.9B** | **94.5%** |
| PaddleOCR-VL v1.0 | 0.9B | 92.6% |
| Gemini 2.5 Pro | — | 88.0% |
| Qwen2.5-VL-72B | 72B | 87.0% |
| GPT-4o | — | 75.0% |

0.9B > 72B. Purpose-built beats general-purpose.

## 版本更新

- **v1.0** (2025-10): 基础文档 OCR, 92.6% OmniDocBench
- **v1.5** (2026-01): text spotting + bbox, seal recog, cross-page table merge, checkbox, skewed docs
- **v1.6** (2026-05): 最新版本 (GitHub, ~3 days before 2026-06-01)

## 部署方式

### Ollama
- `MedAIBase/PaddleOCR-VL:0.9b`
- Q4_K_M: ~300MB (LM) + ~880MB (projector) = ~1-1.5GB total
- ⚠️ registry API 返回 404 (2026-06-01), 但 pip install 已包含 PaddleOCRVL API — 见下方

### pip (PaddlePaddle 原生)
```bash
pip install paddlepaddle-gpu==3.2.0
pip install -U "paddleocr[doc-parser]"
paddleocr doc_parser -i <image_url>
```

### 已验证的 Python API (PaddleOCR-VL via pip, 2026-06-01 实测)
PaddleOCR v3.6.0 已包含 `PaddleOCRVL` 类，无需额外安装：
```python
from paddleocr import PaddleOCRVL
pipeline = PaddleOCRVL()
output = pipeline.predict("screenshot.png")
for res in output:
    res.print()
    res.save_to_json(save_path="output")
    res.save_to_markdown(save_path="output")
```

✅ **关键确认**：PaddleOCR-VL 已通过 pip 安装在本机 `paddleocr` v3.6.0 中。`from paddleocr import PaddleOCRVL` 可用。
- 可直接用于 screen_watcher handler 的 "other" 场景文本提取
- 无需 Ollama pull 或额外下载
- 适用于 CPU (Mac M4 ARM), 109 语言

## 对 Hermes 的意义

- **screen_watcher text extraction**: 补齐 qwen3-vl:2b OCR 弱项
- **极低资源**: 1-1.5GB, M4 24GB 充裕
- **109 语言**: 适合多语言 UI 文本
