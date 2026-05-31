# PaddleOCR-VL 0.9B — CPU-only OCR for Document Understanding

**Source**: InsiderLLM (insiderllm.com) May 2026 Vision Guide + PaddleOCR GitHub
**Found**: 2026-05-31 idle_learning session

## Summary

PaddleOCR-VL 0.9B is a vision-language model optimized for **document OCR**. Key specs:

- **Size**: 0.9B parameters — runs on CPU
- **Accuracy**: 92.6% document-level OCR accuracy
- **Install**: `pip install` (PaddleOCR ecosystem)
- **License**: Apache 2.0
- **Use case**: Extracting text from screenshots, invoices, documents

## Relevance to Hermes

- Could be used in screen_watcher for OCR text extraction from desktop screenshots
- Complements qwen3-vl:2b which does scene classification but not dedicated OCR
- CPU-only inference means no Ollama memory competition

## Limitation

- Document-focused; not designed for general GUI element recognition
- Requires PaddlePaddle ecosystem installation
