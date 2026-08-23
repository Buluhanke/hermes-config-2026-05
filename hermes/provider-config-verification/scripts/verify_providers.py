"""Verify every Hermes provider/model in config.yaml with a REAL HTTP POST.

Run from the hermes-agent venv (curl is hardline-blocked in the agent, so use
this Python http.client probe instead):

    cd ~/.hermes/hermes-agent && ./venv/bin/python3 ~/.hermes/diag_providers.py

Tests each custom_providers entry + each fallback_providers entry by sending a
minimal /chat/completions request and printing the real status code.
"""
import os, sys, json, http.client
sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.hermes/.env"))


def resolve_key(entry):
    if entry.get("api_key"):
        return entry["api_key"]
    for k in ("api_key_env", "key_env"):
        if entry.get(k):
            return os.environ.get(entry[k], "")
    return ""


def test_endpoint(base_url, api_key, model, label):
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply exactly: OK"}],
        "max_tokens": 5,
    }).encode()
    try:
        parsed = http.client.urlsplit(url)
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=8) if parsed.scheme == "https" \
            else http.client.HTTPConnection(parsed.netloc, timeout=8)
        conn.request("POST", parsed.path, body=body,
                     headers={"Content-Type": "application/json",
                              "Authorization": "Bearer " + (api_key or "x")})
        resp = conn.getresponse()
        data = resp.read(600).decode(errors="replace")
        conn.close()
        print(f"[{'OK' if resp.status == 200 else 'FAIL'} {resp.status}] {label}  {data[:160].strip()}")
    except Exception as e:
        print(f"[ERR] {label}  {type(e).__name__}: {e}")


from hermes_cli.config import load_config
cfg = load_config()

print("=== custom_providers ===")
for e in cfg.get("custom_providers", []):
    name = e.get("name", "?")
    base = e.get("base_url", "")
    model = e.get("model") or (e.get("models") or [""])[0]
    test_endpoint(base, resolve_key(e), model, f"{name} (model={model})")

print("\n=== fallback_providers ===")
by_name = {e.get("name"): e for e in cfg.get("custom_providers", [])}
for fb in cfg.get("fallback_providers", []):
    pname = fb.get("provider", "")
    base = fb.get("base_url", "")
    model = fb.get("model", "")
    src = by_name.get(pname.split(":")[-1]) if ":" in pname else by_name.get(pname)
    key = resolve_key(src) if src else ""
    test_endpoint(base, key, model, f"fb {pname} (model={model})")
