#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raw WebSocket CDP driver for 1688 江浙沪找品 (no Playwright; Chrome 151 兼容).

v2: SKU 来自 1688 内部 mtop 接口 queryofferskuselectormodel 的 skuMapOriginal JSON
    （结构化、零正则、零点击、零风控痕迹），比 v1 解析 DOM 文本更快更准。
    规格匹配直接读 specAttrs 字段，覆盖 连写/矩阵/轴名连写 三种写法。

Usage:
  python3 cdp1688.py --dims "25*13*32" "12*13*32" \
    --cat "牛皮纸手提袋" "牛皮纸袋" "纸袋" "手提袋" "牛皮纸" \
    --pages 3 --gap 3 --maxverify 120
"""
import sys, os, json, time, argparse, urllib.parse, re, base64, threading
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
VERIFY_JS = open(os.path.join(HERE, "verify_carton.js"), encoding="utf-8").read()  # 仅品类词过滤
PRICE_JS = open(os.path.join(HERE, "price_clean3.js"), encoding="utf-8").read()      # 兜底

PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"  # 江苏,浙江,上海

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

# 规格归一化：去 .0、去空白、统一 * 记号
def norm(s):
    return s.replace(".0", "").replace(" ", "").strip()

def dim_to_lwh(dim):
    parts = dim.split("*")
    L = norm(parts[0]); W = norm(parts[1] if len(parts) > 1 else parts[0]); H = norm(parts[2] if len(parts) > 2 else parts[0])
    return L, W, H

# 从 specAttrs 串抽取尺寸（支持 连写 / 轴名连写 / 矩阵 写法）
AXIS = "长|侧|宽|高|厚|竖|横|深"
def extract_sizes_from_spec(spec):
    """spec 形如 '（竖）25长*13侧*32高' 或 '8x8（长宽）;9cm（高）' 或 '25*13*32cm'
    返回 (connected_sizes_set, lw_pairs, heights)"""
    connected = set()
    lw = set()
    heights = set()
    # 连写 / 轴名连写：数字 分隔符 数字 分隔符 数字
    for m in re.finditer(r"([0-9][0-9.]*)[ ]*(?:"+AXIS+")?[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*(?:"+AXIS+")?[ ]*[*×xX][ ]*([0-9][0-9.]*)[ ]*(?:"+AXIS+")?[ ]*(cm|CM)?", spec):
        connected.add(norm(m.group(1)+"*"+m.group(2)+"*"+m.group(3)))
    # 矩阵：长宽轴 8x8（长宽）
    for m in re.finditer(r"([0-9][0-9.]*)[ ]*[xX×*][ ]*([0-9][0-9.]*)[ ]*[（(]?长宽", spec):
        lw.add(norm(m.group(1)+"*"+m.group(2)))
    # 高轴：9cm（高） / 9（高） / 高9cm
    for m in re.finditer(r"([0-9][0-9.]*)[ ]*(cm|CM)?[ ]*[（）()]*[ ]*高", spec):
        heights.add(norm(m.group(1)))
    # 组合串 8x8（长宽）;9cm（高）
    for m in re.finditer(r"([0-9][0-9.]*)[ ]*[xX×*][ ]*([0-9][0-9.]*)[ ]*[（(]?长宽[ )]*[;:]?[ ]*([0-9][0-9.]*)[ ]*(cm|CM)?[ ]*[）)]?[ ]*高", spec):
        connected.add(norm(m.group(1)+"*"+m.group(2)+"*"+m.group(3)))
    return connected, lw, heights

CARTON_SIG = re.compile(r"纸箱|瓦楞|快递箱|邮政箱|飞机盒|牛皮纸盒|牛皮纸袋|牛皮纸|搬家箱|收纳箱|包装盒|纸盒|手提袋|纸袋|购物袋|包装袋")
GIFT_SIG = re.compile(r"礼盒|礼品盒|礼品包装|开窗|烫金|巧克力|糖果|食品|蛋糕|首饰|珠宝|化妆品|护肤品|伴手礼")

def parse_sku_json(body):
    """从 skuMapOriginal JSON 文本提取 [(spec, price, stock), ...]"""
    rows = []
    try:
        # body 可能是 JSONP 包裹；去找 skuMapOriginal 数组
        i = body.find("skuMapOriginal")
        if i < 0:
            return rows
        # 取括号配平
        j = body.find("[", i)
        if j < 0:
            return rows
        depth = 0; end = j
        for k in range(j, len(body)):
            if body[k] == "[":
                depth += 1
            elif body[k] == "]":
                depth -= 1
                if depth == 0:
                    end = k + 1; break
        arr = json.loads(body[j:end])
        for it in arr:
            spec = it.get("specAttrs", "")
            price = it.get("discountPrice") or it.get("price")
            stock = it.get("canBookCount")
            rows.append((spec, price, stock))
    except Exception:
        pass
    return rows


class CDP:
    def __init__(self, url="http://127.0.0.1:9222"):
        import urllib.request
        ver = json.loads(urllib.request.urlopen(url + "/json/version", timeout=5).read())
        self.wsurl = ver["webSocketDebuggerUrl"]
        self.ws = websocket.create_connection(self.wsurl, timeout=60)
        self._id = 0
        self.events = []  # 后台收的事件
        self._t = threading.Thread(target=self._reader, daemon=True)
        self._t.start()

    def _reader(self):
        while True:
            try:
                self.events.append(json.loads(self.ws.recv()))
            except Exception:
                break

    def _send(self, method, params=None, session=None):
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        if session is not None:
            msg["sessionId"] = session
        self.ws.send(json.dumps(msg))
        return self._id

    def _recv_until(self, mid, timeout=60):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for idx, e in enumerate(self.events):
                if e.get("id") == mid:
                    self.events.pop(idx)
                    return e
            time.sleep(0.02)
        return None

    def cmd(self, method, params=None, session=None):
        mid = self._send(method, params, session)
        return self._recv_until(mid)

    def new_page(self, url="about:blank"):
        r = self.cmd("Target.createTarget", {"url": url, "background": True})
        target_id = r["result"]["targetId"]
        r2 = self.cmd("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        session = r2["result"]["sessionId"]
        self.cmd("Page.enable", {}, session)
        self.cmd("Runtime.enable", {}, session)
        self.cmd("Network.enable", {}, session)
        return target_id, session

    def navigate(self, session, url, timeout=40000):
        return self.cmd("Page.navigate", {"url": url, "timeout": timeout}, session)

    def evaluate(self, session, expr, await_promise=True, timeout_ms=30000):
        mid = self._send("Runtime.evaluate",
                         {"expression": expr, "returnByValue": True,
                          "awaitPromise": await_promise, "timeout": timeout_ms},
                         session)
        obj = self._recv_until(mid)
        if obj is None:
            return {"__error__": "timeout"}
        if "error" in obj:
            return {"__error__": obj["error"]}
        res = obj.get("result", {}).get("result", {})
        if res.get("subtype") == "error":
            return {"__error__": res.get("description", res.get("value"))}
        return res.get("value")

    def clear_events(self):
        self.events.clear()

    def get_sku(self, session, oid, timeout=18):
        """监听 queryofferskuselectormodel，返回 skuMapOriginal 原始 body 或 None。
        关键：全程轮询事件缓冲、不 clear（避免遍历中 pop 漏元素/时序错位）。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            for e in self.events:
                if e.get("method") == "Network.responseReceived":
                    u = e["params"]["response"]["url"]
                    if "queryofferskuselectormodel" in u:
                        rid = e["params"]["requestId"]
                        rb = self.cmd("Network.getResponseBody", {"requestId": rid}, session)
                        res = rb.get("result", {})
                        if res:
                            b = res.get("body", "")
                            if res.get("base64"):
                                try: b = base64.b64decode(b).decode("utf-8", "ignore")
                                except Exception: pass
                            if "skuMapOriginal" in b:
                                return b
            time.sleep(0.15)
        return None

    def close_target(self, target_id, session):
        try:
            self.cmd("Target.detachFromTarget", {"sessionId": session})
        except Exception:
            pass
        try:
            self.cmd("Target.closeTarget", {"targetId": target_id})
        except Exception:
            pass


