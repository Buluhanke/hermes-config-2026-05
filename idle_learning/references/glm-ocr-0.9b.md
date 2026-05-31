# GLM-OCR 0.9B — 多模态 OCR 模型

**发现日期**：2026-06-01（方向A巡检，HN #3 Bonsai启发 → Ollama vision搜索 → 直接发现）

## 概况

GLM-OCR 是一个轻量级多模态 OCR 模型（0.9B 参数），基于 GLM-V encoder–decoder 架构。

- **OmniDocBench V1.5**: **94.62**（#1 overall，SOTA）
- **参数**: 0.9B
- **架构**: CogViT 视觉编码器 → cross-modal connector（token downsampling） → GLM-0.5B 语言解码器
- **License**: 开源（具体许可证待确认）
- **Ollama 库**: `glm-ocr`（1.3M pulls, 3 tags: latest/q8_0/bf16）
- **其他部署**: vLLM, SGLang 也支持

## 与 PaddleOCR-VL 对比

| 特性 | GLM-OCR | PaddleOCR-VL |
|------|---------|-------------|
| OmniDocBench v1.5 | 94.62 (#1) | 94.5% |
| 参数 | 0.9B | 0.9B |
| Ollama 部署 | `ollama run glm-ocr` 直接可用 | Ollama: MedAIBase/PaddleOCR-VL:0.9b |
| pip 部署 | 需额外配置 | `from paddleocr import PaddleOCRVL` ✅ |
| 首次下载 | 自动（Ollama pull） | 3-5 分钟模型下载 |
| 专长 | 文字/表格/图形识别 | 文档/公式/表格/印章 |

## 对 Hermes 的潜在价值

**screen_watcher 文本提取**：
- qwen3-vl:2b 的 OCR 能力有限（通用 VLM，非 OCR 专项）
- GLM-OCR 0.9B 可做 screen text extraction 的轻量级补充
- 与 qwen3-vl:2b 共存内存估算：1.76GB + ~1GB = ~2.8GB，24GB 充裕
- **但**：当前产线 0% unknown、场景分类正常，无明确收益驱动 pull

## pull 时机

- 当 screen_watcher 需要从 "other" 场景截图中提取文本内容时
- 当出现大量场景分类正确但文本分析失败的 case 时
- 当需要文档/表格 OCR 时

## 限制

- 纯 OCR 模型，无通用对话/推理能力
- 依赖 GLM-V 架构（非 Qwen/LLaMA 生态）
- 文档场景优化，通用 GUI 截图 OCR 精度待验证
