# GUIDE Benchmark — CVPR 2026

**Paper**: GUIDE: A Benchmark for Understanding and Assisting Users in Open-Ended GUI Tasks
**arXiv**: 2603.25864 | **Website**: https://guide-bench.github.io/

## Dataset
- 67.5 hours screen recordings + think-aloud narrations
- 120 novice users, 10 applications
- Photo Editing: Photoshop, GIMP
- Graphic Design: Figma, Canva
- Presentation: PowerPoint, Google Slides
- Video Editing: Premiere Pro, CapCut
- Data Analysis: Google Sheets, Microsoft Excel

## Three-Task Framework

### Task 1: Behavior State Detection
Classify video segment into one of 9 behavior states.

**4-Phase Taxonomy**:
| Planning | Execution | Problem-Solving | Evaluation |
|----------|-----------|-----------------|------------|
| Task Understanding & Preparation | Exploration & Decision-Making | Frustration | Waiting & Monitoring |
| Ideation & Planning | Performing Actions | Debugging | Assessment |
| Seeking External Help | | | |

### Task 2: Intent Prediction
4-way multiple choice — infer user's immediate short-term goal.

### Task 3: Help Prediction
- (3-1) Help Need: binary — does user need help?
- (3-2) Help Content: 4-way MCQ — what kind of help is appropriate?

## Full Benchmark Results

| Model | Behavior Detection | Intent Pred (+Behv) | Help Need (+Behv) | Help Content (+Behv+Intent) |
|-------|-------------------|---------------------|--------------------|------------------------------|
| Claude-4.5-Sonnet | **44.61%** | 72.62% | 59.43% | **82.79%** |
| Gemini-2.5-Pro | 42.44% | 70.16% | **84.73%** | 79.69% |
| GPT-4o | 36.32% | 62.58% | 87.91% | 79.78% |
| Qwen3-VL-8B | 37.97% | 64.03% | 77.36% | 80.11% |
| Gemini-2.5-Flash | 36.91% | 66.77% | 78.07% | 78.59% |
| GPT-4o-mini | 17.65% | 62.19% | 82.26% | 79.84% |
| InternVideo2.5-8B | 21.57% | 45.13% | 35.35% | 73.86% |
| InternVL3-8B | 22.57% | 46.97% | 43.73% | 72.97% |

**+Behv** = with behavior context provided
**+Behv+Intent** = with both behavior and intent context

## Key Finding: Structured Context is the Catalyst

Without context, models achieve ~44.6% (behavior detection) and ~55% (help prediction).
With structured context (behavior + intent), performance jumps dramatically:

- **GPT-4o**: Help Content 45.95% → 87.91% (**+42pp**)
- **Gemini-2.5-Pro**: Help Content 52.74% → 84.73% (**+32pp**)
- **Claude-4.5-Sonnet**: Behavior Detection 44.61% → 45.63% (+1pp, already strong)

**Core insight**: The bottleneck is NOT model capability — it's the lack of structured user context.

## Actionable Insights for Hermes auto_execute

### 1. Confusion/Frustration Detection = Highest Priority
Frustration detection is harder than intent prediction, but more valuable:
- Current Hermes only does scene classification (browser/wechat/...)
- Does NOT detect if user is stuck
- **Action**: Add `confusion_score` to screen_trigger_handler based on:
  - Operation frequency sudden drop
  - Repeated clicks in same region
  - Mouse inactivity duration

### 2. Structured Context Must Be Built-In
Don't just pass screenshot — pass "what the user is doing":
- Current: prompt only contains scene type
- **Should add**: last operation timestamp, mouse idle duration, consecutive error count

### 3. "Waiting & Monitoring" State Is Valuable
Waiting states (rendering, uploading) should NOT trigger auto_execute:
- **Detection**: 3+ consecutive frames with >95% similarity + low operation frequency

### 4. Qwen3-VL-8B Real-World Data
- ScreenSpot: ~94.4%
- GUIDE Intent Prediction: 64.03%
- GUIDE Help Content: 80.11%
- Comparable to Claude-4.5-Sonnet (44.61% / 82.79%)
