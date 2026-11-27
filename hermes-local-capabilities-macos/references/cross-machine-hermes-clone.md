# Clone a working Hermes install to a second Mac

Use when migrating Hermes to another Mac, or finishing a half-installed copy where `~/.hermes` (skills, config, .env, scripts) is already present but `hermes --version` hangs or says `no dependency environment is committed for this install`.

**Principle: copy the built artifacts (venv + install state), do not rebuild them.** A destination Mac often cannot reach the package index; `hermes pm repair` then stalls in `uv sync` and never finishes. Two arm64 Macs can reuse a built venv byte-for-byte.

## 0. Preflight

- Confirm architecture on both hosts: `uname -m`. Never reuse an arm64 venv on Intel or vice versa.
- Confirm both trees are the same release: `md5 -q ~/.hermes/hermes-agent/install-stamp.json` on each. If they differ, sync the source tree first (step 3).
- Confirm SSH key auth non-interactively: `ssh -o BatchMode=yes -o ConnectTimeout=8 <user>@<ip> 'whoami; sw_vers -productVersion; echo $HOME'`. Use the returned home path, never assume the short username.

## Cross-architecture transfers (arm64 ↔ Intel)

If `uname -m` differs between hosts, stop: copying the venv and install state cannot work. A built venv's compiled extensions are architecture-specific (`file <venv>/lib/**/*.so | grep arm64`), and the launcher embeds the source interpreter architecture. Path rewriting alone leaves `bad CPU type in executable` and later `ModuleNotFoundError`. A working `hermes --version` is not proof the install is healthy — verify an import of `ruamel.yaml`, `openai`, and `cryptography`, plus `hermes gateway status`.

- **Rosetta 2 is not an escape hatch from arm64 → Intel.** It translates x86_64 code on Apple Silicon; an Intel Mac cannot execute arm64 binaries. Do not propose installing Rosetta to run the source venv on Intel.
- **Check that the destination interpreter satisfies the lockfile before rebuilding.** Some releases mark the whole dependency graph `python_full_version >= '3.14'` in `uv.lock`; downgrading the interpreter then installs nothing useful and surfaces unrelated build failures in old packages (e.g. `cannot import name 'msvccompiler' from 'distutils'`). Read `requires-python` and the markers first.
- **Check wheel availability for the destination platform before choosing a rebuild.** For example, `cryptography==50.0.2` publishes macOS wheels for arm64 only, so Intel must compile it, which needs OpenSSL headers and pkg-config. `pip download --only-binary :all: --no-deps cryptography==<v>` answers this in seconds.
- **Do not delete and regenerate `uv.lock` to dodge a build error.** Regenerating drops the pinned graph and can surface unrelated metadata-build failures; edit the lock in place or provision the native build dependencies instead.
- **`uv export --format requirements.txt` + manual `pip install` is not a substitute for `uv sync`.** Stripping platform markers pulls Windows-only packages (e.g. `pywin32`) and drops override-driven conflict resolution (e.g. pillow vs browser-harness), so resolution fails even when every individual wheel exists.

## 1. Clear quarantine on every copied executable

```bash
ssh <dest> 'xattr -dr com.apple.quarantine ~/.hermes/tools/ ~/.hermes/hermes-agent/ ~/.hermes/installs/ ~/.local/bin/ 2>/dev/null'
```

Why: files copied between Macs carry `com.apple.quarantine`; dyld defers to Gatekeeper's network notarization check and every launch hangs. Diagnostic: `sample <pid> 3 -file /tmp/s.txt` shows the stack stopped in `_dyld_start` with only ~96K mapped. A healthy gateway sampled at the same moment sits in `kevent` instead. Re-run this after every rsync — copied files bring the attribute back.

## 2. Rewrite hardcoded user-home paths

