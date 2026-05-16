#!/usr/bin/env python3
"""验证 CDP screenshot 链路是否通畅。"""
import os, sys, json, base64

def check_cdp_http():
    """检查 CDP HTTP 端点是否响应。"""
    import httpx
    cdp_url = os.environ.get("HERMES_CDP_URL", "http://127.0.0.1:9333")
    try:
        with httpx.Client(timeout=10) as client:
            tabs = client.get(f"{cdp_url}/json").json()
            print(f"✅ CDP HTTP 端点正常，Tabs: {len(tabs)}")
            if tabs:
                print(f"   首个 Tab: {tabs[0].get('title','')[:40]} — {tabs[0].get('url','')[:50]}")
            return tabs
    except Exception as e:
        print(f"❌ CDP HTTP 端点失败: {e}")
        return None

def check_websocket_client():
    """检查 websocket-client 包是否可用。"""
    try:
        import websocket
        print("✅ websocket-client 已安装")
        return True
    except ImportError:
        print("❌ websocket-client 未安装: pip3 install websocket-client")
        return False

def check_cdp_screenshot(tabs):
    """通过 WebSocket CDP 截取首个 Tab 的截图。"""
    import httpx, json as _json, base64 as _b64, websocket
    if not tabs:
        return
    tab = tabs[0]
    ws_url = tab.get("webSocketDebuggerUrl")
    if not ws_url:
        print("❌ Tab 无 webSocketDebuggerUrl 字段")
        return
    try:
        ws = websocket.create_connection(ws_url, timeout=15)
        ws.settimeout(15)
        ws.send(_json.dumps({"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
        raw = ws.recv()
        ws.close()
        resp = _json.loads(raw)
        if resp.get("result") and resp["result"].get("data"):
            img_data = _b64.b64decode(resp["result"]["data"])
            print(f"✅ CDP WebSocket 截图成功: {len(img_data)} bytes")
        else:
            print(f"❌ CDP 截图失败: {str(raw)[:200]}")
    except Exception as e:
        print(f"❌ CDP WebSocket 截图失败: {e}")

if __name__ == "__main__":
    print("=== CDP Screenshot 链路检查 ===")
    check_websocket_client()
    tabs = check_cdp_http()
    if tabs:
        check_cdp_screenshot(tabs)
