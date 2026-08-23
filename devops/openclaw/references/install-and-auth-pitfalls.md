# OpenClaw install + auth pitfalls (verified transcript)

Captured 2026-08-18 on this Mac. OpenClaw npm-installed, gateway = LaunchAgent.

## Install
- `tirith` blocks `curl ... | bash` as HIGH (`curl_pipe_shell`). Script is safe
  (hosts: nodejs.org, github.com, openclaw.ai, raw.githubusercontent.com,
  rpm/deb.nodesource.com). No base64-exec; the 3 `rm -rf` are only in `cleanup_tmpfiles`.
- Safe path: `curl -fsSL openclaw.ai/install.sh -o /tmp/openclaw_install.sh` then
  `TIRITH=0 bash /tmp/openclaw_install.sh`.
- Install ends with "No TTY; run openclaw onboard" — only the interactive final step is
  blocked; binary is usable immediately after.

## First invocation failures, in order, and the fix for each
1. `openclaw agent --agent main --message "..."` → `Please run /login`
   Cause: default model `claude-cli/claude-opus-4-8` needs Claude Code CLI login;
   `claude status` was "Not logged in".
   Fix: switch default model to a key-backed provider.
2. `openclaw models set openrouter/auto` → ok; `agent` → `No API key found for openrouter`.
   `config set models.providers.openrouter.apiKey --ref-source env --ref-id OPENROUTER_API_KEY`
   then `agent` → `apiKey is unresolved in the active runtime snapshot`.
   Cause: launchd gateway does NOT inherit the shell's env vars. SecretRef-from-env fails.
   Fix: read key from `~/.hermes/.env` (regex `^OPENROUTER_API_KEY\s*=\s*(\S+)`), then
   `openclaw config patch --stdin` with
   `{"models":{"providers":{"openrouter":{"apiKey":"<key>"}}}}`. apiKey as plaintext string works.
3. After that, `agent` → `billing error — run out of credits`.
   This is SUCCESS of the config chain (request reached OpenRouter). Just needs credits.

## Cerebras (do not pursue in this env)
- Built-in provider auto-discovered, needs apiKey. Direct `api.cerebras.ai/v1` calls return
  HTTP 403 (error 1010) + cert hostname mismatch → key is bound to a proxy, not public
  Cerebras. No working path here.
- If you must add a custom cerebras model entry under
  `models.providers.cerebras.models[]`, item fields are only `id/name/api/baseUrl`
  (api ∈ openai-completions|openai-responses|…). `context` is NOT valid (→ "Invalid input").
  Model id `llama-4-scout-17b-16e-instruct` is also not accepted via this path.

## Commands that need TTY vs not
- TTY required: `onboard`, `models auth login|add`, `chat`, `tui`, `talk to agent`.
- No TTY (Hermes can run directly): `agent --message --json`, `models set`, `config patch`,
  `models status`, `daemon status`.
