#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补验：重搜 4 词抓候选 ID，排除已验 18 个，只验剩余；重点筛 14*20 白边(含红边)+12丝。"""
import sys, os, json, time, argparse, urllib.parse, re, base64, threading
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
PROV = "%D5%E3%BD%AD"  # 浙江

EXTRACT = r"""
(()=>{
  const h=document.documentElement.outerHTML;
  const ids=new Set(); let m;
  const re1=/detail\.1688\.com\/offer\/([0-9]+)/g;
  while((m=re1.exec(h))!==null) ids.add(m[1]);
  const re2=/[?&]offerId=([0-9]+)/g;
  while((m=re2.exec(h))!==null) ids.add(m[1]);
  const re3=/offerId["']?\s*[:=]\s*["']?([0-9]+)/g;
  while((m=re3.exec(h))!==null) ids.add(m[1]);
  return JSON.stringify({ids:[...ids].filter(id=>id.length>=9&&id.length<=14)});
})();
"""

def norm(s):
    return s.replace(".0","").replace(" ","").strip()

def extract_2d(spec):
    sizes=set()
    for m in re.finditer(r"(?<![0-9*])([0-9][0-9.]*)\s*[xX×*]\s*([0-9][0-9.]*)\s*(?:cm|CM|毫米|mm)?(?![0-9*])", spec):
        sizes.add(norm(f"{m.group(1)}*{m.group(2)}"))
    return sizes

def extract_thickness(spec):
    t=set()
    for m in re.finditer(r"([0-9][0-9.]*)\s*丝", spec):
        t.add(norm(m.group(1)))
    return t

BAG_SIG = re.compile(r"自封袋|塑料袋|PE袋|opp袋|封口袋|拉链袋|包装袋|骨袋")
GIFT_SIG = re.compile(r"礼盒|礼品盒|开窗|烫金|巧克力|糖果|食品|蛋糕|首饰|珠宝|化妆品|护肤品|伴手礼")

def parse_sku_json(body):
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
        arr=json.loads(body[j:end])
        for it in arr:
            rows.append((it.get("specAttrs",""), it.get("discountPrice") or it.get("price"), it.get("canBookCount")))
    except Exception:
        pass
    return rows

class CDP:
    def __init__(self, url="http://127.0.0.1:9222"):
        import urllib.request
        ver=json.loads(urllib.request.urlopen(url+"/json/version",timeout=5).read())
        self.ws=websocket.create_connection(ver["webSocketDebuggerUrl"],timeout=60)
        self._id=0; self.events=[]; self._t=threading.Thread(target=self._reader,daemon=True); self._t.start()
    def _reader(self):
        while True:
            try: self.events.append(json.loads(self.ws.recv()))
            except Exception: break
    def _send(self,method,params=None,session=None):
        self._id+=1; msg={"id":self._id,"method":method}
        if params is not None: msg["params"]=params
        if session is not None: msg["sessionId"]=session
        self.ws.send(json.dumps(msg)); return self._id
    def _recv_until(self,mid,timeout=60):
        t0=time.time()
        while time.time()-t0<timeout:
            for idx,e in enumerate(self.events):
                if e.get("id")==mid:
                    self.events.pop(idx); return e
            time.sleep(0.02)
        return None
    def cmd(self,method,params=None,session=None):
        return self._recv_until(self._send(method,params,session))
    def new_page(self,url="about:blank"):
        r=self.cmd("Target.createTarget",{"url":url,"background":True})
        tid=r["result"]["targetId"]
        r2=self.cmd("Target.attachToTarget",{"targetId":tid,"flatten":True})
        sid=r2["result"]["sessionId"]
        for m in ("Page","Runtime","Network"): self.cmd(m+".enable",{},sid)
        return tid,sid
    def navigate(self,sid,url,timeout=40000):
        return self.cmd("Page.navigate",{"url":url,"timeout":timeout},sid)
    def evaluate(self,sid,expr,await_p=False,timeout_ms=30000):
        mid=self._send("Runtime.evaluate",{"expression":expr,"returnByValue":True,"awaitPromise":await_p,"timeout":timeout_ms},sid)
        o=self._recv_until(mid)
        if o is None: return {"__error__":"timeout"}
        if "error" in o: return {"__error__":o["error"]}
        r=o.get("result",{}).get("result",{})
        if r.get("subtype")=="error": return {"__error__":r.get("description",r.get("value"))}
        return r.get("value")
    def get_sku(self,sid,timeout=18):
        try:
            h=self.evaluate(sid,"document.documentElement.outerHTML",await_p=False) or ""
            if "skuMapOriginal" in h: return h
        except Exception: pass
        t0=time.time()
        while time.time()-t0<timeout:
            for e in self.events:
                if e.get("method")=="Network.responseReceived":
                    u=e["params"]["response"]["url"]
                    if "queryofferskuselectormodel" in u:
                        rid=e["params"]["requestId"]
                        rb=self.cmd("Network.getResponseBody",{"requestId":rid},sid)
                        res=rb.get("result",{})
                        if res:
                            b=res.get("body","")
                            if res.get("base64"):
                                try: b=base64.b64decode(b).decode("utf-8","ignore")
                                except Exception: pass
                            if "skuMapOriginal" in b: return b
            time.sleep(0.15)
        return None
    def close_target(self,tid,sid):
        try: self.cmd("Target.detachFromTarget",{"sessionId":sid})
        except Exception: pass
        try: self.cmd("Target.closeTarget",{"targetId":tid})
        except Exception: pass