def build_search_url(kw, begin_page):
    return ("https://s.1688.com/selloffer/offer_search.htm?keywords="
            + urllib.parse.quote(kw.encode("gbk")) + "&province=" + PROV + "&beginPage=" + str(begin_page))


def ascii_unescape(s):
    if not isinstance(s, str):
        return s
    try:
        return s.encode("utf-8").decode("unicode_escape")
    except Exception:
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", nargs="+", required=True)
    ap.add_argument("--cat", nargs="+", required=True)
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--gap", type=float, default=3.0)
    ap.add_argument("--maxverify", type=int, default=120)
    ap.add_argument("--out", default=os.path.join(SKILL, "store", "result_v2.json"))
    ap.add_argument("--cdp", default="http://127.0.0.1:9222")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    c = CDP(args.cdp)

    # 暖场
    wt, ws = c.new_page("https://www.1688.com/")
    time.sleep(6)

    # 1) 搜索 + 提取
    seen = set(); all_ids = []
    for kw in args.cat:
        for pg in range(1, args.pages + 1):
            url = build_search_url(kw, pg)
            c.navigate(ws, url)
            time.sleep(7)
            for _ in range(8):
                c.evaluate(ws, "window.scrollTo(0, document.body.scrollHeight)", await_promise=False)
                time.sleep(1.0)
            data = c.evaluate(ws, EXTRACT, await_promise=False)
            try:
                ids = (json.loads(data) or {}).get("ids", [])
            except Exception:
                ids = []
            for i in ids:
                if i not in seen:
                    seen.add(i); all_ids.append(i)
            print(f"[search] {kw} p{pg} +{len(ids)} total {len(all_ids)}")
    c.close_target(wt, ws)
    print(f"[extract] unique candidates: {len(all_ids)}")

    # 2) 详情页核验（v2：监听 SKU JSON）
    # 探针：强制纳入已知在售款，验证命中逻辑
    probe_ids = ["1158678687"]
    for pid in probe_ids:
        if pid not in all_ids:
            all_ids.insert(0, pid)
    vt, vs = c.new_page("about:blank")
    hits = {dim: [] for dim in args.dims}
    captcha_flag = False
    for oid in all_ids[: args.maxverify]:
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url)
            time.sleep(3)
            # 登录态丢失检测
            ttl = ascii_unescape(c.evaluate(vs, "document.title", await_promise=False) or "")
            if "淘宝网" in ttl or "taobao" in (c.evaluate(vs, "location.href", await_promise=False) or ""):
                print(f"[LOGIN-LOST] {oid} -> 登录态失效，停止")
                captcha_flag = "login_lost"; break

            body = c.get_sku(vs, oid, timeout=18)
            if not body:
                # 兜底 DOM
                dom_hit = False
                for dim in args.dims:
                    c.evaluate(vs, f"window.TARGET='{dim}';", await_promise=False)
                    time.sleep(0.4)
                    vraw = c.evaluate(vs, VERIFY_JS, await_promise=False)
                    v = json.loads(ascii_unescape(vraw)) if vraw else {}
                    if v.get("isCarton"):
                        praw = c.evaluate(vs, PRICE_JS, await_promise=False)
                        p = json.loads(ascii_unescape(praw)) if praw else {}
                        rec = {"id": oid, "dim": dim, "title": v.get("title"),
                               "price": p.get("targetPrice"), "stock": p.get("targetStock"),
                               "moq": p.get("moq"), "url": url, "source": "dom"}
                        hits[dim].append(rec)
                        print(f"[HIT(dom) {dim}] {oid} | {rec['price']} | 库存 {rec['stock']}")
                        dom_hit = True; break
                if not dom_hit:
                    print(f"[   ] {oid} SKU接口未抓到, DOM也未命中")
                time.sleep(args.gap); continue

            sku_rows = parse_sku_json(body)
            # 品类词：用页面 title（含「牛皮纸袋手提袋」等） + SKU 里的 specAttrs 汇总
            page_title = ascii_unescape(c.evaluate(vs, "document.title", await_promise=False) or "")
            specs_blob = " ".join(s for s, _, _ in sku_rows)
            title_text = page_title + " " + specs_blob
            carton = bool(CARTON_SIG.search(title_text))
            gift = bool(GIFT_SIG.search(page_title))
            if not carton or gift:
                print(f"[   ] {oid} carton={carton} gift={gift} (sku rows={len(sku_rows)})")
                time.sleep(args.gap); continue

            matched = False
            for dim in args.dims:
                L, W, H = dim_to_lwh(dim)
                target_lw = norm(L + "*" + W); target_lwh = norm(L + "*" + W + "*" + H)
                for spec, price, stock in sku_rows:
                    connected, lw, heights = extract_sizes_from_spec(spec)
                    size_hit = (target_lwh in connected) or (target_lw in lw and H in heights)
                    if size_hit:
                        rec = {"id": oid, "dim": dim, "title": page_title[:36],
                               "price": ("¥" + str(price)) if price else None,
                               "stock": stock, "moq": None, "url": url,
                               "spec": spec, "source": "skujson"}
                        hits[dim].append(rec)
                        print(f"[HIT {dim}] {oid} | {spec} | {rec['price']} | 库存 {stock}")
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                print(f"[   ] {oid} sku rows={len(sku_rows)} 未匹配目标尺寸")
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)}")
        time.sleep(args.gap)

    c.close_target(vt, vs)
    try: c.ws.close()
    except Exception: pass

    result = {"dims": args.dims, "cat": args.cat, "prov": "江浙沪",
              "candidates": len(all_ids), "hits": hits, "captcha_flag": captcha_flag}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[done] candidates={len(all_ids)} "
          + " ".join(f"{d}={len(hits.get(d,[]))}" for d in args.dims)
          + f" -> {args.out}")


if __name__ == "__main__":
    main()
