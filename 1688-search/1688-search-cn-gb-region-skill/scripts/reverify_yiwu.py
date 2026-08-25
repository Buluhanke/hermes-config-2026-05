#!/usr/bin/env python3
# 已知 ID 池重验：不依赖搜页（避开 PC 搜页风控），逐个开详情页用严格 location 字段判定义乌市。
import sys, os, json, re, time, threading
import websocket
HERE = os.path.dirname(os.path.abspath(__file__))

def norm(s): return s.replace(".0","").replace(" ","").strip()

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
    def _recv(self, mid, t=40):
        t0=time.time()
        while time.time()-t0<t:
            for i,e in enumerate(self.events):
                if e.get("id")==mid:
                    self.events.pop(i); return e
            time.sleep(0.02)
        return None
    def cmd(self, m, p=None, s=None): return self._recv(self._send(m,p,s))
    def new_page(self, url="about:blank"):
        r=self.cmd("Target.createTarget",{"url":url,"background":True})
        tid=r["result"]["targetId"]
        s=self.cmd("Target.attachToTarget",{"targetId":tid,"flatten":True})["result"]["sessionId"]
        self.cmd("Page.enable",{},s); self.cmd("Runtime.enable",{},s); self.cmd("Network.enable",{},s)
        return tid, s
    def nav(self, s, url): return self.cmd("Page.navigate",{"url":url},s)
    def ev(self, s, expr):
        mid=self._send("Runtime.evaluate",{"expression":expr,"returnByValue":True},s)
        o=self._recv(mid)
        if o is None: return ""
        if "error" in o: return ""
        v=o.get("result",{}).get("result",{}).get("value")
        if isinstance(v,str): return v
        if isinstance(v,dict): return json.dumps(v,ensure_ascii=False)
        if isinstance(v,(int,float,bool)): return str(v)
        return ""
    def get_sku(self, s, oid, timeout=26):
        h=self.ev(s,"document.documentElement.outerHTML")
        if "skuMapOriginal" in h: return h
        t0=time.time()
        while time.time()-t0<timeout:
            for e in self.events:
                if e.get("method")=="Network.responseReceived":
                    u=e["params"]["response"]["url"]
                    if "queryofferskuselectormodel" in u:
                        rid=e["params"]["requestId"]
                        rb=self.cmd("Network.getResponseBody",{"requestId":rid},s)
                        res=rb.get("result",{})
                        if res:
                            b=res.get("body","")
                            if "skuMapOriginal" in b: return b
            time.sleep(0.15)
        return None
    def close(self, tid):
        try: self.cmd("Target.closeTarget",{"targetId":tid})
        except Exception: pass

def parse_sku(body):
    rows=[]
    try:
        i=body.find("skuMapOriginal")
        if i<0: return rows
        j=body.find("[",i)
        depth=0; end=j
        for k in range(j,len(body)):
            if body[k]=="[": depth+=1
            elif body[k]=="]":
                depth-=1
                if depth==0: end=k+1; break
        for it in json.loads(body[j:end]):
            rows.append((it.get("specAttrs",""), it.get("discountPrice") or it.get("price"), it.get("canBookCount")))
    except Exception: pass
    return rows

def extract_2d(spec):
    out=set()
    for m in re.finditer(r"(?<![0-9*])([0-9][0-9.]*)\s*[xX×*]\s*([0-9][0-9.]*)\s*(?:cm|CM|毫米|mm)?(?![0-9*])", spec):
        out.add(norm(f"{m.group(1)}*{m.group(2)}"))
    return out

def extract_thick(spec):
    return {norm(m.group(1)) for m in re.finditer(r"([0-9][0-9.]*)\s*丝", spec)}

ids = sys.argv[1:]
c = CDP()
vt, vs = c.new_page("about:blank")
results=[]
for oid in ids:
    url=f"https://detail.1688.com/offer/{oid}.html"
    c.nav(vs, url); time.sleep(3)
    h=c.ev(vs,"document.documentElement.outerHTML")
    if "验证码" in h:
        print(f"[CAPTCHA] {oid}"); time.sleep(20); c.nav(vs,url); time.sleep(3); h=c.ev(vs,"document.documentElement.outerHTML")
    loc = ""
    m=re.search(r'"location"\s*:\s*"([^"]*)"', h)
    if m: loc=m.group(1)
    company=""
    mc=re.search(r'"companyName"\s*:\s*"([^"]*)"', h)
    if mc: company=mc.group(1)
    in_yiwu = ("浙江省" in loc and "金华市" in loc and "义乌市" in loc) or ("浙江" in loc and "义乌市" in loc)
    body=c.get_sku(vs, oid, timeout=20)
    rows=parse_sku(body) if body else []
    specs=" ".join(s for s,_,_ in rows)
    white = "白边" in (specs + h[:20000])
    thick=set()
    for s,_,_ in rows: thick|=extract_thick(s)
    for seg in re.split(r"[;；\n|丨]", h): thick|=extract_thick(seg)
    is12 = "12" in thick
    # 14*20 尺寸
    sizes=set()
    for s,_,_ in rows: sizes|=extract_2d(s)
    is1420 = any(p in sizes for p in ["14*20","20*14"])
    rec={"id":oid,"location":loc,"company":company,"yiwu":in_yiwu,
         "white":white,"thick12":is12,"1420":is1420,
         "specs":[s for s,_,_ in rows if any(p in extract_2d(s) for p in ["14*20","20*14"])][:3]}
    results.append(rec)
    print(f"{oid} | loc={loc} | 义乌市={in_yiwu} | 白边={white} | 12丝={is12} | 14*20={is1420} | {company[:20]}")
    time.sleep(2.5)
c.close(vt)
json.dump(results, open("/tmp/bag_yiwu_reverify.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n=== 严格命中(义乌市 + 白边 + 12丝 + 14*20) ===")
for r in results:
    if r["yiwu"] and r["white"] and r["thick12"] and r["1420"]:
        print(f"  ▶ {r['id']} | {r['location']} | {r['company']} | specs={r['specs']}")
        print(f"    https://detail.1688.com/offer/{r['id']}.html")
