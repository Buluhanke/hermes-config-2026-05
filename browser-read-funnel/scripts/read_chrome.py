#!/usr/bin/env python3
"""read_chrome.py — 一键「看到/看清/看懂」前台 Chrome：自动定位最近的 AX 树缓存并结构化解析。

工作流（零截图读懂 L1 的闭环）:
  1. 在对话里让我用 computer_use(mode='ax', app='Google Chrome') 抓一次前台 Chrome 的无障碍树
     → 落盘在 ~/.hermes/cache/computer_use/elements_*.json
  2. 本脚本自动找最新那份缓存，解析并输出结构化结果

用法:
  python3 read_chrome.py                 # 默认: 商品卡片(若在 1688/电商页) 或 全量文本 dump
  python3 read_chrome.py --products     # 商品卡片(标题/价格/销量/供应商)
  python3 read_chrome.py --sku          # SKU 尺寸矩阵
  python3 read_chrome.py --spec         # 件重尺表(长×宽×高×体积×重量)
  python3 read_chrome.py --links        # 可点击链接 + native bounds(供点击)
  python3 read_chrome.py --text         # 全量文本 dump
  python3 read_chrome.py --file <path>  # 指定某个 AX 缓存文件(不走自动定位)
  python3 read_chrome.py --watch        # 找最新文件并报告其路径/时间

注: AX 缓存由 computer_use 工具生成；本脚本只做解析层。抓取动作由对话中的
computer_use(mode='ax') 触发(后台、不抢焦点、零截图、零调试端口、零新实例)。
"""
import os, re, sys, glob, argparse, json

CACHE_DIR = os.path.expanduser("~/.hermes/cache/computer_use")
ELEM_RE = re.compile(r"elements_.*\.json$")


def latest_ax_file():
    files = glob.glob(os.path.join(CACHE_DIR, "elements_*.json"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("elements", [])


def all_labels(elems):
    return [e.get("label") or "" for e in elems]


PRICE_RE = re.compile(r"[¥￥]\s*(\d+(?:\s*\.\s*\d+)?)")
SOLD_RE = re.compile(r"(?:\d[\d万,]*(?:\+)?\s*(?:件|个)?)|(?:近?期\s*\d+\s*人\s*回?购?)|(?:\d+\s*人回?购?)")
SUP_RE = re.compile(r"([\w\u4e00-\u9fff]*?(?:有限公司|包装材料|包装|科技|实业|工贸|商贸|制品|纸箱| boxes))")


def extract_products(elems):
    prods, seen = [], set()
    labels = all_labels(elems)
    for i, e in enumerate(elems):
        lab = e.get("label") or ""
        if e.get("role") != "AXLink" or ("¥" not in lab and "￥" not in lab):
            continue
        chunk = [lab.strip()]
        j = i + 1
        while j < min(i + 10, len(elems)):
            nxt = (elems[j].get("label") or "").strip()
            if re.match(r"^[\d.]+$", nxt) or nxt in ("限时价", "红包价", "新人价", "新客价", "优惠券价"):
                chunk.append(nxt); j += 1
            else:
                break
        merged = " ".join(chunk)
        title = merged.split("¥")[0].split("￥")[0].strip()
        price = PRICE_RE.search(merged)
        price = ("¥" + price.group(1).replace(" ", "")) if price else None
        sold = SOLD_RE.search(merged)
        sold = sold.group(0).strip() if sold else None
        sup = SUP_RE.search(merged)
        sup = sup.group(1) if sup else None
        key = title[:40]
        if key in seen:
            continue
        seen.add(key)
        prods.append({"title": title[:70], "price": price, "sold": sold, "supplier": sup})
    return prods


def extract_spec(elems):
    specs, labels = [], all_labels(elems)
    for i, e in enumerate(elems):
        lab = e.get("label") or ""
        if re.search(r"\d+号\([\d.*]+CM\)", lab) and (";" in lab):
            nums = []
            j = i + 1
            while j < min(i + 12, len(labels)):
                n = labels[j].strip()
                if re.match(r"^[\d.]+$", n):
                    nums.append(n)
                elif re.search(r"\d+号\([\d.*]+CM\)", n):
                    break
                elif n and re.search(r"[\u4e00-\u9fff]", n):
                    break
                j += 1
            specs.append({"spec": lab, "nums": nums})
    return specs


def extract_sku(elems):
    skus, labels = [], all_labels(elems)
    for i, lab in enumerate(labels):
        if lab.strip() == "规格":
            for j in range(i + 1, min(i + 4, len(labels))):
                nxt = labels[j].strip()
                if nxt and "*" in nxt and "CM" in nxt.upper():
                    skus = [s.strip() for s in nxt.split(",") if s.strip()]
                    break
            break
    return skus


def extract_links(elems):
    return [{"label": (e.get("label") or "").strip()[:60], "bounds": e.get("bounds")}
            for e in elems if e.get("role") == "AXLink" and (e.get("label") or "").strip()]


def dump_text(elems):
    out, prev = [], ""
    for lab in all_labels(elems):
        t = lab.strip()
        if t and t != prev:
            out.append(t); prev = t
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", action="store_true")
    ap.add_argument("--sku", action="store_true")
    ap.add_argument("--spec", action="store_true")
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--file", help="指定 AX 缓存文件(不走自动定位)")
    ap.add_argument("--watch", action="store_true", help="只报告最新缓存文件路径")
    args = ap.parse_args()

    path = args.file or latest_ax_file()
    if not path or not os.path.exists(path):
        print("ERR: 找不到 AX 缓存。请先在对话里用 computer_use(mode='ax', app='Google Chrome') 抓一次前台 Chrome。")
        sys.exit(1)
    if args.watch:
        print(path, "(", os.path.getmtime(path), ")")
        return
    elems = load(path)
    if args.products:
        ps = extract_products(elems)
        print(f"# 商品卡片 {len(ps)} 个  (源: {os.path.basename(path)})")
        for p in ps:
            print(f"{p['price'] or '':>9} | {p['sold'] or '':<10} | {p['supplier'] or '':<18} | {p['title']}")
    elif args.sku:
        sk = extract_sku(elems)
        print(f"# SKU 尺寸 {len(sk)} 个")
        print(", ".join(sk))
    elif args.spec:
        ss = extract_spec(elems)
        print(f"# 件重尺表 {len(ss)} 行  (规格 -> [长,宽,高,体积,重量])")
        for s in ss:
            print(f"{s['spec']:<42} -> {s['nums']}")
    elif args.links:
        for l in extract_links(elems):
            print(l)
    else:
        # 默认: 若疑似电商页(有商品)则打商品，否则全量文本
        ps = extract_products(elems)
        if ps:
            print(f"# 商品卡片 {len(ps)} 个  (源: {os.path.basename(path)})")
            for p in ps:
                print(f"{p['price'] or '':>9} | {p['sold'] or '':<10} | {p['supplier'] or '':<18} | {p['title']}")
        else:
            for t in dump_text(elems):
                print(t)


if __name__ == "__main__":
    main()
