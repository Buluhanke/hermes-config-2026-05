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
PROV_DEFAULT = PROV  # 供 argparse default 用（避免 UnboundLocalError）

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

import itertools
def target_perms(dim):
    """目标尺寸的全部排列（顺序无关）：46*26*10 == 46*10*26 == 26*10*46 ..."""
    parts = [norm(p) for p in dim.split("*")]
    s = set()
    for perm in set(itertools.permutations(parts)):
        s.add("*".join(perm))
    return s

def tolerant_perms(dim, tol=5.0):
    """容差匹配：每个维度允许 目标~目标+tol cm（只往上加，不往下减）。
    如 46*26*10 +5 => 长∈[46,51] 宽∈[26,31] 高∈[10,15]，顺序无关。"""
    parts = [float(norm(p)) for p in dim.split("*")]
    def hit(connected):
        for c in connected:
            nums = c.split("*")
            if len(nums) != 3:
                continue
            try:
                vals = [float(n) for n in nums]
            except Exception:
                continue
            for perm in set(itertools.permutations(vals)):
                used = [False]*3
                ok = True
                for j, v in enumerate(perm):
                    mi = -1
                    for i in range(3):
                        if not used[i] and parts[i] - 1e-9 <= v <= parts[i] + tol + 1e-9:
                            mi = i; break
                    if mi < 0:
                        ok = False; break
                    used[mi] = True
                if ok and all(used):
                    return True
        return False
    return hit

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
    for m in re.finditer(r"([0-9][0-9.]*)[ ]*[xX×*][ ]*([0-9][0-9.]*)[ ]*[（(]?长宽[）)]?[ )]*[;:]?[ ]*([0-9][0-9.]*)[ ]*(cm|CM)?[ ]*[（(]?高", spec):
        connected.add(norm(m.group(1)+"*"+m.group(2)+"*"+m.group(3)))
    # 全角【】轴名组合：宽【26cm】高【10cm】;特硬;长【46cm】 或 长46cm】等
    # 抓每个轴 -> 值
    axis_val = {}
    for m in re.finditer(r"([长宽高侧厚竖横深])\s*【\s*([0-9][0-9.]*)\s*(?:cm|CM)?\s*】", spec):
        axis_val[m.group(1)] = norm(m.group(2))
    # 也兼容半角/无括号：长46cm / 宽26cm / 高10cm（后面紧跟非数字）
    for m in re.finditer(r"([长宽高侧厚竖横深])\s*[:：]?\s*([0-9][0-9.]*)\s*(?:cm|CM)?(?![0-9])", spec):
        if m.group(1) not in axis_val:
            axis_val[m.group(1)] = norm(m.group(2))
    if "长" in axis_val and "宽" in axis_val and "高" in axis_val:
        L = axis_val["长"]; W = axis_val["宽"]; H = axis_val["高"]
        connected.add(norm(L+"*"+W+"*"+H))
        lw.add(norm(L+"*"+W)); heights.add(H)
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
        """返回含 skuMapOriginal 的 body。
        1688 通常把 SKU 服务端直出在 HTML（即时可得），优先抓 outerHTML；
        若没有再监听 queryofferskuselectormodel 网络响应兜底。"""
        # 1) 优先：HTML 直出（即时）
        try:
            h = self.evaluate(session, "document.documentElement.outerHTML", await_promise=False) or ""
            if "skuMapOriginal" in h:
                return h
        except Exception:
            pass
        # 2) 兜底：监听 mtop 接口
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


