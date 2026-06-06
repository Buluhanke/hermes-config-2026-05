# Real failure: top-level print in `rhythm.py` broke the drain (2026-06-04)

## Symptom

`drain_watchdog.sh` was always printing two extra lines on every tick:

```
当前时区: work, 可主动: True
发送 medium 消息: True
```

These looked like drain output but came from the top of the chain — `hermes_notify` imports `rhythm`, and `rhythm.py` had a demo at the bottom of the file with module-level `print` + `get_rhythm()` + `should_send_message()` calls. Every import ran them.

Why this is bad beyond "noisy output":
- `get_rhythm()` is pure (no state), but `should_send_message('medium')` *can* trigger side effects in any future code that wraps a counter
- The `__name__ == "__main__"` guard was missing — import-time side effects silently fire across the whole module graph
- A LSP/editor reload after editing `rhythm.py` would re-trigger the demo, leaking non-deterministic "current zone" lines into the user's terminal

## Root cause

When I first wrote `rhythm.py` (the canonical reference impl for `hermes-rhythm-gate`), I appended the user's example verbatim:

```python
# rhythm.py
def get_rhythm() -> RhythmContext: ...
def should_send_message(level: str) -> bool: ...

# 使用示例                          <-- not guarded
ctx = get_rhythm()
print(f"当前时区: {ctx.zone.value}, 可主动: {ctx.should_proactive}")
print(f"发送 medium 消息: {should_send_message('medium')}")
```

The print calls are at **module level**, not under `if __name__ == "__main__":`. Every `import rhythm` runs them.

## How I diagnosed it (the fast path)

1. `python3 -c "import hermes_notify"` printed the lines → import is the trigger
2. `python3 -c "import rhythm"` also printed them → narrowed to rhythm.py
3. `python3 -c "import sys; sys.path.insert(0, '/Users/aimac/.hermes/scripts'); import rhythm; print(rhythm.__name__)"` confirmed `__name__` was `rhythm`, NOT `__main__` → so the demo must be top-level
4. `search_files` for `print` in rhythm.py → found two lines under `# 使用示例` with no `if __name__` above them
5. Patch: wrap in `if __name__ == "__main__":` → import became silent

## The fix (canonical)

Always wrap demos / examples / quick-tests in scripts modules:

```python
# module.py
def real_function(): ...

# Demo / example
if __name__ == "__main__":
    print(real_function())
```

## Lint-style prevention

Add a one-line CI check (or just a grep habit) for any new file under `~/.hermes/scripts/`:

```bash
# Print any top-level print that comes after the LAST def
for f in ~/.hermes/scripts/*.py; do
  awk '/^def / {last_def=NR} /^print\(/ && NR > last_def && last_def > 0 {
    print FILENAME":"NR": unguarded top-level print after function defs"
  }' "$f"
done
```

Not a real linter, but catches 90% of this class of bug at the point of writing.

## Lesson for the skill

The `hermes-rhythm-gate` skill's "Reference impl" section describes `rhythm.py` as "pure data" — but the user's examples or my own convenience tests can quietly add side effects. Updated pitfall #8 in SKILL.md captures this. Templates reference impls should be **the cleanest possible version**, with all demos guarded.
