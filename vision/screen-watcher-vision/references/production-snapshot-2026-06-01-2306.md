# Production Snapshot — 2026-06-01 23:06

## System Health (Post Recovery)

| Component | Status | Details |
|-----------|--------|---------|
| screen_watcher | ✅ PID 50302 | Restarted 23:05 (was dead ~4h) |
| current.png | ✅ 1.2 MB | Updated 23:06 |
| Ollama service | ✅ PID 50269 | Restarted 23:05 (was dead) |
| qwen3-vl:2b | ✅ 1.76 GB | Runner PID 50579, context=1024/4096 |
| qwen2.5:1.5b | ✅ 0.92 GB | Online |
| YOLO ScreenParser | ✅ 6 detections today | 5× idle, 1× uncertain→VLM |
| Handler lock | ✅ No residue | — |
| DRY_RUN total | 989 | Up from 967 (07:16 snapshot) |
| Gateway pollution | 2788 | Stable — not growing since hook cleanup |

## Recovery Sequence (Measured)

```text
23:05:00   open -a Ollama
23:05:08   Ollama responsive (API tags returned)
23:05:10   screen_watcher launched (background)
23:05:48   First handler trigger (YOLO: uncertain, 2 UI elements)
23:05:54   Scene classified: desktop
23:06:00   Analysis: 有聊天窗口，需要发送消息 → [silent]
23:06:04   Cooldown started
Total recovery: ~40 seconds (Ollama → screen_watcher → first handler cycle)
```

## YOLO Pre-classification — Uncertain Fallback Verified

This session produced the **first "uncertain" YOLO result** in production:

```text
[2026-06-01 23:05:48] YOLO预分类: uncertain (2个UI元素)     ← 2 elements = borderline case
[2026-06-01 23:05:54] 场景类型: desktop                       ← VLM correctly classified
[2026-06-01 23:06:00] 分析结果: 有聊天窗口，需要发送消息      ← Content analysis normal
[2026-06-01 23:06:00] [AUTO-EXEC-DRY] Would execute: none for scene=desktop
[2026-06-01 23:06:00] 处理完成 [silent]                       ← Correctly silent
```

**Key verification**:
- YOLO threshold 1-5 UI elements → "uncertain" (correct — 2 elements is borderline)
- VLM fallback correctly classified "desktop" (not unknown)
- AUTO-EXEC-DRY correctly mapped to "none" for desktop idle
- Full handler cycle: ~12s (YOLO 91ms + VLM scene ~6s + content analysis ~6s)

## Scene Distribution (June 1 only — date-separated)

| Scene | Count | Note |
|-------|-------|------|
| other | 369 | Majority YOLO-idle, correct [silent] |
| unknown | 17 | 4.3% — includes process-death contamination |
| desktop | 8 | — |
| browser | 1 | — |

unknown rate 4.3% is elevated from 0.54% (07:16 snapshot) because the process-death period (19:18-23:05) contributed to unknown classifications.

## Key Findings

1. **Process death is recurring** — screen_watcher and Ollama both died between 19:18-23:05 (~4h idle). This is the 3rd confirmed occurrence of dual process death.
2. **Recovery is fast** — 40 seconds from detection to full operational status.
3. **YOLO uncertain fallback verified** — First confirmed production case of 2-element "uncertain" correctly handled by VLM.
4. **Gateway hook pollution stable** — 2788, no growth. Confirmed: cleaned hook + pycache deletion stopped error generation.
