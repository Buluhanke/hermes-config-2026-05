---
name: python-debugpy
description: "Debug Python: pdb REPL + debugpy remote (DAP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [debugging, python, pdb, debugpy, breakpoints, dap, post-mortem]
    related_skills: [systematic-debugging, node-inspect-debugger, debugging-hermes-tui-commands]
---

# Python Debugger (pdb + debugpy)

## Overview

Three tools, picked by situation:

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add `breakpoint()` in the source, run normally, get a REPL at that line. |
| **`python -m pdb`** | Launch an existing script under pdb with no source edits. Useful for quick poking. |
| **`debugpy`** | Remote / headless / "attach to already-running process." Talks DAP, scriptable from terminal, works for long-lived processes (gateway, daemon, PTY children). |

**Start with `breakpoint()`.** It's the cheapest thing that works.

## When to Use

- A test fails and the traceback doesn't reveal why a value is wrong
- You need to step through a function and watch a collection mutate
- A long-running process (hermes gateway, tui_gateway) misbehaves and you can't restart it
- Post-mortem: an exception fired in prod-ish code and you want to inspect locals at the crash site
- A subprocess / child (Python `_SlashWorker`, PTY bridge worker) is the actual bug site

**Don't use for:** things `print()` / `logging.debug` solve in under a minute, or things `pytest -vv --tb=long --showlocals` already reveals.

## pdb Quick Reference

Inside any pdb prompt (`(Pdb)`):

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `j N` | jump to line N (same function only) |
| `l` / `ll` | list source around current line / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up / down in the stack |
| `a` | print args of the current function |
| `p expr` / `pp expr` | print / pretty-print expression |
| `display expr` | auto-print expr on every stop |
| `b file:line` | set breakpoint |
| `b func` | break on function entry |
| `b file:line, cond` | conditional breakpoint |
| `cl N` | clear breakpoint N |
| `tbreak file:line` | one-shot breakpoint |
| `!stmt` | execute arbitrary Python (assignments included) |
| `interact` | drop into full Python REPL in current scope (Ctrl+D to exit) |
| `q` | quit |

The `interact` command is the most powerful — you can import anything, inspect complex objects, even call methods that mutate state. Locals are read-only by default; use `!x = 42` from the `(Pdb)` prompt to mutate.

## Recipe 1: Local breakpoint

Easiest. Edit the file:

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Run the code normally. You land at the `breakpoint()` line with full access to locals.

**Don't forget to remove `breakpoint()` before committing.** Use `git diff` or a pre-commit grep:
```bash
rg -n 'breakpoint\(\)' --type py
```

## Recipe 2: Launch a script under pdb (no source edits)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```

## Recipe 3: Debug a pytest test

The hermes test runner and pytest both support this:

```bash
# Drop to pdb on failure (or on any raised exception):
scripts/run_tests.sh tests/path/to/test_file.py::test_name --pdb

# Drop to pdb at the START of the test:
scripts/run_tests.sh tests/path/to/test_file.py::test_name --trace

# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

Note: `scripts/run_tests.sh` uses xdist (`-n 4`) by default, and pdb does NOT work under xdist. Add `-p no:xdist` or run a single test with `-n 0`:

```bash
scripts/run_tests.sh tests/foo_test.py::test_bar --pdb -p no:xdist
# or
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

This bypasses the hermetic-env guarantees — fine for debugging, but re-run under the wrapper to confirm before pushing.

## Recipe 4: Post-mortem on any exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Or wrap a whole script:

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Or set a global hook in a repl/jupyter:

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```

## Recipe 5: Remote debug with debugpy (attach to running process)

For long-lived processes: Hermes gateway, tui_gateway, a daemon, a process that's already misbehaving and can't be restarted clean.

### Setup

```bash
source /home/bb/hermes-agent/.venv/bin/activate
pip install debugpy
```

### Pattern A: Source-edit — process waits for debugger at launch

Add near the top of the entry point (or inside the function you want to debug):

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

Start the process; it blocks on `wait_for_client()`.

### Pattern B: No source edit — launch with `-m debugpy`

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

Equivalent for module entry:

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Pattern C: Attach to an already-running process

Needs the PID and debugpy preinstalled in the target's environment:

```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Some kernels/security configs block the ptrace-based injection (`/proc/sys/kernel/yama/ptrace_scope`). Fix with:
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Connecting a client from the terminal

