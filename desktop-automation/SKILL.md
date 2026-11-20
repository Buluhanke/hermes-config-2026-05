---
name: desktop-automation
description: Desktop GUI automation via accessibility tree + refs.
category: devops
version: 0.1.0
author: Hermes Agent
license: MIT
hermes:
  tags: [desktop, automation, agent-desktop, accessibility]
  related_skills: [cua-driver-rs]
---

# desktop-automation

Class-level skill: drive native desktop GUIs by reading the OS accessibility tree and acting on element refs, instead of screenshots or pixel matching. Covers agent-desktop (Vercel Labs CLI / MCP / C library) as the primary driver, with macOS-specific window-discovery fixes and Hermes scheduling integration.

## When to Use
- Task requires driving a **native desktop app or window** (settings panes, file managers, IDE windows, custom GUI controls, system dialogs).
- Task **does not** require a web page or browser tab — for web content use agent-browser / agent-cu, not this.
- The app exposes its UI through the OS accessibility tree (macOS AX, Windows UI Automation, Linux AT-SPI). If the app draws its own controls without an accessibility tree, this class cannot see it.

## What this class covers
- Observe a native app's window / elements through AX (macOS), UI Automation (Windows), AT-SPI (Linux).
- Act on elements via snapshot-qualified refs (`@<snapshot_id>:<element_index>`).
- Observe again to verify the result.
- Use headless ref actions by default; `--headed` only when physical input is explicitly required.

## Always-on rules
1. **Do not build from scratch.** Before writing a new automation path, search GitHub for an existing driver, fork, or harness (agent-desktop, agent-browser, Webwright, cua-driver, etc.) and reuse it. The goal is standing on prior work, not re-implementing the same loop.
2. **Install a tested build, not a source-from-scratch path, unless you know the build chain.** Prefer a pinned release binary or a reviewed fork. Verify checksums when the release publishes them.
3. **macOS: install the Call Desk fork, not upstream.** Upstream `agent-desktop` has unstable global window inventory on macOS (`global_window_inventory_unstable` / `WINDOW_NOT_FOUND` even when the app is running). The `joewilsonai/call-desk-agent-desktop` fork (tag `call-desk-macos-2026-11-02`) adds macOS window discovery from `AXMainWindow` / `AXFocusedWindow` / `AXChildren` and process-identity frontmost verification. It is a fork, not an upstream Vercel release — do not treat it as one.
4. **`list-apps` is UNSTABLE on macOS.** It times out with `application_inventory_unstable` even when the app is running (150+ attempts, 0 churn). Treat it as unusable for window discovery. Use `launch <app> --activate` to start/activate the app, then `snapshot --window-id <id>` for element ops. `launch` returns the window id in `data.window.id`, so no separate inventory step is needed.
5. **Refs are bound to their snapshot.** After any UI change, a stale or ambiguous ref returns `STALE_REF` or `AMBIGUOUS_TARGET`. Take a new snapshot before acting.
6. **Headless by default.** Ref actions use semantic accessibility calls and do not move the pointer, take focus, synthesize keys, or touch the clipboard. Only switch to `--headed` when the task explicitly requires physical input (double-click, hover, drag, focus).
7. **Screen recording is a separate permission.** `accessibility` must be granted; `screen_recording` is denied by default and only affects screenshot / overlay / visual capture features, not headless element reads.

## The observe–act–verify loop (macOS)

`--app` filter is UNSTABLE on macOS. The stable path is:

```bash
# 1. launch + activate the app; `launch` prints the window id in `data.window.id`
agent-desktop launch "<App Name>" --activate

# 2. snapshot the specific window
agent-desktop snapshot --window-id <w-id> -i --compact

# 3. drill if dense (optional)
agent-desktop snapshot --root @<snapshot>:<element> -i --compact

# 4. act
agent-desktop click '@<snapshot>:<element>'
agent-desktop type '@<snapshot>:<element>' --stdin   # text through stdin, not argv

# 5. verify: re-read the same region
agent-desktop snapshot --root @<snapshot>:<element> -i --compact
```

- `-i` keeps interactive nodes only. Dense apps need a skeleton + `--root` drill first.
- `wait` for async UI changes; never hard `sleep`.
- `type` / `set-value` / `clipboard-set` accept `--stdin` to keep text out of process arguments.
- PowerShell: quote every ref (`'@s8f3k2p9:e8'`) — a bare `@token` is the splatting operator.
- A command that finishes with `ok: true` does NOT prove the app changed. Read the postcondition.

## What this class does NOT cover
- Web page automation (use agent-browser for that; do not point agent-desktop at a browser tab).
- Electron app web content: agent-desktop sees the app through its accessibility tree; connect agent-browser to a loopback DevTools port for web content inside a Chromium app.
- Screenshots as the primary signal. Screenshots are for visual-only issues (obscured button, chart, layout) that the accessibility tree cannot express.
- Credential/permission/payment/2FA dialogs.
