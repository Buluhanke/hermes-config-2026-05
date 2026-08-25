#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1688 自封袋专用驱动（2D 尺寸：宽*高，非 3D 箱）。
场景：14*20cm 白边*12丝 塑料自封袋，地区=义乌市（浙江）。

匹配逻辑：
  - 尺寸：2D 宽*高，顺序无关（14*20 == 20*14）
  - 白边：规格含 “白边”/“红边”/“加宽边”（用户口径：有红边就有白边）
  - 12丝：只认「含目标尺寸的 spec」里的丝数（不并整页无关段，防误判）
  - 地区：1688 定位字段标“浙江省金华市”=义乌产业带；非金华即跳过
  - 品类：自封袋/塑料袋/PE袋/opp袋

2026-08-25 故障修复（全部收编进本驱动，勿再散落独立脚本）：
  - 标题乱码：CDP evaluate 已是正常 utf-8，删掉错误的 ascii_unescape（原是 AppleScript 通道修法，CDP 不需要）
  - 白边信号扩词（白边/红边/加宽边）
  - 厚度按「含目标尺寸的 spec」精确判定，不并整页
  - 登录墙自动重注 inject_cookies.py（连续2次触发），阈值提到8才停
  - 搜索阶段即落盘 candidates.txt + 每验1个实时写盘（可观测/可续跑）
  - PC 搜页被验证码自动降级移动端 m.1688.com
  - 内置 --reverify FILE 模式（读候选ID，跳过已验，复用主逻辑）
  - 注意：macOS 无 timeout 命令，本脚本不依赖它