def build_search_url(kw, begin_page, prov=PROV):
    base = ("https://s.1688.com/selloffer/offer_search.htm?keywords="
            + urllib.parse.quote(kw.encode("gbk")))
    if prov:
        base += "&province=" + prov
    base += "&beginPage=" + str(begin_page)
    return base


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
    ap.add_argument("--prov", default=PROV_DEFAULT, help="省份筛选GBK编码，传空串 '' 关闭地域限制")
    ap.add_argument("--mobile", action="store_true", help="用 m.1688.com 移动端搜页（PC搜页被风控时绕行）")
    ap.add_argument("--tol", type=float, default=0.0, help="容差cm：每维允许+0~tol（如5=每个尺寸网上加5cm内都算命中）")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    c = CDP(args.cdp)
    PROV = args.prov  # 覆盖模块级 PROV，供 build_search_url 用

    def build_search_url(kw, begin_page, prov=PROV):
        if args.mobile:
            base = ("https://m.1688.com/offer_search.html?keywords="
                    + urllib.parse.quote(kw.encode("gbk")) + "&page=" + str(begin_page))
        else:
            base = ("https://s.1688.com/selloffer/offer_search.htm?keywords="
                    + urllib.parse.quote(kw.encode("gbk")))
            if prov:
                base += "&province=" + prov
            base += "&beginPage=" + str(begin_page)
        return base
    wt, ws = c.new_page("https://www.1688.com/")
    time.sleep(6)

    # 搜页风控：检测到验证码就退避重试，不在被拦时硬撞
    def search_page_captcha():
        h = c.evaluate(ws, "document.documentElement.outerHTML", await_promise=False) or ""
        return ("验证码" in h) or ("captcha" in (c.evaluate(ws, "location.href", await_promise=False) or "").lower())

    backoff = 1
    # 1) 搜索 + 提取
    seen = set(); all_ids = []
    for kw in args.cat:
        for pg in range(1, args.pages + 1):
            # 退避期检测：若当前就是验证码页，先等恢复
            waited = 0
            while search_page_captcha() and waited < 600:
                print(f"[CAPTCHA] 搜页被拦, 退避 {backoff*15}s (已等{waited}s)")
                time.sleep(backoff * 15); waited += backoff * 15
                backoff = min(backoff + 1, 4)
            url = build_search_url(kw, pg)
            c.navigate(ws, url)
            time.sleep(7)
            if search_page_captcha():
                print(f"[CAPTCHA] {kw} p{pg} 被拦, 退避后重试")
                time.sleep(backoff * 15); backoff = min(backoff + 1, 4)
                c.navigate(ws, url); time.sleep(7)
                if search_page_captcha():
                    print(f"[CAPTCHA] {kw} p{pg} 仍被拦, 跳过该词后续页")
                    break
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
            if not ids and not search_page_captcha():
                # 真没结果（非风控），翻页也白搭
                pass
    c.close_target(wt, ws)
    print(f"[extract] unique candidates: {len(all_ids)}")

    # 2) 详情页核验（v2：监听 SKU JSON）
    vt, vs = c.new_page("about:blank")
    hits = {dim: [] for dim in args.dims}
    captcha_flag = False
    save_state = lambda: json.dump(
        {"dims": args.dims, "cat": args.cat, "prov": args.prov or "全国",
         "candidates": len(all_ids), "hits": hits, "captcha_flag": captcha_flag},
        open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    login_lost_streak = 0
    for idx, oid in enumerate(all_ids[: args.maxverify]):
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url)
            time.sleep(3)
            # 详情页验证码/登录态检测
            page_html0 = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
            if "验证码" in page_html0:
                print(f"[CAPTCHA] {oid} 详情页被拦, 退避")
                time.sleep(30); c.navigate(vs, url); time.sleep(4)
                page_html0 = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
                if "验证码" in page_html0:
                    print(f"[CAPTCHA] {oid} 仍被拦, 跳过")
                    captcha_flag = "detail_captcha"; time.sleep(args.gap); continue
            # 登录态丢失检测（单个登录墙商品不应终止整个核验）
            ttl = ascii_unescape(c.evaluate(vs, "document.title", await_promise=False) or "")
            href = c.evaluate(vs, "location.href", await_promise=False) or ""
            if "淘宝网" in ttl or "taobao" in href:
                login_lost_streak += 1
                print(f"[LOGIN-WALL] {oid} 登录墙商品, 跳过 (连续{login_lost_streak})")
                if login_lost_streak >= 5:
                    print(f"[LOGIN-LOST] 连续5个登录墙, 判定会话失效停止")
                    captcha_flag = "login_lost"; break
                time.sleep(args.gap); continue
            login_lost_streak = 0

            body = c.get_sku(vs, oid, timeout=26)
            # 整页文本（含正文/规格区写的组合串，不只 skuMapOriginal 的 specAttrs）
            page_html = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
            if not body:
                # 整页兜底：直接对 outerHTML 抽尺寸
                full_hit = False
                for dim in args.dims:
                    perms = target_perms(dim)
                    # 从整页里逐段抽 spec 串（按常见分隔切）
                    for seg in re.split(r"[;；\n|丨]", page_html):
                        if "长" in seg or "宽" in seg or "高" in seg or re.search(r"[0-9][0-9.]*[xX×*][0-9]", seg):
                            connected, lw, heights = extract_sizes_from_spec(seg)
                            if any(p in connected for p in perms):
                                rec = {"id": oid, "dim": dim, "title": "", "price": None,
                                       "stock": None, "moq": None, "url": url, "spec": seg[:40], "source": "page"}
                                hits[dim].append(rec)
                                print(f"[HIT(page) {dim}] {oid} | {seg[:40]}")
                                full_hit = True; break
                    if full_hit: break
                if full_hit:
                    time.sleep(args.gap); continue
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
            # 品类词：用页面 title + SKU specAttrs + 整页文本
            page_title = ascii_unescape(c.evaluate(vs, "document.title", await_promise=False) or "")
            specs_blob = " ".join(s for s, _, _ in sku_rows)
            title_text = page_title + " " + specs_blob + " " + page_html[:20000]
            carton = bool(CARTON_SIG.search(title_text))
            gift = bool(GIFT_SIG.search(page_title))
            if gift:
                print(f"[   ] {oid} gift=True skipped (sku rows={len(sku_rows)})")
                time.sleep(args.gap); continue
            if not carton:
                print(f"[   ] {oid} carton=False(非纸包装类目), 跳过")
                time.sleep(args.gap); continue

            matched = False
            for dim in args.dims:
                perms = target_perms(dim)  # 顺序无关精确匹配
                tol_hit = tolerant_perms(dim, args.tol) if args.tol > 0 else (lambda conn: any(p in conn for p in perms))
                # 1) skuMapOriginal specAttrs
                for spec, price, stock in sku_rows:
                    connected, lw, heights = extract_sizes_from_spec(spec)
                    size_hit = tol_hit(connected)
                    if size_hit:
                        rec = {"id": oid, "dim": dim, "title": page_title[:36],
                               "price": ("¥" + str(price)) if price else None,
                               "stock": stock, "moq": None, "url": url,
                               "spec": spec, "source": "skujson",
                               "exact": any(p in connected for p in perms)}
                        hits[dim].append(rec)
                        print(f"[HIT {dim}{'(近似)' if not rec['exact'] else ''}] {oid} | {spec} | {rec['price']} | 库存 {stock}")
                        matched = True
                        break
                if matched:
                    break
                # 2) 整页文本兜底：逐段抽组合串/连写尺寸
                for seg in re.split(r"[;；\n|丨]", page_html):
                    if "长" in seg or "宽" in seg or "高" in seg or re.search(r"[0-9][0-9.]*[xX×*][0-9]", seg):
                        connected, lw, heights = extract_sizes_from_spec(seg)
                        if tol_hit(connected):
                            rec = {"id": oid, "dim": dim, "title": page_title[:36],
                                   "price": None, "stock": None, "moq": None, "url": url,
                                   "spec": seg[:40], "source": "page",
                                   "exact": any(p in connected for p in perms)}
                            hits[dim].append(rec)
                            print(f"[HIT(page) {dim}{'(近似)' if not rec['exact'] else ''}] {oid} | {seg[:40]}")
                            matched = True
                            break
                if matched:
                    break
            if not matched:
                print(f"[   ] {oid} sku rows={len(sku_rows)} 未匹配目标尺寸")
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:80]}")
        time.sleep(args.gap)
        # 增量写盘：每查完一个候选就落盘，防中途被杀丢结果
        if (idx + 1) % 5 == 0 or any(hits[d] for d in args.dims):
            save_state()

    c.close_target(vt, vs)
    try: c.ws.close()
    except Exception: pass
    save_state()  # 最终落盘

    result = {"dims": args.dims, "cat": args.cat, "prov": args.prov or "全国",
              "candidates": len(all_ids), "hits": hits, "captcha_flag": captcha_flag}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[done] candidates={len(all_ids)} "
          + " ".join(f"{d}={len(hits.get(d,[]))}" for d in args.dims)
          + f" -> {args.out}")


if __name__ == "__main__":
    main()
