---
name: deepseek-harness
description: "DeepSeek Harness dsh CLI安装配置Web UI。Use when 安装配置dsh命令行"
trigger: install DeepSeek Harness / configure dsh model / dsh web / wire OpenRouter into dsh / DeepSeek Harness Socket / everything is a plugin harness
---

# DeepSeek Harness (`dsh`)

DeepSeek Harness is DeepSeek AI's agent harness (MIT, developer preview, released 2026-08-13). Runtime is Node.js. The CLI is `dsh`. Architecture: "everything is a plugin" on the Cordis runtime. LLM models, tools, skills, and even other agents (Codex/Claude Code) are interchangeable plugins.

## Install
Requires Node.js ^22.19.0 or >=24 (verified on v22.23.1). pnpm only needed for source builds.

```sh
npm install -g @deepseek-ai/dsh
# one-shot alternative (slower, re-resolves each run): npx -y @deepseek-ai/dsh web
dsh --version   # -> 0.1.0-rc.7
```

PREFER GLOBAL over `npx`. `npx ... web` re-resolves the 531-dep tree every launch and a long-lived server launched under `npx` can get SIGTERM'd if the parent shell is interrupted mid-resolution. Global install puts the bin at `~/.local/bin/dsh`.

## Launch the Web UI
```sh
cd ~/DeepSeekProjects && dsh web
# serves http://127.0.0.1:3080  (loopback only — answers on your machine, nowhere else)
```
Long-lived server (daemon). Launch in background; verify with `curl -sI --max-time 6 http://127.0.0.1:3080` (expect `HTTP/1.1 200`). Open the URL in a browser to use the UI. First launch shows a preview notice; click through.

## Config layout (the part that bites)
Profiles live at `~/.dsh/profiles/<profile>/` (NOT `~/.config/deepseek-harness` — that dir stays near-empty; the real profile store is `~/.dsh`):
- `cordis.yml` — auto-generated empty root. DO NOT EDIT.
- `cordis.patch.yml` — YOUR patch layer. Edit this.
- `package.json`, `pnpm-workspace.yaml` — bundle metadata.

Each profile (`web`, `headless`, ...) has its OWN `cordis.patch.yml`. Patching only `web` does NOT change `headless`. Apply the same patch to every profile you intend to use.

## Wiring a model provider — the pi-ai adapter
The LLM seam has two adapters:
- `dsh-llm` — core service, patch id `llm`
- `dsh-llm-pi-ai` — generic multi-provider adapter, patch id `llm-pi-ai`

To add an OpenAI-compatible endpoint (OpenRouter, NVIDIA NIM, a self-hosted server), patch the **`llm-pi-ai`** plugin.

### PITFALL (cost a restart to learn)
A patch entry with `id: llm` targets the core service and silently fails to load your `providers` block — `dsh --profile web --dump-config` will show `llm-pi-ai` with no `config.providers`. Use `id: llm-pi-ai` and `name: '@deepseek-ai/dsh-llm-pi-ai'`.

### Hand-declared route shape
```yaml
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
```
Secrets are read from the env var named by `apiKeyEnv` AT REQUEST TIME — never stored in the file. Export the key before launching `dsh`:
```sh
export OPENROUTER_API_KEY=<key>; dsh web
```

### Make it the default model
```yaml
- id: agent-default-model
  name: '@deepseek-ai/dsh-agent-default-model'
  config:
    provider: openrouter
    model: deepseek/deepseek-chat
```

### Verify the patch loaded
```sh
dsh --profile web --dump-config | grep -iA4 "llm-pi-ai"
# expect: - id: llm-pi-ai / name: ... / config: / providers: / openrouter:
```
RESTART `dsh web` after editing the patch — the UI reads patches only at startup. A refresh of the browser tab is NOT enough.

## Dead official DeepSeek key workaround
If `DEEPSEEK_API_KEY` returns `{"error":{"message":"Authentication Fails...invalid"}}`, the default `deepseek-official` route fails with `MISSING_CREDENTIAL`/auth error. Route DeepSeek models through a working OpenAI-compatible provider instead:
- OpenRouter: `deepseek/deepseek-chat` confirmed working 2026-08-19 (real completion returned).
- NVIDIA NIM: lists `deepseek-ai/deepseek-v4-flash-0731` but returned `529 Service temporarily overloaded` that day — flaky, don't rely on it.
Do NOT bother debugging the dead official key; just repoint via the pi-ai route above.

## Socket.dev protection (standing user instruction)
User requires Socket to protect the dsh install/execution.
```sh
npm install -g socket
socket --version   # 1.1.158
```
`socket scan create` and `socket package score` REQUIRE a Socket API token (org-based). Anonymous CLI only shows `--help`. After `socket login`:
```sh
cd ~/.local/lib/node_modules/@deepseek-ai/dsh && socket scan create .
```
CAVEAT: global `npm install -g` writes no lockfile, so `npm audit` errors `ENOLOCK`. To audit, generate a lockfile in a temp dir (slow for 531 deps):
```sh
cd /tmp && mkdir dsh-audit && cd dsh-audit && echo '{"name":"x","version":"1.0.0"}' > package.json && npm install --package-lock-only @deepseek-ai/dsh@0.1.0-rc.7 && npm audit --omit=dev
```

## End-to-end verification
```sh
export OPENROUTER_API_KEY=<key>; dsh --profile headless "Reply with exactly: DSH-OK"
# expect output containing: DSH-OK
```
If it errors `MISSING_CREDENTIAL ... deepseek-official`, the `headless` profile patch is missing — copy the same `cordis.patch.yml` to `~/.dsh/profiles/headless/`.

## Pitfalls summary
1. Patch id must be `llm-pi-ai`, never `llm`.
2. Each profile (`web`, `headless`) has its own patch file — patch all you use.
3. Restart `dsh web` after editing a patch (UI loads patches at startup; browser refresh is insufficient).
4. `dsh web` is a long-lived server — launch background, don't block the foreground on it.
5. Global install has no lockfile → `npm audit` needs a temp lockfile dir.
6. `timeout` is NOT installed on macOS — don't use it; use background + notify or `dsh --profile headless` directly.

## References
- `references/deepseek-harness-config.md` — ready-to-copy `cordis.patch.yml` for both web and headless profiles.
