# Fallback Chain Config — Notes

## Status (2026-06-06)
**No active fallback chain.** Primary model: `MiniMax-M2.7-highspeed` via `minimax-cn` provider (direct).

## Cleanup (2026-06-06)
Old `model.fallback_chain` referenced unregistered providers (`nv-nemotron-3-super`, `nv-deepseek-v4-flash`, `or-deepseek-chat-v3`), generating 20+ `provider not configured` warnings/day.

**Fixed via:**
```bash
hermes config set model.fallback_chain ''
hermes gateway restart
```

## Legacy Config (Archived — no longer in use)
v2.aicodee.com relay was removed on 2026-06-02 due to 429 rate limits. All scripts now point to `https://api.minimaxi.com/v1` directly.

> This file is archived reference only. Current config is in `~/.hermes/config.yaml`.
