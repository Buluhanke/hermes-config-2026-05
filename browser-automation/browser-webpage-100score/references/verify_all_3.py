#!/usr/bin/env python3
"""综合验证：88 → 100 三个缺口都关上"""
import json, urllib.request, sys
from websocket import create_connection

CDP_HTTP = "http://127.0.0.1:9333"
print("=" * 60)
print("浏览器反指纹 88→100 三缺口综合验证")
print("=" * 60)

targets = json.loads(urllib.request.urlopen(f"{CDP_HTTP}/json").read())
page_tab = [t for t in targets if t.get("type") == "page" and "browserleaks" in t.get("url","")]
if not page_tab:
    page_tab = [t for t in targets if t.get("type") == "page"][:1]
tab = page_tab[0]
print(f"\n[1] 当前 tab: {tab['url'][:60]}")

ws = create_connection(tab["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
mid = [1]
def cdp(method, params=None):
    mid[0] += 1
    ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == mid[0]:
            return m

# === 缺口 1: plugins 补丁 ===
print("\n[2] 缺口 1 — plugins 指纹补丁 (期望 +3 → 91)")
r = cdp("Runtime.evaluate", {"expression": """
JSON.stringify({
    plugins_len: navigator.plugins.length,
    plugins_names: Array.from(navigator.plugins).map(p=>p.name),
    mimeTypes_len: navigator.mimeTypes.length,
    headless_loaded: !!window.__anti_detect_loaded__,
    plugins_loaded: !!window.__anti_detect_plugins_loaded__
})
""", "returnByValue": True})
v = json.loads(r["result"]["result"]["value"])
ok1 = (v['plugins_len'] == 3 and 'Native Client' in v['plugins_names'] and v['plugins_loaded'])
print(f"  plugins: {v['plugins_len']} 个, 含 Native Client: {'✅' if 'Native Client' in v['plugins_names'] else '❌'}, loaded: {'✅' if v['plugins_loaded'] else '❌'}")

# === 缺口 2: 12 字段 ===
print("\n[3] 核心 12 字段 (期望 12/12)")
r2 = cdp("Runtime.evaluate", {"expression": """
JSON.stringify({
    webdriver: navigator.webdriver,
    ua: navigator.userAgent,
    platform: navigator.platform,
    langs: navigator.languages,
    hw: navigator.hardwareConcurrency,
    mem: navigator.deviceMemory,
    has_touch: 'ontouchstart' in window,
    has_chrome: !!window.chrome,
    chrome_runtime: !!(window.chrome && window.chrome.runtime),
    plugins_count: navigator.plugins.length,
    headless_in_ua: /\\bHeadlessChrome\\b/.test(navigator.userAgent),
    notification: Notification.permission
})
""", "returnByValue": True})
v2 = json.loads(r2["result"]["result"]["value"])

def is_falsy(v):
    if v is None or v is False: return True
    if isinstance(v, str) and v.lower() in ('undefined','false','null',''): return True
    return False
def is_truthy(v): return v is True or v == True
def is_positive(v):
    if isinstance(v,(int,float)) and v>0: return True
    if isinstance(v,str):
        try: return float(v)>0
        except: return False
    return False
def is_valid_platform(v): return v in ('MacIntel','Win32','Linux x86_64')
def is_valid_langs(v): return isinstance(v,list) and len(v)>=1
def is_bool(v): return isinstance(v,bool)
def is_valid_notif(v): return v in ('default','granted','denied')
def is_realistic_plugins(c): return isinstance(c,(int,float)) and 1<=c<=4

checks = [
    ("webdriver", is_falsy(v2.get('webdriver'))),
    ("UA非headless", v2.get('headless_in_ua') is False),
    ("platform", is_valid_platform(v2.get('platform'))),
    ("languages", is_valid_langs(v2.get('langs'))),
    ("hw", is_positive(v2.get('hw'))),
    ("mem", is_positive(v2.get('mem'))),
    ("touchstart", is_bool(v2.get('has_touch'))),
    ("chrome", is_truthy(v2.get('has_chrome'))),
    ("chrome.runtime", is_truthy(v2.get('chrome_runtime'))),
    ("plugins", is_realistic_plugins(v2.get('plugins_count'))),
    ("Notification", is_valid_notif(v2.get('notification'))),
    ("plugins_loaded", v.get('plugins_loaded') is True),
]
ok2_count = sum(1 for _,ok in checks if ok)
for name,ok in checks:
    print(f"  {'✓' if ok else '✗'} {name}")
print(f"  → {ok2_count}/12")
ok2 = ok2_count == 12
ws.close()

# === 缺口 3: 自愈 driver ===
print("\n[4] 自愈驱动 E2E")
import subprocess
r3 = subprocess.run(["python3","/Users/aimac/.hermes/scripts/self_healing_driver.py","--test"],
                   capture_output=True,text=True,timeout=30)
ok3 = "总累计 attempts: 9" in r3.stdout
print(f"  {'✅ 9条 attempts' if ok3 else '❌ '+r3.stdout[-200:]}")

# === 缺口 4: 轨迹录制 ===
print("\n[5] 轨迹录制 CLI")
r4 = subprocess.run(["python3","/Users/aimac/.hermes/scripts/trajectory_recorder.py","list","-n","3"],
                    capture_output=True,text=True,timeout=10)
ok4 = "turns" in r4.stdout and "has_video" in r4.stdout
print(f"  {'✅ list正常' if ok4 else '❌ '+r4.stdout[:200]}")

# === 总分 ===
print("\n" + "=" * 60)
total = 88 + (3 if ok1 else 0) + (5 if ok3 else 0) + (4 if ok4 else 0)
print(f"  缺口1 plugins: {'✅ +3' if ok1 else '❌'}")
print(f"  缺口2 12字段: {'✅ 12/12' if ok2 else f'⚠️ {ok2_count}/12'}")
print(f"  缺口3 自愈: {'✅ +5' if ok3 else '❌'}")
print(f"  缺口4 轨迹: {'✅ +4' if ok4 else '❌'}")
print(f"  总分: {total} / 100")
