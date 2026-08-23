# OpenClaw ↔ Hermes Bridge — verified recipes

Session: 2026-08-18. macOS, Hermes gateway + OpenClaw gateway both running locally.

## 1. OpenClaw MCP bridge — register + verify

OpenClaw gateway listens at `ws://127.0.0.1:18789` (LaunchAgent `ai.openclaw.gateway`).
Token is in `~/.openclaw/openclaw.json` under the `token` key (mode: token).

`hermes mcp add` fails its connect test for stdio servers needing `--url`, so write the entry as a
JSON string (Hermes blocks hand-editing config.yaml but allows `hermes config set`):

```bash
hermes config set mcp_servers.openclaw '{"command":"openclaw","args":["mcp","serve","--url","ws://127.0.0.1:18789","--token","75e6f691fbde57d6ca52ceb79703508162e873984b789e4c"],"enabled":true}'
```

Then restart the Hermes gateway from a **separate** shell (not from inside the gateway process):
```bash
hermes gateway restart
```

Verify with a raw JSON-RPC probe (do NOT trust `hermes mcp test` — it crashes on stdio entries):
```python
import subprocess, json, os, time
p = subprocess.Popen(
    ["openclaw","mcp","serve","--url","ws://127.0.0.1:18789","--token","<TOKEN>"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ))
def rpc(i, m, params=None):
    p.stdin.write(json.dumps({"jsonrpc":"2.0","id":i,"method":m,"params":params or {}})+"\n"); p.stdin.flush()
rpc(1,"initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"p","version":"1"}})
time.sleep(2); p.stdout.readline()
rpc(2,"tools/list",{}); time.sleep(1)
print([t["name"] for t in json.loads(p.stdout.readline())["result"]["tools"]])
p.terminate()
```
Expected: 9 tools (conversations_list, conversation_get, messages_read, attachments_fetch,
events_poll, events_wait, messages_send, permissions_list_open, permissions_respond).

## 2. PYTHONPATH cross-Python contamination (pydantic_core ABI crash)

Symptom: a Python (e.g. system 3.14) running a package that imports `fastapi`/`pydantic` dies with
`ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`, even though `pydantic_core`
imports fine in its OWN interpreter.

Root cause: the process inherited `PYTHONPATH=/Users/aimac/.hermes/hermes-agent:/Users/aimac/.hermes/hermes-agent/venv/lib/python3.11/site-packages`
from its parent. Python 3.14 then resolves `pydantic_core` to the 3.11-compiled `.so`
(ABI-incompatible) and fails. The Hermes *gateway* process pops PYTHONPATH itself, but its children
(subprocesses it spawns) can still inherit a leaked value from the original app-launch environment.

Diagnosis:
```bash
echo "$PYTHONPATH"                 # shows the 3.11 venv path leak
python3.14 -c "import pydantic_core"   # works in clean shell, fails when PYTHONPATH is set
```

Fix — launch with `env -i` (wipe inherited env) and an explicit clean PATH:
```bash
env -i HOME=/Users/aimac PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/local/bin:/usr/bin:/bin \
  /usr/local/bin/python3.14 -m skillclaw start --daemon
```

For a persistent service, wrap it in a LaunchAgent whose `ProgramArguments` uses
`/bin/sh -c 'exec env -i HOME=… PATH=… python3.14 -m …'` and an explicit `EnvironmentVariables`
dict (no PYTHONPATH). This survives reboots and never inherits the leak.

Note: the leak is runtime-only (not in any .zshrc/launchd plist). It disappears after the desktop
app is relaunched, but the LaunchAgent isolation makes SkillClaw immune regardless.

## 3. SkillClaw reinstall from upstream

If `skillclaw` is an *editable* install whose `direct_url.json` points at a deleted temp dir
(`file:///private/tmp/skillclaw_tmp`), the package source is physically gone — `pip show` reports
it but `import skillclaw` fails. Reinstall from source:

```bash
git clone --depth 1 https://github.com/AMAP-ML/SkillClaw.git /tmp/SkillClaw
cd /tmp/SkillClaw
env -i PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/local/bin:/usr/bin:/bin \
  /usr/local/bin/python3.14 -m pip uninstall -y skillclaw
env -i PATH=/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/local/bin:/usr/bin:/bin \
  /usr/local/bin/python3.14 -m pip install .
```

After install, smoke test: `python3.14 -m skillclaw status` → `running (proxy=:30000)`,
and `curl -s http://127.0.0.1:30000/healthz` → `{"ok":true}`.
