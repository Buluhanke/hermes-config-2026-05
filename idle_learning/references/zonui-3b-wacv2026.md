# ZonUI-3B — Lightweight Cross-Resolution GUI Grounding VLM (WACV 2026)

**Source**: Hsieh, Wei, Yang (arXiv:2506.23491, WACV 2026)
**GitHub**: Han1018/ZonUI-3B (24 stars, 3 forks)
**License**: CC BY-NC 4.0 (check GitHub for updated license)
**Model**: 3B parameters, HuggingFace transformers

## Key Metrics

| Benchmark | Score | Ranking |
|-----------|-------|---------|
| ScreenSpot | **84.9%** | #1 among GUI-specific models (beats Aguvis-7B 84.4%, OS-Atlas-7B 82.5%) |
| ScreenSpot-v2 | **86.4%** | #1 among all models (beats UI-TARS-2B 84.7%, OS-Atlas-7B 84.1%) |

## Highlights
- **Only 24K training samples** — extremely data efficient
- **Single RTX 4090 24GB** training, <48 hours
- **3B parameters** (~2GB at Q4) — **M4 24GB compatible**
- Resolution-aware design for cross-resolution GUI grounding
- Publishes training data: UGround-V1-8k, AMEX-8k, ShowUI-web-8k

## Hermes Relevance
- **Best upgrade candidate** for qwen3-vl:2b scene classification
- Lightweight enough for M4 24GB (3B param ~2GB GGUF)
- State-of-the-art GUI grounding in a small package
- **TODO**: Verify Ollama/GGUF availability (original code uses HF transformers)

## BibTeX
```
@misc{hsieh2025zonui3b,
  title = {ZonUI-3B: A Lightweight Vision-Language Model for Cross-Resolution GUI Grounding},
  author = {Hsieh, ZongHan and Wei, Tzer-Jen and Yang, ShengJing},
  year = {2025},
  howpublished = {\url{https://arxiv.org/abs/2506.23491}}
}
```
