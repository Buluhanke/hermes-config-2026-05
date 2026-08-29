---
name: windows-wmi-exec
description: Use when SSH/RDP/WinRM closed, SMB/RPC open on Windows.
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [windows, wmi, impacket, lateral-movement, lan, sysadmin]
    related_skills: [agent-rdp, hackintosh-recovery]
---

# Windows WMI Remote Exec

## When to use
Target is a Windows host reachable on LAN but with **no remote-exec port open**:
- 22/3389/5985 closed, **445 + 135 OPEN** ← your entry.
Fallback for `agent-rdp` when RDP is down.

## Required
- **Admin credentials** (user + password + domain/`WORKGROUP`). Cannot shell without them — ask, never guess.
- Same /24 LAN or routed.

## Diagnostic (controlling Mac/Linux)
```bash
ping -c 3 <WIN_IP>
for p in 22 3389 445 139 5985 5900 135; do
  if nc -z -w 2 <WIN_IP> $p 2>/dev/null; then echo "OPEN   $p"; else echo "closed $p"; fi
done
```

## Install impacket (controlling host)
```bash
python3 -m pip install impacket          # yields wmiexec.py / psexec.py
wmiexec.py 2>&1 | head -2                 # verify
```
System Python 3.14 puts console scripts in the framework bin dir (e.g. `/Library/Frameworks/Python.framework/Versions/3.14/bin/`); use full path or prepend PATH.

## Shell
```bash
wmiexec.py 'Administrator:PASSWORD@<WIN_IP>'          # WORKGROUP default
wmiexec.py 'DOMAIN/Administrator:PASSWORD@<WIN_IP>'   # domain-joined
psexec.py 'Administrator:PASSWORD@<WIN_IP>' cmd.exe   # fallback (drops service bin)
```

## Deliver a fix script without touching Windows
1. Host over LAN HTTP on the Mac:
   ```bash
   cd /path/to/scripts && python3 -m http.server 8000 --bind <MAC_LAN_IP>
   curl -s -m 3 http://<MAC_LAN_IP>:8000/script.ps1 -o /dev/null -w "%{http_code}"   # expect 200
   ```
   **Lifecycle gotcha:** a server launched with trailing `&` inside a foreground terminal call is reaped when that call returns. Launch it as a real background process (`terminal(background=true)` / `nohup ... &` disown) so it survives.
2. From the Windows shell (wmiexec), one-liner:
   ```
   powershell -ep Bypass -c "irm http://<MAC_LAN_IP>:8000/script.ps1 | iex"
   ```

## Pitfalls
- **Confirm target is NOT localhost.** If the user says "另一台电脑 / 不是本机", plan remote access immediately — do NOT scan/operate on localhost.
- `nc -z -w` against a firewalled host can hang the whole loop past the tool timeout — bound each probe with its own `nc -w` and a generous tool timeout.
- impacket needs WMI/DCOM: port **135 + dynamic RPC (49152+)**. If high RPC ports are firewalled, wmiexec may fail — fall back to dropping the script on an exposed SMB share + Task Scheduler/`at`.
- Always back up before mutating remote state.

## Overlap
Complements `agent-rdp` (RDP-based Windows control). Use this when RDP(3389) is closed but SMB/RPC are open.
