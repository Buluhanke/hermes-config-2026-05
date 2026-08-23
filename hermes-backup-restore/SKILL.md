---
name: hermes-backup-restore
description: Safely back up and restore a Hermes Agent (~/.hermes) installation —
  config, custom skills, scripts, memory databases, cron jobs. Covers the data-destroying
  pitfalls that occur when a backup folder is copied naively (empty .env placeholder,
  0-byte state.db, older config, GPG-restore script misuse).
version: 1.0.0
author: Hermes Agent
license: MIT
triggers:
- Use when hermes backup restore
trigger_type: general
---

# Hermes Backup & Restore

## When to use
- User says "restore my Hermes backup", "set up Hermes from this folder", "install everything from `hermes_backup_*-HHMMSS`", or points you at a backup directory.
- **User asks "装完了没 / is the backup done / complete?" → VERIFY first (see `references/backup-verification.md`). Do not assume a finished folder — it's frequently partial/stalled.**
- Migrating Hermes data to a new machine (skills, scripts, memory, cron).
- Recovering after a broken reinstall/upgrade.

## What lives in ~/.hermes
- `config.yaml` — settings (model, display, memory, tools). **Write-protected**: the agent cannot edit it directly; use `hermes config set <section.key> <val>` (e.g. `hermes config set display.language zh-CN`).
- `.env` — API keys / secrets (real data; ~24KB when populated).
- `state.db` — live session store (SQLite FTS5), actively written (has `-wal` sidecar).
- `skills/` — installed skills, one dir per skill with `SKILL.md`.
- `scripts/` — user scripts (hermes_backup.sh, daily_*, etc.).
- Memory/telemetry DBs: `memory_store.db`, `mnemosyne.db`, `perception_memory.db`, `sessions.db`, `kanban.db`, `script_metrics.db`, `llm_traces.db`, `response_store.db`, `verification_evidence.db`, `plans.db`.
- `cron/jobs.json`, `lancedb/`, `memories/`, `profiles/`, `auth.json`, `chrome-profile-mirror/`.

## Restore workflow (from an extracted backup folder)
**Do NOT `cp -r` the whole backup over `~/.hermes`.** A backup is frequently a partial/stale snapshot, and naive copy wipes live data. Follow this sequence:

1. **Inventory both sides first.** For each item compare backup vs current (byte counts). Decide per-item restore-or-skip.
   ```bash
   BK=~/Desktop/hermes_backup_YYYYMMDD_HHMMSS; H=~/.hermes
   stat -f%z "$BK/.env" "$H/.env"          # if backup << current → keep current
   stat -f%z "$BK/state.db" "$H/state.db"  # if backup is 0 → keep current
   wc -c "$BK/config.yaml" "$H/config.yaml"
   ```
2. **Take an emergency snapshot of current `~/.hermes`** before any destructive step (gives 100% rollback):
   ```bash
   SNAP="$HOME/Desktop/hermes_emergency_backup_$(date +%Y%m%d_%H%M%S)"
   mkdir -p "$SNAP" && rsync -a --exclude='chrome-profile-mirror' --exclude='cache' \
     --exclude='logs' --exclude='bootstrap-cache' --exclude='node' ~/.hermes/ "$SNAP"/
   ```
3. **Skills** — If `skills_backup/` is a full tree (each skill a subdir with `SKILL.md` + `references/` + `scripts/`), `cp -a` it over `~/.hermes/skills/`. If it's only flat `*_SKILL.md` files (~45), that's a DEGRADED backup — **rebuild the full tree from live `~/.hermes/skills`** (keeping the running config's skills) rather than restoring flat files. New/changed skills need a Hermes **restart** to load.
4. **Scripts** — `cp -a "$BK/scripts_backup/." "$H/scripts/"`.
5. **Memory DBs** — safe to copy if current doesn't already have them; if current has a live (non-empty) version, prefer keeping current.
6. **config.yaml / AGENTS.md / CLAUDE.md** — DIFF before overwriting. Backup config is often OLDER/incomplete (e.g. `model.provider: auto` vs current `nous`). Preserve the config that currently works.
7. **crontab** — check `crontab -l`; backup tasks may already be installed (pointing at the restored scripts). Don't duplicate. Only `crontab <file>` if tasks are genuinely missing.
8. **Restart the Hermes App** for skills/cron/config to take effect.

## CRITICAL pitfalls (data-destroying if ignored)
- **`.env` empty placeholder** — backups often contain a 57-byte placeholder `.env`; current holds 24KB real keys. Literal overwrite → Hermes loses all API keys and goes offline. **Always preserve current `.env`.**
- **`state.db` 0 bytes** — backup `state.db` can be empty (0 B) while current has real sessions (hundreds of KB + `-wal` sidecar). Overwrite → wipes all chat history. **Preserve current `state.db`.**
- **`skills_backup` as flat `*_SKILL.md` = DEGRADED backup** — a correct `skills/` backup is a *tree* (one dir per skill with `SKILL.md` + `references/` + `scripts/`, ~497 files). If you find only ~45 flat `name_SKILL.md` files, it's a broken/flattened snapshot that lost `references/`, `scripts/`, and whole skills. **Do NOT restore flat files** — re-copy the FULL tree from live `~/.hermes/skills` (see `references/backup-verification.md` repair block). Restore-from-live beats restoring degraded files.
- **`hermes_restore.sh` is NOT for extracted folders** — it concatenates + GPG-decrypts multi-part cloud volume backups. For an already-unpacked folder, do manual selective restore (above). Don't run it against a plain dir.
- **`config.yaml` is write-protected** — direct `patch`/write is refused ("Refusing to write to Hermes config file"). Use `hermes config set <section.key> <val>`.
- **`config.yaml` byte-size is NOT a recency signal** — a backup `config.yaml` can be LARGER than live yet STALE (seen: backup 14360 B vs live 4864 B; the smaller live one was the actually-running config). Compare by **validity/content**, not bytes. When restoring, keep the file the live process is actually using. (Still write-protected — use `hermes config set <section.key> <val>`.)
- **`chrome-profile_backup`** is huge (browser mirror, GBs) and usually redundant — skip unless specifically needed.
- **Ask before destructive overwrite** — if you'd replace a non-empty current file with an empty/stale backup file, stop and confirm. Restoring "nothing" is worse than doing nothing.

## Verification
```bash
ls ~/.hermes/skills | wc -l        # skill count grew
ls ~/.hermes/scripts | wc -l      # scripts present
crontab -l | grep -vcE '^#|^$'    # cron jobs intact
stat -f%z ~/.hermes/.env          # real keys still there
stat -f%z ~/.hermes/state.db      # sessions preserved
hermes config set display.language zh-CN   # example safe config write
```

## Support files
- `references/restore-checklist.md` — step-by-step decision checklist with exact commands.
- `references/backup-verification.md` — **"is the backup complete?" verification + repair recipe** (catches placeholder `.env`, 0-byte `state.db`, degraded flat `skills_backup`, and missing runtime singletons; fills gaps additively from live `~/.hermes`).
- `scripts/safe_restore_from_folder.sh` — deterministic safe-restore: emergency snapshot + selective copy, auto-skips empty `.env`/`state.db`, places skills flat. Set `BK`/`H` before running.
