#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cdp_client.py — raw websocket CDP client for 1688 sourcing (no focus steal).

Design rules (per refactor directive):
- NEVER touch the user's normal Chrome / no AppleScript / no computer_use / no GUI automation.
- All driving goes through a dedicated CDP Chrome on ws://127.0.0.1:9222
  (launched with --remote-debugging-port=9222 --user-data-dir=$HOME/chrome-cdp-profile
   --no-startup-window --start-minimized).
- Tabs are created in the BACKGROUND (Target.createTarget with no window raise), so the
  user can keep using the computer normally.
- No Playwright.connectOverCDP (setDownloadBehavior is broken on 151). Pure websocket.

API:
    from cdp_client import CDPBrowser
    b = CDPBrowser(port=9222)
    tab = b.new_tab("https://s.1688.com/...")   # background tab, returns CDPTab
    tab.navigate(url)
    html = tab.eval("document.documentElement.outerHTML")
    tab.close()
"""
import json
import sys
import time
import urllib.request
import websocket  # websocket-client

DEFAULT_PORT = 9222
DEFAULT_ORIGIN = "http://127.0.0.1:%d" % DEFAULT_PORT


def _http_get_json(url, timeout=5):
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-cdp"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class CDPTab:
    """A single attached page target. Commands carry the attached sessionId."""

    def __init__(self, browser, target_id, session_id):
        self.browser = browser
        self.target_id = target_id
        self.session_id = session_id

    def _cmd(self, method, params=None, timeout=30):
        return self.browser._send(method, params or {}, session_id=self.session_id, timeout=timeout)

    def enable(self):
        self._cmd("Page.enable")
        self._cmd("Runtime.enable")

    def navigate(self, url, wait_until="load", timeout=30):
        self._cmd("Page.navigate", {"url": url})
        if wait_until == "load":
            self._wait_event("Page.loadEventFired", timeout=timeout)

    def eval(self, expression, timeout=30, return_by_value=True):
        """Run JS in the page. expression must be a JS expression (not a statement block)."""
        r = self._cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": return_by_value,
            "awaitPromise": False,
        }, timeout=timeout)
        if "exceptionDetails" in r and r["exceptionDetails"]:
            raise RuntimeError("JS eval exception: %s" % json.dumps(r["exceptionDetails"], ensure_ascii=False))
        return r.get("result", {}).get("value")

    def eval_fn(self, fn_body, *args, timeout=30):
        """Run a JS function body with JSON-serializable args. fn_body is the INSIDE of an arrow fn."""
        arg_json = json.dumps(list(args), ensure_ascii=False)
        expr = "(()=>{%s}).apply(null, %s)" % (fn_body, arg_json)
        return self.eval(expr, timeout=timeout)

    def _wait_event(self, event, timeout=30):
        return self.browser._wait_event(event, session_id=self.session_id, timeout=timeout)

    def close(self):
        self.browser._send("Target.closeTarget", {"targetId": self.target_id})


class CDPBrowser:
    def __init__(self, port=DEFAULT_PORT, origin=None, auto_open_fallback=True):
        self.port = port
        self.origin = origin or ("http://127.0.0.1:%d" % port)
        self.auto_open_fallback = auto_open_fallback
        self._msg_id = 0
        self._ws = None
        self._connected = False
        self._pending = {}      # msg id -> event
        self._event_buf = []    # unsolicited events for _wait_event

    # ---- low level ----
    def _connect(self):
        if self._connected:
            return
        ver = _http_get_json("%s/json/version" % self.origin)
        ws_url = ver["webSocketDebuggerUrl"]
        self._ws = websocket.create_connection(ws_url, suppress_origin=True, timeout=15)
        self._connected = True

    def _send(self, method, params=None, session_id=None, timeout=30):
        self._connect()
        self._msg_id += 1
        mid = self._msg_id
        msg = {"id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        if session_id:
            msg["sessionId"] = session_id
        self._ws.send(json.dumps(msg))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self._ws.recv()
            obj = json.loads(raw)
            if obj.get("id") == mid:
                if "error" in obj:
                    raise RuntimeError("CDP error on %s: %s" % (method, json.dumps(obj["error"], ensure_ascii=False)))
                return obj.get("result", {})
            else:
                # event — buffer it for _wait_event
                self._event_buf.append(obj)
        raise TimeoutError("CDP %s timed out after %ds" % (method, timeout))

    def _wait_event(self, event, session_id=None, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            for i, obj in enumerate(self._event_buf):
                if obj.get("method") == event and (session_id is None or obj.get("sessionId") == session_id):
                    self._event_buf.pop(i)
                    return obj
            raw = self._ws.recv()
            obj = json.loads(raw)
            if obj.get("method") == event and (session_id is None or obj.get("sessionId") == session_id):
                return obj
            self._event_buf.append(obj)
        raise TimeoutError("CDP event %s timed out" % event)

    # ---- high level ----
    def list_targets(self):
        return self._send("Target.getTargets").get("targetInfos", [])

    def new_tab(self, url="about:blank"):
        """Create a BACKGROUND tab (no window raise) and attach a flattened session."""
        res = self._send("Target.createTarget", {"url": url, "background": True})
        target_id = res["targetId"]
        attached = self._send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        session_id = attached["sessionId"]
        tab = CDPTab(self, target_id, session_id)
        tab.enable()
        return tab

    def attach_existing_tab(self, url_prefix="about:blank"):
        """Fallback: reuse an existing page target instead of opening a new one."""
        for t in self.list_targets():
            if t.get("type") == "page" and (t.get("url", "").startswith(url_prefix) or url_prefix == "*"):
                attached = self._send("Target.attachToTarget", {"targetId": t["targetId"], "flatten": True})
                tab = CDPTab(self, t["targetId"], attached["sessionId"])
                tab.enable()
                return tab
        raise RuntimeError("no existing tab matching %s" % url_prefix)

    def get_or_create_tab(self, url="about:blank"):
        if self.auto_open_fallback:
            try:
                return self.attach_existing_tab("about:blank")
            except Exception:
                pass
        return self.new_tab(url)

    def close(self):
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._connected = False


def smoke_test(port=DEFAULT_PORT):
    """Prove the channel works with zero focus steal."""
    b = CDPBrowser(port=port)
    tab = b.new_tab("https://www.example.com")
    tab.navigate("https://www.example.com")
    title = tab.eval("document.title")
    href = tab.eval("location.href")
    h1 = tab.eval("document.querySelector('h1') ? document.querySelector('h1').textContent : null")
    print(json.dumps({"title": title, "href": href, "h1": h1}, ensure_ascii=False))
    tab.close()
    b.close()
    return True


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    smoke_test(p)
