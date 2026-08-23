# pi-computer-use Bridge — Protocol & Session Details

## Protocol Commands (verified against binary v0.4.3)

All commands: send JSON request object, receive one JSON response line.

### diagnostics
```python
{"id": "req_1", "cmd": "diagnostics", "protocolVersion": 6}
# → {"ok": true, "result": {protocolVersion, accessibility, screenRecording, invariants[], pid, parentPid}}
```

### listApps
```python
{"id": "req_2", "cmd": "listApps"}
# → {"ok": true, "result": [{appName, bundleId?, pid, isFrontmost}, ...]}
# No TCC required
```

### getFrontmost
```python
{"id": "req_3", "cmd": "getFrontmost"}
# → {"ok": true, "result": {windowTitle, windowRef, appName, pid, bundleId}}
# windowRef is a CGWindow ID string ("w5")
# No TCC required
```

### listWindows(pid: int)
```python
{"id": "req_4", "cmd": "listWindows", "pid": 936}
# → {"ok": true, "result": [{windowId?, windowRef, title, pid, appName, ...}, ...]}
# Most apps return [] (CGWindow layer doesn't register them)
# Use listApps first to get pid of target app
```

### listRoots(title?: "")
```python
{"id": "req_5", "cmd": "listRoots", "title": ""}
# → {"ok": true, "result": {"roots": [{rootRef, windowId?, pid, appName, bundleId, title, role, ...}]}}
# rootRef is a CGWindow ID (e.g. "w2"), NOT an AX ref
# Combine with listWindows to find usable windows
```

### look(windowRef: string, windowId?: int)
```python
{"id": "req_6", "cmd": "look", "windowRef": "w2", "windowId": 123}
# → {"ok": true, "result": {lookId, outline: {nodes: [{ref, role, subrole, title, value, canPress, canFocus, isTextInput}, ...]}}}
# Requires TCC: accessibility=true AND screenRecording=true
# windowRef alone may fail with root_not_found — try with both windowRef and windowId
# Returns 0 nodes for WebView windows (Chrome, Clash Verge WebView)
```

### act(lookId: string, action: string, target: {}, params: {})
```python
{"id": "req_7", "cmd": "act", "lookId": "...", "action": "left", "target": {"ref": "@e5"}, "params": {"clickCount": 1}}
# action: "left", "right", "double", "setValue", "press"
# target: {"ref": "@e5"} or {"x": 100, "y": 200}
# params: {"clickCount": 1} or {"text": "hello"} or {"keys": ["cmd", "t"]}
```

## This System: macOS 26.5.1 arm64

### Daemon socket paths (two independent daemons)
- `/tmp/test-bridge.sock` — spawned from terminal, has full TCC permissions
- `~/Library/Caches/pi-computer-use/bridge.sock` — launch agent (open -n -g), TCC NOT inherited

### Working commands without TCC
- `diagnostics`, `listApps`, `getFrontmost` — always work

### Commands requiring TCC
- `look` → `{'error': {'code': 'root_not_found'}}` without TCC
- `act` → needs prior successful `look`

### Commands with mixed results
- `listWindows` → most apps return `[]` (Chrome, Hammerspoon, Notification Center)
- Clash Verge returns 1 window but `look` gives nodes=0 (WebView limitation)

## Auto-Open System Settings

```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
```

## Bridge Binary

- Path: `/Applications/pi-computer-use.app/Contents/MacOS/bridge`
- Protocol version: 6
- Architecture: arm64 (Mach-O)

## NPM Package

```bash
npm install @injaneity/pi-computer-use  # v0.4.3
```
