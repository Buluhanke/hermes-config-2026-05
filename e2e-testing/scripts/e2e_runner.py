#!/usr/bin/env python3
"""
E2E Test Runner — Hermes Edition
Cypress-style structured E2E test executor.
"""

import argparse
import sys
import time
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any

# ── Browser Control ──────────────────────────────────────────
def get_browser_driver(cdp_url: str = "http://localhost:9222", headless: bool = True):
    """Connect to Chrome via CDP."""
    try:
        import httpx
        client = httpx.Client(base_url=cdp_url, timeout=10)
        # Verify connection
        resp = client.get("/json/version")
        resp.raise_for_status()
        print(f"  → Connected to Chrome: {resp.json()['Browser']}")
        return client
    except Exception as e:
        print(f"  ✗ Cannot connect to Chrome at {cdp_url}: {e}")
        sys.exit(1)


def execute_cdp(driver, method: str, params: dict = None) -> dict:
    """Execute a CDP command and return the result."""
    resp = driver.post("/json", json={"method": method, "params": params or {}})
    resp.raise_for_status()
    return resp.json()


def get_active_tab(driver) -> str:
    """Get the targetId of the active tab."""
    tabs = driver.get("/json/list").json()
    for tab in tabs:
        if tab.get("attached", False):
            return tab["id"]
    return tabs[0]["id"] if tabs else None


# ── Actions ──────────────────────────────────────────────────
def action_navigate(driver, tab_id: str, url: str):
    """Navigate to URL."""
    resp = driver.post(f"/json/new", json={"url": url})
    # For existing tab:
    execute_cdp(driver, "Page.navigate", {"url": url}, tab_id)
    execute_cdp(driver, "Page.loadEventFired", {}, tab_id)
    print(f"  ✓ Navigated to {url}")


def action_click(driver, tab_id: str, selector: str, timeout: int = 5000):
    """Click an element by CSS selector."""
    script = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) throw new Error('Element not found: {selector}');
        el.click();
    }})()
    """
    execute_cdp(driver, "Runtime.evaluate",
                {"expression": script, "awaitPromise": True}, tab_id)
    print(f"  ✓ Clicked {selector}")


def action_type(driver, tab_id: str, selector: str, text: str, clear: bool = True):
    """Type text into an element."""
    if clear:
        clear_script = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) throw new Error('Element not found: {selector}');
            el.value = '';
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
        }})()
        """
        execute_cdp(driver, "Runtime.evaluate",
                    {"expression": clear_script}, tab_id)

    escaped_text = text.replace("'", "\\'")
    type_script = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) throw new Error('Element not found: {selector}');
        el.value = '{escaped_text}';
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
    }})()
    """
    execute_cdp(driver, "Runtime.evaluate",
                {"expression": type_script}, tab_id)
    print(f"  ✓ Typed into {selector}")


def action_hover(driver, tab_id: str, selector: str):
    script = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) throw new Error('Element not found: {selector}');
        el.dispatchEvent(new MouseEvent('mouseover', {{bubbles: true}}));
    }})()
    """
    execute_cdp(driver, "Runtime.evaluate", {"expression": script}, tab_id)
    print(f"  ✓ Hovered {selector}")


def action_screenshot(driver, tab_id: str, name: str, path: str = "./screenshots") -> str:
    """Take a screenshot and save it."""
    Path(path).mkdir(parents=True, exist_ok=True)
    result = execute_cdp(driver, "Page.captureScreenshot",
                        {"format": "png"}, tab_id)
    import base64
    data = base64.b64decode(result["data"])
    filepath = Path(path) / f"{name}.png"
    filepath.write_bytes(data)
    print(f"  ✓ Screenshot saved: {filepath}")
    return str(filepath)


def action_wait_for(driver, tab_id: str, selector: str, state: str = "visible",
                    timeout: int = 10000):
    """Wait for element state."""
    state_map = {
        "present": "document.querySelector('{s}') !== null",
        "visible": """
            (() => {{
                const el = document.querySelector('{s}');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }})()
        """,
        "hidden": """
            (() => {{
                const el = document.querySelector('{s}');
                if (!el) return true;
                const r = el.getBoundingClientRect();
                return r.width === 0 || r.height === 0;
            }})()
        """,
        "enabled": """
            (() => {{
                const el = document.querySelector('{s}');
                return el && !el.disabled;
            }})()
        """,
    }
    condition = state_map.get(state, state_map["visible"]).format(s=selector)
    script = f"""
    (async () => {{
        const deadline = Date.now() + {timeout};
        while (Date.now() < deadline) {{
            if ({condition}) return true;
            await new Promise(r => setTimeout(r, 500));
        }}
        throw new Error('Timeout waiting for {selector} [{state}]');
    }})()
    """
    execute_cdp(driver, "Runtime.evaluate",
                {"expression": script, "awaitPromise": True, "timeout": timeout / 1000}, tab_id)
    print(f"  ✓ {selector} is {state}")


