#!/usr/bin/env python3
# 精确抓取 1688 详情页 JSON 结构里的 省/市/区 字段名与值
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
oid = sys.argv[1] if len(sys.argv)>1 else "964776286173"  # 义乌真品
tid, s = c.new_page(f"https://detail.1688.com/offer/{oid}.html")
time.sleep(5)
h = c.ev(s, "document.documentElement.outerHTML") or ""
# 抓所有 provinceName/cityName/countyName/districtName/townName + 附近值
for key in ["provinceName","cityName","countyName","districtName","townName","companyProvince","companyCity","companyArea","sellerProvince","sellerCity"]:
    for m in re.finditer(re.escape(key) + r'"\s*:\s*"([^"]*)"', h):
        print(f"  {key} = {m.group(1)}")
# 也抓 "address" 附近
for m in re.finditer(r'"address"\s*:\s*"([^"]{0,40})"', h):
    print("  address =", m.group(1))
c.cmd("Target.closeTarget",{"targetId":tid})