The easiest terminal-side DAP client is VS Code CLI or a small script. From inside Hermes you have two practical options:

**Option 1: `debugpy`'s own CLI REPL** — not an official feature, but a tiny DAP client script:

```python
# /tmp/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

This is fine for one-off automation but painful as an interactive UX.

**Option 2: Attach from VS Code / Cursor / Zed** — if the user has one open, they can add a `launch.json`:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "/home/bb/hermes-agent" }
  ]
}
```

**Option 3: Ditch DAP, use `remote-pdb`** — usually what you actually want from a terminal agent:

```bash
pip install remote-pdb
```

In your code:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

Then from the terminal:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

`remote-pdb` is the cleanest agent-friendly choice when `debugpy`'s DAP protocol is overkill. Use `debugpy` only when you actually need IDE integration.

## Debugging Hermes-specific Processes

### Tests
See Recipe 3. Always add `-p no:xdist` or run single tests without xdist.

### `run_agent.py` / CLI — one-shot
Easiest: add `breakpoint()` near the suspect line, then run `hermes` normally. Control returns to your terminal at the pause point.

### `tui_gateway` subprocess (spawned by `hermes --tui`)
The gateway runs as a child of the Node TUI. Options:

**A. Source-edit the gateway:**
```python
# tui_gateway/server.py near the top of serve()
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
Start `hermes --tui`. The TUI will appear frozen (its backend is waiting). Attach a client; execution resumes when you `continue`.

**B. Use `remote-pdb` at a specific handler:**
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # in the RPC handler you want to trap
```
Trigger the matching slash command from the TUI, then `nc 127.0.0.1 4444` in another terminal.

### `_SlashWorker` subprocess
Same pattern — `remote-pdb` with `set_trace()` inside the worker's `exec` path. The worker is persistent across slash commands, so the first trigger blocks until you connect; subsequent slash commands pass through normally unless you re-arm.

### Gateway (`gateway/run.py`)
Long-lived. Use `remote-pdb` at a handler, or `debugpy` with `--wait-for-client` if you're restarting the gateway anyway.

## Common Pitfalls

1. **pdb under pytest-xdist silently does nothing.** You won't see the prompt, the test just hangs. Always use `-p no:xdist` or `-n 0`.

2. **`breakpoint()` in CI / non-TTY contexts hangs the process.** Safe locally; never commit it. Add a pre-commit grep as a safety net.

3. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls. Check the env if your breakpoint isn't hitting:
   ```bash
   echo $PYTHONBREAKPOINT
   ```

4. **`debugpy.listen` blocks only if you also call `wait_for_client()`.** Without it, execution continues and your first breakpoint may fire before the client is attached.

5. **Attach to PID fails on hardened kernels.** `ptrace_scope=1` (Ubuntu default) allows only same-user ptrace of child processes. Workaround: `echo 0 > /proc/sys/kernel/yama/ptrace_scope` (needs root) or launch under `debugpy` from the start.

6. **Threads.** `pdb` only debugs the current thread. For multithreaded code, use `debugpy` (thread-aware DAP) or set `threading.settrace()` per thread.

7. **asyncio.** `pdb` works in coroutines but `await` inside pdb requires Python 3.13+ or `await` from `interact` mode on older versions. For 3.11/3.12, use `asyncio.run_coroutine_threadsafe` tricks or `!stmt`-based awaits via `asyncio.ensure_future`.

8. **`scripts/run_tests.sh` strips credentials and sets `HOME=<tmpdir>`.** If your bug depends on user config or real API keys, it won't reproduce under the wrapper. Debug with raw `pytest` first to repro, then re-confirm under the wrapper.

9. **Forking / multiprocessing.** pdb does not follow forks. Each child needs its own `breakpoint()` or `set_trace()`. For Hermes subagents, debug one process at a time.

## Verification Checklist

