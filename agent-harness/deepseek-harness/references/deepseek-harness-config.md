# DeepSeek Harness — ready-to-use config

Copy this entire file to BOTH `~/.dsh/profiles/web/cordis.patch.yml` AND
`~/.dsh/profiles/headless/cordis.patch.yml` (each profile has its own patch).

It wires OpenRouter as an OpenAI-compatible DeepSeek model source (the machine's
official `DEEPSEEK_API_KEY` was invalid on 2026-08-19) and sets it as the default.

```yaml
# dsh profile patch: wire OpenRouter (OpenAI-compatible) as a DeepSeek model source.
# DeepSeek's own API key on this machine is invalid, so we route DeepSeek models through
# OpenRouter, which serves deepseek/deepseek-chat and deepseek/deepseek-r1. The secret is
# read from the OPENROUTER_API_KEY env var at request time (never stored in this file).
- id: llm-pi-ai
  name: '@deepseek-ai/dsh-llm-pi-ai'
  config:
    providers:
      openrouter:
        displayName: OpenRouter (DeepSeek)
        apiKeyEnv: OPENROUTER_API_KEY
        api: openai-completions
        baseURL: https://openrouter.ai/api/v1
        models:
          - id: deepseek/deepseek-chat
            name: DeepSeek Chat (via OpenRouter)
            contextWindow: 64000
          - id: deepseek/deepseek-r1
            name: DeepSeek R1 (via OpenRouter)
            contextWindow: 64000
# Make the OpenRouter DeepSeek route the default so the harness runs out of the box
# (DeepSeek's official key is invalid on this machine).
- id: agent-default-model
  name: '@deepseek-ai/dsh-agent-default-model'
  config:
    provider: openrouter
    model: deepseek/deepseek-chat
```

## Launch
```sh
cd ~/DeepSeekProjects
export OPENROUTER_API_KEY=$(grep "^OPENROUTER_API_KEY=" ~/.hermes/.env | cut -d= -f2-)
dsh web   # http://127.0.0.1:3080
```

## Verify
```sh
dsh --profile web --dump-config | grep -iA4 "llm-pi-ai"   # expect openrouter: block
curl -sI --max-time 6 http://127.0.0.1:3080               # expect HTTP/1.1 200
export OPENROUTER_API_KEY=<key>; dsh --profile headless "Reply with exactly: DSH-OK"  # expect DSH-OK
```

## Notes
- Official DeepSeek chat API test on 2026-08-19: `Authentication Fails ... invalid`.
- OpenRouter `deepseek/deepseek-chat` returned a real completion the same day.
- NVIDIA NIM `deepseek-ai/deepseek-v4-flash-0731` listed but returned 529 overloaded.
- Socket.dev CLI (`npm i -g socket`) needs `socket login` (API token) before `socket scan create` works.