```bash
# text only — grep -I (capital I) skips binaries, otherwise wheels/.so files get corrupted
grep -rIl '/Users/<old>' <dirs> | while read f; do
  sed -i '' 's|/Users/<old>|/Users/<new>|g' "$f"
done

# grep -r does not follow symlinks — rebuild those separately
find ~/.hermes -type l -lname '/Users/<old>*' | while read l; do
  t=$(readlink "$l" | sed 's|/Users/<old>|/Users/<new>|g')
  ln -sfn "$t" "$l"
done
```

macOS `sed -i ''` needs the empty backup argument. Verify with `grep -rIl '/Users/<old>' <dirs> | wc -l` → 0. Check the venv's `bin/python` symlink explicitly.

## 3. Sync source tree and built artifacts

```bash
rsync -a --stats --exclude='.git' --exclude='.venv' --exclude='node_modules' \
  --exclude='__pycache__' --exclude='*.pyc' -e "ssh -o BatchMode=yes" \
  ~/.hermes/hermes-agent/ <dest>:~/.hermes/hermes-agent/

rsync -a --stats -e "ssh -o BatchMode=yes" \
  ~/.hermes/installs/<source-hash>/ <dest>:~/.hermes/installs/<source-hash>/
```

Then repeat steps 1 and 2 — rsync restores quarantine attributes and old paths.

## 4. Populate the DESTINATION install-state directory

The SHA16 under `installs/` is derived from the destination project-root path, so the source hash directory is NOT the one the destination CLI reads. Ask Hermes for the real one:

```bash
<dest-python> -I -c "import sys; sys.path.insert(0,'$HOME/.hermes/hermes-agent'); \
  from pm.paths import runtime_facts_path; print(runtime_facts_path())"
```

Then fill it with real directories:

```bash
DST=~/.hermes/installs/<dest-hash>
cp -a ~/.hermes/installs/<source-hash>/environments "$DST/environments"
cp ~/.hermes/installs/<source-hash>/facts.json "$DST/facts.json"
sed -i '' "s|/Users/<old>|/Users/<new>|g; s|installs/<source-hash>|installs/<dest-hash>|g" "$DST/facts.json"
rm -f "$DST/.repair-incomplete"
```

**Delete `.repair-incomplete` LAST, after every stamp/env fix.** Each failed repair rewrites it as `{"attempts": N}`, and the CLI force-repairs unconditionally whenever it exists — so a stale marker keeps `hermes --version` hanging even after the stamp is correct. Re-check it after the final fix and confirm `hermes --version` does not print `repairing the recorded dependency environment`.

**Use a real directory, not a symlink** to the source-hash environment. `_runtime_state_matches()` resolves the recorded `environment` path and requires it to equal `selected_venv()`; a symlink fails with `dependency environment is missing or outside this install` even though the files are reachable.

## 5. Reconcile the venv stamp — do not run `pm repair` for this

A copied facts.json carries the source machine's stamp, but that stamp hashes the destination's plugin set. `venv_is_current()` returns False and `hermes gateway status` reports `venv: out of sync with uv.lock`. Running `hermes pm repair` here needlessly triggers `uv sync`. Compute the correct stamp and write it into `$DST/facts.json` instead:

```python
# Run with the DESTINATION venv's python — the base python lacks ruamel.
import sys, json
sys.path.insert(0, '/Users/<new>/.hermes/hermes-agent')
from pm.install import get_package, _carried, _member_inputs
from pm.paths import runtime_facts_path

# Read extras from the RUNTIME facts file. facts_path() can resolve to an
# unrelated empty ~/.hermes/tools/facts.json on a copied tree; Facts(...) then
# returns None and expected_stamp raises TypeError on a None subscript.
facts = json.load(open(runtime_facts_path()))
p = get_package('venv')
enabled = sorted(set(_carried(p, facts['packages']['venv']['extras'])))
print(p.expected_stamp(enabled, **_member_inputs(None)))
```