- [ ] After `pip install debugpy`, confirm: `python -c "import debugpy; print(debugpy.__version__)"`
- [ ] For remote debug, confirm the port is actually listening: `ss -tlnp | grep 5678`
- [ ] First breakpoint actually hits (if it doesn't, you likely have `PYTHONBREAKPOINT=0`, you're under xdist, or execution finished before attach)
- [ ] `where` / `w` shows the expected call stack
- [ ] Post-debug cleanup: no stray `breakpoint()` / `set_trace()` in committed code
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```

## One-Shot Recipes

**"Why is this dict missing a key?"**
```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**"This test passes in isolation but fails in the suite."**
```bash
scripts/run_tests.sh tests/the_test.py --pdb -p no:xdist
# But if it only fails WITH other tests:
source .venv/bin/activate
python -m pytest tests/ -x --pdb -p no:xdist
# Now it pdb-traps at the exact failing test after state accumulated.
```

**"My async handler deadlocks."**
```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```
Trigger the handler. `nc 127.0.0.1 4444`, then `w` to see the suspended frame, `!import asyncio; asyncio.all_tasks()` to see what else is pending.

**"Post-mortem on a crash in an Ink child process / subprocess."**
```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```

---

## Recipe 6: Remote Debugging — Complete Configuration

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  debugpy server (Python process)                            │
│  listen("0.0.0.0", 5678)  ←─── TCP DAP connection ──────  │
│  wait_for_client()                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                    network (TCP port 5678)
                              │
┌─────────────────────────────────────────────────────────────┐
│  DAP client (VS Code / Zed / JetBrains / debugpy CLI)     │
│  initialize → attach → setBreakpoints → configurationDone │
└─────────────────────────────────────────────────────────────┘
```

### Server Patterns

**Pattern A: Launch-and-wait (blocking)**

```python
import debugpy

# Listen on all interfaces — allows remote connections
debugpy.listen(("0.0.0.0", 5678))
print("Waiting for debugger attach...", flush=True)
debugpy.wait_for_client()  # Blocks until client connects
print("Debugger attached!", flush=True)
```

**Pattern B: Listen-only (non-blocking)**

```python
import debugpy

debugpy.listen(("0.0.0.0", 5678))
# Execution continues immediately — breakpoints will queue events
```

**Pattern C: Launch with module**

```bash
python -m debugpy \
  --listen 0.0.0.0:5678 \
  --wait-for-client \
  --log-to /tmp/debugpy.log \
  -m your_module arg1 arg2
```

**Pattern D: Attach to running process by PID**

```bash
python -m debugpy --attach 5678 --pid $(pgrep -f "your_script.py")
```

### Remote Host Configuration (SSH tunnel)

If the target runs on a remote server, tunnel the port:

```bash
# From LOCAL machine
ssh -L 5678:127.0.0.1:5678 user@remote-host
# Then connect your local IDE to 127.0.0.1:5678
```

Or reverse:

```bash
# From REMOTE machine
ssh -R 5678:127.0.0.1:5678 user@local-machine
```

### Security Considerations

- **Never** expose debugpy port to the public internet
- Use `127.0.0.1` for same-machine, `0.0.0.0` only on trusted networks
- Consider firewall rules: `iptables -A INPUT -p tcp --dport 5678 -j DROP`
- For production, prefer `remote-pdb` with `hn-TERM` secret:

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444, secret="your-secret-token")
# Client connects with:
# nc host 4444
# (remote-pdb will ask for secret if set)
```

---

## Recipe 7: VS Code Integration

### launch.json Configuration

Create `.vscode/launch.json` in the workspace root:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Attach to debugpy",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "127.0.0.1",
        "port": 5678
      },
      "justMyCode": false,
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/path/on/remote/server"
        }
      ],
      "redirectOutput": true,
      "showReturnValue": true
    },
    {
      "name": "Python: Remote Attach (SSH tunnel)",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "justMyCode": false,
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/home/deploy/hermes-agent"
        }
      ]
    },
    {
      "name": "Python: Launch Module",
      "type": "debugpy",
      "request": "launch",
      "module": "your_module",
      "args": ["arg1", "arg2"],
      "justMyCode": false,
      "subProcess": true
    },
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "justMyCode": false
    }
  ]
}
```

### VS Code Settings (settings.json)

```json
{
  "python.defaultInterpreterPath": "/home/deploy/hermes-agent/.venv/bin/python",
  "python.debugJustMyCode": false,
  "debug.console": {
    "inheritEnvironment": true
  },
  "remote.containers": {
    "debuggerPath": "/workspace"
  }
}
```

### Step-by-Step Attach Flow

1. **Server side** — add to entry point:

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```

