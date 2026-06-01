# UI-S1: Advancing GUI Automation via Semi-online Reinforcement Learning

**Source**: arXiv 2509.11543
**Authors**: Zhengxi Lu, Jiabo Ye, Fei Tang, Yongliang Shen, Haiyang Xu, Ziwei Zheng, Weiming Lu, Ming Yan, Fei Huang, Jun Xiao, Yueting Zhuang (Alibaba Group)
**Date**: 2025-09 (found 2026-06-02 via ZJU Awesome-GUI-Agents README Updates)

## Core Innovation

Semi-online RL paradigm — simulates online RL on offline trajectories.

### Problem
- **Offline RL**: Stable training on pre-collected trajectories, but struggles with multi-step task execution (no trajectory-level reward signals)
- **Online RL**: Captures reward signals through environment interaction, but suffers from sparse rewards and prohibitive deployment costs

### Solution
- Patch Module adaptively recovers divergence between offline/online policies
- Each rollout preserves original model output within multi-turn dialogue
- Semi-online: simulate environment rollouts on offline data

## Relevance to Hermes

| Aspect | Mapping |
|--------|---------|
| screen_watcher dry-run logs | = offline trajectories (history of ~600+ dry-runs) |
| DRY_RUN=False decision | = when to switch from offline evaluation to online execution |
| auto_execute policy | = the RL policy that needs trajectory-level reward signals |
| Semi-online RL | = train on dry-run logs without needing real-world execution risks |

**Key insight**: Hermes doesn't need to flip DRY_RUN=False wholesale. Semi-online RL suggests training on historical dry-run logs to improve the policy *before* going live.

## Status

- [ ] Create full reference document with technical details
- [ ] Evaluate: can screen_trigger_handler's scene classification be improved with semi-online training on dry-run logs?
