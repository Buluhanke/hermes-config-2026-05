# 2026-06-01 Idle Learning Session (Direction A — Vision)

## Summary

- Fixed ACTION_WHITELIST flatness: idle scenes → "none", active scenes → "wininfo"
- Verified PaddleOCR-VL pip availability (`from paddleocr import PaddleOCRVL`)
- Read Codersera Apple Silicon guide (May 2026, MLX won on Mac, Ollama 0.19+ uses MLX)
- Read Datature Gemma 4 Computer Vision guide (native bbox output, OCR, video understanding)
- HN top stories: Cloudflare Turnstile WebGL, Creatine Alzheimer's, The Website Specification, Dav2d

## ACTION_WHITELIST Fix Details

### Before (flat, all scenes → wininfo)
- 9 scenes all mapped to `("wininfo", None)`
- 99% of June 1 drry-run logs were idle scenes writing redundant "Would execute: wininfo"

### After (semantic separation)
- Active: browser, wechat, 1688, dingtalk, telegram → `("wininfo", None)`
- Idle: other, unknown, desktop, calculator → `("none", None)`

### Production data
- June 1 02:50 fix applied
- 141/142 dry-run records (99%) from idle scenes eliminated going forward
- Only 1 browser scene worth logging on June 1

## System Health

| Component | Status |
|-----------|--------|
| screen_watcher | PID 8748 ✅ running |
| Screenshot freshness | 02:51 (2 min ago) ✅ |
| Ollama | qwen3-vl:2b + qwen2.5:1.5b ✅ |
| Dry-run total | 735 records |
| June 1 unknown | 0% ✅ |
| Network | github:ok, hn:ok ✅ |

## Direction A — Key Findings

### Gemma 4 E4B for screen_watcher
- 5.5GB at Q4, `ollama pull gemma4:e4b` available
- inline OCR + bounding box output would be useful for "other" scene text extraction
- **Decision**: not installing now — current qwen3-vl:2b is sufficient (0% unknown on June 1)
- If OCR needed, PaddleOCR-VL (pip available, no download) is the more lightweight path

### PaddleOCR-VL
- Confirm: `from paddleocr import PaddleOCRVL` works ✅
- PaddleOCR v3.6.0 ships with it
- Could be integrated into handler for text extraction from "other" scenes

### MLX Advantage
- Ollama 0.19+ uses MLX backend on Apple Silicon automatically
- 30-40% faster than llama.cpp Metal backend
- Our existing setup already benefits from this — no action needed

### InsiderLLM May 2026
- 24GB pick: Qwen 3.6-27B dense Q4_K_M (16.8GB, 18-28 tok/s) "tight but doable"
- Gemma 4 E4B (5.5GB, 57 tok/s) "safe choice"
- Vision models: qwen3-vl:2b remains best small vision model for M4 24GB

## Next Direction
Direction B — 理解层（GUI grounding 最新进展：ScreenParse v2 方法论落地、LocateAnything-3B、TRISHUL）
