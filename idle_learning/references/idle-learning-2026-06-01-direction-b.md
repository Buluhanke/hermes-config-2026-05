# 2026-06-01 Idle Learning — Direction B: Understanding Layer

## Key Findings

### 1. ScreenParse v2 (ICML 2026)
- **Screenshots**: 1,447,100 (up from v1 771K)
- **UI annotations**: 25,575,213 (up from v1 21M)
- **Pipeline**: Webshot (unchanged)
- **Key**: leaf-element filtering, multiple viewport resolutions

### 2. ScreenParser — YOLO11-Large on ScreenParse v2 (NEW!)
- HuggingFace: docling-project/ScreenParser
- 55 UI element classes at 1280px resolution
- Apache 2.0, IBM Research - ETH Zurich
- Usage: `YOLO("docling-project/ScreenParser")`, `pip install ultralytics` (already v8.4.57)
- ultralytics in hermes venv (Python 3.11), NOT in system Python
- HF download test: `curl: (35) Connection reset` — unstable, deploy when network recovers
- **Value**: ~millisecond inference vs VLM 7-11s for scene classification

### 3. PaddleOCR-VL 0.9B v1.5/v1.6
- **OmniDocBench**: v1.5: **94.5%** (v1.0: 92.6%)
  - vs Qwen2.5-VL-72B: 87.0%, Gemini 2.5 Pro: 88.0%, GPT-4o: 75.0%
- **Ollama**: MedAIBase/PaddleOCR-VL:0.9b (registry API 404, needs verification)
- v1.5 added: text spotting with bbox, seal recog, cross-page table merge, checkbox detection
- v1.6: updated 3 days before June 1
- llama.cpp b8110 merged (Feb 19, 2026)
- Llama.cpp deploy: `llama-server -m GGUF --mmproj MMPROJ -c 20000 --fit off --jinja --chat-template-file`
- **Requires --jinja + --chat-template-file** or the model crashes
- **Value**: fills qwen3-vl:2b OCR gap for screen_watcher text extraction

### 4. GUIDE Benchmark (CVPR 2026) — Full Results
- **Data**: 67.5h screen recordings, 120 novice users, 10 apps
- **Behavior taxonomy (9 classes)**:
  - Planning: Task Understanding, Ideation, Seeking External Help
  - Execution: Exploration/Decision-Making, Performing Actions
  - Problem-Solving: Frustration, Debugging
  - Evaluation: Waiting/Monitoring, Assessment

| Model | Behavior Det (9cls) | Intent Pred (4-MCQ) | Help Need (+full ctx) | Help Content (+full ctx) |
|-------|:------------------:|:-------------------:|:---------------------:|:------------------------:|
| Claude-4.5-Sonnet | **44.61%** | **71.39%** | 59.43% | **82.79%** |
| Gemini-2.5-Pro | 42.44% | 67.80% | **82.38%** | 79.69% |
| Qwen3-VL-8B | 37.97% | 62.70% | 77.36% | 80.11% |
| GPT-4o | 36.32% | 61.19% | **87.91%** | 79.78% |
| Gemini-2.5-Flash | 36.91% | 65.40% | 78.07% | 78.59% |
| GPT-4o-mini | 17.65% | 60.76% | 82.26% | 79.84% |
| InternVideo2.5-8B | 21.57% | 43.79% | 35.25% | 73.86% |
| InternVL3-8B | 22.57% | 46.11% | 46.82% | 72.97% |

**Key insight**: Structured context (behavior + intent) boosts help prediction from 55% to 82.79% (+27.79pp). All models struggle on raw behavior detection (< 45%).

### 5. Health Snapshot
- screen_watcher: PID 8748, screenshot 02:06 today, 692 dry-run records
- Ollama: qwen2.5:1.5b + qwen3-vl:2b, both running
- Network: github/hn blocked, HN Firebase API OK
- Disk: 249 Gi free

## Actionable Improvements
1. ScreenParser YOLO: fast scene classifier for handler (deploy when HF network recovers)
2. PaddleOCR-VL: `ollama pull MedAIBase/PaddleOCR-VL:0.9b` for text extraction (verify registry)
3. GUIDE behavior classification: extend negation fix into 9-class state recognition

## Next Direction
C — Decision making (DRY_RUN=False readiness, AVR routing, Verify phase)
