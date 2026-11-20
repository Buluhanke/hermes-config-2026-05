# agent-desktop on macOS — window discovery fix

**Root cause:** `agent-desktop list-apps` is unstable on macOS. It times out with `application_inventory_unstable` even when the app is running (150+ attempts, 0 churn). It is not a transient fluke. Do not rely on it for window discovery.

**Stable workflow (macOS):**

```bash
# 1. Launch + activate the target app. `launch` prints the window id
#    in `data.window.id` — no separate inventory step needed.
agent-desktop launch "Finder" --activate
# => {"app":"访达","pid":1199,...,"window":{"id":"w-1166","title":"应用程序","visible":true},...}

# 2. Snapshot the specific window by id.
agent-desktop snapshot --window-id w-1166 -i --compact

# 3. Drill if dense; act; verify
agent-desktop snapshot --root @<snapshot>:<element> -i --compact
agent-desktop click '@<snapshot>:<element>'
agent-desktop type '@<snapshot>:<element>' --stdin
agent-desktop snapshot --root @<snapshot>:<element> -i --compact
```

**Why `list-apps` fails:** agent-desktop's macOS inventory uses a global window enumeration loop that never stabilises. The app exists in the accessibility tree (visible in `System Events` process list), but `list-apps` cannot return a stable result set.

**Why `snapshot --skeleton -i` is NOT a replacement:** `snapshot --skeleton -i` reads the **currently focused** app, not the specified one. After `launch` activates Finder, the terminal may still hold focus. Always use `launch` to target a specific app, then snapshot with its window id.

**Key commands:**
- `agent-desktop launch "<App>" --activate` — starts or activates; returns `data.window.id`
- `agent-desktop snapshot --window-id <id> --compact` — snapshot a specific window
- `agent-desktop list-windows --app <App>` — list windows of an app (unstable; use only for display)

**Configuration:**
- Accessibility permission: granted
- Screen recording permission: granted (needed only for `screenshot`/`overlay`)
- Automation permission (System Events): required for `snapshott` and element ops