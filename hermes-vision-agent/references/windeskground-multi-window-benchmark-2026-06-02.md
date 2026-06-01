# WinDeskGround — Multi-Window Desktop GUI Grounding Benchmark

**arXiv**: [2605.16402](https://arxiv.org/abs/2605.16402)
**Date**: May 13, 2026
**Authors**: Haoren Zhao, Tianyi Chen

## Summary

WinDeskGround is a benchmark and synthesis framework for evaluating GUI grounding robustness in real-world desktop environments characterized by multi-window stacking, occlusion, and visual clutter.

## Key Specs

- 585 high-resolution real window screenshots
- 1,356 instructions
- 9 major application domains (productivity tools, browsers, development tools, etc.)
- Parameterized evaluation space: layout density, occlusion, semantic similarity
- Simulated multi-window desktop synthesis framework

## Relevance to Hermes

- Directly maps to M4 desktop environment use case
- Multi-window GUI grounding is a core capability gap for desktop agents
- Could serve as evaluation benchmark for Hermes vision pipeline (qwen3-vl:2b)

## Status

🆕 Newly discovered (2026-06-02 idle learning). Not yet evaluated on Hermes vision pipeline.
