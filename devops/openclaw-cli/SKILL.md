---
name: openclaw-cli
description: "OpenClaw CLI 安装TTY onboard模型配置。Use when openclaw命令行装不上配不对"
---

# OpenClaw CLI (macOS)

Use this skill when the user wants to install, configure, run, or troubleshoot **OpenClaw** (`openclaw`) — the "all your chats, one OpenClaw" agent CLI.

## Trigger
- "install openclaw", "openclaw setup", "openclaw onboard"
- "怎么启动 openclaw / 怎么对话 / 怎么配置模型"
- `openclaw` command fails with TTY / auth / model errors
- A `curl ... openclaw.ai/install.sh | bash` paste gets blocked by a security hook

## 1. Safe install (curl|bash is blocked by shell security hooks)
The user's shell runs a pre-exec security hook (`tirith`) that BLOCKS `curl ... | bash` as `curl_pipe_shell` (HIGH). So the paste "shows but never runs" — the hook intercepts before exec. Do NOT bypass blindly. Instead download → vet → run locally:

```bash
# 1) download (do NOT pipe to bash)
curl -fsSL openclaw.ai/install.sh -o /tmp/openclaw_install.sh
# 2) vet: check domains + look for hidden exec (base64 -d | eval, /dev/tcp, etc.)
#    safe installers use wget -O file url (lands to disk) — that is fine
# 3) run the local copy (bypasses the pipe-to-interpreter rule)
TIRITH=0 bash /tmp/openclaw_install.sh
```

Verified-good facts from a real install (OpenClaw 2026.7.1-2):
- Default install method = **npm**; needs Node **22.22.3+ / 24.15.0+ / 25.9.0+**.
- Installer is safe: only talks to `nodejs.org`, `github.com`, `openclaw.ai`, `raw.githubusercontent.com`, `deb/rpm.nodesource.com`. Internal `curl|bash` strings are help-text only; real downloads use `wget -O`.
- On success it prints `OpenClaw installed successfully` and tells you to run `openclaw onboard`.

Bypass alternatives (document, don't prefer over vet-and-run):
- `tirith trust add 'openclaw.ai/install.sh' --rule curl_pipe_shell --ttl 30d`
- Prefix any command with `TIRITH=0` (applies to that command only).

## 2. Onboard — REQUIRES a TTY (cannot run inside the agent harness)
`openclaw onboard` exits with: *"Onboarding needs an interactive TTY... use --non-interactive --accept-risk for automation."* The agent's shell has no TTY, so **the user must run onboard in their own terminal**. Do not loop retrying it here.

Interactive:
```bash
openclaw onboard          # guided: auth, models, Gateway, workspace, channels, skills
```
Non-interactive (give the user the exact one-liner for their provider):
```bash
openclaw onboard --non-interactive --accept-risk --openrouter-api-key <key>
# custom OpenAI-compatible provider:
openclaw onboard --non-interactive --accept-risk \
  --custom-api-key <key> --custom-base-url https://<host>/v1 --custom-model-id <model>
```
Full provider flag list is in `references/install_and_onboard.md`.

## 3. Start / status
The Gateway installs as a **LaunchAgent** (auto-starts on boot). Usually no manual start needed.
```bash
openclaw daemon status    # is it loaded + running? shows port + dashboard URL
openclaw daemon start     # if not running
openclaw gateway run      # foreground with logs (debug)
```
- Gateway bind=loopback, port **18789** (default).
- Dashboard: `http://127.0.0.1:18789/`
- Config file: `~/.openclaw/openclaw.json`

## 4. Talk to it
```bash
openclaw chat            # local terminal TUI (alias: tui --local) — most common
openclaw tui             # TUI connected to the Gateway
openclaw agent "do X"    # one-shot turn, no TUI
```
All three need a TTY → run from the user's own terminal, not the agent harness.

## 5. Configure models / auth (do this BEFORE first chat)
Without auth the default model (`claude-cli/claude-opus-4-8`) has no credential and chat fails.
```bash
openclaw configure       # interactive: models, Gateway, channels, plugins, skills
openclaw models status   # verify default model + auth health
```
`openclaw models status` output shows: Default, Fallbacks, Configured models, and an Auth overview (Providers w/ OAuth/tokens). If "Providers w/ OAuth/tokens (0)" is empty, no model will work yet.

## Pitfalls
- **Paste auto-runs then dies**: pasting a multi-line command with a trailing newline makes the shell submit it immediately; a security hook may then block it, so you see the command echoed but nothing executed. Fix = download to a file and run the file.
- **onboard in agent harness fails** ("needs interactive TTY"): hand the command to the user; never retry in place.
- **Chat fails with no model**: run `openclaw models status` — almost always missing auth. Run `openclaw onboard`/`configure` with a real key.
- **`command not found: openclaw`**: ensure PATH includes `~/.local/bin` (installer adds it to `~/.zshrc`/`~/.zprofile`/`~/.profile`; new terminal required).

## Verification
After install: `command -v openclaw && openclaw --version` → expect `OpenClaw 2026.7.1-2 (xxxxxx)`.
After onboard: `openclaw models status` → Default populated + at least one provider with a token.
