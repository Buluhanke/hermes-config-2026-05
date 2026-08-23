# OpenClaw install & onboard reference

## Install script safety verdict (OpenClaw 2026.7.1-2)
- Safe. Real downloads use `wget -O <file> <url>` (lands to disk, not piped to shell).
- The many `curl ... | bash` strings in the script are HELP TEXT only (Usage/Examples sections).
- External domains contacted: `nodejs.org`, `github.com`, `openclaw.ai`, `raw.githubusercontent.com`, `deb.nodesource.com`, `rpm.nodesource.com`.
- No `base64 -d | eval`, no `/dev/tcp/`, no hidden remote exec.
- `rm -rf` appears only in `cleanup_tmpfiles()` removing mktemp temp files on EXIT/INT/TERM traps.
- Needs Node 22.22.3+ / 24.15.0+ / 25.9.0+. Install method default = npm.

## onboard auth-choice values (provider selection)
```
custom-api-key  skip  claude-cli  apiKey  anthropic-cli  setup-token
arceeai-api-key  byteplus-api-key  cerebras-api-key  chutes  chutes-api-key
clawrouter-api-key  cloudflare-ai-gateway  cohere-api-key  copilot-proxy
deepinfra-api-key  deepseek-api-key  featherless-api-key  fireworks-api-key
google-gemini-cli  github-copilot  gmi-api-key  gemini-api-key  google-vertex
groq-api-key  huggingface-api-key  kilocode-api-key  kimi-code-api-key  litellm
lmstudio  longcat-api-key  meta-api-key  microsoft-foundry  minimax-cn  minimax-global
mistral-api-key  moonshot-api-key  novita-api-key  nvidia-api-key  ollama  ollama-cloud
openai  openai-device-code  opencode-go  opencode-zen  openrouter  openrouter-oauth
qianfan-api-key  qwen-oauth  qwen-standard-api-key  sglang  stepfun  synthetic-api-key
together-api-key  venice-api-key  vllm  volcengine-api-key  xai  xai-device-code
xiaomi-api-key  zai  zai-cn  zai-coding  zai-global  tokenhub  tokenplan
```

## Common non-interactive onboard one-liners
```bash
# OpenRouter
openclaw onboard --non-interactive --accept-risk --openrouter-api-key <key>

# DeepSeek
openclaw onboard --non-interactive --accept-risk --deepseek-api-key <key>

# OpenAI
openclaw onboard --non-interactive --accept-risk --openai-api-key <key>

# Gemini
openclaw onboard --non-interactive --accept-risk --gemini-api-key <key>

# NVIDIA NIM
openclaw onboard --non-interactive --accept-risk --nvidia-api-key <key>

# Custom OpenAI-compatible provider
openclaw onboard --non-interactive --accept-risk \
  --custom-api-key <key> --custom-base-url https://<host>/v1 --custom-model-id <model>
```

## Flow / auth flags
- `--flow quickstart|advanced|manual|import`
- `--auth-choice <value>` (from list above)
- `--gateway-auth token|password`, `--gateway-bind loopback|tailnet|lan|auto|custom`
- `--gateway-port <port>`, `--gateway-token <token>`, `--gateway-password <password>`

## Post-install verification
```bash
command -v openclaw && openclaw --version   # OpenClaw 2026.7.1-2 (xxxxxx)
openclaw daemon status                       # running, port 18789
openclaw models status                        # Default set + >=1 provider with token
```
