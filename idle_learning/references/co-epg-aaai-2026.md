# Co-EPG: Co-Evolution of Planning and Grounding (AAAI 2026)

- **arXiv**: 2511.10705 (Nov 2025)
- **Accepted**: AAAI 2026
- **Authors**: Yuan Zhao, Hualei Zhu, Tingyu Jiang, Shen Li, Xiaohang Xu, Hao Henry Wang

## Core Innovation
Self-iterative training framework where planning and grounding co-evolve through a positive feedback loop:

```
Planning Model → explores strategies under grounding-based reward guidance via GRPO
     ↓
generates diverse data to optimize Grounding model
     ↓
optimized Grounding model → provides more effective rewards for Planning GRPO training
     └──────────── positive feedback loop ──────────┘
```

## Key Results
- 3 iterations → surpasses SOTA on Multimodal-Mind2Web and AndroidControl
- No external data required
- Consistent improvement per iteration (self-enhancement demonstrated)

## Hermes Relevance
- Directly applicable to screen_trigger_handler optimization:
  - Planning = scene classification + action decision
  - Grounding = coordinate mapping + element identification
- GRPO-based loop mirrors Hermes' iterative self-evolution philosophy
- Shifts from isolated optimization to integrated co-evolution

## Limitations
- GUI domain only (mobile + web)
- Training cost of 3 iterations not disclosed
- GRPO requires verifiable reward signals (not always available in desktop automation)
