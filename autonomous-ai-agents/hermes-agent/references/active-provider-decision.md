# Active Provider Decision (2026-05-16)

## The Rule

The user's configured and approved provider is **only** `minimax-cn` (MiniMax China domestic direct API) with model **MiniMax-M2.7**.

## Explicitly Rejected Alternatives

| Provider | Rejected Because |
|---|---|
| `minimax` (global) | User said "你搞错了不是走这个" — not the global API |
| `minimax-oauth` (OAuth/browser login) | User said "不是走这个" — not OAuth flow |
| `deepseek-v4-flash` / any DeepSeek | System auto-switched mid-session; user corrected back immediately |

## How to Revert When Wrong Provider Is Active

If you find yourself on the wrong provider (either by noticing annotations in the conversation header or by user correction):

- **In current session:** tell the user to type `/model MiniMax-M2.7` (in-session slash command)
- **For all new sessions:** ensure `config.yaml` has `model.default: MiniMax-M2.7` and `model.provider: minimax-cn`, then start a fresh `/new` session
- Config changes do NOT affect an already-running session; they only take effect on `/new`

## API Key Prefixes

- `YOUR_API_KEY-*` = MiniMax native key (used with minimax-cn)
- `YOUR_API_KEY...` = aicodee key (NOT for MiniMax endpoints)
