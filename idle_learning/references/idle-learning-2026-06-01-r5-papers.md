# Direction B — GUI Understanding Papers Found 2026-06-01 (R5)

## 1. GUI-CIDER: Mid-training GUI Agents via Causal Internalization
**arXiv**: 2605.28534 | **Date**: May 27, 2026 | **Authors**: Zheng Wu et al.

**Core Innovation**: "Mid-training" as a third paradigm between SFT and RL for GUI agents
- **Causal Internalization**: Distills static planning + dynamic causal knowledge from GUI trajectories into text
- **Density-aware Exemplar Reselection**: Rewards causal structure, penalizes semantic redundancy
- **Three stages**: Data synthesis → exemplar reselection → mid-training
- **To Hermes**: 803 dry-run logs could serve as mid-training knowledge source; causal internalization could integrate into auto_execute action decision logic

## 2. DocOS: Proactive Document-Guided Actions in GUI Agents
**arXiv**: 2605.18048 | **Date**: May 18, 2026 | **Authors**: Jingjing Liu et al.

**Core Innovation**: GUI agents actively search online documentation to resolve long-tailed tasks
- **Dual bottlenecks**: Agents struggle to locate relevant information during proactive search AND fail to faithfully ground retrieved instructions into precise actions
- Document-guided interaction is the crucial pathway for self-evolving GUI agents
- **To Hermes**: Handler's "other" scene currently goes [silent]; could be upgraded to document-search fallback using DocOS paradigm

## 3. Macaron-A2UI: Generative UI for Personal Agents
**arXiv**: 2605.24830 | **Date**: May 24, 2026 | **Authors**: Fancy Kong et al. (Tencent)

**Core Innovation**: Beyond text-only chat — agents dynamically synthesize UI controls
- 30B/235B/754B models, LoRA SFT + RL training
- A2UI-Bench: 75.6% without schema hints (beats full-schema frontier baselines)
- **To Hermes**: Generative UI concept could extend handler action_whitelist — dynamically generate actions instead of static mapping
- Models/benchmark released: github.com/tencent

## 4. DynamicUI: GUI Agents in High-Dynamic Environments
**arXiv**: 2604.25380 (v2 May 8) | **Authors**: Enqi Liu et al.

**Core Innovation**: Single-screenshot decisions create POMDP; video input solves dynamic environments
- DynamicGUIBench: 10 applications, cross-action interface changes
- DynamicUI: Dynamic perceiver (cluster frames) → refinement strategy → reflection module
- **To Hermes**: screen_watcher currently analyzes single screenshots. Could borrow DynamicUI's video-awareness

## 5. GUI Grounding Sensitivity Benchmark
**Venue**: EACL 2026 Findings (p2772-2785) | **Authors**: Surgan Jandial et al. (Microsoft)

**Core Finding**: 12 grounding models sensitive to different descriptions of the same UI element
- Existing benchmarks only evaluate "best" description accuracy
- Desktop Windows elements severely neglected (biased toward web/mobile)
- GUI Grounding Diagnosis Agent: 84% instructions fail SOTA models
- **To Hermes**: Scene classification prompt needs multi-angle validation. Single prompt may not be robust

## 6. CutVerse: Compositional GUI Agent Benchmark for Media Production
**arXiv**: 2605.19484 | **Date**: May 19 | **Authors**: Haobo Hu et al.

**Core Contribution**: 186 long-horizon media editing tasks (Premiere Pro, Photoshop)
- Existing agents: only 36.0% task success
- **To Hermes**: Validates long-horizon as universal bottleneck. Single-snapshot analysis insufficient for cross-step workflows

## Action_Whitelist Implications
1. **Mid-training** (GUI-CIDER): Use accumulated dry-run data as training signal
2. **Document guidance** (DocOS): "Other" scenes could search knowledge base before silence
3. **Generative actions** (Macaron-A2UI): Static action whitelist → learned action-scene mapping
4. **Video-aware** (DynamicUI): Single screenshot is fundamental limitation for multi-step
5. **Multi-prompt** (Sensitivity Benchmark): Single classification prompt may be fragile
6. **Long-horizon** (CutVerse): 36% success confirms single-step focus insufficient
