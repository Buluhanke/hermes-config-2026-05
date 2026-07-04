# mac-mini Homebrew & Python venv Survival Guide

**When to load**: Before running `brew upgrade`, before installing any skill or package that triggers a Homebrew maintenance run (`mac-maintenance` skill, `brew update && brew upgrade`), or when user reports "my venv is broken" / "pip can't find packages" after a Mac update.

**Sources verified 2026-07-02** (cross-checked 3 sources):
- Homebrew official docs: https://docs.brew.sh/Homebrew-and-Python
- uv issue tracker: https://github.com/astral-sh/uv/issues/1640
- Stack Overflow + Homebrew community (AlexNg9527/fix-venv.sh gist)

---

## TL;DR

`brew upgrade python` + `brew cleanup` **breaks** every virtualenv that was created with the OLD Python's symlink path. Newer venv/virtualenv (Python 3.12+) are immune because they use the stable `$(brew --prefix)/opt/python@3.x/` path. **Always snapshot your venv count before + verify after.**

```bash
# Before brew upgrade python (or any package update)
ls ~/Projects/*/.venv/bin/python 2>/dev/null | wc -l   # count live venvs
find ~ -maxdepth 5 -name 'pyvenv.cfg' 2>/dev/null | wc -l   # broader sweep

# Run upgrade
brew update && brew upgrade python

# After upgrade — verify nothing died
ls ~/Projects/*/.venv/bin/python 2>/dev/null | wc -l   # should match
# If lower → run fix-venv.sh (see below)
```

---

## The Failure Mechanism

Homebrew installs Python to a versioned path:
- `/opt/homebrew/Cellar/python@3.12/3.12.X/bin/python3.12`

Then symlinks `python3.12` → `python3` → `pip3` under `/opt/homebrew/bin/`.

When you `python3 -m venv myproj`, the venv's `pyvenv.cfg` records `home = /opt/homebrew/bin/` (a stable path) AND copies/symlinks the actual python binary.

**On `brew upgrade python@3.12`**:
1. Homebrew moves `/opt/homebrew/Cellar/python@3.12/3.12.X/` → `/opt/homebrew/Cellar/python@3.12/3.12.Y/`
2. venv's pyvenv.cfg still says `home = /opt/homebrew/bin/` (stable, OK)
3. BUT the venv's `bin/python` symlink points to the OLD Cellar path
4. **`brew cleanup`** then deletes `/opt/homebrew/Cellar/python@3.12/3.12.X/` (the old version)
5. Every venv now has a dangling symlink → `python: command not found` or `bad interpreter: No such file or directory`

**Python 3.12+ is immune** because venv/virtualenv now uses `$(brew --prefix)/opt/python@3.X/bin/python3.X` which is a stable symlink Homebrew maintains across upgrades.

---

## Recovery: fix-venv.sh

From AlexNg9527's gist (verified working, bash only):

```bash
#!/bin/bash
# Recreate broken venv symlinks after brew cleanup
set -e

BREW_PY_PREFIX="$(brew --prefix)/opt/python@3.12/libexec/bin"
if [ ! -d "$BREW_PY_PREFIX" ]; then
    BREW_PY_PREFIX="$(brew --prefix)/opt/python@3.13/libexec/bin"
fi

find ~ -maxdepth 5 -name 'pyvenv.cfg' 2>/dev/null | while read -r cfg; do
    venv_dir="$(dirname "$cfg")"
    # Skip if the python binary already works
    [ -x "$venv_dir/bin/python" ] && continue
    # Re-symlink
    ln -sf "$BREW_PY_PREFIX/python3" "$venv_dir/bin/python"
    ln -sf "$BREW_PY_PREFIX/python3" "$venv_dir/bin/python3"
    echo "fixed: $venv_dir"
done
```

Save to `~/.hermes/scripts/fix-brew-venvs.sh` and `chmod +x`. Run after any `brew upgrade python` + `brew cleanup`.

---

## Prevention

| Strategy | Effort | Reliability |
|---|---|---|
| Use `pyenv` instead of Homebrew Python | Medium (one-time setup) | High — Python versions isolated |
| Pin venvs to system Python (3.12+) with `python3.12 -m venv` | Low | High (3.12+ immune to symlink drift) |
| Use `uv` for venv management | Low (`uv pip install ...`) | High — uv handles symlink drift automatically |
| Never `brew cleanup` (let old Cellar versions pile up) | Zero | Medium — works but disk fills |
| Snapshot venv count before brew upgrade | Zero | Diagnostic only — still need fix-venv.sh |

**Recommendation for this Mac mini (24GB, multi-project)**: keep Homebrew Python, but install `uv` (`brew install uv`) and use `uv venv` for new projects. `uv` detects broken venvs and reuses the system Python correctly.

---

## mac-maintenance skill — what it does and what it doesn't

The `mac-maintenance` skill (installed 2026-07-02, `steipete/agent-scripts/mac-maintenance`, 39 installs) does:
1. `brew update && brew upgrade` — **includes Python by default**
2. `git -C ~/Projects/* pull --ff-only` — pulls clean repos, skips dirty ones
3. `osascript -e 'tell application "Finder" to empty trash'`

**It does NOT**:
- Snapshot or restore venvs
- Relink broken Python venvs after upgrade
- Verify Python interpreters still work

**Before invoking `mac-maintenance`**:
```bash
# 1. Snapshot venv count
echo "$(date +%s) $(find ~ -maxdepth 5 -name 'pyvenv.cfg' 2>/dev/null | wc -l)" \
  >> ~/.hermes/logs/venv-snapshots.log

# 2. Run maintenance
# (trigger via cron or /skill-name mac-maintenance)

# 3. Verify + auto-fix
~/.hermes/scripts/fix-brew-venvs.sh
echo "$(date +%s) $(find ~ -maxdepth 5 -name 'pyvenv.cfg' 2>/dev/null | wc -l)" \
  >> ~/.hermes/logs/venv-snapshots.log

# 4. If dropped → investigate (brew may have actually removed python@3.X)
diff <(tail -2 ~/.hermes/logs/venv-snapshots.log) && echo "OK" || echo "INVESTIGATE"
```

---

## Related

- `mac-maintenance` skill — runs the upgrade; does NOT protect venvs
- `hermes-skill-discovery` — install path + security scanner pitfalls
- `hermes-runtime-fortress` — Mac mini 24GB runtime umbrella (this file lives there)