# Chrome CDP Control — Full Setup Recipe (macOS)

## 0. Safety check (cross-machine config merge)
If you were handed a config exported from ANOTHER machine (different `$HOME`, different user, bound to external keys/endpoints):
```bash
grep -oE '^[A-Z_]+=' ~/.hermes/.env | sed 's/=$//' | sort   # which keys actually exist here?
```
A full overwrite will DESTROY a working install if the imported keys are absent. Prefer ADDITIVE edits: only add the new capability (browser CDP), leave `model:` and `web:` alone. Confirm scope with the user first.

## 1. Mirror login state (run once)
```bash
SRC="$HOME/Library/Application Support/Google/Chrome"
DST="$HOME/.hermes/chrome-profile-mirror"
mkdir -p "$DST"
cp "$SRC/Local State" "$DST/Local State"
cp -R "$SRC/Default" "$DST/Default"
chmod -R u+rwX "$DST"
```

## 2. Launch the debug instance (background)
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$DST" \
  --no-first-run \
  --no-default-browser-check
# Do NOT pass --no-startup-window (process exits immediately on Chrome 150).
```

## 3. Wire config.yaml (security-protected — use `hermes config set`, NOT patch)
```bash
hermes config set browser.cdp_url ws://127.0.0.1:9222
hermes config set browser.engine auto
hermes config set browser.command_timeout 30
hermes config set browser.dialog_policy must_respond
hermes config set browser.dialog_timeout_s 300
hermes config set browser.allow_private_urls false
hermes config set browser.auto_local_for_private_urls true
hermes config set browser.record_sessions false
hermes config set mcp_servers.chrome-devtools-mcp.command npx
```

## 4. Fix the MCP args list (hermes config set stringifies lists!)
`hermes config set ...args '["-y","chrome-devtools-mcp@latest","--browserUrl=http://127.0.0.1:9222"]'`
stores a STRING. Repair with a python yaml pass:
```python
import yaml
p = "/Users/kk/.hermes/config.yaml"
c = yaml.safe_load(open(p))
c.setdefault("mcp_servers", {})["chrome-devtools-mcp"] = {
    "command": "npx",
    "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl=http://127.0.0.1:9222"],
}
yaml.safe_dump(c, open(p, "w"), sort_keys=False, allow_unicode=True)
```
Verify: `python3 -c "import yaml;print(type(yaml.safe_load(open('/Users/kk/.hermes/config.yaml'))['mcp_servers']['chrome-devtools-mcp']['args']).__name__)"`
must print `list`.

## 5. Persist with launchd (autostart + crash recovery)
Install `templates/com.hermes.chrome-cdp.plist` to `~/Library/LaunchAgents/` and:
```bash
launchctl load ~/Library/LaunchAgents/com.hermes.chrome-cdp.plist
launchctl list | grep chrome-cdp
```

## 6. Verify — see scripts/verify_cdp.py
- `curl -s -m5 http://127.0.0.1:9222/json/version`
- cookie count for google.com / github.com proves login state carried over
- navigation + `Runtime.evaluate("document.title")` proves read control

## Known-good versions
- Chrome 150.0.7871.115 (macOS) — requires custom `--user-data-dir` (Chrome 148+ rule).
- `websocket-client` 1.9.0 (pip install websocket-client).
