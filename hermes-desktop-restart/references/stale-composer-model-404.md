# Stale composer.model → desktop App 404 (model name mismatch)

Reproduced 2026-07-16 on kk's machine. Desktop App threw
`HTTP 404: Model 'tencent/hy3' requires available credits` while the CLI
(`hermes chat`) worked and `~/.hermes/config.yaml` already had
`default: tencent/hy3:free`.

## What was actually happening
The App sends `request.body.model` to the gateway. That value came from its
Electron localStorage key `hermes.desktop.composer.model`
(`~/Library/Application Support/Hermes/Local Storage/leveldb`). The cached value
was `tencent/hy3` (NO `:free` suffix) — a stale seed from before config was
updated. The App's `refreshCurrentModel` only overwrites that value when the
in-memory copy is empty, so the stale name was never corrected.

## Evidence-gathering recipe
1. Parse session request dumps for the exact model the App sent:
```bash
python3 - <<'PY'
import json, glob, os
for f in sorted(glob.glob(os.path.expanduser('~/.hermes/sessions/request_dump_*.json')),
                key=os.path.getmtime, reverse=True)[:6]:
    try:
        d = json.load(open(f))
        body = d.get('request', {}).get('body', {})
        if body.get('model'):
            print(os.path.basename(f), '->', body['model'])
    except Exception:
        pass
PY
```
2. Read the live App cache (leveldb is append-only; the LAST occurrence of a key
   wins). Plaintext key/value pairs are visible with `strings`:
```bash
cd "$HOME/Library/Application Support/Hermes/Local Storage/leveldb"
strings 00000*.log 00000*.ldb 2>/dev/null | grep -o 'composer.model[^.]\{0,25\}'
# stale run showed:  ...composer.model  tencent/hy3:free   (earlier)
#                     ...composer.model  tencent/hy3        (LAST = the bug)
```
3. Prove the *correct* model works (rules out a real account/credit problem).
   Use the venv so deps resolve:
```bash
cd ~/.hermes/hermes-agent
HERMES_HOME=~/.hermes ./.venv/bin/python - <<'PY' 2>&1 | tail -15
import sys, json, urllib.request
sys.path.insert(0, '.')
from hermes_cli import auth
state = auth.get_provider_auth_state('nous') or {}
tok = state.get('access_token') or ''
base = (state.get('inference_base_url') or 'https://inference-api.nousresearch.com/v1').rstrip('/')
body = json.dumps({"model":"tencent/hy3:free",
                   "messages":[{"role":"user","content":"say hi in one word"}],
                   "max_tokens":20}).encode()
req = urllib.request.Request(base+'/chat/completions', data=body,
        headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.loads(r.read().decode())
    print("OK:", out['choices'][0]['message']['content'][:60])
except Exception as e:
    print("ERR:", str(e)[:300])
PY
```
Result was `OK: Hello.` — the free model itself is fine; only the name was wrong.

## Fix applied
```
pkill -f "Hermes.app/Contents/MacOS/Hermes"
rm -rf "$HOME/Library/Application Support/Hermes/Local Storage/leveldb"
open /Applications/Hermes.app
# after ~4s the re-seeded value carries the suffix again
```

## Recurrence guard
Because `refreshCurrentModel` only re-seeds when empty, a manually-picked model
(or a value seeded before a config edit) sticks. If the 404 returns after the
user switched models, repeat the leveldb wipe. Durable fix = always trust
config unless the model was changed in the current session.