Set `packages.venv.stamp` in `$DST/facts.json` to that value. Verify the venv warning is gone from `hermes gateway status`.

Useful internals when diagnosing: `pm.paths.facts_path()`, `pm.paths.runtime_facts_path()`, `pm.environments.selected_venv(root)`, `pm.install.venv_is_current()`, `pm.install.drift()`.

**Also repoint the repo-local `.venv`.** A copied tree can carry `~/.hermes/hermes-agent/.venv` as a symlink to a Python that does not exist on the destination (`.../cpython-3.11-macos-aarch64-none`, or a stale 3.13). `uv sync` then warns `Ignoring existing virtual environment linked to non-existent Python interpreter`, recreates it with the wrong interpreter, and cron jobs fail with `No module named <module>` even though `pm drift` is clean. Replace the stale link so it points at the real install venv:
```bash
ln -sfn ~/.hermes/installs/<dest-hash>/environments/<env>/venv ~/.hermes/hermes-agent/.venv
ls -ld ~/.hermes/hermes-agent/.venv   # confirm it resolves to the install venv
```
`pm.install.check()` returning `[]` is the authoritative "dependencies fine" signal — when it is empty but commands still trigger `repairing the recorded dependency environment`, suspect `.venv` or `.repair-incomplete`, not the dependency set.

## 6. Verify end to end

- `hermes --version` — prints version / upstream / Python / SDK, with no `pm repair` message.
- `hermes pm doctor` — required tools show ✓.
- `hermes gateway status` — launchd-supervised; no `venv out of sync`, no `Service definition is stale` (the latter is cleared by `hermes gateway start`).
- `zsh -lic 'which hermes; hermes --version'` — interactive PATH includes `~/.local/bin`.
- `find ~/.hermes/skills -name SKILL.md | wc -l` matches the source count.
- `tail -3 ~/.hermes/logs/gateway.log` — log is still advancing.

## 7. Last resort: manual dependency install when the pinned interpreter cannot be changed

Use only when a wheelless pinned dependency cannot be compiled and the lockfile cannot be regenerated. This restores CLI usability (`hermes --version` with a populated SDK version, core imports OK) but does **not** guarantee gateway/plugin parity — verify plugins separately.

```bash
uv export --no-emit-project --no-emit-workspace --format requirements.txt > /tmp/req.txt
# Strip `; marker` suffixes, `--hash` continuation lines and comments; drop
# Windows-only dists (pywin32, winrt-runtime); pin the wheelless package to a
# version that has a wheel for this platform.
python3 parse_script.py   # emit one `name==version` per line
pip install --no-deps -r /tmp/req-clean.txt
pip install --no-deps --no-build-isolation -e <project>
```

`--no-deps` is deliberate: with markers stripped, pip sees mutually exclusive pins (e.g. pillow 13 vs browser-harness 12.3) and refuses to resolve even though every wheel exists. `uv export --format pip` is invalid — the format is `requirements.txt`.

## 8. Resolve bot-channel collisions after cloning

A clone copies `.env` verbatim, so both machines claim the SAME Telegram / Feishu / WeCom / Weixin / QQ tokens. One bot token can be attached to only one gateway; whichever claims it first answers and the other adapter is parked. Verify by comparing token **values** on both hosts before promising an overlap-free setup — a plain clone contains no independent channel to "restore".

Decision order:

1. Second machine needs only local CLI work → uninstall its gateway so it claims no bot at all. `hermes gateway stop` is **insufficient**: launchd `RunAtLoad` / `KeepAlive` relaunches it within seconds. Use `hermes gateway uninstall`, which removes `~/Library/LaunchAgents/ai.hermes.gateway.plist` and the launchd job. Credentials stay in `.env`, so `hermes gateway install && hermes gateway start` restores it.
2. Second machine must own a channel → it needs genuinely NEW bot credentials supplied by the user. Never reuse or invent tokens.
3. `profiles/<name>/gateway.parked` (written by `hermes -p <name> gateway stop`) excludes a secondary profile from multiplexing, but the **default** profile cannot be parked — only uninstalling the host gateway stops it.

