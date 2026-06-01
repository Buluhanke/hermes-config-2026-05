# Towards GUI Agents: Vision-Language Diffusion Models for GUI Grounding

- **arXiv**: 2603.26211
- **Submitted**: 27 Mar 2026
- **Conference**: CVPR 2026
- **Authors**: Shrinidhi Kumbhar, Haofu Liao, Srikar Appalaraju, Kunwar Yashraj Singh

## Core Innovation

First exploration of **Discrete Diffusion Vision-Language Models (DVLMs)** for GUI grounding, 
challenging the dominance of autoregressive (AR) VLMs in this domain.

## Method

- Framework: Adapted **LLaDA-V** for single-turn action prediction and bounding-box generation
- Task formulation: GUI grounding as text generation from multimodal (image + instruction) input
- **Hybrid Masking Schedule**: combines linear masking (uniform) with deterministic masking (structure-aware)
  - Captures hierarchical structure of bounding-box geometry
  - +6.1 points Step Success Rate (SSR) over linear-masking-only variant

## Results

- Evaluated across **4 datasets** spanning web, desktop, and mobile interfaces
- Hybrid masking consistently outperforms linear-masking variant
- **Competitive with autoregressive counterparts** despite limited pretraining

## Ablations

- Increasing diffusion steps → higher accuracy but longer latency (plateaus beyond certain steps)
- Longer generation length → better results
- More training data (diverse GUI domains) → **-1.3s latency, +20pp grounding accuracy**

## Relevance to Hermes

- **New paradigm**: diffusion-based (bidirectional attention + parallel token generation + iterative refinement) 
  vs current AR approach (qwen3-vl:2b)
- Potential **failure-mode diversity**: DVLMs may miss on different cases than AR VLMs
- M4 24GB deployment: latency tradeoff needs testing (diffusion steps vs real-time requirement)
- Track for when LLaDA-V GUI-trained weights become publicly available