def action_assert_text(driver, tab_id: str, selector: str, expected: str):
    """Assert element text matches expected."""
    script = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        return el ? el.textContent.trim() : null;
    }})()
    """
    result = execute_cdp(driver, "Runtime.evaluate", {"expression": script}, tab_id)
    actual = result.get("result", {}).get("value", "")
    passed = expected in actual if actual else False
    if passed:
        print(f"  ✓ Text assertion passed: {selector}")
    else:
        raise AssertionError(f"Text mismatch on {selector}: expected '{expected}', got '{actual}'")


def action_execute_js(driver, tab_id: str, script: str):
    """Execute arbitrary JavaScript."""
    result = execute_cdp(driver, "Runtime.evaluate",
                         {"expression": script, "returnByValue": True}, tab_id)
    print(f"  ✓ JS executed")
    return result.get("result", {}).get("value")


def action_refresh(driver, tab_id: str):
    execute_cdp(driver, "Page.reload", {}, tab_id)
    print("  ✓ Page refreshed")


def action_scroll(driver, tab_id: str, selector: str):
    script = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        el && el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
    }})()
    """
    execute_cdp(driver, "Runtime.evaluate", {"expression": script}, tab_id)
    print(f"  ✓ Scrolled to {selector}")


# ── Fixture ───────────────────────────────────────────────────
def load_fixture(path: str) -> dict:
    """Load a fixture file (YAML or JSON)."""
    p = Path(path)
    if not p.exists():
        print(f"  ⚠ Fixture not found: {path}, skipping")
        return {}

    if p.suffix in (".yaml", ".yml"):
        import yaml
        with open(p) as f:
            data = yaml.safe_load(f) or {}
    elif p.suffix == ".json":
        with open(p) as f:
            data = json.load(f)
    else:
        data = {}

    # Expand environment variables
    def expand(val):
        if isinstance(val, str) and val.startswith("{{ ENV."):
            import os
            key = val[7:-2]
            return os.environ.get(key, val)
        return val

    def walk(obj):
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk(i) for i in obj]
        else:
            return expand(obj)

    return walk(data)


def expand_text(text: str, fixture: dict) -> str:
    """Expand {{ key }} placeholders in text using fixture data."""
    import re
    def replacer(m):
        key = m.group(1).strip()
        keys = key.split(".")
        val = fixture
        for k in keys:
            val = val.get(k, m.group(0))
        return str(val)
    return re.sub(r"\{\{(.+?)\}\}", replacer, text)