"""
import sys, os, json, time, argparse, urllib.parse, re, base64, threading, subprocess
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

# 地区默认浙江（义乌在浙江金华；用户要义乌时传 --city 义乌 + --prov 浙江）
PROV_ZHEJIANG = "%D5%E3%BD%AD"   # 浙江
PROV_JZH = "%D5%E3%BD%AD,%BD%AD%CE%AA,%C9%CF%BA%A3"  # 江浙沪

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
    return s.replace(".0", "").replace(" ", "").strip()

def target_perms_2d(dim):
    """2D 宽*高 全部排列（顺序无关）：14*20 == 20*14"""
    parts = [norm(p) for p in dim.split("*")]
    if len(parts) < 2:
        return set()
    a, b = parts[0], parts[1]
    return {f"{a}*{b}", f"{b}*{a}"}

# 2D 尺寸抽取：宽*高（恰好两个数字，避免误中三个数字的箱规）
def extract_2d(spec):
    sizes = set()
    for m in re.finditer(r"(?<![0-9*])([0-9][0-9.]*)\s*[xX×*]\s*([0-9][0-9.]*)\s*(?:cm|CM|毫米|mm)?(?![0-9*])", spec):
        sizes.add(norm(f"{m.group(1)}*{m.group(2)}"))
    return sizes

def extract_thickness(spec):
    """厚度（丝）：12丝 / 12丝厚 / 厚12丝"""
    t = set()
    for m in re.finditer(r"([0-9][0-9.]*)[\s]*丝", spec):
        t.add(norm(m.group(1)))
    return t

# 塑料自封袋品类硬卡：必须含「塑料/PE/opp」且是「自封袋」，排除茶叶/铝箔/牛皮纸/食品袋
# （这些是广义自封袋但不是用户要的"塑料自封袋"，搜页登录掉时会被误收）
BAG_SIG = re.compile(r"自封袋|封口袋|拉链袋|骨袋")
BAG_PLASTIC = re.compile(r"塑料|PE|opp|OPP|pvc|PVC|复合")
BAG_EXCLUDE = re.compile(r"茶叶|铝箔|牛皮纸|食品|干货|花茶|狗粮|坚果|农药|化肥|宠物|中药")
# 礼盒信号仅在 SKU spec 明确出现时才排除（不用标题，自封袋标题常含"包装"误伤）
GIFT_SIG = re.compile(r"礼盒|礼品盒|开窗|烫金|巧克力|糖果|蛋糕|首饰|珠宝|伴手礼")
WHITE_SIG = re.compile(r"白边|红边|加宽边")

def parse_sku_json(body):
    rows = []
    try:
        i = body.find("skuMapOriginal")
        if i < 0:
            return rows
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
        self.events = []
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
        # CDP returnByValue 直接返回正常 unicode 字符串，勿再做 ascii_unescape
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

    def get_sku(self, session, oid, timeout=18):
        try:
            h = self.evaluate(session, "document.documentElement.outerHTML", await_promise=False) or ""
            if "skuMapOriginal" in h:
                return h
        except Exception:
            pass
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


def _str(v):
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v if isinstance(v, str) else ""


def reauth_cookies(port=9222):
    """登录态静默丢失时自动重注默认 Chrome 的 cookie（不落盘明文）。"""
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "inject_cookies.py"), str(port)],
                           timeout=90, capture_output=True, text=True)
        return r.returncode == 0 and "注入成功" in (r.stdout or "")
    except Exception:
        return False


def build_search_url(kw, pg, prov, use_mobile):
    if use_mobile:
        return ("https://m.1688.com/offer_search.html?keywords="
                + urllib.parse.quote(kw.encode("gbk")) + "&page=" + str(pg))
    base = ("https://s.1688.com/selloffer/offer_search.htm?keywords="
            + urllib.parse.quote(kw.encode("gbk")))
    if prov:
        base += "&province=" + prov
    base += "&beginPage=" + str(pg)
    return base


def search_captcha(c, ws):
    h = _str(c.evaluate(ws, "document.documentElement.outerHTML", await_promise=False))
    href = _str(c.evaluate(ws, "location.href", await_promise=False)).lower()
    return ("验证码" in h) or ("captcha" in href)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", nargs="+", required=True, help="目标尺寸 宽*高，如 14*20")
    ap.add_argument("--cat", nargs="+", default=["自封袋", "塑料自封袋", "白边自封袋"])
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--gap", type=float, default=2.5)
    ap.add_argument("--maxverify", type=int, default=220)
    ap.add_argument("--out", default=os.path.join(SKILL, "store", "bag_result.json"))
    ap.add_argument("--cdp", default="http://127.0.0.1:9222")
    ap.add_argument("--prov", default=PROV_ZHEJIANG, help="省份GBK，传 '' 关闭")
    ap.add_argument("--city", default="义乌", help="地区市/县关键词，如 义乌")
    ap.add_argument("--white", default="白边", help="白边信号词（已内置红边/加宽边）")
    ap.add_argument("--thick", type=float, default=12.0, help="厚度丝数，如 12")
    ap.add_argument("--reverify", default="", help="候选ID文件(每行一个)，跳过已验只验剩余")
    args = ap.parse_args()

    dim_targets = {d: target_perms_2d(d) for d in args.dims}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cands_path = os.path.join(os.path.dirname(args.out),
                              os.path.splitext(os.path.basename(args.out))[0] + "_candidates.txt")
    c = CDP(args.cdp)
    PROV = args.prov

    # 已验ID（reverify 跳过）
    verified_ids = set()
    if os.path.exists(args.out):
        try:
            d = json.load(open(args.out, encoding="utf-8"))
            for lst in d.get("hits", {}).values():
                for h in lst:
                    verified_ids.add(h["id"])
        except Exception:
            pass

    # ---------- 搜索阶段（或 reverify 直接读ID） ----------
    all_ids = []
    if args.reverify:
        with open(args.reverify, encoding="utf-8") as f:
            all_ids = [l.strip() for l in f if l.strip().isdigit()]
        print(f"[reverify] 读候选 {len(all_ids)} 个，已验 {len(verified_ids)} 跳过")
    else:
        wt, ws = c.new_page("https://www.1688.com/")
        time.sleep(6)
        seen = set()
        # 每个词独立记录是否需切移动端
        use_mobile = {kw: False for kw in args.cat}
        backoff = 1
        search_auth = 0
        for kw in args.cat:
            for pg in range(1, args.pages + 1):
                # 导航前先确认没掉登录（搜索页登录墙会返回0候选）
                href0 = _str(c.evaluate(ws, "location.href", await_promise=False)).lower()
                if "login.taobao" in href0 or "验证码" in _str(c.evaluate(ws, "document.documentElement.outerHTML", await_promise=False)):
                    if search_auth < 2:
                        print(f"[REAUTH] 搜页登录墙, 重注登录态 (#{search_auth+1})")
                        if reauth_cookies(int(args.cdp.split(":")[-1]) if ":" in args.cdp else 9222):
                            search_auth += 1
                            c.navigate(ws, "https://www.1688.com/"); time.sleep(5)
                waited = 0
                while search_captcha(c, ws) and waited < 600:
                    print(f"[CAPTCHA] 搜页被拦, 退避 {backoff*15}s (已等{waited}s)")
                    time.sleep(backoff * 15); waited += backoff * 15
                    backoff = min(backoff + 1, 4)
                url = build_search_url(kw, pg, PROV, use_mobile[kw])
                c.navigate(ws, url)
                time.sleep(7)
                if search_captcha(c, ws):
                    # PC 被拦 → 自动降级移动端重试该词
                    if not use_mobile[kw]:
                        print(f"[MOBILE] {kw} p{pg} PC被拦, 切 m.1688.com 重搜")
                        use_mobile[kw] = True
                        url = build_search_url(kw, pg, PROV, True)
                        c.navigate(ws, url); time.sleep(7)
                    if search_captcha(c, ws):
                        print(f"[CAPTCHA] {kw} p{pg} 仍被拦, 退避重试")
                        time.sleep(backoff * 15); backoff = min(backoff + 1, 4)
                        c.navigate(ws, url); time.sleep(7)
                        if search_captcha(c, ws):
                            print(f"[CAPTCHA] {kw} p{pg} 跳过")
                            break
                for _ in range(8):
                    c.evaluate(ws, "window.scrollTo(0, document.body.scrollHeight)", await_promise=False)
                    time.sleep(1.0)
                try:
                    ids = (json.loads(c.evaluate(ws, EXTRACT, await_promise=False) or "{}") or {}).get("ids", [])
                except Exception:
                    ids = []
                for i in ids:
                    if i not in seen:
                        seen.add(i); all_ids.append(i)
                print(f"[search] {kw} p{pg} +{len(ids)} total {len(all_ids)}")
                # 实时落盘候选，防搜页卡死丢结果
                with open(cands_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(all_ids))
        try:
            c.close_target(wt, ws)
        except Exception:
            pass
        print(f"[extract] unique candidates: {len(all_ids)} -> {cands_path}")

    # ---------- 核验阶段 ----------
    vt, vs = c.new_page("about:blank")
    hits = {d: [] for d in args.dims}
    captcha_flag = False

    def save_state():
        json.dump({
            "dims": args.dims, "cat": args.cat, "prov": args.prov or "全国",
            "city": args.city, "candidates": len(all_ids),
            "hits": hits, "captcha_flag": captcha_flag,
        }, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    login_streak = 0
    auth_tried = 0
    todo = [i for i in all_ids if i not in verified_ids]
    for idx, oid in enumerate(todo[: args.maxverify]):
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url)
            time.sleep(3)
            page0 = _str(c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False))
            if "验证码" in page0:
                print(f"[CAPTCHA] {oid} 详情页被拦, 退避")
                time.sleep(30); c.navigate(vs, url); time.sleep(4)
                page0 = _str(c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False))
                if "验证码" in page0:
                    captcha_flag = "detail_captcha"; time.sleep(args.gap); continue
            ttl = _str(c.evaluate(vs, "document.title", await_promise=False))
            href = _str(c.evaluate(vs, "location.href", await_promise=False))
            if "淘宝网" in ttl or "taobao" in href:
                login_streak += 1
                print(f"[LOGIN-WALL] {oid} 登录墙 (连续{login_streak})")
                # 自动重注（最多2次），成功则重置继续
                if login_streak >= 2 and auth_tried < 2:
                    print(f"[REAUTH] 尝试重注登录态 (#{auth_tried+1})")
                    if reauth_cookies(int(args.cdp.split(":")[-1]) if ":" in args.cdp else 9222):
                        auth_tried += 1; login_streak = 0
                        c.navigate(vs, url); time.sleep(4)
                        page0 = _str(c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False))
                        if "淘宝网" in page0 or "taobao" in href:
                            time.sleep(args.gap); continue
                    else:
                        auth_tried += 1
                if login_streak >= 8:
                    captcha_flag = "login_lost"; break
                time.sleep(args.gap); continue
            login_streak = 0

            body = c.get_sku(vs, oid, timeout=26)
            page_html = _str(c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False))
            if not body:
                print(f"[   ] {oid} 未抓到 SKU")
                time.sleep(args.gap); continue

            sku_rows = parse_sku_json(body)
            page_title = _str(c.evaluate(vs, "document.title", await_promise=False))
            specs_blob = " ".join(s for s, _, _ in sku_rows)
            title_text = page_title + " " + specs_blob + " " + page_html[:20000]
            # 品类硬卡：自封袋类 + 含塑料词 + 不含茶叶/铝箔/食品等排除词
            if not BAG_SIG.search(title_text):
                print(f"[   ] {oid} 非自封袋类目, 跳过")
                time.sleep(args.gap); continue
            if BAG_EXCLUDE.search(title_text) and not BAG_PLASTIC.search(title_text):
                print(f"[   ] {oid} 茶叶/铝箔/食品袋, 跳过")
                time.sleep(args.gap); continue
            if not BAG_PLASTIC.search(title_text):
                print(f"[   ] {oid} 非塑料自封袋, 跳过")
                time.sleep(args.gap); continue
            if any(GIFT_SIG.search(s) for s, _, _ in sku_rows):
                print(f"[   ] {oid} 礼盒类, 跳过")
                time.sleep(args.gap); continue

            loc = ""
            m = re.search(r'"location"\s*:\s*"([^"]*)"', page_html)
            if m: loc = m.group(1)
            company = ""
            mc = re.search(r'"companyName"\s*:\s*"([^"]*)"', page_html)
            if mc: company = mc.group(1)
            in_region = ("浙江省" in loc) or ("江苏省" in loc) or ("上海市" in loc)
            in_yiwu = in_region and ("金华市" in loc)

            # 尺寸匹配（2D 顺序无关）。关键：白边/丝数必须「同一条含尺寸spec」齐备，
            # 不能跨spec并集（否则 10丝白边款 + 12丝款 会被误判成「白边12丝」）。
            matched_dim = None
            for d in args.dims:
                perms = dim_targets[d]
                # 找「同时含尺寸+白边+目标丝数」的那条spec（精确目标款）
                target_spec = None
                for spec, price, stock in sku_rows:
                    if not any(p in extract_2d(spec) for p in perms):
                        continue
                    has_white = bool(WHITE_SIG.search(spec)) or (not any(WHITE_SIG.search(s) for s, _, _ in sku_rows) and WHITE_SIG.search(page_title))
                    has_thick = norm(str(args.thick)) in extract_thickness(spec)
                    if has_white and has_thick:
                        target_spec = spec
                        break
                # 仅含尺寸（不论边色/丝数）也算命中该尺寸，边色/丝数如实标记
                size_specs = [s for s, _, _ in sku_rows if any(p in extract_2d(s) for p in perms)]
                if not size_specs:
                    continue
                # 白边：任一条含尺寸spec含边色词，或标题含边色词且无spec含边色词
                matched_white = any(WHITE_SIG.search(s) for s in size_specs) or WHITE_SIG.search(page_title)
                # 12丝：任一条含尺寸spec含目标丝数
                matched_thick = any(norm(str(args.thick)) in extract_thickness(s) for s in size_specs)
                # 精确目标款（白边+丝数同条）
                exact_target = target_spec is not None

                # 地域硬卡：浙江省 + 金华市(=义乌)
                if not in_region:
                    print(f"[   ] {oid} 非浙江({loc}), 跳过")
                    matched_dim = None
                    break
                if args.city and not in_yiwu:
                    print(f"[   ] {oid} 非{args.city}({loc}), 跳过")
                    matched_dim = None
                    break

                matched_dim = d
                # 取该尺寸的精确价/库存（优先精确目标款那条）
                price = stock = None
                pick = target_spec or size_specs[0]
                for spec, p, s in sku_rows:
                    if spec == pick:
                        price, stock = p, s
                        break
                rec = {
                    "id": oid, "dim": d, "title": page_title[:60],
                    "price": ("¥" + str(price)) if price else None,
                    "stock": stock, "url": url,
                    "spec": pick,
                    "location": loc, "company": company,
                    "region_jzh": in_region, "yiwu_jh": in_yiwu,
                    "white_edge": matched_white, "thick_12si": matched_thick,
                    "exact_target": exact_target,
                }
                hits[d].append(rec)
                tag = []
                if in_yiwu: tag.append("金华(义乌)")
                if matched_white: tag.append("白边(含红边)")
                if matched_thick: tag.append(f"{args.thick}丝")
                print(f"[HIT {d}] {oid} | {rec['spec']} | {rec['price']} | 库存{stock} | {loc} | {'/'.join(tag) or '缺特征'}")
                break
            if not matched_dim:
                print(f"[   ] {oid} sku rows={len(sku_rows)} 无 {args.dims} 尺寸")
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:80]}")
        time.sleep(args.gap)
        save_state()  # 每验1个实时写盘（修复#2/#8可观测）

    c.close_target(vt, vs)
    try: c.ws.close()
    except Exception: pass
    save_state()
    print(f"[done] candidates={len(all_ids)} todo={len(todo)} "
          + " ".join(f"{d}={len(hits.get(d,[]))}" for d in args.dims)
          + f" -> {args.out}")


if __name__ == "__main__":
    main()
