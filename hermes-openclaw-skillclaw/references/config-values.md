# Config Values & Token Locations — Hermes + OpenClaw + SkillClaw

## Token / key locations
- Hermes keys (OpenRouter/DeepSeek/Gemini/GLM/ZAI/NVIDIA): `~/.hermes/.env` (names: `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`, `GLM_API_KEY`, `ZAI_API_KEY`, `NVIDIA_API_KEY`). GLM base: `GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`.
- OpenClaw gateway token + url: `~/.openclaw/openclaw.json` (`url: ws://127.0.0.1:18789`, `token` under gateway config). Also used in MCP bridge entry.
- SkillClaw config: `~/.skillclaw/config.yaml`.

## SkillClaw `~/.skillclaw/config.yaml` key fields
```yaml
llm:
  api_base: https://open.bigmodel.cn/api/paas/v4
  api_key: <GLM_API_KEY>
  model_id: glm-4-flash
  provider: openai
sharing:
  backend: local
  local_root: /Users/aimac/.skillclaw/shared
  enabled: true
  session_upload_interval: 30   # <-- correct key; NOT session_upload_interval at top level
session_backend: local
skills:
  skills_dir: /Users/aimac/.hermes/skills
evolve:
  server_url: http://127.0.0.1:8787
```

## Hermes `~/.hermes/config.yaml` mcp_servers block
```yaml
mcp_servers:
  filesystem: {command: mcp-server-filesystem, args: [/], enabled: true}
  github: {command: mcp-server-github, enabled: true}
  memory: {command: mcp-server-memory, enabled: true}
  taibu: '{"type": "streamable_http", "url": "https://mcp.mingai.fun/mcp"}'
  openclaw: '{"command":"openclaw","args":["mcp","serve","--url","ws://127.0.0.1:18789","--token":"<tok>"],"enabled":true}'
```
Note: stringified JSON values (like `taibu`, `openclaw`) are parsed by Hermes. `hermes mcp list/test` crashes on stdio entries (assumes `url` present) — ignore; runtime works.

## LaunchAgent plist shapes (both use `env -i` to avoid PYTHONPATH leak)
`~/Library/LaunchAgents/ai.skillclaw.plist` — runs `env -i HOME=/Users/aimac PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/Users/aimac/.local/bin:/usr/local/bin:/usr/bin:/bin /usr/local/bin/python3.14 -m skillclaw start --daemon`, KeepAlive=true, RunAtLoad=true.

`~/Library/LaunchAgents/ai.skillclaw-evolve.plist` — runs `env -i ... OPENAI_API_KEY=<GLM> OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4 /Library/Frameworks/Python.framework/Versions/3.14/bin/skillclaw-evolve-server --engine workflow --use-skillclaw-config --local-root /Users/aimac/.skillclaw/shared --model glm-4-flash --llm-api-type openai-completions --interval 300 --port 8787`, KeepAlive=true, RunAtLoad=true.

`~/Library/LaunchAgents/ai.hermes.gateway.plist` — `hermes gateway run --replace`, KeepAlive=true. Restart via `kill -9 $(pgrep -f "hermes_cli.main gateway")` (NOT `hermes gateway restart`/`launchctl stop` — those are tool-guarded).

## Commands that work (verified)
- SkillClaw status/stop: `/usr/local/bin/python3.14 -m skillclaw status|stop` (with `env -i PATH=<3.14 bin>`).
- OpenClaw agent test: `openclaw agent --agent main --message "..." --timeout 25 --json`.
- Evolve one cycle: `skillclaw-evolve-server --engine workflow --once --use-skillclaw-config --local-root ~/.skillclaw/shared --model glm-4-flash --llm-api-type openai-completions`.
- Telegram verify: `hermes send -t telegram "ping"` → expects `Sent to telegram home channel`.
- MCP bridge probe: spawn `openclaw mcp serve --url ws://127.0.0.1:18789 --token <tok>`, send JSON-RPC `initialize` then `tools/list` → 9 tools.