This is distinct from the same-machine two-profile credential collision in Pitfalls: there, commenting duplicate keys in the secondary profile suffices; here the whole gateway on the secondary machine must go.

Operational notes:

- Stop may refuse with `N live session(s) would be interrupted` — zombie turns hold the service open. Confirm no wanted session is running, then `hermes gateway stop --yes`.
- `pkill -f gateway` and `launchctl bootout <domain>/ai.hermes.gateway` are blocked by the harness guard (it forbids killing a gateway from within the gateway process tree). Use the official `hermes gateway restart` / `uninstall` subcommands.
- Verify with `ps aux | grep -c "[g]ateway run"` immediately **and again after ~10s**: zero now but nonzero later means launchd relaunched it. Also confirm the plist is gone.
- After uninstall, one-shot `hermes -z` no longer completes (it delegates to the gateway) while `hermes --version` still works. Do not claim full CLI chat parity without testing it.

## Pitfalls

- **Manually assembled wheels must match the ABI of the interpreter that loads them.** Installing cp312 wheels into a venv that the gateway launches with a 3.14 interpreter yields `ImportError: cannot import name <symbol> from <compiled_module> (unknown location)` — the pure-Python package resolves but its compiled extension cannot. Pin every install to the exact interpreter the launcher and launchd will use, and confirm `python -V` inside the venv before declaring success.
- **Never delete or pop the `stamp` to "let pm recompute it."** An absent stamp makes `venv_is_current()` false; pm starts a background `uv lock`, holds `.install.lock`, and the CLI hangs on `dependency lock still held after 10.0s; continuing without it` instead of repairing. Write the computed stamp immediately. If the loop already began, kill `uv lock --python` and `pm/worker.py`, delete `.install.lock` and `.repair-incomplete`, write the stamp, confirm `venv_is_current()` is `True`, then retest.
- **A gateway process started before the venv swap keeps stale imports in memory.** After replacing the venv or facts, run `hermes gateway start` to refresh the launchd definition and reload; otherwise the old process raises `ImportError: cannot import name <symbol>` for symbols that exist on disk.
- **Redirect long-running probes to a log file.** `ssh host 'hermes --version 2>&1 | head -10'` buffers and hides diagnostics; use `cmd > /tmp/probe.log 2>&1; echo EXIT=$? >> /tmp/probe.log` in a background job with a completion notification, then read the file.
- **The install hash is path-derived.** Identical source trees under `/Users/a` and `/Users/b` produce different SHA16 directories. Never assume the source hash directory exists on the destination.
- **Do not start `uv sync` on an egress using fake-ip DNS** (`lsof` shows connections to `198.18.0.0/15`). It stalls with no bytes transferred, leaves the install lock held, and produces misleading `dependency lock still held after 10.0s; continuing without it` noise. Copying the venv sidesteps the download entirely.
- **`xattr -dr` reports harmless errors** for symlinks and racing temp paths. Only chase permission errors on the executable you are actually launching.
- **Credential-collision warnings can be cleared without new tokens.** `gateway status` warns when two profiles hold the same platform credential, even when `gateway: multiplex_profiles: true` is set and `gateway migrate --multiplex` reports the gateway already serves both — the check is static and the migration command will not silence it. The fix is to stop the non-owner profile from claiming the same bot: back up its `.env`, comment out the duplicated `TELEGRAM_BOT_TOKEN` / `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `WECOM_BOT_ID` / `WECOM_SECRET` / `WEIXIN_TOKEN` lines, and keep them only in the owner profile. Confirm with `duplicate_credential_findings()` from `hermes_cli.gateway_migrate` → 0 before restarting the gateway. Do not invent or paste token values — only edit keys that already exist locally.
