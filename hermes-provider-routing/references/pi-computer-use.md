# pi-computer-use Bridge Protocol Notes

## Live Commands (verified against binary v0.4.3)

**Always probe the live binary rather than trusting TypeScript source comments.** The TS source sometimes describes commands that aren't yet in the compiled binary.

| Command | Args | Returns |
|---|---|---|
| `diagnostics` | — | `protocolVersion`, `accessibility`, `screenRecording`, `invariants` |
| `listApps` | — | `[{"appName", "bundleId", "pid", "isFrontmost"}]` |
| `listRoots` | `title: ""` | `{"roots": [...]}` with `rootRef`, `windowId`, `bundleId`, `appName` |
| `getFrontmost` | — | `{"windowRef", "pid", "windowId", "appName", "windowTitle"}` |
| `look` | `windowRef: "wN"` | Full look response with `lookId`, `outline.nodes`, `image` |
| `act` | `rootRef`, `action`, `target`, `params` | `{"outcome", "execution"}` |
| `focusWindow` | `pid: N` | Focus result |
| `hitTest` | `lookId`, `x`, `y` | Element at coordinate |
| `getMousePosition` | — | `{"x", "y"}` |

## Key TCC/Permission Notes

- `diagnostics.accessibility` and `diagnostics.screenRecording` reflect TCC permission state **as seen by the daemon process itself**
- A background launch agent may report `accessibility: false` even when AX actually works for real apps — test with a real app (Terminal) rather than system UI (loginwindow)
- If `look` returns `root_not_found`: the app's AX elements are not accessible to the daemon process — TCC boundary, not a code bug
- Permissions are granted per-process: the daemon needs its own TCC entry in **System Settings → Privacy & Security → Accessibility**
- `com.apple.loginwindow` is never AX-accessible — don't try to automate it

## Hermes Backend Integration

Hermes's `computer_use` tool uses a swappable `ComputerUseBackend` in `tools/computer_use/backend.py`. The env var `HERMES_COMPUTER_USE_BACKEND` selects the backend:
- `cua` / `cua-driver` (default) → CuaDriverBackend
- `pi` / `pi-computer-use` → PiComputerUseBackend (in `tools/computer_use/backends/pi_backend.py`)

To add a new backend: create `tools/computer_use/backends/<name>_backend.py` implementing `ComputerUseBackend`, then register it in `tools/computer_use/tool.py` `_get_backend()`.
