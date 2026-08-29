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
import sys, os, json, time, argparse, urllib.parse, re, base64, threading, subprocess
import random
import websocket


def human_gap(base_gap):
    """高斯随机延迟替代固定 sleep：均值=base_gap，σ=base_gap*0.35，下限 1.5s。
    模拟真人浏览节奏的不规则间隔，降低被风控模式识别的概率。"""
    g = random.gauss(base_gap, max(base_gap * 0.35, 0.8))
    return max(g, 1.5)

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
  // 排除「趋势商机/跟风热卖」推荐挂件(opportunity.CardItem / pages-fast.1688.com)
  const RECS=[/opportunity\.CardItem/, /pages-fast\.1688\.com/];
  const ids2=new Set();
  for(const id of ids){
    // 在原始HTML中定位该id，附近含推荐标记则丢弃
    const idx=h.indexOf(id);
    const s=Math.max(0,idx-400), e=Math.min(h.length, idx+400);
    if(!RECS.some(r=>r.test(h.slice(s,e)))) ids2.add(id);
  }
  return JSON.stringify({ids:[...ids2].filter(id=>id.length>=9&&id.length<=14)});
})();
"""

# 滑块定位 JS：返回滑块按钮中心坐标 + 轨道可拖距离
JS_FIND_SLIDER = r"""
(()=>{
  // 阿里系滑块常见选择器（nc-1 无痕验证 / punish 页）
  const btnSels = ['#nc_1_n1z','#nc_1__scale_text .nc-lang-cnt','.nc_iconfont.btn_slide',
                   '.btn_slide','[data-role="slider"]','.slidetounlock',
                   '.J_MIDDLEWARE_FRAME_WIDGET [class*="btn"]'];
  let btn=null;
  for(const s of btnSels){const e=document.querySelector(s); if(e){btn=e;break;}}
  if(!btn){
    // 兜底：找文本含"拖动/滑动"的可点小元素
    for(const e of document.querySelectorAll('span,div,i')){
      const t=(e.textContent||'').trim();
      if((t.includes('拖动')||t.includes('滑动')) && e.offsetWidth>20 && e.offsetWidth<80
         && e.offsetHeight>15 && e.offsetHeight<60){btn=e;break;}
    }
  }
  if(!btn) return JSON.stringify({ok:false});
  const b=btn.getBoundingClientRect();
  // 轨道：父容器宽度 - 按钮宽度 = 可拖距离
  let track=btn.parentElement;
  let dist=Math.max((track?track.getBoundingClientRect().width:300)-b.width,100);
  return JSON.stringify({ok:true,x:Math.round(b.x+b.width/2),y:Math.round(b.y+b.height/2),
                         dist:Math.round(dist)});
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


# 跨段组合串兜底：整段/整页扫描轴名尺寸（如 "宽【26cm】高【10cm】;特硬;长【46cm】"
# 被 ; 切碎后逐段调用 extract_sizes_from_spec 凑不齐三轴 → 在此整页一次性拼出三轴）。
# 只三轴（长/宽/高）齐了才返回 {长*宽*高} 归一化集合，缺轴则空（避免误匹配）。
def parse_dims_cross_segment(text):
    axis_val = {}
    # 全角括号：宽【26cm】
    for m in re.finditer(r"([长宽高侧厚竖横深])\s*【\s*([0-9][0-9.]*)\s*(?:cm|CM)?\s*】", text):
        axis_val[m.group(1)] = norm(m.group(2))
    # 轴名连写/半角（含 compatibility）：宽26cm / 长46（后面紧跟非数字）
    for m in re.finditer(r"([长宽高侧厚竖横深])\s*[:：]?\s*([0-9][0-9.]*)\s*(?:cm|CM)?(?![0-9])", text):
        if m.group(1) not in axis_val:
            axis_val[m.group(1)] = norm(m.group(2))
    if "长" in axis_val and "宽" in axis_val and "高" in axis_val:
        return {norm(axis_val["长"] + "*" + axis_val["宽"] + "*" + axis_val["高"])}
    return set()

# 品类硬卡：锁定纸包装/手提袋类目，避免"电器+牛皮纸包装描述"误中（2026-08-27 实战：搜出电器）
# 扩展词集（2026-08-28 固化）：补白卡纸盒/卡纸盒/彩盒/纸盒/天地盖/翻盖盒，覆盖白卡纸盒类目
CARTON_DEFAULT = "纸箱|瓦楞|快递箱|邮政箱|飞机盒|牛皮纸盒|牛皮纸袋|牛皮纸手提袋|搬家箱|收纳箱|手提袋|纸袋|购物袋|包装袋|牛皮纸袋手提|白卡纸盒|卡纸盒|纸盒|彩盒|天地盖|翻盖盒"
CARTON_SIG = re.compile(CARTON_DEFAULT)
# 反向排除：详情页若主打这些品类，即便含纸包装描述也跳过（电器/数码/五金等借"牛皮纸包装"蹭词）
EXCLUDE_SIG = re.compile(r"电器|数码|数据线|充电器|适配器|电源|插座|灯具|LED|五金|工具|机械|电机|水泵|开关|插头|电池|耳机|音箱|手机|平板|电脑|键盘|鼠标|服装|鞋|袜|玩具|文具|家具|表板蜡|清洁上光|还原剂|仪表盘|内饰护理|车用|汽车用品|皮革护理|上光剂")
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

    # ---------- 滑块验证码：CDP Input.dispatchMouseEvent 拟人拖动 ----------
    def mouse(self, session, etype, x, y, buttons="", click_count=0):
        p = {"type": etype, "x": x, "y": y, "button": "left",
             "buttons": buttons, "clickCount": click_count}
        return self.cmd("Input.dispatchMouseEvent", p, session)

    def human_slide(self, session, max_tries=2):
        """检测滑块并拟人拖动。变速缓动 + 随机抖动 + 终点回弹。
        返回 True=通过（页面不再含验证码），False=尝试失败（含异常）。"""
        for attempt in range(1, max_tries + 1):
            try:
                h = self.evaluate(session, "document.documentElement.outerHTML", await_promise=False) or ""
                if "验证码" not in h and "captcha" not in (self.evaluate(
                        session, "location.href", await_promise=False) or "").lower():
                    return True  # 已通过/无滑块
                geo = self.evaluate(session, JS_FIND_SLIDER, await_promise=True) or {}
                if isinstance(geo, str):
                    try:
                        geo = json.loads(geo)
                    except Exception:
                        geo = {}
                if not isinstance(geo, dict) or not geo.get("ok"):
                    print(f"[SLIDE] 未定位到滑块元素 (attempt {attempt})")
                    time.sleep(8); continue
                sx, sy, dist = geo["x"], geo["y"], geo["dist"]
                print(f"[SLIDE] attempt {attempt}: start=({sx},{sy}) dist={dist}px")
                # 按下
                self.mouse(session, "mousePressed", sx, sy, buttons="1", click_count=1)
                time.sleep(random.uniform(0.08, 0.18))
                # 变速轨迹：快-慢-回弹，模拟真人手部加速/犹豫
                moved = 0.0
                steps = random.randint(28, 42)
                for i in range(steps):
                    t = (i + 1) / steps
                    base = dist * (1 - (1 - t) ** 2.2)
                    jitter = random.uniform(-1.5, 1.5) if t < 0.85 else random.uniform(-0.4, 0.4)
                    nx = sx + base + jitter - moved
                    ny = sy + random.uniform(-2.0, 2.0)
                    self.mouse(session, "mouseMoved", nx, ny, buttons="1")
                    moved = sx + base + jitter
                    time.sleep(random.uniform(0.008, 0.03) if random.random() > 0.15
                               else random.uniform(0.06, 0.16))
                self.mouse(session, "mouseMoved", sx + dist + random.uniform(3, 7),
                           sy + random.uniform(-1, 1), buttons="1")
                time.sleep(random.uniform(0.12, 0.25))
                self.mouse(session, "mouseMoved", sx + dist, sy, buttons="1")
                time.sleep(random.uniform(0.1, 0.2))
                self.mouse(session, "mouseReleased", sx + dist, sy, buttons="")
                time.sleep(3.5)
                h = self.evaluate(session, "document.documentElement.outerHTML", await_promise=False) or ""
                if "验证码" not in h:
                    print(f"[SLIDE] 通过 ✓")
                    return True
                print(f"[SLIDE] attempt {attempt} 失败, 等 10s 再试" if attempt < max_tries
                      else f"[SLIDE] {max_tries} 次均失败, 放弃(转退避)")
                time.sleep(10)
            except Exception as e:
                print(f"[SLIDE] 异常 {repr(e)[:60]}, attempt {attempt} 跳过")
                time.sleep(5)
        return False


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


def reauth_cookies(port=9222):
    """登录态静默丢失时自动重注默认 Chrome 的 cookie（不落盘明文）。
    复用 inject_cookies.py：读默认 Chrome 的 1688/taobao cookie 注入后台 CDP 实例。"""
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "inject_cookies.py"), str(port)],
                           timeout=90, capture_output=True, text=True)
        return r.returncode == 0 and "注入成功" in (r.stdout or "")
    except Exception:
        return False


