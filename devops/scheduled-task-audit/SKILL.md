---
name: scheduled-task-audit
description: "Audit Hermes' scheduled-task surface (launchd plists, crontab, scripts/ self-evolution) for conflicts, orphaned schedules, half-broken scripts, and destructive side effects (pkill Chrome, restart services). Use when the user asks '查自动学习任务有没有冲突', 'audit scheduled jobs', or after adding/removing scheduled scripts. Triggers on questions about self_evolution, daily_*, ai_knowledge_collector, self_optimization, hermes_self_check, or any ~/.hermes/scripts/*.{sh,py} with `time/sleep/cron` semantics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [cron, launchd, scheduled-tasks, audit, self-evolution, conflict-detection]
    related_skills: [script-provider-independence, gateway-http-pool-tuning]
---

# Scheduled-Task Audit

Hermes accumulates a lot of scheduled work over months of self-evolution:
launchd plists, cron jobs, `self_evolution.sh` with three modes, daily
scripts nobody maintains, and AI knowledge collectors with no schedule.
The "user says check for conflicts" request is **the high-frequency
trigger** — twice in 2026-06 alone. This skill gives a single audit
methodology that scales to whatever the surface has become.

## When this skill applies

Trigger on **any** of these signals:

- User asks "查一下自动学习任务有没有冲突" / "audit scheduled jobs"
  / "what runs at startup" / "what's in cron"
- After adding a new `~/.hermes/scripts/*.{sh,py}` with `cron` or
  `sleep` semantics
- After editing any `~/Library/LaunchAgents/ai.hermes.*.plist`
- When `~/.hermes/logs/evolution.log` shows overlapping timestamps
- When the user complains about daily noise / unexpected Chrome restarts

## The 6-step audit (run all 6 — each one catches a different bug class)

### Step 1 — Inventory ALL scheduling surfaces

Don't trust `crontab -l` alone. The surface is **at least 4 places**:

```bash
# 1a. Hermes-managed launchd plists
ls -la ~/Library/LaunchAgents/ai.hermes.*.plist 2>/dev/null

# 1b. Each plist's actual schedule (LaunchInterval OR CalendarInterval)
for f in ~/Library/LaunchAgents/ai.hermes.*.plist; do
  echo "=== $f ==="
  plutil -p "$f" | grep -E "StartCalendarInterval|StartInterval|KeepAlive|Label"
done

# 1c. User crontab (often empty in Hermes, but check)
crontab -l 2>/dev/null

# 1d. Hermes in-process cronjob tool (may run regardless of launchd)
# via the `cronjob` MCP tool
```

Cross-reference: any **script with a `cron`-style comment at the top but
no actual schedule** is an orphan. Example: `ai_knowledge_collector.sh`
has `# Cron: 0 3 * * * ...` but the user's crontab is empty → dead
schedule.

### Step 2 — Detect time-overlap conflicts

List each task with its actual fire time. Look for:

- **Same-second collision** (two plists both at `Hour=9 Minute=0`)
- **Within-window collision** (`StartInterval=1800` = every 30 min +
  one at minute 0 = guaranteed hit at 9:00, 9:30, 10:00, ...)