2. **Start the process:**

```bash
python your_server.py
# Output: Waiting for debugger attach...
```

3. **VS Code** — set breakpoint in source file

4. **VS Code** — press F5, select "Python: Attach to debugpy"

5. Execution pauses at first breakpoint

### Remote SSH debugging with VS Code

If the target is on a remote server via SSH:

```json
{
  "name": "Remote SSH",
  "type": "debugpy",
  "request": "attach",
  "connect": {
    "host": "remote-server",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/home/user/project"
    }
  ]
}
```

Install the **"Remote - SSH"** extension in VS Code, connect to the remote host, then attach.

---

## Recipe 8: Docker Container Debugging

### Dockerfile Setup

Add debugpy to your container:

```dockerfile
FROM python:3.11-slim

# Install debugpy for debugging
RUN pip install debugpy

# For remote debugging, expose the debug port
EXPOSE 5678

# For local development with docker-compose, map the port
# ports:
#   - "5678:5678"
```

### Option A: Debug a new container (listen mode)

```bash
# Start container with debugpy waiting for attach
docker run --rm \
  -p 5678:5678 \
  -v $(pwd):/app \
  python:3.11-slim \
  python -m debugpy --listen 0.0.0.0:5678 --wait-for-client /app/your_script.py
```

### Option B: Attach to running container

```bash
# Get the container's PID
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' container_name)

# Use nsenter to enter the container's namespace and run debugpy
docker exec container_name python -m debugpy --attach 5678 --pid 1
```

Or more directly:

```bash
# Install debugpy in the running container and attach
docker exec container_name pip install debugpy
docker exec container_name python -m debugpy --listen 127.0.0.1:5678 --pid $(docker inspect --format '{{.State.Pid}}' container_name)
```

### Option C: docker-compose integration

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "5678:5678"
    command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m your_module
    # Or for development:
    # command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client your_script.py
```

### Container-to-Host path mapping

When attaching from host to container, map paths:

```json
{
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "/app"
    }
  ]
}
```

### docker-compose with volume mounts (development)

```yaml
services:
  app:
    build: .
    ports:
      - "5678:5678"
    volumes:
      - .:/app
    command: >
      python -m debugpy
      --listen 0.0.0.0:5678
      --wait-for-client
      --log-to /tmp/debugpy.log
      your_script.py
    environment:
      - DEBUG=1
```

### Verify container has debugpy

```bash
docker exec container_name python -c "import debugpy; print(debugpy.__version__)"
```

### Multi-container debugging

If your app spans multiple containers, each needs its own debugpy port:

```yaml
services:
  api:
    ports:
      - "5678:5678"
    command: python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m api
  worker:
    ports:
      - "5679:5679"
    command: python -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m worker
```

Attach to each separately with different ports.

---

## Recipe 9: Common Troubleshooting

### Issue: "Connection refused" or debugger never attaches

**Diagnosis checklist:**

```bash
# 1. Is the port actually listening?
ss -tlnp | grep 5678
# or on macOS:
lsof -i :5678

# 2. Is the process still running?
ps aux | grep debugpy | grep -v grep

# 3. Is there a firewall?
sudo iptables -L -n | grep 5678

# 4. Is debugpy installed in the right environment?
python -c "import debugpy; print(debugpy.__version__)"

