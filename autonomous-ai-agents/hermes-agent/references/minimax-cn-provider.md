# MiniMax-CN Provider: Debugging Session (2026-05-16)

## Problem
Switching to MiniMax-M2.7 via minimax-cn provider kept failing with `HTTP 404 — 404 Not Found` from nginx at `https://api.minimaxi.com`.

## Root Cause
Two issues:

### 1. Wrong base_url (primary cause)
`https://api.minimaxi.com` is the **bare** API server root — it returns nginx 404.
The Anthropic-compatible endpoint requires the `/anthropic` path:
- **China domestic**: `https://api.minimaxi.com/anthropic` (note: `minimaxi.com`, NOT `minimax.io`)
- **International**: `https://api.minimax.io/anthropic`

Full API call path: `{base_url}/v1/messages` → `https://api.minimaxi.com/anthropic/v1/messages` (returns 200)

### 2. .env override (silent failure)
The `.env` file had `MINIMAX_CN_BASE_URL=https://api.minimaxi.com` which silently **overrides** the `model.base_url` in `config.yaml`. Even after fixing config.yaml, the `.env` kept feeding the wrong URL.

**Fix**: Update BOTH files:
- `config.yaml`: `model.base_url: https://api.minimaxi.com/anthropic`
- `.env`: `MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic`

## Verification
`curl -s -o /dev/null -w "%{http_code}" "https://api.minimaxi.com/anthropic/v1/messages" -H "x-api-key: YOUR_API_KEY-..." -H "anthropic-version: 2023-06-01" -H "Content-Type: application/json" -d '{"model":"MiniMax-M2.7","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'`

Returns `200` when both config.yaml and .env are correct.

## User Preference
- When user says "switch to X model", DO IT directly — no analysis, no options, no confirmation questions.
- The user is extremely brief and wants action, not discussion.
