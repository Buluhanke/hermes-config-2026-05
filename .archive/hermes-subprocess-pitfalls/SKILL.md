---
name: hermes-subprocess-pitfalls
description: "hermes_tools仅execute_code沙盒可用的坑。Use when 子进程里调不到hermes工具"
triggers:
  - "write a script for a skill"
  - "hermes_tools not found"
  - "skill ships a runnable .py"
  - "subprocess vs execute_code"
l1: scripting
l2: hermes-internals
l3: core
---

# Hermes Subprocess Pitfalls

## The core gotcha: two execution contexts
A Python snippet inside an `execute_code` block and a `python3 scripts/foo.py`
launched from `terminal` are **different environments**:

- **execute_code sandbox** — has `hermes_tools` pre-importable
  (`web_search`, `web_extract`, `read_file`, `terminal`, `write_file`,
  `search_files`, `patch`, ...). This is the ONLY place
  `from hermes_tools import web_extract` works.
- **Plain `python3` subprocess** (terminal, nohup, cronjob, background,
  `os.system`) — `hermes_tools` is NOT importable
  → `ModuleNotFoundError: No module named 'hermes_tools'`. The process runs in
  whatever python is next on PATH (system or active venv).

### Consequence (the trap)
If your skill ships a script that needs to fetch a webpage, do NOT write
`from hermes_tools import web_extract` inside it and expect it to run from
`terminal`. It will fail at import. Either:
- **(a)** call `web_extract` from the `execute_code` tool inside the agent loop
  (it has `hermes_tools`), or
- **(b)** make the standalone script self-sufficient with directly-invokable
  CLI tools that need no import: `scrapling extract`, `curl`, `python3 -c
  "import requests"`, etc.

## Verified working pattern: standalone degradation chain (no hermes_tools)
A zero-screenshot URL reader that runs as a plain script (proven working):
1. `scrapling extract get <url> <tmp.md>`            — HTTP, local, anti-bot
2. `scrapling extract fetch <url> <tmp.md> --network-idle` — JS/SPA rendered
3. `curl -sL --max-time 60 <url>`                    — bare fallback
All three are real subprocess CLIs. scrapling must be installed first:
`hermes skills install official/research/scrapling` then `scrapling install`
(helps the dynamic/stealth fetchers; the HTTP `get` works without a browser).

## Other gotchas confirmed this session
- **scrapling CLI shape**: `scrapling extract get|fetch|stealthy-fetch <url>
  <out-file>`. NOT the old `Paparazzi.fetch()` Python API some docs show.
- **Output-size threshold**: judge "valid content" at ~80 bytes, not 200.
  Tiny pages (example.com) are ~196 bytes; a `> 200` filter wrongly rejects
  them and silently falls through the whole chain.
- **PyObjC ≠ free AX access**: `ApplicationServices` reads fine on system
  `python3`, but Chrome's `AXChildren` returns `kAXError -25211` (permission)
  unless the process holds the CuaDriver TCC identity. Don't expect a pure
  PyObjC script to dump a foreground app's AX tree.
- **cua-driver `get_accessibility_tree`** enumerates only Hermes + Cua Driver
  windows, NOT Chrome/third-party app windows — so you can't get Chrome's
  `window_id` that way. Foreground Chrome AX reads go through the `computer_use`
  tool (`capture, mode='ax', app='Google Chrome'`), which is already authorized.

## Decision rule: execute_code vs a shipped script
- Need Hermes tools (web_extract, read_file, terminal, patch) → use
  `execute_code` (has `hermes_tools`).
- Need a re-runnable, shareable, deterministic action the USER can run
  themselves → ship `scripts/*.py` that depends ONLY on subprocess CLIs +
  stdlib (scrapling, curl, requests). Never import `hermes_tools` there.
