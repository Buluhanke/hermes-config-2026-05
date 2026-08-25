#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1688 找品任务前置探针（FAIL-FAST）。
在任何 cdp1688*.py 全量跑之前先跑它，30 秒内判定通道是否健康，
避免像 2026-08-25 那样搜页登录态已死却硬跑 15 分钟、最后"搜出全是茶叶/铝箔袋"。

检测两项：
  1) 详情页登录态：开一个已知 detail 页，看是否跳 login.taobao.com / 无 skuMapOriginal
  2) 搜页登录态：开一个搜索页，看候选数是否为 0（0 = 被踢去登录中转，不是没货）

判定：
  PASS  → 直接开跑主驱动
  FAIL  → 打印可执行的下一步（重注 / 让用户回默认 Chrome 登录 1688）
"""
import sys, os, json, time, argparse, urllib.parse, re, threading
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
ZHEJIANG = "%D5%E3%BD%AD"  # 浙江 GBK


class CDP:
    def __init__(s, url="http://127.0.0.1:9222"):
        import urllib.request
        v = json.loads(urllib.request.urlopen(url + "/json/version", timeout=5).read())
        s.ws = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=60)
        s._id = 0; s.ev = []; threading.Thread(target=s._r, daemon=True).start()
    def _r(s):
        while True:
            try: s.ev.append(json.loads(s.ws.recv()))
            except: break
    def _s(s, m, p=None, sid=None):
        s._id += 1; o = {"id": s._id, "method": m}
        if p is not None: o["params"] = p
        if sid is not None: o["sessionId"] = sid
        s.ws.send(json.dumps(o)); return s._id
    def _recv(s, mid, to=60):
        t = time.time()
        while time.time() - t < to:
            for i, e in enumerate(s.ev):
                if e.get("id") == mid:
                    s.ev.pop(i); return e
            time.sleep(0.02)
        return None
    def cmd(s, m, p=None, sid=None): return s._recv(s._s(m, p, sid))
    def np(s, u="about:blank"):
        r = s.cmd("Target.createTarget", {"url": u, "background": True})
        tid = r["result"]["targetId"]
        r2 = s.cmd("Target.attachToTarget", {"targetId": tid, "flatten": True})
        sid = r2["result"]["sessionId"]
        for mm in ("Page", "Runtime", "Network"): s.cmd(mm + ".enable", {}, sid)
        return tid, sid
    def nav(s, sid, u, to=40000): return s.cmd("Page.navigate", {"url": u, "timeout": to}, sid)
    def evaluate(s, sid, x, ap=False, t=20000):
        mid = s._s("Runtime.evaluate", {"expression": x, "returnByValue": True,
                                         "awaitPromise": ap, "timeout": t}, sid)
        o = s._recv(mid)
        if o is None: return None
        if "error" in o: return None
        r = o.get("result", {}).get("result", {})
        if r.get("subtype") == "error": return None
        return r.get("value")
    def ct(s, tid, sid):
        try: s.cmd("Target.detachFromTarget", {"sessionId": sid})
        except: pass
        try: s.cmd("Target.closeTarget", {"targetId": tid})
        except: pass


EXTRACT = r"""
(()=>{const h=document.documentElement.outerHTML;const ids=new Set();let m;
const re1=/detail\.1688\.com\/offer\/([0-9]+)/g;while((m=re1.exec(h))!==null)ids.add(m[1]);
const re2=/[?&]offerId=([0-9]+)/g;while((m=re2.exec(h))!==null)ids.add(m[1]);
return JSON.stringify({ids:[...ids].filter(id=>id.length>=9&&id.length<=14)});})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cdp", default="http://127.0.0.1:9222")
    ap.add_argument("--probe-id", default="685142110437",
                    help="已知在售 detail 页（默认义乌白边12丝自封袋，2026-08-25 验证存活）")
    ap.add_argument("--kw", default="白边自封袋", help="探搜页用的关键词")
    ap.add_argument("--prov", default=ZHEJIANG, help="省份GBK，传 '' 关")
    args = ap.parse_args()

    print("=== 1688 找品通道前置探针 ===")
    # 0) 9222 在线？
    try:
        import urllib.request
        json.loads(urllib.request.urlopen(args.cdp + "/json/version", timeout=5).read())
    except Exception as e:
        print("[FAIL] 9222 CDP 未在线：", e)
        print("       执行: bash", os.path.join(HERE, "start_cdp_1688.sh"))
        sys.exit(1)
    print("[OK] 9222 CDP 在线")

    c = CDP(args.cdp)
    wt, ws = c.np("https://www.1688.com/")
    time.sleep(5)

    # 1) 详情页登录态
    c.nav(ws, f"https://detail.1688.com/offer/{args.probe_id}.html"); time.sleep(3)
    href = c.evaluate(ws, "location.href", ap=False) or ""
    ttl = c.evaluate(ws, "document.title", ap=False) or ""
    html = c.evaluate(ws, "document.documentElement.outerHTML", ap=False) or ""
    detail_wall = ("login.taobao" in href) or ("淘宝网" in ttl) or ("skuMapOriginal" not in html)
    print(f"[{'FAIL' if detail_wall else 'OK'}] 详情页 {args.probe_id} "
          f"{'登录墙/无SKU' if detail_wall else '登录态正常'}")

    # 2) 搜页登录态（0 候选 = 被踢去登录，不是没货）
    url = ("https://s.1688.com/selloffer/offer_search.htm?keywords="
           + urllib.parse.quote(args.kw.encode("gbk")))
    if args.prov:
        url += "&province=" + args.prov
    url += "&beginPage=1"
    c.nav(ws, url); time.sleep(6)
    shref = c.evaluate(ws, "location.href", ap=False) or ""
    shtml = c.evaluate(ws, "document.documentElement.outerHTML", ap=False) or ""
    search_wall = ("login.taobao" in shref) or ("验证码" in shtml)
    try:
        ids = (json.loads(c.evaluate(ws, EXTRACT, ap=False) or "{}") or {}).get("ids", [])
    except Exception:
        ids = []
    print(f"[{'FAIL' if search_wall else 'OK'}] 搜页 '{args.kw}' -> 候选 {len(ids)} "
          f"{'登录墙' if search_wall else '正常'}")

    c.ct(wt, ws)

    if detail_wall or search_wall:
        print("\n[VERDICT] FAIL —— 登录态已掉，直接跑会 '搜出其他品'/0命中。下一步：")
        print("  1) 重注: bash", os.path.join(HERE, "start_cdp_1688.sh"))
        print("  2) 重试本探针；若仍 FAIL → 用户在默认 Chrome 重新登录 1688 后再跑")
        print("  3) 或改用主驱动 --reverify 模式只验已知ID池（不依赖搜页）")
        sys.exit(1)
    if len(ids) == 0:
        print("\n[VERDICT] WARN —— 登录态在但搜页 0 候选，可能关键词过窄/被风控，先确认词再跑")
        sys.exit(2)
    print("\n[VERDICT] PASS —— 通道健康，直接开跑主驱动")
    sys.exit(0)


if __name__ == "__main__":
    main()
