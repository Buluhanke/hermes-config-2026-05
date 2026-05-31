# Production Snapshot — 2026-06-01 07:16

## System Health

| Component | Status | Details |
|-----------|--------|---------|
| screen_watcher | ✅ PID 48245 | Live since 07:06 |
| current.png | ✅ 3.3 MB | Updated 07:16 |
| Ollama service | ✅ PID 98043 | Running since 00:07 |
| qwen3-vl:2b | ✅ 1.76 GB | Scene classification model |
| qwen2.5:1.5b | ✅ 0.92 GB | General text model |
| YOLO ScreenParser | ✅ 28 detections today | All idle→silent, 93ms avg |
| Handler lock | ✅ No residue | — |
| DRY_RUN total | 967 | Up from 747 (R3 snapshot) |

## YOLO Pre-classification Performance (Layer 1)

- **Total idle detections**: 28 (all on June 1, starting ~07:12)
- **Accuracy**: 100% (all 28 correctly identified idle/1-element screens)
- **Speed**: ~91ms @ 320px CPU (ultralytics 8.4.57)
- **Impact**: Saves ~7-8s per idle detection cycle (YOLO 93ms vs full VLM ~8s)

## Scene Distribution (June 1 only — date-separated)

| Scene | Count | Note |
|-------|-------|------|
| other | 369 | 28 caught by YOLO pre-classification |
| unknown | 2 | 0.54% — historic low |
| desktop | 1 | — |
| browser | 1 | — |

**No 1688/wechat/dingtalk/telegram/calculator scenes** detected on June 1 (idle period).

## Gateway Hook Pollution

```
screen_watch count: 1916
Growth since last check (~149): ~21/day
Trend: Slow, manageable. No gateway restart needed.
```

## Memory Snapshot

| Metric | Value |
|--------|-------|
| Ollama runtime memory | ~2.7 GB (qwen3-vl:2b, context=4096) |
| YOLO model | ~146 MB (lazy-loaded in handler) |
| System idle | ~13 GB+ estimated |
| Total model footprint | ~4.4 GB (qwen3-vl:2b + qwen2.5:1.5b + YOLO) |

## Key Findings

1. **Two-layer classifier stable in production**: YOLO (93ms) → qwen3-vl:2b (~3s) → ask_screen (~5s)
2. **Idle scenarios fully optimized**: 44x faster with YOLO pre-screen
3. **Qwen3.5:2b not needed**: Current setup meets all production requirements
4. **LocateAnything-3B skipped**: 7.8GB, no Ollama support, low ROI for M4 24GB
5. **Gateway hook pollution**: Tracking at 1916, slow growth, no action required
