"""Shared two-axis SKU verification core for 1688 detail pages.

Single source of truth for the "exact size + 江浙沪 location" check, reused by
both `cdp_client.py` (the primary driver's verify command) and
`verify_two_axis.py` (the standalone checker) so the parsing logic can never
drift between the two.

WHY THIS EXISTS (2026-08-22, user-corrected miss):
1688 carton shops encode size as TWO independent SKU axes —
  `8x8（长宽）;9cm（高）`  (长宽 base + 高 variant)
— NOT a literal triple `8*8*9`. The old verifier only matched the literal
triple and returned 0 hits across 190 real candidates. The authoritative
source is the inlined `skuMapOriginal` JSON `specAttrs` field (virtual-scroll
safe), parsed entry-by-entry for an exact L,W,H match with stock > 0.
Province is extracted from body text for 江浙沪 / province filtering.
"""
import re
import time

PROV_MAP = {
    "江浙沪": "江苏|浙江|上海",
    "江苏": "江苏", "浙江": "浙江", "上海": "上海",
    "广东": "广东", "福建": "福建", "山东": "山东",
}


def parse_dim(s):
    """'8*8*9' / '8x8x9' -> (8, 8, 9)."""
    parts = [p.strip() for p in re.split(r"[*xX×]", s) if p.strip()]
    while len(parts) < 3:
        parts.append(parts[0] if parts else "0")
    return int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))


def prov_re_for(prov):
    return re.compile(PROV_MAP.get(prov, prov))


def norm_dim(spec):
    """Parse one specAttrs string into (L, W, H) or None.

    Covers (verified against real 1688 corpus 2026-08-22):
      - two-axis:  `8x8（长宽）;9cm（高）`
      - inline triple with double-star separator: `2号500**250**30mm;五层抗压`
        -> (50, 25, 3)  [mm -> cm, single dim <=200]
      - mm triple: `80*80*90mm` / `500**250**30mm` -> (8,8,9)/(50,25,3)
      - cm triple: `8x8x9cm` / `8*8*9cm` / `8X8X9cm` / `8×8×9cm`
    Sep char class includes: * (single and DOUBLE **) x X × and the unicode ×
    The double-star `**` must be consumed greedily so it is treated as ONE separator.
    """
    # normalize separator: collapse ** / *× / etc to single '*' for uniform splitting
    s = spec.replace('**', '*')
    # two-axis base + height
    m = re.search(r'(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[（(]?\s*长宽\s*[）)]?\s*[;；]?\s*(\d+(?:\.\d+)?)\s*cm\s*[（(]?\s*高\s*[）)]?', s)
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    # mm triple (mm -> cm: divide by 10; no upper cap — cartons routinely hit 500-600mm
    # and those ARE legit cm when divided; the cm-triple branch handles "8x8x9cm" separately)
    # use findall so a leading "N号"/"半高N号" prefix can't consume the first digit
    for m in re.finditer(r'(\d+)\s*[xX*×]\s*(\d+)\s*[xX*×]\s*(\d+)\s*mm', s):
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return a / 10.0, b / 10.0, c / 10.0
    # cm triple — keep decimals EXACT (float): 8x8x9.5 must NOT collapse to 8x8x9
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*[xX*×]\s*(\d+(?:\.\d+)?)\s*[xX*×]\s*(\d+(?:\.\d+)?)\s*cm', s, re.I):
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    # labeled triple: `（竖）25长*13侧*32高` / `25长*13侧*32高` / `25长x13侧x32高`
    # paper-bag convention: 长=Length, 侧=side gusset(W), 高=Height (2026-08-23 offer 1158678687)
    m = re.search(r'(\d+(?:\.\d+)?)\s*长\s*[xX*×]\s*(\d+(?:\.\d+)?)\s*侧\s*[xX*×]\s*(\d+(?:\.\d+)?)\s*(?:高)?', s)
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    # labeled scattered dims: `宽【26cm】高【10cm】;特硬;长【46cm】` / `长46宽16高10`
    # order-free; stray digits like "高【10cm】3" are ignored because each number
    # must be preceded by an axis label. (2026-08-24 offer 752445610436 corpus)
    dims = dict(re.findall(r'([长宽高深侧])\s*[【(\[]?\s*(\d+(?:\.\d+)?)', s))
    if {"长", "宽", "高"} <= set(dims):
        return float(dims["长"]), float(dims["宽"]), float(dims["高"])
    return None


