# Quick Reference & Troubleshooting

## Checklist
- [ ] Browser toolset enabled: `hermes tools enable browser`
- [ ] Chromium path set (if needed): `hermes config set browser.chromium_path '/path/to/chrome'`
- [ ] agent-browser installed (optional): `npm i -g @agent-browser/cli`
- [ ] Chrome launched with remote debugging (if attaching):
  ```bash
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug-profile"
  ```
- [ ] Connected in Hermes: `/browser connect --port 9222`
- [ ] Navigated: `browser_navigate --url 'https://example.com'`
- [ ] Snapshot taken: `browser_snapshot` (note refs like `@e3`)
- [ ] Interacted: `browser_type`, `browser_click`, `browser_vision`
- [ ] Disconnected when done: `/browser disconnect`

## Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `browser_navigate` does nothing / returns empty snapshot | Chrome not launched with debugging port or wrong port | Ensure Chrome started with `--remote-debugging-port=<port>` and match it in `/browser connect --port <port>` |
| Connection refused error on `/browser connect` | Chrome not running or firewall blocking | Start Chrome; verify no proxy/firewall blocks localhost:<port> |
| Element refs (`@eX`) missing after snapshot | Page still loading; DOM not ready | After `browser_navigate`, send a harmless key press (`browser_press --key 'Tab'`) or wait 2 seconds before snapshot |
| Click/type does nothing | Element not visible (off‑screen or inside iframe) | Scroll into view (`browser_scroll down`) or switch context if inside iframe (use `browser_cdp` to target frame) |
| Vision tool returns blank or error | Screenshot failed (headless mode or no GPU) | Ensure you are using headed Chromium (default) and not forcing headless via config; disable any `--headless` flags |
| After Hermes restart, previous login state lost | Using Hermes‑launched Chromium (no persistent profile) | Attach to a persistent Chrome user‑data dir as shown in the checklist |
| Multiple tabs confusing which ref belongs to which tab | No tab tracking in snapshot | Use `/browser list` (if available) or manually open new tab with `Control+t` then navigate; note that each `browser_navigate` loads URL in current tab unless you opened a new one first |

## Quick Commands Reference

- **Enable tools:** `hermes tools enable browser`
- **Set Chromium path:** `hermes config set browser.chromium_path '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'`
- **List available browser commands:** `/help` (look for `browser_*` commands)
- **Connect to existing Chrome:** `/browser connect --port 9222`
- **Disconnect:** `/browser disconnect`
- **Open new tab:** `browser_press --key 'Control+t'`
- **Refresh page:** `browser_press --key 'F5'` or `browser_press --key 'Control+r'`
- **Scroll down:** `browser_scroll --direction down`
- **Take screenshot (optional):** `browser_vision --question 'Describe the page'` (returns description; for actual image use `browser_vision` with `annotate:true` then read `screenshot_path` from output)

Keep this file handy; it updates as you discover new tips.