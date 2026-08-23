---
name: pi-computer-use
description: |
  Hermes alternative backend for the `computer_use` tool — pi-computer-use Swift daemon
  provides AX-ref-first semantic desktop control. Activate via HERMES_COMPUTER_USE_BACKEND=pi.
  Requires one-time TCC authorization in System Settings.
version: 1.0.1
platforms: [macos]
---

# pi-computer-use Backend for Hermes

pi-computer-use (injaneity/pi-computer-use, MIT, ~1.1K stars) is a Swift daemon that
exposes macOS Accessibility (AX) API via Unix socket JSON-RPC. Hermes has a
`PiComputerUseBackend` that plugs into the standard `computer_use` tool interface.

## Activation

```bash
HERMES_COMPUTER_USE_BACKEND=pi hermes gateway start
```

Backend implemented at:
- `~/.hermes/hermes-agent/tools/computer_use/backends/pi_backend.py`
- `~/.hermes/hermes-agent/tools/computer_use/tool.py` (backend registration in `_get_backend()`)

## TCC Authorization (Required — One-Time)

**Auto-open System Settings panes:**
```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
```

1. **Accessibility** → add `/Applications/pi-computer-use.app`
2. **Screen Recording** → add `pi-computer-use.app`

### Critical TCC Finding

`open -n -g` (launch agent / Login Item) does **NOT** inherit terminal TCC context.
A bridge spawned from terminal gets full permissions; the launch agent needs its own grant.

Symptom: terminal-spawned daemon → `accessibility: true`, launch agent → `accessibility: false`.

Fix: after manual TCC grant, kill and restart the launch agent:
```bash
kill $(ps aux | grep "bridge serve.*library/Caches" | grep -v grep | awk '{print $2}')
open -n -g -b com.injaneity.pi-computer-use --args serve --socket ~/Library/Caches/pi-computer-use/bridge.sock
```

Verify TCC:
```python
import socket, json, os
sock_path = os.path.expanduser("~/Library/Caches/pi-computer-use/bridge.sock")
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(sock_path)
sock.sendall((json.dumps({"id":"d","cmd":"diagnostics","protocolVersion":6})+"\n").encode())
r = json.loads(sock.recv(4096).decode())["result"]
print(r["accessibility"], r["screenRecording"])  # Both must be True
```

## Key Protocol Facts

- Socket: `~/Library/Caches/pi-computer-use/bridge.sock`
- Commands: `diagnostics`, `listApps`, `listRoots`, `getFrontmost`, `listWindows(pid:int)`, `look(windowRef, windowId?)`, `act(lookId, action, target, params)`, `focusWindow`, `getMousePosition`
- `listRoots` returns CGWindow IDs (`"w2"`), NOT AX refs — use `look` to resolve to AX tree
- `look` returns `root_not_found` on system-protected surfaces (loginwindow) or without TCC
- `listApps` + `listWindows(pid)` together give the full window inventory per app
- `getFrontmost` + `look` is the primary capture flow

## cua-driver vs pi-backend

| | cua-driver | pi-backend |
|---|---|---|
| Click | Coordinates | AX ref (`@eN`) |
| UI-change resilient | No | Yes |
| macOS background | Full | Full (needs TCC) |
| Windows | Yes | Yes (UIA) |

Use pi when: app UI changes frequently, or AX coverage is rich. Use cua-driver as default.

## Known Limitations

- `look` on loginwindow, menu bar, system-protected surfaces → `root_not_found`
- Chrome/浏览器窗口在 CGWindow layer 返回 `[]`（WebView 不注册系统窗口）
- launch agent 方式权限与 terminal 方式不同，需单独授权

## Pitfalls

### Chrome multi-instance: duplicate bundle IDs

Chrome can run multiple independent processes. When `listWindows` or `look` returns
empty results for an app that is visibly open, check if Chrome has two running
instances (bundle ID `com.google.Chrome` appears twice in `ps aux`).

Each instance owns different windows. The instance that owns the window you want
depends on how Chrome was launched — user gesture vs. automation.

**Fix**: If targeting a specific Chrome window fails, try connecting via CDP on the
correct Chrome instance's debugging port (`chrome://inspect/#devices`), or use the
Chrome window's CGWindow ID directly rather than the PID.

## Bridge Binary Info

- Path: `/Applications/pi-computer-use.app/Contents/MacOS/bridge`
- Architecture: `Mach-O 64-bit executable arm64` (Mac mini M4)
- Protocol version: 6
- NPM: `npm install @injaneity/pi-computer-use` (v0.4.3)

## Open System Settings Panes via URL

```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
```