# Pull skuMapOriginal from the FULL outerHTML (reliable, what dump1688.py used).
# The structured window.context model is flaky (not always hydrated), so outerHTML is primary.
JS = r"""
(() => {
  const out = {ctx: '', locs: [], shop: '', title: document.title, structured: null};
  // --- structured model (preferred, when hydrated) ---
  try {
    const R = window.context && window.context.result;
    const d = R && R.data;
    const twp = d && d.mainPrice && d.mainPrice.fields && d.mainPrice.fields.finalPriceModel;
    const ss = d && d.shippingServices && d.shippingServices.fields;
    const fi = ss && ss.freightInfo;
    const loc = (fi && (fi.location || fi.recieveAddress)) || (ss && ss.location) || null;
    if (loc) out.locs = [loc];
    out.structured = {hasMap: !!(twp && twp.skuMapOriginal),
                      nSku: twp && twp.skuMapOriginal ? twp.skuMapOriginal.length : 0,
                      divCode: fi ? fi.locationDivisionCode : null};
  } catch(e) { out.structured = {err: String(e).slice(0,120)}; }
  // --- primary: full outerHTML scan for skuMapOriginal (no truncation) ---
  const html = document.documentElement.outerHTML;
  const i = html.indexOf('skuMapOriginal');
  if (i >= 0) {
    out.ctx = html.slice(i);  // from skuMapOriginal onward — full SKU list
  }
  // location fallback: structured location field OR freightInfo literal in HTML
  if (out.locs.length === 0) {
    const locM = html.match(/"location"\s*:\s*"(浙江|江苏|上海|[^"]{2,8}省[^"]{0,10})"/);
    if (locM) out.locs = [locM[1]];
  }
  if (out.ctx && out.locs.length === 0) {
    // last resort: body text province scan
    const body = document.body.innerText || '';
    const locRe = /(江苏|浙江|上海|广东|山东|福建|安徽|江西|河南|河北|北京|天津|湖北|湖南|四川|重庆|辽宁|吉林|黑龙江|陕西|山西|广西|云南|贵州|甘肃|海南|内蒙古|宁夏|青海|新疆|西藏)([省市]?)([一-龥]{2,10}?(市|区|县|镇|街道))?/g;
    let m; const locs = new Set();
    while ((m = locRe.exec(body)) !== null) locs.add(m[0]);
    out.locs = Array.from(locs).slice(0,30);
  }
  if (!out.shop) {
    const body = document.body.innerText || '';
    const shopM = body.match(/(义乌|金华|杭州|宁波|温州|苏州|常州|无锡|上海|南京|嘉兴|绍兴|台州|丽水等?)[^\n]{0,30}?(公司|厂|商行|包装|制品)/);
    if (shopM) out.shop = shopM[0];
  }
  return out;
})()
"""

ENTRY_RE = re.compile(r'"canBookCount":(\d+),"specAttrs":"([^"]+)","price":"([\d.]+)"')


def _wait_ready(cdp, timeout_s=10.0, poll=0.5):
    """Poll until skuMapOriginal is present in the DOM (or captcha page detected).

    Replaces the old fixed 6s sleep: pages that hydrate fast (1-2s) proceed
    immediately; slow ones still get up to timeout_s. Returns as soon as ready.
    """
    probe = "!!(document.documentElement.outerHTML.indexOf('skuMapOriginal') >= 0 || /验证码拦截/.test(document.title))"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = cdp.send("Runtime.evaluate",
                         {"expression": probe, "returnByValue": True},
                         timeout=8)
            if r.get("result", {}).get("result", {}).get("value"):
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def verify_one(cdp, oid, TL, TW, TH, prov_re, wait_timeout=10.0):
    """Open detail page, return dict with exact-size hit + 江浙沪 province + price/stock."""
    cdp.navigate("https://detail.1688.com/offer/%s.html" % oid, wait=0)
    _wait_ready(cdp, timeout_s=wait_timeout)
    res = cdp.evaluate(JS, timeout=40)
    ctx = res.get("ctx", "")
    locs = res.get("locs", [])
    prov = next((l for l in locs if prov_re.search(l)), "")
    hit_spec = hit_price = hit_stock = None
    n = 0
    specs_raw = []
    # detect captcha/intercept page — report instead of silently "no match"
    title = res.get("title", "")
    if "验证码拦截" in title or "x5secdata" in ctx or "哎哟喂" in ctx:
        return {"id": oid, "cap": True, "title": title,
                "url": "https://detail.1688.com/offer/%s.html" % oid}
    for m in ENTRY_RE.finditer(ctx):
        stock, spec, price = m.group(1), m.group(2), m.group(3)
        n += 1
        d = norm_dim(spec)
        if d:
            specs_raw.append(spec)
        if d and d[0] == TL and d[1] == TW and d[2] == TH:
            hit_spec, hit_price, hit_stock = spec, price, stock
    return {
        "specs_raw": specs_raw,
        "id": oid,
        "prov": prov,
        "jzh": bool(prov),
        "hit": hit_spec is not None,
        "spec": hit_spec,
        "price": hit_price,
        "stock": hit_stock,
        "n_specs": n,
        "shop": res.get("shop", ""),
        "title": res.get("title", ""),
        "url": "https://detail.1688.com/offer/%s.html" % oid,
    }
