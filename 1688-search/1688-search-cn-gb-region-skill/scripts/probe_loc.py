#!/usr/bin/env python3
# 探测 1688 详情页"真实所在地"字段写法，用于严格校验 义乌市。
import sys, os, json, re, time, threading
import websocket
HERE = os.path.dirname(os.path.abspath(__file__))

class CDP:
    def __init__(self, url="http://127.0.0.1:9222"):
        import urllib.request
        ver = json.loads(urllib.request.urlopen(url + "/json/version", timeout=5).read())
        self.ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=60)
        self._id = 0; self.events = []
        threading.Thread(target=self._r, daemon=True).start()
    def _r(self):
        while True:
            try: self.events.append(json.loads(self.ws.recv()))
            except Exception: break
    def _send(self, m, p=None, s=None):
        self._id += 1; msg={"id":self._id,"method":m}
        if p is not None: msg["params"]=p
        if s is not None: msg["sessionId"]=s
        self.ws.send(json.dumps(msg)); return self._id
    def _recv(self, mid, t=30):
        t0=time.time()
        while time.time()-t0<t:
            for i,e in enumerate(self.events):
                if e.get("id")==mid:
                    self.events.pop(i); return e
            time.sleep(0.02)
        return None
    def cmd(self, m, p=None, s=None):
        return self._recv(self._send(m,p,s))
    def new_page(self, url="about:blank"):
        r=self.cmd("Target.createTarget",{"url":url,"background":True})
        tid=r["result"]["targetId"]
        s=self.cmd("Target.attachToTarget",{"targetId":tid,"flatten":True})["result"]["sessionId"]
        self.cmd("Page.enable",{},s); self.cmd("Runtime.enable",{},s)
        return tid, s
    def nav(self, s, url):
        return self.cmd("Page.navigate",{"url":url},s)
    def ev(self, s, expr):
        mid=self._send("Runtime.evaluate",{"expression":expr,"returnByValue":True},s)
        o=self._recv(mid)
        if o is None: return None
        if "error" in o: return None
        return o.get("result",{}).get("result",{}).get("value")

c = CDP()
ids = sys.argv[1:] or ["850442269481","758946228536","964776286173","546706443426","994627723638"]
for oid in ids:
    tid, s = c.new_page(f"https://detail.1688.com/offer/{oid}.html")
    time.sleep(5)
    h = c.ev(s, "document.documentElement.outerHTML") or ""
    # 找所在地相关片段
    print(f"\n===== {oid} (html {len(h)} bytes) =====")
    # 1) 省份/城市 字段
    for m in re.finditer(r'"(?:provinceName|cityName|countyName|townName|province|city|area|locate|location|address|companyLocation|companyAddress)"\s*:\s*"([^"]*)"', h):
        print("  JSON:", m.group(1))
    # 2) 中文"所在地/公司/地址"附近 60 字
    for kw in ["所在地","公司所在地","公司地址","经营地址","发货地","省份","城市"]:
        for m in re.finditer(kw + r'.{0,40}', h):
            seg = re.sub(r'\s+',' ', m.group(0))
            if re.search(r'[一-龥]', seg):
                print(f"  {kw}» {seg[:50]}")
    # 3) 江浙沪/义乌 上下文
    for m in re.finditer(r'(浙江|江苏|上海|广东|福建|山东|河北|义乌|金华)[^<>"\n]{0,12}', h):
        print("  LOC:", m.group(0))
    c.cmd("Target.closeTarget",{"targetId":tid})