- **Multi-mode scripts** (`self_evolution.sh hourly|daily|weekly` invoked
  by 3 different plists → must confirm they don't all hit on Mon 09:00)

Output as a timeline table:

| Plist | Mode | Schedule | What it does |
|---|---|---|---|
| `ai.hermes.self-evolution` | hourly | StartInterval=1800 | lightweight PID/port/disk probe |
| `ai.hermes.self-evolution-daily` | daily | 09:00 | full self_evolution.sh daily mode |
| `ai.hermes.self-evolution-weekly` | weekly | Mon 09:00 | self_evolution.sh weekly mode |

**Mon 09:00 fires BOTH daily and weekly** — same script different mode.
Acceptable (different code paths in `if [ "$MODE" = ... ]` blocks) but
flag it as a resource-doubling risk.

### Step 3 — Detect half-broken scripts

For every script in `~/.hermes/scripts/` that any plist references, read
the file end-to-end looking for:

- **TODO / SKIP / FIXME** on the actual work logic
- **Hardcoded paths** that no longer match the current environment
  (e.g. port `9222` when the user's CDP is on `9333`)
- **Last-modified staleness** (mtime > 90 days = suspect)

```bash
# Quick scan: count "TODO/SKIP/FIXME" lines per script
for f in ~/.hermes/scripts/*.{sh,py}; do
  cnt=$(grep -cE "TODO|SKIP|FIXME|XXX|HACK" "$f" 2>/dev/null)
  [ "$cnt" -gt 0 ] && echo "$cnt  $f"
done
```

A "half-broken" script is one where the shell scaffolding works
(logging, dirs, error handling) but the actual work steps are
commented out or log `[SKIP]`. These are **silent liabilities** — they
cost cycles to load + may have destructive side effects in the
scaffolding itself (see Step 4).

### Step 4 — Detect destructive side effects

Read the **script body** (not just the plist) for commands that mutate
user state:

```bash
# Scan ALL scheduled scripts for destructive patterns
for f in ~/.hermes/scripts/*.{sh,py}; do
  echo "=== $f ==="
  grep -nE "pkill|kill -9|killall|rm -rf|rm -f|launchctl (unload|bootout)|defaults delete|mkfs|dd " "$f" 2>/dev/null
done
```

The most common finding (2026-06): **`daily_learning.sh` calls
`pkill -9 -f "Chrome"`** to ensure Chrome is running for CDP scraping.
If a user accidentally invokes this script (or its plist fires), the
entire Chrome process tree dies — including any other window the user
has open and any debug-port session the gateway is hooked to.

Decision matrix:

| Pattern | Risk | Action |
|---|---|---|
| `pkill -f Chrome` | HIGH — nukes user's browser | Refactor to `pgrep` + targeted restart, OR delete the script |
| `launchctl unload` | MEDIUM — disables a service the user may want | Confirm with user first |
| `rm -f *.pid` | LOW — only if pid file ownership is unambiguous | OK to keep |
| `rm -rf ~/.cache/...` | MEDIUM — depends on path specificity | Verify path is hermetic |

### Step 5 — Detect Chrome CDP port conflicts

If a script kills Chrome to ensure a CDP-capable instance is running,
verify **which port** it targets:

```bash
# 1. What ports does the user ACTUALLY have Chrome listening on?
lsof -nP -iTCP -sTCP:LISTEN | grep -i chrome

# 2. What ports does each script hardcode?
grep -nE "remote-debugging-port|--port=|9222|9333" ~/.hermes/scripts/*.{sh,py} \
  ~/Library/LaunchAgents/ai.hermes.*.plist 2>/dev/null
```

Common conflict: script targets port `9222` (the default) but user's
real debug instance is on `9333` (a port that was relocated to escape
collision with another process). The script's `pkill` would still
kill Chrome even though the port it then re-opens is wrong.

### Step 6 — Synthesize a verdict

For each task, output a one-line status:

- ✅ KEEP — no conflicts, no destructive side effects, script works
- ⚠️ REVIEW — minor conflict / half-broken logic / port mismatch
- 🔴 DELETE — orphan schedule + half-broken + destructive side effects
- 🔧 RECONFIGURE — needs schedule change or script patch

Then propose a single recommended action. Do **not** auto-delete —
destruction of scheduled work needs explicit user approval per the
真人化行为准则 ("破坏性删除必须授权").

## Output format the user actually wants

A 5-line answer with the actionable items, not a 30-row table. The user
already knows what their scripts do; they want to know **which ones
are silently broken or dangerous**.

```
| 任务 | 调度 | 状态 |
|---|---|---|
| self-evolution (hourly) | StartInterval=1800 | ✅ KEEP |
| self-evolution-daily | 09:00 | ✅ KEEP |
| self-evolution-weekly | Mon 09:00 | ⚠️ 09:00 与 daily 重叠 |
| daily_learning.sh | 无调度 | 🔴 半残废 + 含 pkill Chrome |
| ai_knowledge_collector.sh | 注释里 cron 失效 | 🔧 挂载 launchd 或删注释 |
```

Then propose "建议" (recommendations), wait for user approval before
deleting.

## Pitfalls

- **`KeepAlive=true` plists are not "scheduled tasks"** — they fire on
  demand from the gateway, not on a clock. Don't conflate them with
  `StartCalendarInterval` plists in the conflict report.
- **`StartInterval` is per-process-per-tick, not wall-clock** — if the
  machine sleeps for 8 hours and wakes up, the interval restarts from
  the last fire, not from "now". Don't promise "every 30 min on the dot".
- **launchd's `StartCalendarInterval` with multiple entries fires on
  ALL of them**, not the next one. If you put Mon 09:00 + Fri 17:00, it
  fires twice a week.
- **macOS launchd needs `~/Library/LaunchAgents/`, NOT
  `/Library/LaunchAgents/`** unless running as root. Don't write to the
  system-wide path from a non-root agent.
- **A plist that's `RunAtLoad=true` AND `StartInterval=1800`** fires
  once immediately at launch then every 30 min — not "every 30 min
  starting 30 min from launch". Read the whole plist.
- **The Hermes `cronjob` tool is a SECOND, in-process scheduler** —
  it runs regardless of launchd. Always check both with
  `cronjob(action='list')` and `ls ~/Library/LaunchAgents/`.
- **"Manual trigger" scripts with no schedule are STILL liabilities** —
  if `ai_knowledge_collector.sh` has `# Cron: 0 3 * * *` commented at
  the top, somebody will eventually copy-paste that into a real cron
  without realizing the script is half-broken.
- **`StartCalendarInterval` with `Weekday` uses ISO %V, not %W** —
  when generating weekly report filenames from `date`, use `%Y-W%V` (ISO
  week). Using `%W` (Monday-based) produces a filename like
  `2026-W22.md` while the in-document title is `2026-W23` — title and
  filename get out of sync within the same script run. Pick one format
  and use it for both.
- **Bash `set -uo pipefail` + numeric var check is a footgun** —
  `if [ "$DISK" -gt 80 ]` aborts the script with `unbound variable`
  on the first run of the day when `$DISK` hasn't been computed yet
  by an earlier `df` step. Either use `${DISK:-0}` default, or hoist
  the `df` call above the conditional. Verifying with
  `bash -n script.sh` only catches syntax errors, not runtime
  unbound-variable errors.
- **Modify a plist? `launchctl load` is NOT idempotent — must unload first (2026-06-05)**.
  After editing `~/Library/LaunchAgents/ai.hermes.*.plist` (changing
  `StartCalendarInterval` time, etc.), the steps are:
  ```bash
  launchctl unload ~/Library/LaunchAgents/ai.hermes.<name>.plist
  launchctl load   ~/Library/LaunchAgents/ai.hermes.<name>.plist
  launchctl list | grep <name>     # 确认 - 0 PID 也在 (launchd 占位)
  ```
  Skipping `unload` results in launchd keeping the OLD plist in memory
  and silently ignoring your edit. The file on disk looks right, the
  task keeps firing at the OLD time, and you waste a day debugging
  "why is daily still running at 9:00 instead of 9:30?". Always verify
  with `launchctl list` after — `-  0  ai.hermes.foo` means loaded
  (PID 0 because launchd hasn't spawned it yet on calendar schedule).
- **Scheduled scripts with destructive side effects need a `--dry-run`
  flag (2026-06-05)**. Once you have a script that does
  `kill -TERM` / `pkill` / `rm -rf` on a schedule, you need a way to
  verify the script's detection logic without the destructive part
  firing. Pattern:
  ```bash
  DRY_RUN=false
  [ "${2:-}" = "--dry-run" ] && DRY_RUN=true
  do_run() {
      [ "$DRY_RUN" = "true" ] && { log "🧪 [DRY-RUN] $*"; return 0; }
      "$@"
  }
  # Wrap each destructive call: do_run kill -TERM "$pid"
  ```
  Then `bash script.sh hourly --dry-run` shows what would fire without
  actually killing anything. Apply this BEFORE you ship the script —
  retrofitting is much harder once something has already gone wrong.

- **Bash `[[ X == Y ]] && cmd` returns the `[[ ]]` truth value, not 0 —
  breaks launchd exit-code reporting (2026-06-05)**. The pattern
  ```bash
  log() {
      [[ "$DRY_RUN" == "true" ]] && echo "$msg"   # ← problem
  }
  ```
  looks innocent but: when `DRY_RUN=false`, `[[ false == "true" ]]`
  returns **1**; the `&&` short-circuits and the whole expression
  returns **1** (not 0). If `log` is the **last** function called by
  the script, **the script exits 1** even though every line of logic
  ran successfully. `launchctl print` will then show
  `last exit code = 1` and the script's last line will still be in
  the log file (`✓ done`) — making the failure look like a bug in
  the work logic when it's actually in the log function itself.
  Fix: use explicit `if/fi` and a trailing `return 0`:
  ```bash
  log() {
      msg="[$(ts)] $*"
      echo "$msg" >> "$LOG"
      if [[ "$DRY_RUN" == "true" ]]; then
          echo "$msg"
      fi
      return 0
  }
  ```
  Detection: `bash script.sh >/dev/null; echo $?` returns 1, but
  `tail $LOG` shows the script completed all its check lines.
  Diagnosis: `bash -x script.sh | tail -20` shows the `[[ ... ]] &&`
  line evaluating to false. Always re-test after any watchdog-style
  script edit; the symptom of "last exit code = 1 but logic worked"
  is uniquely this bug.
- **`[ ! -w "$FILE" ] 2>/dev/null` is silently ignored by bash
  (2026-06-05)**. The redirect **inside** the `[ ]` test is not legal
  bash syntax — bash swallows it without error and proceeds with the
  test, but the redirect is discarded. If the file doesn't exist or
  isn't writable, the test still runs (returning false), but you
  lose the stderr suppression you were trying to get. The right way
  to test writability quietly:
  ```bash
  if ! (>: "$FACT_DB") 2>/dev/null; then
      log "❌ $FACT_DB 不可写"
  fi
  ```
  or just `if [ ! -w "$FACT_DB" ]; then` and let the (rare) stderr
  through. Combining the two bugs above (a `[[ ]] &&` log function
  + a `[ ]` test with mis-placed redirect) produces a script that
  always exits 1, with no obvious cause in the work logic.
- **Watchdog scripts: separate "detect" from "restart" (2026-06-05)**.
  A health-check script whose job is to fire periodically and report
  status should **not** itself try to restart the failed service.
  Reason: the restart is the "destructive" part, and when it fails
  (e.g. spawns a process that doesn't bind its port), the launchd
  exit code of the script goes to 1 — and the watchdog is now
  mis-reporting "I am broken" instead of "service X is broken".
  Correct pattern:
  1. Watchdog detects (process / port / disk / memory), logs findings
  2. If anything is down, log a clear `⚠️  X is down — needs restart`
  3. A **separate** recovery script (owned by a different plist, or
     triggered manually by user) actually does the restart
  4. The watchdog never mutates user state on its own
  This separation also makes `bash watchdog.sh --dry-run` safe to
  run any time, since there are no destructive actions to wrap.
  Anti-pattern: `self_heal_watchdog.sh v1.2` had `nohup gateway run`
  in the same script as the detection logic; when the gateway
  restart failed, launchd marked the watchdog itself as failed. The
  v1.3 fix was to delete the restart block entirely — keepalive
  scripts now own restarts, the watchdog just watches.
- **Times in plist are local timezone, NOT UTC (2026-06-05)**.
  `StartCalendarInterval` `Hour=9 Minute=30` fires at 9:30 **local
  time**. If your machine is on UTC (servers, CI), that's different
  from a developer Mac. Add a one-line comment to the plist:
  ```xml
  <!-- 9:30 local time (= 01:30 UTC if Mac is on UTC) -->
  <key>Hour</key><integer>9</integer>
  <key>Minute</key><integer>30</integer>
  ```
  and verify with `date` after the next scheduled fire. Mismatch is
  the #1 reason "the script ran at the wrong time" tickets linger
  for days.
- **`launchctl list <label>` returns a plist dump, not the
  PID-Status-Label table (2026-06-05)**. The pattern
  ```bash
  if launchctl list "$LABEL" 2>/dev/null | grep -qE "^[0-9]"; then
      PID=$(launchctl list "$LABEL" | awk 'NR==2{print $1}')
  fi
  ```
  is **wrong** — `launchctl list <label>` walks the **print** path
  and returns a JSON-ish plist block. The grep `^[0-9]` never matches
  and the script thinks the service is dead on every run. Use the
  un-targeted `launchctl list | grep` pattern instead:
  ```bash
  LINE=$(launchctl list 2>/dev/null | grep -E "^[0-9-]+\s+[0-9-]+\s+$LABEL$")
  if [ -n "$LINE" ]; then
      PID=$(echo "$LINE" | awk '{print $1}')
      [ "$PID" = "-" ] && PID=""
  fi
  ```
  This bug bit **two** scripts in the same session: `hermes_self_check.sh`
  (kept mis-reporting Gateway dead every 15 min, 138KB of kickstart
  noise) and `daily_health_check.sh` (new script, would have shipped
  broken). Fix once, never re-debug.
- **launchd `Status` column is the **last exit code**, not current
  state (2026-06-05)**. `launchctl list` output:
  ```
  -9  ai.hermes.gateway
  ```
  `-9` means "the last time the service exited, the exit code was 9
  (= SIGKILL)". It does **not** mean the service is currently dead.
  Pair every launchd status check with **two** corroborating signals:
  (1) **Live process** — `pgrep -fl "<service-binary>"` or
  `lsof -p <pid> -P -i` to confirm socket binding; (2) **HTTP / health
  probe** — `curl -sS -o /dev/null -w "%{http_code}" --max-time 3
  http://127.0.0.1:<known-port>/health`. The HTTP probe is the gold
  standard — if `/health` returns 200, the service is healthy
  regardless of what launchd's bookkeeping says. This pattern
  rescued `daily_health_check.sh` from reporting Gateway as ❌ when
  it was actually fine (8642 /health 200, 0.6ms).
- **The `hermes send` CLI flag shape — `-t <target> <message>`,
  positional message, not `--target/--message` (2026-06-05)**.
  ```bash
  # WRONG — silent fail, no Telegram message
  hermes send --target "telegram" --message "hello"
  # RIGHT — actually sends
  hermes send -t "telegram" "hello"
  ```
  The CLI's argparse uses `-t/--to TARGET` with the message as a
  positional argument. Run `hermes send --help` to confirm before
  wiring any `hermes send`-based script. The `--target/--message`
  form is what `send_message` (the tool) takes, not `hermes send`
  (the CLI subcommand) — different code paths. Verify success: the
  command prints `Sent to telegram home channel (chat_id: <id>)`.
- **Platform configuration lives in `hermes status`, NOT
  `hermes platforms list` (2026-06-05)**. `hermes platforms list`
  does not exist as a subcommand. The platform list lives under
  `◆ Messaging Platforms` in `hermes status` output, formatted as
  `  Telegram      ✓ configured (home: 7359677525)`. Match patterns
  must use `LC_ALL=C` to handle the U+2713 `✓` glyph on macOS bash:
  ```bash
  if echo "$HERMES_STATUS" | LC_ALL=C grep -qE "$p.*configured|$p.*connected"; then
      PLAT_OK+=("$p")
  fi
  ```
  Without `LC_ALL=C`, the grep silently fails on multi-byte UTF-8
  chars and reports all platforms as ❌ even when they're configured.
- **`StandardOutPath` collides with script-internal `exec >> "$LOG"
  2>&1` (2026-06-05)**. A self-check script that starts with
  ```bash
  exec >> "$LOG" 2>&1
  echo "=== [$(date)] start ==="
  ```
  routes its stdout to `$LOG` (the script-internal log file). If the
  plist's `StandardOutPath` points at a **different** path, the
  plist's `StandardOutPath` file is **empty** on every run, and you
  conclude "the script isn't running" — wrong, it's running, output
  is just going to the wrong file. Hit by `hermes_self_check.sh`
  (its output went to `self_healer.log` for months, making
  `self_check.log` permanently 0 bytes). Fix: either drop the
  `exec >>` and let plist's `StandardOutPath` win, or keep the
  `exec >>` and point the plist at the same file. Verify by
  `tail`ing **both** candidate files after a kickstart. Detection:
  `wc -l self_check.log` is 0 but the process is in `pgrep` and
  `lsof` shows it holding the LOG fd.
- **`tee -a "$LOG"` in launchd scripts causes double-print of every
  line (2026-06-05)**. The `log()` function pattern
  `echo "..." | tee -a "$LOG"` writes to both the log file AND stdout.
  launchd captures stdout and **also** writes it to the same log file
  (because `StandardOutPath` points at the same `$LOG`). Result: every
  line appears twice. Hit by both `mem_patrol.sh` and `self_evolution.sh`
  independently — same bug, two scripts. Fix: drop `tee -a`, write
  explicitly to the file and let stdout be a separate `echo`:
  ```bash
  log() {
      msg="$(date '+...') [$MODE] $1"
      echo "$msg" >> "$LOG"   # write to log file
      echo "$msg"             # let launchd capture stdout
  }
  ```
  Detection: `tail -5 $LOG` shows each line twice with the same
  timestamp. Verify by counting `wc -l` after a known single-execution
  run. Applies to any launchd-driven script where `StandardOutPath`
  and the in-script log file point at the same path.
- **Multiple programs owning Chrome with different `--user-data-dir`
  is the real cause of "登录态平白无故丢失" (2026-06-05)**. The
  symptom users see is "I logged into 9 AI stations and an hour later
  the tabs are empty / logged out". The real chain is:
  1. `ai.hermes.chrome.plist` (5/9 旧) launches Chrome with
     `--user-data-dir=/Users/aimac/.hermes/chrome-debug` (隔离 profile)
  2. `com.aimac.hermes-chrome-debug.plist` (6/1 旧) launches another
     Chrome with **the same** `--user-data-dir=/Users/aimac/.hermes/chrome-debug`
  3. `chrome-on-demand.sh` (on-demand 脚本) hard-codes the same
     `~/.hermes/chrome-debug` path
  4. `self_evolution.sh` hourly runs `pkill -f "chrome.*9333"` which
     kills all of the above (including the user's daily Chrome if
     its renderer processes match the pattern)
  5. `chrome_keepalive.sh` (the "fix") launches with **a different**
     `--user-data-dir=.../Chrome/Default` (system profile, retains
     login state)
  Net effect: 5 programs all want to own Chrome, 3 use 隔离 profile, 1
  uses system profile, 1 kills them all hourly. The user thinks
  "登录态平白无故丢失" — what's actually happening is **different
  profiles reading different cookie databases**, and the hourly
  killer erasing the debug-profile tabs that did have valid logins.
  Fix: rename legacy plists to `.plist.disabled` (not delete — user
  might want to re-enable), update every launcher to use a single
  `--user-data-dir` (system Default — shares cookies with user's
  daily Chrome so login state is always visible), and have the
  hourly 修复 path delegate to the keepalive script instead of
  doing its own pkill. Verify with
  `pgrep -fl "Google Chrome.*--user-data-dir"` — should show ONE
  unique path across all live processes.
- **User principle: "治本不治标" — fix root cause, not symptoms
  (2026-06-05)**. When the user complains about a recurring failure
  ("登录态一直在丢" / "每天都要修"), do NOT ship a 5th mitigation
  script. The right move is:
  1. List every program that touches the failing component
  2. Identify which ones are using the **wrong** config (path, profile,
     env var, mode)
  3. Disable / consolidate to ONE owner with the right config
  4. Verify the user's actual problem is gone, not just "no error log"
  Detect this trigger: user says "平白无故" / "永远在维修的路上" /
  "治本" / "别治标" → stop adding scripts, go audit the surface and
  consolidate. The skill `browser-webpage-100score` is the
  authoritative home for the "9-站 Chrome 登录态" topic; load it for
  the detailed `--user-data-dir` unification procedure.
- **`python yaml.safe_dump` round-trips flood `errors.log` with
  "unknown config keys ignored" (2026-06-05)**. Editing `config.yaml`
  via Python (`yaml.safe_load` → mutate dict → `yaml.safe_dump`)
  reorders/re-formats unrelated keys; the strict-mode schema
  validator in `hermes_cli/config.py` flags each as a warning. The
  framework still loads the file correctly (warnings are non-fatal)
  but you get dozens of redundant lines. Diagnosis procedure:
  1. `grep "unknown config keys" errors.log | awk -F'ignored: ' '{print $2}' | sort -u` — list distinct unknown keys
  2. Cross-check each against `_KNOWN_KEYS` / `_CAMEL_ALIASES` in `hermes_cli/config.py` to confirm not whitelisted
  3. If the key is from a **legacy** field (e.g. `alias:` in `fallback_providers`), the warnings are pre-existing — don't try to fix them in a YAML round-trip. Instead edit the targeted section via `hermes config set key=value` (uses the framework's own validation, never writes keys outside `_KNOWN_KEYS`).
  Lesson: prefer `hermes config set` for surgical changes; reserve
  `python yaml.safe_dump` for adding a NEW top-level key. The 32
  unknown-key warnings seen in 2026-06-04 were all from a legacy
  `alias:` field that pre-dated the stricter schema — they
  self-resolved once that section was rewritten via `hermes config set`.

## Reference

- 2026-06-03 audit session output: `references/2026-06-03-task-conflict-audit.md`
- 2026-06-04 self-check plist mount: `references/2026-06-04-self-check-plist-mount.md`
- 2026-06-05 external channels dead → local 4-way fallback SOP: `references/2026-06-05-external-channels-dead-local-sop.md`
- 2026-06-05 self_heal_watchdog.sh `last exit code = 1` debugging transcript (3 stacked bugs: `[[ ]] &&` truth return, `[ ! -w ] 2>/dev/null` silent ignore, watchdog-restart-separation): `references/2026-06-05-watchdog-exit-code-debug.md`
- 2026-06-05 daily plist 三件套上线 + 6 个新坑实战 (launchctl list <label> 走 print / Status 列是 exit code / hermes send flag / hermes status 平台源 / exec 吞 stdout / LC_ALL=C ✓): `references/2026-06-05-daily-plist-rollout.md`
- One-liner audit script: `scripts/audit_scheduled_tasks.sh`
- Conflict matrix template: `templates/conflict-table.md`
