# SkillClaw Diagnosis (symptom → root cause map)

SkillClaw is the "skills evolve collectively across Hermes + OpenClaw" companion.
On this box it was installed 2026-07-25 and has been dead since first launch.

## Symptom 1 — `import skillclaw` fails: `No module named 'skillclaw'`

Root cause: the package was installed as an **editable** pip install whose source
lived in `file:///private/tmp/skillclaw_tmp`. macOS purged that temp dir, so the
editable `.pth` finder (`__editable__.skillclaw-0.4.0.pth` +
`__editable___skillclaw_0_4_0_finder.py` in the 3.14 site-packages) now points at a
nonexistent path. The `.py` source exists nowhere on disk (verified by full-disk
`find / -path "*skillclaw/cli.py"` → no results).

Fix: re-obtain the SkillClaw source from wherever it originally came from
(local repo, share, install script). `pip install skillclaw` will 404 — it is not on
PyPI. Do NOT try to "repair" in place; there is no source to repair.

Verify reinstall worked:
```bash
# /usr/local/bin/python3.14 is the interpreter the stub uses
env -i /usr/local/bin/python3.14 -c "import skillclaw; print(skillclaw.__file__)"
```

## Symptom 2 — `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`

This was the *first* crash in the log (2026-07-25), before the source was even lost.
It looks like a missing dependency but is **cross-Python ABI pollution**:

- The stub `/Library/Frameworks/Python.framework/Versions/3.14/bin/skillclaw` is shebanged
  `#!/usr/local/bin/python3.14`.
- But `PYTHONPATH` (a login-env export) contained
  `/Users/aimac/.hermes/hermes-agent/venv/lib/python3.11/site-packages`.
- So 3.14 imported `fastapi`/`pydantic` from the 3.11 venv and tried to load
  3.11-compiled `pydantic_core._pydantic_core` (a `.so`) under a 3.14 ABI → fails.

Debugging pattern worth reusing: when a tool dies on
`No module named '<pkg>._<ext>'` (note the leading underscore = compiled extension)
under an interpreter version *different* from where the dep is actually installed,
check `PYTHONPATH`/`.pth` for cross-version `.so` injection BEFORE assuming the
package is missing. Clearing `PYTHONPATH` for that invocation isolates it:
```bash
PYTHONPATH= /usr/local/bin/python3.14 -m skillclaw ...   # only useful if source still present
```

## Config (what survived)

`~/.skillclaw/config.yaml` still exists and is valid:
```
agent_type: hermes
claw_type: openclaw
configure_openclaw: true
dashboard:  enabled:false  port:3788
evolve:     (server_url empty)
prm:        enabled:true
```

The config is fine; the code is what's gone. Re-point `configure_openclaw` + the
source path on reinstall and the dashboard/evolve layers come back.

## Bottom line for future sessions

If the user asks "did the Hermes↔OpenClaw fusion improve anything / is SkillClaw
working" — the honest answer is: SkillClaw has never run on this box. The OpenClaw
**MCP bridge** is the only real integration, and even that needs the gateway restart
step (see SKILL.md "Working MCP bridge recipe"). Don't overclaim fusion capability.
