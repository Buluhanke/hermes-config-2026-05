#!/usr/bin/env python3
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
    def ev(self, s, expr):
        mid=self._send("Runtime.evaluate",{"expression":expr,"returnByValue":True},s)
        o=self._recv(mid)
        if o is None: return None
        if "error" in o: return None
        return o.get("result",{}).get("result",{}).get("value")
c = CDP()
oid = sys.argv[1] if len(sys.argv)>1 else "964776286173"
tid, s = c.new_page(f"https://detail.1688.com/offer/{oid}.html")
time.sleep(5)
h = c.ev(s, "document.documentElement.outerHTML") or ""
for addr in ["浙江省金华市","河北省邢台市","广东省深圳市","义乌市"]:
    for m in re.finditer(re.escape(addr), h):
        start = max(0, m.start()-80); end = min(len(h), m.end()+20)
        ctx = h[start:end]
        # 截到最近的左花括号后的键名
        print(f"\n--- context around [{addr}] ---")
        print(ctx.replace("\n"," "))
c.cmd("Target.closeTarget",{"targetId":tid})
