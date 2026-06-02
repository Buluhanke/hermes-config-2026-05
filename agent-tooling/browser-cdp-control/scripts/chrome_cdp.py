#!/usr/bin/env python3
"""
chrome_cdp.py — Chrome CDP Direct Controller
Bypasses mcp-chrome-stdio, controls Chrome directly via HTTP+WebSocket on port 9333.
用法: python3 chrome_cdp.py <action> [args]
Actions:
  list                    — 列出所有标签页
  new <url>              — 创建新标签并导航
  navigate <tab_id> <url> — 导航已有标签
  eval <tab_id> <js>     — 在标签页执行JS
  screenshot <tab_id>    — 截图保存
  tabs                   — 快速显示标签摘要
"""
import urllib.request, json, websocket, time, sys, os, base64, struct, argparse

CDP_URL = 'http://localhost:9333'

def list_tabs():
    with urllib.request.urlopen(f'{CDP_URL}/json', timeout=10) as f:
        return json.loads(f.read())

def ws_connect(tab_id):
    tabs = list_tabs()
    tab = next((t for t in tabs if t['id'] == tab_id), None)
    if not tab:
        raise ValueError(f"Tab {tab_id} not found")
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id":1,"method":"Runtime.enable"}))
    ws.recv()
    return ws

def send_ws(ws, data):
    ws.send(json.dumps(data))

def recv_ws(ws):
    raw = ws.recv()
    return json.loads(raw)

def recv_all_ws(ws, timeout=5):
    results = []
    ws.settimeout(timeout)
    while True:
        try:
            results.append(json.loads(ws.recv()))
        except websocket.WebSocketTimeoutException:
            break
    return results

def create_new_tab(url=None):
    req = urllib.request.Request(f'{CDP_URL}/json/new', method='POST')
    with urllib.request.urlopen(req, timeout=10) as f:
        tab = json.loads(f.read())
    if url:
        ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
        ws.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":url}}))
        ws.recv(); ws.close()
        time.sleep(2)
    return tab

def navigate_tab(tab_id, url):
    tabs = list_tabs()
    tab = next((t for t in tabs if t['id'] == tab_id), None)
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":url}}))
    ws.recv(); ws.close()
    time.sleep(2)

def eval_js(tab_id, js_expr, timeout=20):
    """Execute JS in tab, return result value."""
    tabs = list_tabs()
    tab = next((t for t in tabs if t['id'] == tab_id), None)
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id":1,"method":"Runtime.enable"}))
    ws.recv()
    ws.send(json.dumps({"id":2,"method":"Runtime.evaluate","params":{"expression":js_expr,"returnByValue":True,"timeout":timeout*1000}}))
    resp = json.loads(ws.recv())
    ws.close()
    if 'result' in resp and 'result' in resp['result']:
        return resp['result']['result']['value']
    return None

def capture_screenshot(tab_id, path=None):
    tabs = list_tabs()
    tab = next((t for t in tabs if t['id'] == tab_id), None)
    ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
    ws.send(json.dumps({"id":1,"method":"Page.captureScreenshot","params":{"format":"png","quality":50}}))
    resp = json.loads(ws.recv())
    ws.close()
    if 'result' not in resp: return None
    img_data = resp['result']['result']['value']
    if path is None:
        path = f'/tmp/screenshot_{tab_id[:8]}_{int(time.time())}.png'
    with open(path, 'wb') as f:
        f.write(base64.b64decode(img_data))
    return path

def batch_open_sites(sites):
    """sites: list of (url, name) — opens each in a new tab"""
    results = {}
    for url, name in sites:
        tab = create_new_tab(url)
        results[name] = tab['id']
        print(f"✅ {name}: {tab['id'][:12]}")
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chrome CDP Controller')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('list', help='List all tabs')
    sub.add_parser('tabs', help='Quick tab summary')
    new_p = sub.add_parser('new', help='Create new tab')
    new_p.add_argument('url')
    nav_p = sub.add_parser('navigate', help='Navigate tab')
    nav_p.add_argument('tab_id')
    nav_p.add_argument('url')
    eval_p = sub.add_parser('eval', help='Eval JS')
    eval_p.add_argument('tab_id')
    eval_p.add_argument('js')
    ss_p = sub.add_parser('screenshot', help='Screenshot')
    ss_p.add_argument('tab_id')
    ss_p.add_argument('--path', default=None)

    args = parser.parse_args()

    if args.cmd == 'list':
        tabs = list_tabs()
        print(json.dumps(tabs, indent=2))
    elif args.cmd == 'tabs':
        tabs = list_tabs()
        pages = [t for t in tabs if t.get('type') == 'page']
        print(f'Chrome Tabs ({len(pages)}):')
        for t in pages:
            print(f"  {t['id'][:12]}: {t['url'][:70]}")
    elif args.cmd == 'new':
        tab = create_new_tab(args.url)
        print(f"Created: {tab['id'][:12]} -> {args.url}")
    elif args.cmd == 'navigate':
        navigate_tab(args.tab_id, args.url)
        print(f"Navigated {args.tab_id[:12]} -> {args.url}")
    elif args.cmd == 'eval':
        result = eval_js(args.tab_id, args.js)
        print(result)
    elif args.cmd == 'screenshot':
        path = capture_screenshot(args.tab_id, args.path)
        print(f"Saved: {path}")
    elif args.cmd == 'screenshot_all':
        tabs = list_tabs()
        for t in tabs:
            if t.get('type') == 'page':
                try:
                    p = capture_screenshot(t['id'])
                    print(f"  {t['id'][:12]}: {p}")
                except Exception as e:
                    print(f"  {t['id'][:12]}: ERROR {e}")