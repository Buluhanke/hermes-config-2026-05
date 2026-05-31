# Idle Learning 2026-06-01 Session — Direction B (Understanding)

## Trigger
Cron job (03:36 CST), idle_learning skill

## System State Snapshot
- screen_watcher: PID 8748, running since 01:27
- Ollama: qwen3-vl:2b (1.76GB) + qwen2.5:1.5b (0.92GB), stable
- Screenshot: 3.37MB, real-time
- Dry-run: 777 records, all `other` → [silent] (negation detection working)
- github: ✅ RECOVERED (was blocked for weeks)
- HN: ❌ blocked (stable)
- Firebase: ✅ 200

## GitHub Recovery Impact
This was the first session where github.com was accessible. We verified:
- https://github.com/fzkuji/GUI-Agent-Harness — 32 stars, 542 commits, active (5hr ago)
- https://github.com/QwenLM/Qwen-VLA — 258 stars, 9 forks, 38 commits
- https://github.com/Mininglamp-AI/Mano-P — 2.2k stars, 213 forks, Apache-2.0
- https://huggingface.co/nvidia/LocateAnything-3B — 571 likes, 3B params (GitHub 404)
- https://huggingface.co/docling-project/ScreenParser — YOLO11-L, 55 UI classes, Apache-2.0

## Key Findings

### 1. Mano-P — #1 OSWorld Specialized (58.2%)
- GitHub live at Mininglamp-AI/Mano-P
- 2.2k stars, 213 forks, Apache-2.0
- Requires **32GB RAM minimum** (M4 24GB can't run locally)
- Think-Act-Verify loop confirms auto_execute direction
- Cider SDK INT8 acceleration for Apple Silicon
- More info: references/mano-p-2026-05-31.md

### 2. Qwen-VLA — VLA Architecture Validation
- GitHub: QwenLM/Qwen-VLA (258 stars)
- Qwen3.5-4B + 1.15B DiT decoder (~5.15B total)
- Q4 quantization ~4GB, M4 24GB possible
- More info: references/qwen-vla-2026-06-01.md

### 3. GUI-Agent-Harness — Has Verify Phase auto_execute is missing
- Fzkuji/GUI-Agent-Harness, 32 stars, 542 commits
- 4-phase loop: Observe → Verify → Plan → Dispatch
- macOS-first (Apple Vision OCR + pynput + AX API)
- Visual Memory cache (~5x faster, ~60x fewer tokens)
- More info: references/gui-agent-harness-2026-06-01.md

### 4. LocateAnything-3B — PBD Coordinate Decoding
- HuggingFace: nvidia/LocateAnything-3B (571 likes)
- 3B params, M4 24GB capable
- PBD (Parallel Box Decoding) = single-step bbox, no token-by-token
- vLLM + Transformers deployment
- More info: references/locateanything-3b-2026-06-07.md

### 5. ScreenParser — YOLO11-L Fast UI Detector
- HuggingFace: docling-project/ScreenParser (1 like, very new)
- YOLO("docling-project/ScreenParser") via ultralytics
- Apache-2.0, IBM Research - ETH Zurich
- Millisecond inference, 55 UI classes at 1280px

## Upstream Skill Patches Applied
1. Network pre-check: added github:ok path + browser_navigate suggestion
2. Mano-P: updated from "blocked" to "accessible, 32GB required"
3. ScreenParser: HF status from "unstable" to "verified accessible"
4. LocateAnything-3B: corrected repo location (HF only, GitHub 404)
5. FastVLM: removed "github blocked" assumption

## Next Direction
C — Decision layer: DRY_RUN=False 6-condition assessment + ScreenParser YOLO local test