# ── Report ────────────────────────────────────────────────────
def generate_html_report(results: list, output_dir: str, spec_name: str):
    """Generate an HTML test report."""
    from pathlib import Path
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_dir) / f"e2e-report-{spec_name}-{ts}.html"

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    total = len(results)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>E2E Report: {spec_name}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; margin: 40px; background: #fafafa; }}
  h1 {{ color: #333; }}
  .summary {{ padding: 16px; border-radius: 8px; margin-bottom: 24px; }}
  .summary.passed {{ background: #d4edda; color: #155724; }}
  .summary.failed {{ background: #f8d7da; color: #721c24; }}
  .step {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .step.passed {{ border-left: 4px solid #28a745; }}
  .step.failed {{ border-left: 4px solid #dc3545; }}
  .step-header {{ font-weight: bold; margin-bottom: 8px; }}
  .step-time {{ color: #888; font-size: 0.85em; }}
  .error {{ color: #dc3545; background: #f8f8f8; padding: 8px; border-radius: 4px;
            font-family: monospace; font-size: 0.9em; margin-top: 8px; }}
  img {{ max-width: 600px; border: 1px solid #ddd; margin-top: 8px; border-radius: 4px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px;
            font-size: 0.8em; margin-left: 8px; }}
  .badge-passed {{ background: #d4edda; color: #155724; }}
  .badge-failed {{ background: #f8d7da; color: #721c24; }}
</style></head><body>
<h1>🧪 E2E Test Report: {spec_name}</h1>
<div class="summary {'passed' if failed == 0 else 'failed'}">
  <strong>{'✅ ALL PASSED' if failed == 0 else f'❌ {failed} FAILED'}</strong>
  — {passed}/{total} steps passed — Generated {ts}
</div>
"""
    for r in results:
        html += f"""
<div class="step {r['status']}">
  <div class="step-header">
    Step {r['index']}: {r['action']} {r.get('selector', r.get('url', ''))}
    <span class="badge badge-{r['status']}">{r['status']}</span>
    <span class="step-time">{r.get('duration', 0):.2f}s</span>
  </div>
"""
        if r.get("screenshot"):
            html += f'<img src="file://{r["screenshot"]}" loading="lazy"/>'
        if r.get("error"):
            html += f'<div class="error">Error: {r["error"]}</div>'
        html += "</div>"

    html += "</body></html>"
    report_path.write_text(html, encoding="utf-8")
    print(f"\n📊 Report saved: {report_path}")
    return report_path


# ── Main Runner ────────────────────────────────────────────────
ACTION_MAP = {
    "navigate": action_navigate,
    "click": action_click,
    "type": action_type,
    "hover": action_hover,
    "screenshot": action_screenshot,
    "wait_for": action_wait_for,
    "assert_text": action_assert_text,
    "execute_js": action_execute_js,
    "refresh": action_refresh,
    "scroll_into_view": action_scroll,
}


def run_step(driver, tab_id: str, step: dict, fixture: dict, screenshots_dir: str) -> dict:
    """Execute a single step and return result dict."""
    action = step.get("action")
    if not action:
        return {"action": "unknown", "status": "failed", "error": "No action specified"}

    start = time.time()
    result = {"action": action, "index": step.get("_index", 0), "status": "passed"}

    try:
        # Expand fixture placeholders
        s = {k: expand_text(str(v), fixture) if isinstance(v, str) else v
             for k, v in step.items()}

        func = ACTION_MAP.get(action)
        if not func:
            raise ValueError(f"Unknown action: {action}")

        if action == "screenshot":
            result["screenshot"] = func(driver, tab_id, s.get("name", "step"),
                                        s.get("path", screenshots_dir))
        elif action == "navigate":
            func(driver, tab_id, s["url"])
        elif action == "wait_for":
            func(driver, tab_id, s["selector"], s.get("state", "visible"),
                 s.get("timeout", 10000))
        elif action == "assert_text":
            func(driver, tab_id, s["selector"], s["expected"])
        elif action in ("click", "type", "hover", "scroll_into_view"):
            func(driver, tab_id, s["selector"])
        elif action == "execute_js":
            func(driver, tab_id, s["script"])
        elif action == "refresh":
            func(driver, tab_id)
        else:
            func(driver, tab_id, **s)

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)

    result["duration"] = time.time() - start
    return result


def run_spec(spec_path: str, cdp_url: str, headless: bool, output_dir: str, record: bool):
    """Run a single spec file."""
    spec_name = Path(spec_path).stem
    print(f"\n{'='*60}")
    print(f"Running: {spec_name}")
    print(f"{'='*60}")

    # Load spec
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    steps = spec.get("steps", [])
    fixture_path = spec.get("fixture")
    fixture = load_fixture(fixture_path) if fixture_path else {}

    # Connect browser
    driver = get_browser_driver(cdp_url, headless)
    tab_id = get_active_tab(driver)
    if not tab_id:
        print("✗ No active tab found")
        return []

    results = []
    all_steps = list(spec.get("before", [])) + steps + list(spec.get("after", []))

    for i, step in enumerate(all_steps):
        step["_index"] = i + 1
        print(f"\n[{i+1}/{len(all_steps)}] {step.get('action', '?')} "
              f"{step.get('selector', step.get('url', step.get('name', '')))}")
        r = run_step(driver, tab_id, step, fixture,
                     screenshots_dir=f"{output_dir}/{spec_name}")
        results.append(r)

        if r["status"] == "failed" and spec.get("error_handling", {}).get("on_step_error") != "continue":
            print(f"  ✗ Step failed, aborting: {r.get('error')}")
            break

    # Generate report
    report = generate_html_report(results, output_dir, spec_name)

    # Summary
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"\n{'='*60}")
    print(f"Result: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Hermes E2E Test Runner")
    parser.add_argument("--spec", help="Single spec file path")
    parser.add_argument("--spec-dir", help="Directory of spec files")
    parser.add_argument("--browser", default="chrome")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    parser.add_argument("--headless", type=bool, default=True)
    parser.add_argument("--output", default="./e2e-results")
    parser.add_argument("--record", type=bool, default=False)
    args = parser.parse_args()

    if args.spec:
        run_spec(args.spec, args.cdp_url, args.headless, args.output, args.record)
    elif args.spec_dir:
        for spec_file in Path(args.spec_dir).glob("**/*.yaml"):
            run_spec(str(spec_file), args.cdp_url, args.headless, args.output, args.record)
    else:
        print("Error: --spec or --spec-dir required")
        sys.exit(1)


if __name__ == "__main__":
    main()
