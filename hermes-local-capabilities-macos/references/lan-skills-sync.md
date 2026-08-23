# Sync skills from a sibling LAN Mac that also runs Hermes

Use this when the user has another Mac on the LAN (e.g. a Mac mini) with its own
Hermes install and wants skills brought over. The skills are plain files at
`~/.hermes/skills/` on the remote — pull, curate, merge. Do NOT bulk-copy.

## Hard rule: curate before importing (user instruction)
The user explicitly rejected a wholesale copy: "我不要全部拿，是需要你检阅过的，对我们有用的".
Workflow per import:
1. Pull ONLY the index + each `SKILL.md`'s frontmatter/trigger/one-line description first.
2. Inspect each: does this machine already have it? Does it fit the user's actual use cases?
3. Fetch full text for the curated subset only; dedup & merge into `~/.hermes/skills/`.
4. Report: introduced / why useful / skipped / skip reason.

## Reachability probe (do this before asking for creds)
- `ping` + port scan (22, 139/445 SMB, 548 AFP, 5900 VNC, 5000/7000).
- Observed on one LAN Mac mini: `22` and `5900` open; `5000`/`7000` are **Apple AirTunes**
  (HTTP 403, `Server: AirTunes/...`), NOT Hermes; **SMB(445)/AFP(548) closed** → no file-share
  shortcut, so SSH (or VNC) is the only entry. If SMB/AFP were open, `mount_smbfs` would be
  the easy path and you'd skip SSH entirely.

## Auth gotcha — macOS sshd rejects paramiko password auth
macOS "Remote Login" presents the password prompt as **keyboard-interactive**, not the
`password` method. So:
```python
paramiko.SSHClient().connect(host, username, password=...)   # -> AuthenticationException
transport.auth_interactive(user, handler)                     # also commonly fails on macOS
```
**Fix:** drive the REAL `ssh` binary with `pexpect` and surface the true prompt:
```python
import pexpect
child = pexpect.spawn("ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password,keyboard-interactive kk@192.168.0.4", encoding="utf-8", timeout=25)
i = child.expect([r"[Pp]assword:\s*", pexpect.EOF, pexpect.TIMEOUT], timeout=20)
if i == 0:
    child.sendline(PASS)
    # reconnect with child after auth to run commands / use the interactive shell
```
This also *proves* whether a credential is actually wrong: a real `Permission denied,
please try again.` + second password prompt means the password is wrong, not a method bug.
(That is exactly how we confirmed the supplied `3308` was not `kk`'s SSH password.)

## Python deps — install into the Hermes venv, not system
The connecting Mac's system `python3` is 3.9 and its `venv` lacks pip; the Hermes venv is
3.11 at `/Users/kk/.hermes/hermes-agent/venv`. Install there:
```bash
/Users/kk/.hermes/hermes-agent/venv/bin/pip install paramiko pexpect
/Users/kk/.hermes/hermes-agent/venv/bin/python your_script.py
```
Avoid `brew`/`sshpass` — usually absent and not worth installing just for this.

## Once authenticated: pull, then curate
```bash
# index + frontmatter only (stage 1)
ssh kk@192.168.0.4 'find ~/.hermes/skills -maxdepth 2 -name SKILL.md'
# then for each: read frontmatter; after curation, pull full dirs:
rsync -avz kk@192.168.0.4:~/.hermes/skills/<curated>/ ~/.hermes/skills/<curated>/
```
No `sshpass`? The user can run the `scp`/`rsync` themselves on the Mac mini and hand you
`/tmp/mm_skills` to inspect — same curated result, just user-mediated.
