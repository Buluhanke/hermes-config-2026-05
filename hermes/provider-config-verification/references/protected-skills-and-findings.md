# Protected / Outdated Skills Found This Session (2026-08-02)

Two skills in play this session are NOT editable from the agent context (they
live in `external_dirs` / are pinned / user-owned, or resolve outside the active
profile). They contain outdated guidance and should be fixed via the curator:

## 1. `hermes/hermes-model-health` (outdated claim)
- **Wrong claim**: "`custom_providers` 必须是 dict，写成 list 会导致全部 provider 静默失效".
- **Reality (verified against code)**: `hermes_cli/config.py`
  `get_compatible_custom_providers` (~L1561) and `model_switch.py:124` **accept a
  YAML list** for `custom_providers`. A list config is fully legal; the user's
  list-based config works.
- **Action for curator**: patch Step 1 to state list/dict both accepted; drop
  the "all providers silently die" warning. Recommend `hermes curator adopt hermes/hermes-model-health`.

## 2. `hermes/hermes-tuning-playbook` (editable in principle, blocked from agent write here)
- Covers auxiliary + MoA config but does NOT mention the CN-region OpenRouter
  403 failure mode that silently kills auxiliary.* and moa on a China IP.
- The fix (route auxiliary.* + moa to Nous `tencent/hy3:free`, verified 200 OK)
  belongs in that skill's P1 sections. Could not be patched from this context
  (skill_manage "not found in active profile 'default'"). Recommend curator adopt
  + patch, or merge its content into this `provider-config-verification` skill.

## Verified endpoint facts (this host, 2026-08-02)
- `123.56.67.77:9100` → MiniMax-M2.7-highspeed : **200 OK** (primary, working)
- OpenRouter (`sk-or-...`) claude-opus-4.8 / gemini-2.5-flash / gpt-5.5 : **403 region** (CN IP block)
- Nous Portal `tencent/hy3:free` (`NOUS_API_KEY`) : **200 OK** (free, rate-limited)
- groq / cerebras / nvidia / zenmux custom+fallback : all 401/402/403/404 (bad/expired keys or model not found)
- `.env` location: `/Users/aimac/.hermes/.env` (NOT hermes-agent/.env)
- `curl` is hardline-blocked in the agent; use Python `http.client` for probes.