# 5. Can you reach it locally?
curl -v telnet://127.0.0.1:5678
```

**Fixes:**

- If using SSH tunnel, verify tunnel is active: `ssh -O check user@host`
- If connecting remotely, ensure `0.0.0.0` not `127.0.0.1` on the server
- Check if process started but already finished: add `print("started")` before `wait_for_client()`

### Issue: Breakpoints not hitting

**Common causes:**

1. **File path mismatch** — pathMappings must match exact paths

```json
// Wrong:
"localRoot": "${workspaceFolder}"
// Right — must match the path debugpy sees:
"localRoot": "/Users/you/project",
"remoteRoot": "/app"
```

2. **Source file differs** — container may have old code

```bash
# Verify the source file contains your breakpoint
docker exec container_name grep -n breakpoint /app/your_script.py
```

3. **Optimized bytecode** — Python may be running `.pyc` only

```bash
# Ensure PYTHONDONTWRITEBYTECODE is NOT set
echo $PYTHONDONTWRITEBYTECODE
# Should be empty or "0"
```

4. **Breakpoint set before initialization**

Add `debugpy.wait_for_client()` before your first breakpoint, then set breakpoints after attach.

### Issue: "ptrace_scope" prevents attach by PID

```bash
# Check current value
cat /proc/sys/kernel/yama/ptrace_scope

# Temporary fix (needs root):
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Permanent fix — edit /etc/sysctl.d/10-ptrace.conf:
kernel.yama.ptrace_scope = 0
```

### Issue: Debugger attaches but immediately exits

The client sent `disconnect` or `shutdown` request. Check:
- VS Code's "disconnect" button was pressed
- Client timeout settings
- The process exited naturally after startup

### Issue: debugpy hangs on import

```bash
# Check for circular imports or slow imports
python -c "import debugpy; print('imported')"
# If this hangs, something in the environment is blocking
```

### Issue: Permission denied in Docker

```bash
# Container user may not match host user
docker exec -u root container_name tee /proc/sys/kernel/yama/ptrace_scope <<< 0
```

Or run container as privileged (not for production):

```bash
docker run --privileged ...
```

### Issue: VS Code "Cannot debug" — no module named debugpy

```bash
# Install debugpy in the Python environment VS Code is using
pip install debugpy
# Or in the selected interpreter:
/path/to/venv/bin/python -m pip install debugpy
```

### Issue: async/await not stepping correctly

For asyncio code in debugpy, set `justMyCode: false` and enable:

```json
{
  "python.experimental.debugger": {
    "defaultInterface": "async"
  }
}
```

Or use Python 3.13+ which has improved async debugging in pdb.

### Issue: subprocess debugging

When forking a child process, attach to each by name:

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```

Add this before fork, and each child will inherit the listener.

### Issue: Debugpy log analysis

Enable verbose logging:

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678), log_to=10)  # log_to=10 = STDOUT
# or:
debugpy.listen(("127.0.0.1", 5678), log_dir="/tmp")
```

Logs go to `/tmp/debugpy.log` or stdout. Look for:
- `DAP <-- initialize` — client connected
- `DAP <-- setBreakpoints` — breakpoints registered
- `DAP <-- configurationDone` — execution started

### Quick Reference: Debugpy Log Levels

| Level | Value | Output |
|-------|-------|--------|
| `None` | 0 | No debug output |
| `10` | 10 | STDOUT (simplest) |
| `debugpy.LOG_ALL` | 9 | All events + DAP messages |
| Path string | — | Log to file |

---

## Quick Reference Cheatsheet

| Scenario | Tool | Command |
|----------|------|---------|
| Local breakpoint | `breakpoint()` | Run normally |
| Local script debugging | `python -m pdb` | `python -m pdb script.py` |
| Attach to running process | debugpy | `python -m debugpy --listen 5678 --pid <PID>` |
| Wait for debugger on launch | debugpy | `python -m debugpy --listen 5678 --wait-for-client -m module` |
| Terminal DAP client | debugpy CLI | `python -m debugpy --connect 5678` |
| nc-style REPL (simplest) | remote-pdb | `from remote_pdb import set_trace; set_trace(port=4444)` |
| Docker container | debugpy | `docker run -p 5678:5678 ... python -m debugpy --listen 5678 ...` |
| VS Code attach | launch.json | Select "Attach to debugpy", F5 |
| Post-mortem | pdb | `python -m pdb -c continue script.py` |
