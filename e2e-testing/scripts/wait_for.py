#!/usr/bin/env python3
"""
Wait For Element — poll for DOM element state changes.
"""

import time
import sys
import argparse
from typing import Literal


State = Literal["present", "visible", "hidden", "enabled", "disabled"]


def wait_for_element(cdp_url: str, tab_id: str, selector: str,
                     state: State = "visible", timeout: int = 10000) -> bool:
    """Wait for an element to reach a given state."""
    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
        import httpx

    client = httpx.Client(base_url=cdp_url, timeout=30)

    scripts = {
        "present": f"""
        document.querySelector('{selector}') !== null
        """,
        "visible": f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
        }})()
        """,
        "hidden": f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return true;
            const r = el.getBoundingClientRect();
            return r.width === 0 || r.height === 0 || getComputedStyle(el).visibility === 'hidden';
        }})()
        """,
        "enabled": f"""
        (() => {{
            const el = document.querySelector('{selector}');
            return el && !el.disabled;
        }})()
        """,
        "disabled": f"""
        (() => {{
            const el = document.querySelector('{selector}');
            return el && el.disabled;
        }})()
        """,
    }

    condition = scripts.get(state, scripts["visible"]).replace("{selector}", selector)
    deadline = time.time() + timeout / 1000
    interval = 0.5

    while time.time() < deadline:
        resp = client.post("/json", json={
            "method": "Runtime.evaluate",
            "params": {"expression": condition, "returnByValue": True}
        })
        try:
            data = resp.json()
            if isinstance(data, dict):
                # CDP returns result.value directly in some versions
                val = (data.get("result") or {}).get("value") or data.get("value")
                if val:
                    return True
        except Exception:
            pass

        time.sleep(interval)

    client.close()
    raise TimeoutError(f"Timeout waiting for '{selector}' to be {state} after {timeout}ms")


def wait_for_url(cdp_url: str, tab_id: str, pattern: str, timeout: int = 15000) -> bool:
    """Wait for URL to match a pattern."""
    import re
    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
        import httpx

    client = httpx.Client(base_url=cdp_url, timeout=30)
    deadline = time.time() + timeout / 1000
    interval = 0.5

    while time.time() < deadline:
        resp = client.get(f"/json/{tab_id}")
        try:
            url = resp.json().get("url", "")
            if re.match(pattern.replace("*", ".*"), url):
                return True
        except Exception:
            pass
        time.sleep(interval)

    client.close()
    raise TimeoutError(f"Timeout waiting for URL pattern '{pattern}' after {timeout}ms")


def wait_for_text(cdp_url: str, tab_id: str, text: str, timeout: int = 8000) -> bool:
    """Wait for a specific text to appear on the page."""
    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
        import httpx

    client = httpx.Client(base_url=cdp_url, timeout=30)
    deadline = time.time() + timeout / 1000
    interval = 0.5
    escaped_text = text.replace("'", "\\'")

    while time.time() < deadline:
        resp = client.post("/json", json={
            "method": "Runtime.evaluate",
            "params": {
                "expression": f"document.body.textContent.includes('{escaped_text}')",
                "returnByValue": True
            }
        })
        try:
            data = resp.json()
            val = (data.get("result") or {}).get("value")
            if val:
                client.close()
                return True
        except Exception:
            pass
        time.sleep(interval)

    client.close()
    raise TimeoutError(f"Timeout waiting for text '{text}' after {timeout}ms")


def main():
    parser = argparse.ArgumentParser(description="Wait for element utilities")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    parser.add_argument("--tab-id", help="Tab ID (omit to use first tab)")
    parser.add_argument("--selector")
    parser.add_argument("--state", default="visible",
                        choices=["present", "visible", "hidden", "enabled", "disabled"])
    parser.add_argument("--timeout", type=int, default=10000)
    parser.add_argument("--pattern", help="URL pattern for wait_for_url")
    parser.add_argument("--text", help="Text to wait for")
    args = parser.parse_args()

    try:
        import httpx
        client = httpx.Client(base_url=args.cdp_url, timeout=30)
        if args.tab_id:
            tab_id = args.tab_id
        else:
            tabs = client.get("/json/list").json()
            tab_id = tabs[0]["id"] if tabs else None
        client.close()
    except Exception as e:
        print(f"✗ Connection error: {e}")
        sys.exit(1)

    try:
        if args.selector:
            wait_for_element(args.cdp_url, tab_id, args.selector, args.state, args.timeout)
            print(f"✅ Element '{args.selector}' is {args.state}")
        elif args.pattern:
            wait_for_url(args.cdp_url, tab_id, args.pattern, args.timeout)
            print(f"✅ URL matches '{args.pattern}'")
        elif args.text:
            wait_for_text(args.cdp_url, tab_id, args.text, args.timeout)
            print(f"✅ Text '{args.text}' found")
        else:
            print("Error: --selector, --pattern, or --text required")
            sys.exit(1)
    except TimeoutError as e:
        print(f"⏰ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
