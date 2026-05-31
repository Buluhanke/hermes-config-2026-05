# PAGER: Bridging the Semantic-Execution Gap in Point-Precise Geometric GUI Control

**arXiv**: 2605.15963, May 15 2026 (v2: May 24)
**Authors**: Jingxuan Wei, Xi Bai, Shan Liu, Caijun Jia et al. (UCAS / Shanghai AI Lab / China University of Petroleum)

## Core Contribution

### Semantic-Execution Gap
- General multimodal models: >88% action type accuracy → <6% task success
- Specialized GUI agents: <9% step success → PAGER raises to >62% (4.1x improvement)
- The gap: models know *what* to do (semantic) but fail at *where* to do it (spatial accuracy)

### Region-Tolerant Paradigm Limitation
- Current GUI agents assume "nearby pixels inside same component remain valid"
- **Precision-sensitive GUI tasks** break this: actions must land on specific points in continuous canvas space
- Coordinate errors cascade through dependency chains like perturbations under a dependency Jacobian

### PAGE Bench
- 4,906 geometry problems
- 53,277 high-level construction tasks
- 224,497 low-level GUI actions (pixel-level annotations)
- Process-supervised trajectories with canvas states, execution feedback, pixel geometric annotations

### PAGER Framework
1. **Dependency-structured planning**: construction graph → topologically valid sub-task order
2. **Pixel-level execution**: each sub-task → concrete GUI actions on current canvas state
3. **Pixel-grounded SFT**: establishes executable action grammar + sequential drawing behavior
4. **Precision-aligned RL**: parameter-accuracy rewards drive continuous-space control, geometric validity optimization

## Relevance to Hermes

### Direct Applicability
1. **auto_execute coordinate mapping** (Direction D bottleneck): qwen3-vl:2b outputs normalized 0-999 coordinates → needs same precision handling as PAGER
2. **Negative action knowledge** (from 2026-06-01 DRY_RUN=False R3): PAGER confirms semantic understanding ≠ spatial accuracy is a known general problem, not unique to Hermes
3. **DRY_RUN=False 前置条件④** (坐标映射链): PAGER's dependency-structured planning suggests we need more than coordinate conversion — we need canvas state tracking

### Key Number to Remember
- Step success: <9% (GUI-specialized) → 62% (PAGER) = **6.9x improvement on spatial precision**
- This is the same magnitude of win Hermes needs for the coordinate mapping step

### Source
https://arxiv.org/abs/2605.15963
https://arxiv.org/html/2605.15963v1 (HTML with full methodology)
