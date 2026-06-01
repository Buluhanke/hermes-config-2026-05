# MVP: Multiple View Prediction Improves GUI Grounding

- **arXiv**: 2512.08529 (Dec 9, 2025)
- **Venue**: CVPR 2026
- **GitHub**: ZJUSCL/MVP
- **Authors**: Yunzhu Zhang, Zeyu Pan, Zhengwen Zeng, Shuheng Shen, Changhua Meng, Linchao Zhu

## Core Innovation

**Training-free framework** that addresses coordinate prediction instability in GUI grounding models.

### Key Insight
Single-view predictions are inherently unstable — minor visual perturbations (e.g., cropping a few pixels) can drastically alter predictions, flipping results between correct and incorrect. Multi-view aggregation can effectively distinguish correct coordinates from outliers.

### Two Components

1. **Attention-Guided View Proposal** — Derives diverse views guided by instruction-to-image attention scores
2. **Multi-Coordinates Clustering** — Ensembles predictions by selecting the centroid of the densest spatial cluster

## Results (ScreenSpot-Pro)

| Model | Baseline | +MVP |
|-------|----------|------|
| UI-TARS-1.5-7B | baseline | **56.1%** |
| GTA1-7B | baseline | **61.7%** |
| Qwen3VL-8B-Instruct | baseline | **65.3%** |
| Qwen3VL-32B-Instruct | baseline | **74.0%** |

## Hermes Relevance

**Direction D** — Directly addresses coordinate prediction instability, the core challenge in auto_execute's coordinate mapping chain. Current screen_trigger handler has zero uncertainty handling in coordinate prediction. MVP's multi-view ensemble approach could be ported to the screen_trigger handler's action prediction pipeline.

**Direction B** — CVPR 2026 GUI grounding paper, expands the knowledge base of ensemble techniques for coordinate grounding.

## Key Takeaways

- No retraining required — plug-and-play with any existing grounding model
- Addresses a problem that affects all single-pass GUI grounding: instability to pixel-level perturbations
- Clustering-based ensemble is simple enough to implement locally without GPU dependency
