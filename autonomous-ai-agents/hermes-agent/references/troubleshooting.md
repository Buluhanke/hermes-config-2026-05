# Troubleshooting

### Voice not working
1. Check `stt.enabled: true` in config.yaml
2. Verify provider: `pip install faster-whisper` or set API key
3. In gateway: `/restart`. In CLI: exit and relaunch.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes auth` — re-authenticate OAuth providers (or `hermes auth add <provider>`)
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `hermes -s name` (or the skill's own `/<name>` slash command)

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF-8 BOM config, line endings): see `references/windows-quirks.md`.

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

### QQ Bot multi-profile setup
Hermes QQ Bot supports only one account per profile (QQ_APP_ID + QQ_CLIENT_SECRET). To run multiple QQ Bots:
1. `hermes profile create <name>` — creates isolated profile
2. Copy API keys from default `.env` to `~/.hermes/profiles/<name>/.env`
3. Add `QQ_APP_ID` and `QQ_CLIENT_SECRET` to the new profile's `.env`
4. `hermes gateway restart --yes` — loads new profile as independent QQ Bot

### "Reset permissions" / auto-approving everything
See `references/security-privacy.md` — wipe the "Always allow" stores, don't touch yolo mode.

### Stuck or aborted `hermes update`
Diagnose before re-running: a killed update can already be at the new commit while only its completion tail is missing.
```bash
export PATH="/usr/bin:$PATH"   # stale Homebrew git may be x86-only on arm64 ("Bad CPU type"); Apple git is universal
hermes --version                # compare local sha/version against the release tag
hermes update --check
```
- `git ls-remote` exit 128 during `--check` with a valid remote is a PATH problem, not network: the updater shells out to `git` from PATH.
- A detached HEAD (`## HEAD (no branch)`) after a git install is normal — don't check out a branch mid-update.
- A re-run replays every expensive dependency step and can hang again at `Preparing Node dependencies…`; `--no-gateway-restart` does not avoid it. Don't loop more than twice.
- macOS has no `timeout` binary — wrapping the update in it exits 127 without running. Use the terminal tool's own timeout or a background job with notification.
- `Preparing Node dependencies…` hanging is almost always a **stale `.cache/node-deps.lock`**, not a registry outage. Check the network first: `curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" -m 8 https://registry.npmjs.org/` — a 200 in ~1s means the network is fine and the lock is the culprit. The lock file is `{"token":…,"pid":…,"host":…}`; `node-deps.mjs` refreshes its mtime from a heartbeat worker (~1s), treats it stale after 30s, and a waiter gives up after 10 minutes. A SIGKILLed updater leaves the file behind, so each retry freezes until that cap — `--no-gateway-restart` does NOT bypass it.
- A long-lived `npm exec @playwright/mcp@latest` process under the gateway is its normal MCP server, not the hung update. Don't kill it as a "fix".

Recovery once the update PID is dead but state remains:
1. Check `.cache/node-deps.lock` (and `.cache/node-deps.lock.guard`): if its `pid` is dead and no `node-deps.mjs` / `node-deps-heartbeat.mjs` process is running, delete both. This is the lock that freezes `Preparing Node dependencies…`.
2. Confirm the PID in `.git/hermes-update.lock` is dead, then delete that lock — a dead owner means the marker is stale, not held.
3. Delete `source-completion-pending` under `~/.hermes/installs/<install-key>/`; that file is what makes every launch print `a source update is unfinished`.
4. In `~/.hermes/logs/update_receipts/`, set each `outcome: running` receipt with `finished_at: null` to `outcome: interrupted` plus a `finished_at` timestamp, and repoint `latest.json` at the newest receipt.
5. Verify: `hermes --version` prints no warning and `hermes update --check` says `Up to date with the latest release`. A detached HEAD and already-current node_modules are fine — the code landed even if the completion tail never ran.
6. Run `hermes gateway status` — require `Service definition matches the current Hermes install` and launchd supervision. A dead health endpoint alone is not proof the update failed.

