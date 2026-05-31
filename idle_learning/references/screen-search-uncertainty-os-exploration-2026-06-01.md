# ScreenSearch: Uncertainty-Aware OS Exploration (arXiv 2605.16024, May 15 2026)

## 基本信息
- **标题**: ScreenSearch: Uncertainty-Aware OS Exploration
- **作者**: Michael Solodko, Justin Wagle
- **来源**: arXiv 2605.16024, cs.AI
- **提交**: May 15, 2026

## 核心洞察
Desktop GUI agents operate under **partial observability**: visually similar screens can correspond to different underlying workflow states, so locally plausible actions can lead to sharply different outcomes.

Frames this as a **computer/OS state exploration** problem where effective behavior requires both (1) expanding the reachable frontier and (2) reducing ambiguity before committing.

## 方法

### 1. Structural Screen Retrieval + Deduplication
- UIA (UI Automation) trees → location-aware structural features
- Sparse token search + metadata filters for related screen indexing
- Shared deduplicated state graph across VM workers

### 2. Ambiguity-Aware PUCT Graph-Bandit
- **Ambiguity signal**: matched-action outcome dispersion — if similar screens produce different next states under the same action signature → state should be probed further
- Frontier rewards for exploration combining novelty + ambiguity
- Large-scale exploration with replay-start policy evaluation

### 3. 规模
- 1M screenshots collected across 11 desktop applications
- 30K+ deduplicated states
- Substantial cross-application and within-application diversity

## Novelty-Ambiguity Trade-off
Reducing ambiguity alone is NOT a sufficient exploration objective. Policies that reduce ambiguity quickly tend to discover little frontier. Three factors all matter:
1. State identity (what's the current screen)
2. Proposal quality (how good are action candidates)
3. Ambiguity-aware search (when to probe vs when to commit)

## 对 Hermes 的影响

### 直接映射到 handler
| ScreenSearch | Hermes handler | 差距 |
|-------------|---------------|------|
| State graph (30K states) | Single-shot classification | 相邻帧间无状态跟踪 |
| Ambiguity signal via outcome dispersion | 60s cooldown (粗糙) | PUCT bandit 更细粒度 |
| UIA tree structural features | Pure vision (screenshot→VLM) | Vision-only 是设计选择 |
| Probe-vs-commit decision | Dry-run all (never probe/commit) | DRY_RUN=False 时需此框架 |

### 关键启示
- Desktop 状态空间可观（30K deduplicated）→ 有限场景分类方向正确
- 纯 ambiguity reduction 不够 → handler 不能只看 "whether to act"，还要看 "whether to explore"
- Reply-start policy evaluation → screen_watcher 的 "cooling" 机制可在旧截图标记为 low-ambiguity 时提前解除

## 参考文献
- Paper: https://arxiv.org/abs/2605.16024
- 相关: PUCT (Predictor + UCT) bandit algorithm
- 相关: UIA (UI Automation) framework for Windows desktop
