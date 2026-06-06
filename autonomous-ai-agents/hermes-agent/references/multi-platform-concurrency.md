# Multi-Platform Concurrency & Model Sharing

## The Phenomenon

When the Hermes gateway connects to **multiple messaging platforms simultaneously** (e.g., Telegram + QQBot + Feishu), messages on different platforms arrive concurrently. If they all route to the **same model/provider**, the gateway processes them **in parallel** — but the model has bounded concurrency, causing slower individual response times.

**This is working as designed, NOT a bug.** Each platform's session runs its own agent loop independently.

## Observed Behavior (2026-06-04)

| Time | Platform | Session | Event |
|------|----------|---------|-------|
| 00:35:58 | Telegram | 20260604_003443 | Message received |
| 00:36:05 | QQBot | 20260604_003537 | API call #1 (5.9s) |
| 00:36:10 | Telegram | 20260604_003443 | API call #4 (6.1s, 95% cache) |
| 00:36:13 | QQBot | 20260604_003537 | terminal tool (8.47s) |
| 00:36:16 | Telegram | 20260604_003443 | Response ready |

Two sessions (Telegram + QQBot) both using `MiniMax-M2.7` via `minimax-cn` competed for inference slots. The Telegram user perceived ~18s delay because QQBot was simultaneously consuming model capacity.

## Key Insight

The gateway is a **shared inference router**. When multiple platforms receive messages simultaneously:
1. Each platform starts its own `agent.run_conversation()` loop
2. Both loops call the same model endpoint (`minimax-cn`)
3. The model provider handles concurrent requests (bounded by its own concurrency limits)
4. Individual response times increase proportionally to concurrency level

## Mitigations

### 1. Use Different Providers per Platform (理想的)
Assign different platforms to different model providers:
- Telegram → `minimax-cn` (MiniMax-M2.7)
- QQBot → `openrouter` (nemotron-3-super-120b)

This eliminates provider-level contention.

### 2. Model-Level Fallback Chain
Configure `fallback_providers` with models on different endpoints:
```yaml
fallback_providers:
  - provider: minimax-cn
    model: MiniMax-M2.7
  - provider: openrouter
    model: nvidia/nemotron-3-super-120b-a12b
```

### 3. Reduce Concurrency
Limit the number of platforms running simultaneously, or add a message queue to serialize requests to the same model.

### 4. Monitor with `hermes status --all`
Shows all platform connections and active sessions.

## Log Patterns to Recognize

When diagnosing "slowness" across platforms, grep for concurrent sessions:

```bash
grep "inbound message" ~/.hermes/logs/gateway.log | tail -20
grep "response ready" ~/.hermes/logs/gateway.log | tail -10
grep "api_call #" ~/.hermes/logs/agent.log | grep -E "session_id|TIME"
```

Look for multiple `conversation_loop` entries with different `session=` values but the same `model=` and `provider=` — that's concurrent inference on the same model.

## Remember

- **Parallel platform sessions ≠ parallel model inference guarantee**
- When in doubt: `hermes platforms` (or `/platforms` in gateway chat) shows all connected platforms
- The gateway log's `response ready` line shows `time=Ns` — if N is high, check if other sessions were running concurrently