def ascii_unescape(s):
    if not isinstance(s,str): return s
    try: return s.encode("utf-8").decode("unicode_escape")
    except Exception: return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dims",nargs="+",default=["14*20"])
    ap.add_argument("--cat",nargs="+",default=["14*20cm白边12丝塑料自封袋","14*20自封袋白边","白边自封袋","塑料自封袋"])
    ap.add_argument("--pages",type=int,default=4)
    ap.add_argument("--gap",type=float,default=2.5)
    ap.add_argument("--out",default=os.path.join(SKILL,"store","bag_14x20_yiwu_reverify.json"))
    ap.add_argument("--skipfile",default=os.path.join(SKILL,"store","bag_14x20_yiwu.json"))
    ap.add_argument("--city",default="义乌")
    ap.add_argument("--thick",type=float,default=12.0)
    args=ap.parse_args()

    # 已验 ID
    skip=set()
    try:
        d=json.load(open(args.skipfile,encoding="utf-8"))
        for h in d.get("hits",{}).get("14*20",[]):
            skip.add(h["id"])
    except Exception: pass
    print(f"[skip] 已验 {len(skip)} 个排除")

    c=CDP()
    wt,ws=c.new_page("https://www.1688.com/"); time.sleep(6)
    def _str(v):
        return v if isinstance(v,str) else ""
    def search_captcha():
        h=_str(c.evaluate(ws,"document.documentElement.outerHTML",await_p=False))
        href=_str(c.evaluate(ws,"location.href",await_p=False)).lower()
        return ("验证码" in h) or ("captcha" in href)

    seen=set(); all_ids=[]
    backoff=1
    for kw in args.cat:
        for pg in range(1,args.pages+1):
            waited=0
            while search_captcha() and waited<600:
                print(f"[CAPTCHA] 退避 {backoff*15}s"); time.sleep(backoff*15); waited+=backoff*15; backoff=min(backoff+1,4)
            url=("https://s.1688.com/selloffer/offer_search.htm?keywords="
                 +urllib.parse.quote(kw.encode("gbk"))+"&province="+PROV+"&beginPage="+str(pg))
            c.navigate(ws,url); time.sleep(7)
            if search_captcha():
                time.sleep(backoff*15); backoff=min(backoff+1,4); c.navigate(ws,url); time.sleep(7)
                if search_captcha(): print(f"[skip] {kw} p{pg}"); break
            for _ in range(8):
                c.evaluate(ws,"window.scrollTo(0,document.body.scrollHeight)",await_p=False); time.sleep(1.0)
            try: ids=json.loads(c.evaluate(ws,EXTRACT,await_p=False) or "{}").get("ids",[])
            except Exception: ids=[]
            for i in ids:
                if i not in seen: seen.add(i); all_ids.append(i)
            print(f"[search] {kw} p{pg} +{len(ids)} total {len(all_ids)}")
    c.close_target(wt,ws)

    # 只验未验
    todo=[i for i in all_ids if i not in skip]
    print(f"[todo] 未验候选 {len(todo)} (总 {len(all_ids)}, 已验 {len(skip)})")

    vt,vs=c.new_page("about:blank")
    hits=[]
    login_streak=0
    def save():
        json.dump({"dims":args.dims,"cat":args.cat,"city":args.city,"todo":len(todo),
                    "hits":hits},open(args.out,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    for idx,oid in enumerate(todo):
        try:
            url=f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs,url); time.sleep(3)
            page0=_str(c.evaluate(vs,"document.documentElement.outerHTML",await_p=False))
            if "验证码" in page0:
                time.sleep(30); c.navigate(vs,url); time.sleep(4)
                page0=_str(c.evaluate(vs,"document.documentElement.outerHTML",await_p=False))
                if "验证码" in page0: save(); time.sleep(args.gap); continue
            ttl=ascii_unescape(_str(c.evaluate(vs,"document.title",await_p=False)))
            href=_str(c.evaluate(vs,"location.href",await_p=False))
            if "淘宝网" in ttl or "taobao" in href:
                login_streak+=1; print(f"[LOGIN-WALL] {oid} ({login_streak})")
                if login_streak>=5: print("[STOP] 登录墙连续5"); break
                time.sleep(args.gap); continue
            login_streak=0
            body=c.get_sku(vs,timeout=26)
            page_html=_str(c.evaluate(vs,"document.documentElement.outerHTML",await_p=False))
            if not body:
                time.sleep(args.gap); continue
            rows=parse_sku_json(body)
            specs_blob=" ".join(s for s,_,_ in rows)
            title_text=ttl+" "+specs_blob+" "+page_html[:20000]
            if not BAG_SIG.search(title_text):
                time.sleep(args.gap); continue
            if GIFT_SIG.search(ttl):
                time.sleep(args.gap); continue
            loc=""; m=re.search(r'"location"\s*:\s*"([^"]*)"',page_html)
            if m: loc=m.group(1)
            company=""; mc=re.search(r'"companyName"\s*:\s*"([^"]*)"',page_html)
            if mc: company=mc.group(1)
            in_region=("浙江省" in loc) or ("江苏省" in loc) or ("上海市" in loc)
            in_yiwu=in_region and ("金华市" in loc)
            if not in_region or not in_yiwu:
                time.sleep(args.gap); continue
            # 白边信号：白边/红边/加宽边
            white = ("白边" in specs_blob or "红边" in specs_blob or "加宽边" in specs_blob
                     or "白边" in page_html[:20000] or "红边" in page_html[:20000])
            # 12丝：必须精确 spec 那条含 12丝
            thick_vals=set()
            for s,_,_ in rows: thick_vals|=extract_thickness(s)
            for seg in re.split(r"[;；\n|丨]",page_html): thick_vals|=extract_thickness(seg)
            is_thick = norm(str(args.thick)) in thick_vals
            # 尺寸匹配
            matched=False
            for d in args.dims:
                perms={norm(f"{a}*{b}") for a in d.split("*") for b in d.split("*") if a!=b}  # fallback
                from itertools import permutations
                perms={f"{a}*{b}" for a,b in permutations([norm(x) for x in d.split("*")],2)}
                for spec,price,stock in rows:
                    if any(p in extract_2d(spec) for p in perms):
                        matched=True
                        rec={"id":oid,"dim":d,"title":ttl[:40],"price":("¥"+str(price)) if price else None,
                             "stock":stock,"url":url,"spec":spec,"location":loc,"company":company,
                             "white_edge":white,"thick_12si":is_thick}
                        hits.append(rec)
                        tag=[]
                        if white: tag.append("白边(含红边)")
                        if is_thick: tag.append("12丝")
                        print(f"[HIT] {oid} | {spec} | {rec['price']} | {loc} | {'/'.join(tag) or '缺特征'}")
                        break
                if matched: break
            if not matched:
                print(f"[   ] {oid} sku={len(rows)} 无14*20")
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:80]}")
        time.sleep(args.gap)
        if (idx+1)%5==0: save()
    c.close_target(vt,vs)
    try: c.ws.close()
    except Exception: pass
    save()
    print(f"[done] todo={len(todo)} hits={len(hits)} -> {args.out}")

if __name__=="__main__":
    main()