def clean_title(s):
    """CDP 通道返回的是真实 UTF-8 文本，切勿再走 ascii_unescape（会把正常中文变 mojibake）。
    仅做 latin-1 误读还原兜底（极少数 CDP 桥回传被标错编码的情况）。"""
    if not isinstance(s, str):
        return s
    try:
        s.encode("latin-1").decode("utf-8")
        return s.encode("latin-1").decode("utf-8")
    except Exception:
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", nargs="+", required=True)
    ap.add_argument("--cat", nargs="+", required=True)
    ap.add_argument("--cat-sign", default="", help="品类硬卡信号词(逗号分隔)，空则用默认纸包装词集(纸箱/白卡纸盒/彩盒/纸盒等)")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--gap", type=float, default=3.0)
    ap.add_argument("--maxverify", type=int, default=120)
    ap.add_argument("--out", default=os.path.join(SKILL, "store", "result_v2.json"))
    ap.add_argument("--cdp", default="http://127.0.0.1:9222")
    ap.add_argument("--prov", default=PROV_DEFAULT, help="省份筛选GBK编码，传空串 '' 关闭地域限制")
    ap.add_argument("--mobile", action="store_true", help="用 m.1688.com 移动端搜页（PC搜页被风控时绕行）")
    ap.add_argument("--tol", type=float, default=0.0, help="容差cm：每维允许+0~tol（如5=每个尺寸网上加5cm内都算命中）")
    ap.add_argument("--resume", default="", help="从已保存的 .ids.json 加载候选ID，跳过搜索阶段（被中断后续跑）")
    ap.add_argument("--start", type=int, default=0, help="核验起点索引（跳过前N个已验候选，分片续跑）")
    args = ap.parse_args()

    # 品类硬卡信号词参数化（坑4固化）：--cat-sign 覆盖默认纸包装词集，避免每换类目改源码
    if args.cat_sign:
        global CARTON_SIG
        CARTON_SIG = re.compile(args.cat_sign)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    c = CDP(args.cdp)
    PROV = args.prov  # 覆盖模块级 PROV，供 build_search_url 用

    def build_search_url(kw, begin_page, prov=PROV):
        if args.mobile:
            base = ("https://m.1688.com/offer_search.html?keywords="
                    + urllib.parse.quote(kw.encode("gbk")) + "&page=" + str(begin_page))
            if prov:
                base += "&province=" + prov
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
    # 1) 搜索 + 提取（或 --resume 复用已抓ID）
    seen = set(); all_ids = []
    if args.resume and os.path.exists(args.resume):
        try:
            all_ids = json.load(open(args.resume, encoding="utf-8"))
            seen = set(all_ids)
            print(f"[resume] 从 {args.resume} 载入 {len(all_ids)} 个候选ID，跳过搜索")
        except Exception as e:
            print(f"[resume] 载入失败 {e}，重新搜索")
            args.resume = ""
    for kw in (args.cat if not args.resume else []):
        for pg in range(1, args.pages + 1):
            # 退避期检测：若当前就是验证码页，先等恢复
            waited = 0
            while search_page_captcha() and waited < 600:
                print(f"[CAPTCHA] 搜页被拦, 尝试拟人滑块解锁")
                if c.human_slide(ws):
                    break
                print(f"[CAPTCHA] 滑块未通过, 退避 {backoff*15}s (已等{waited}s)")
                time.sleep(backoff * 15); waited += backoff * 15
                backoff = min(backoff + 1, 4)
                c.navigate(ws, build_search_url(args.cat[0], 1)); time.sleep(7)
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
    try:
        json.dump(all_ids, open(args.out + ".ids.json", "w", encoding="utf-8"))
        print(f"[extract] 已保存候选ID -> {args.out}.ids.json")
    except Exception:
        pass

    # 2) 详情页核验（v2：监听 SKU JSON）
    vt, vs = c.new_page("about:blank")
    # 续跑：载入已有 hits 累加（不重复）
    hits = {dim: [] for dim in args.dims}
    if os.path.exists(args.out):
        try:
            _prev = json.load(open(args.out, encoding="utf-8")).get("hits", {})
            for d, lst in _prev.items():
                if d in hits:
                    hits[d].extend(lst)
            print(f"[resume-hits] 载入已有命中: " + ", ".join(f"{d}={len(hits[d])}" for d in args.dims))
        except Exception:
            pass
    captcha_flag = False
    save_state = lambda: json.dump(
        {"dims": args.dims, "cat": args.cat, "prov": args.prov or "全国",
         "candidates": len(all_ids), "hits": hits, "captcha_flag": captcha_flag},
        open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    login_lost_streak = 0
    for idx, oid in enumerate(all_ids[: args.maxverify]):
        if idx < args.start:   # 分片续跑：跳过已验
            time.sleep(0.01); continue
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url)
            time.sleep(3)
            # 详情页验证码/登录态检测
            page_html0 = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
            if "验证码" in page_html0:
                print(f"[CAPTCHA] {oid} 详情页被拦, 尝试拟人滑块解锁")
                if not c.human_slide(vs):
                    time.sleep(30); c.navigate(vs, url); time.sleep(4)
                    page_html0 = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
                    if "验证码" in page_html0:
                        print(f"[CAPTCHA] {oid} 仍被拦, 跳过")
                        captcha_flag = "detail_captcha"; time.sleep(human_gap(args.gap)); continue
            # 登录态丢失检测（单个登录墙商品不应终止整个核验）
            ttl = clean_title(c.evaluate(vs, "document.title", await_promise=False) or "")
            href = c.evaluate(vs, "location.href", await_promise=False) or ""
            if "淘宝网" in ttl or "taobao" in href:
                login_lost_streak += 1
                print(f"[LOGIN-WALL] {oid} 登录墙商品 (连续{login_lost_streak})")
                # 连续 2 个登录墙即尝试自动重注默认 Chrome cookie（坑2：避免尾部候选被整段跳过）
                if login_lost_streak == 2:
                    cport = int(args.cdp.split(":")[-1]) if ":" in args.cdp else 9222
                    print(f"[REAUTH] 连续2个登录墙, 自动重注 cookie (port={cport})")
                    if reauth_cookies(cport):
                        login_lost_streak = 0
                        print(f"[REAUTH] 重注成功, 继续核验")
                        time.sleep(human_gap(args.gap)); continue
                    else:
                        print(f"[REAUTH] 重注失败, 继续计数")
                if login_lost_streak >= 5:
                    print(f"[LOGIN-LOST] 连续5个登录墙(重注无效), 判定会话失效停止")
                    captcha_flag = "login_lost"; break
                time.sleep(human_gap(args.gap)); continue
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
                                # 整页兜底命中也尝试抠价（坑3：否则 price/stock 恒 None）
                                praw = c.evaluate(vs, PRICE_JS, await_promise=False)
                                p = json.loads(ascii_unescape(praw)) if praw else {}
                                rec = {"id": oid, "dim": dim, "title": "",
                                       "price": p.get("targetPrice"),
                                       "stock": p.get("targetStock"),
                                       "moq": p.get("moq"), "url": url, "spec": seg[:40], "source": "page"}
                                hits[dim].append(rec)
                                print(f"[HIT(page) {dim}] {oid} | {seg[:40]} | {rec['price']}")
                                full_hit = True; break
                    # 跨段组合串兜底：整页一次性拼三轴（覆盖被 ; 切碎的轴名串）
                    if not full_hit:
                        cross = parse_dims_cross_segment(page_html)
                        if any(p in cross for p in perms):
                            praw = c.evaluate(vs, PRICE_JS, await_promise=False)
                            p = json.loads(ascii_unescape(praw)) if praw else {}
                            rec = {"id": oid, "dim": dim, "title": "",
                                   "price": p.get("targetPrice"),
                                   "stock": p.get("targetStock"),
                                   "moq": p.get("moq"), "url": url, "spec": "cross-segment", "source": "page-cross"}
                            hits[dim].append(rec)
                            print(f"[HIT(page-cross) {dim}] {oid} | {rec['price']}")
                            full_hit = True
                if full_hit:
                    time.sleep(human_gap(args.gap)); continue
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
                time.sleep(human_gap(args.gap)); continue

            sku_rows = parse_sku_json(body)
            # 品类词：只用 页面title + 真实SKU specAttrs（不含整页sidebar，避免相关推荐蹭词误中）
            page_title = clean_title(c.evaluate(vs, "document.title", await_promise=False) or "")
            specs_blob = " ".join(s for s, _, _ in sku_rows)
            title_text = str(page_title) + " " + str(specs_blob)
            carton = bool(CARTON_SIG.search(title_text))
            exclude = bool(EXCLUDE_SIG.search(title_text))
            if exclude:
                print(f"[   ] {oid} exclude=非纸盒类目, 跳过")
                time.sleep(human_gap(args.gap)); continue
            if not carton:
                print(f"[   ] {oid} carton=False(非纸包装类目), 跳过")
                time.sleep(human_gap(args.gap)); continue

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
                # 跨段组合串兜底：整页一次性拼三轴
                cross = parse_dims_cross_segment(page_html)
                if tol_hit(cross):
                    rec = {"id": oid, "dim": dim, "title": page_title[:36],
                           "price": None, "stock": None, "moq": None, "url": url,
                           "spec": "cross-segment", "source": "page-cross",
                           "exact": any(p in cross for p in perms)}
                    hits[dim].append(rec)
                    print(f"[HIT(page-cross) {dim}{'(近似)' if not rec['exact'] else ''}] {oid}")
                    matched = True
                    break
            if not matched:
                print(f"[   ] {oid} sku rows={len(sku_rows)} 未匹配目标尺寸")
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:80]}")
        time.sleep(human_gap(args.gap))
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
