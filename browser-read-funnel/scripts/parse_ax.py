#!/usr/bin/env python3
"""parse_ax.py — 解析 computer_use 落盘的 Chrome 前台 AX 树 JSON，输出结构化表格。
这是「零截图读懂网页(L1)」的解析层：computer_use(mode='ax') 抓树 → 本脚本结构化。

用法:
  python3 parse_ax.py <ax_json>                 # 全量文本 dump（去重相邻空行）
  python3 parse_ax.py <ax_json> --products      # 提取商品卡片(标题/价格/销量/供应商)
  python3 parse_ax.py <ax_json> --spec          # 提取规格型号件重尺表(长×宽×高×体积×重量)
  python3 parse_ax.py <ax_json> --sku           # 提取 SKU 尺寸矩阵(规格字段里的 40+ 尺寸)
  python3 parse_ax.py <ax_json> --links         # 列出可点击 AXLink(带 native bounds)
坐标提示: click 用 coordinate = native bounds ÷ 1.36（Cua Driver 0.17 缩放）。
"""
import json, re, sys

PRICE_RE = re.compile(r'[¥￥]\s*(\d+(?:\s*\.\s*\d+)?)')  # 容忍 ¥ 0 .15 这种数字与小数点间有空格的碎裂形态
SOLD_RE = re.compile(r'(?:\d[\d万,]*(?:\+)?\s*(?:件|个)?)|(?:近?期\s*\d+\s*人\s*回?购?)|(?:\d+\s*人回?购?)')
SUP_RE = re.compile(r'([\w\u4e00-\u9fff]*?(?:有限公司|包装材料|包装|科技|实业|工贸|商贸|制品|纸箱| boxes))')


def load(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('elements', [])


def all_labels(elems):
    return [e.get('label') or '' for e in elems]


def dump_text(elems):
    out, prev = [], ''
    for lab in all_labels(elems):
        t = lab.strip()
        if t and t != prev:
            out.append(t); prev = t
    return out


def extract_products(elems):
    """商品卡片 = 含价格的 AXLink。
    1688 把价格拆成多个独立 StaticText 节点(¥ / 0 / .15 / 限时价 各自分开)，
    所以不能用单一 link.label——要合并该 link 之后的相邻数字/价格节点。
    策略: 找含 '¥' 的节点(价格符号节点)，向后合并直到非价格/非数字节点，再正则抽完整价格。"""
    prods, seen = [], set()
    labels = all_labels(elems)
    for i, e in enumerate(elems):
        lab = e.get('label') or ''
        if e.get('role') != 'AXLink' or ('¥' not in lab and '￥' not in lab):
            continue
        # 合并从该 ¥ 节点起、后续相邻的 价格/数字/价格词 节点，拼成一段文本
        chunk = [lab.strip()]
        j = i + 1
        while j < min(i + 10, len(elems)):
            nxt = (elems[j].get('label') or '').strip()
            if re.match(r'^[\d.]+$', nxt) or nxt in ('限时价', '红包价', '新人价', '新客价', '优惠券价'):
                chunk.append(nxt); j += 1
            else:
                break
        merged = ' '.join(chunk)
        title = merged.split('¥')[0].split('￥')[0].strip()
        price = PRICE_RE.search(merged)
        price = price.group(1).replace(' ', '') if price else None
        price = ('¥' + price) if price else None
        sold = SOLD_RE.search(merged)
        sold = sold.group(0).strip() if sold else None
        sup = SUP_RE.search(merged)
        sup = sup.group(1) if sup else None
        key = title[:40]
        if key in seen:
            continue
        seen.add(key)
        prods.append({'title': title[:70], 'price': price, 'sold': sold, 'supplier': sup})
    return prods


def extract_spec(elems):
    """规格型号件重尺表: 形如 '13号(13*8*4.5CM);三层低档' 后跟 长/宽/高/体积/重量 数字列。
    1688 把每个数字拆成独立 StaticText 节点，需跨多个节点收集直到遇到下一个规格行或非数字块。"""
    specs, labels = [], all_labels(elems)
    for i, e in enumerate(elems):
        lab = e.get('label') or ''
        if re.search(r'\d+号\([\d.*]+CM\)', lab) and (';' in lab):
            nums = []
            j = i + 1
            # 收集紧随其后的纯数字节点，直到遇到下一个规格行/含中文的行
            while j < min(i + 12, len(labels)):
                n = labels[j].strip()
                if re.match(r'^[\d.]+$', n):
                    nums.append(n)
                elif re.search(r'\d+号\([\d.*]+CM\)', n):
                    break  # 下一个规格行，停止
                elif n and re.search(r'[\u4e00-\u9fff]', n):
                    break  # 含中文(字段名等)，停止
                j += 1
            specs.append({'spec': lab, 'nums': nums})
    return specs


def extract_sku(elems):
    """SKU 尺寸矩阵: '规格' 字段后的一长串 '50*40*30CM,60*40*40CM,...'。"""
    skus, labels = [], all_labels(elems)
    for i, lab in enumerate(labels):
        if lab.strip() == '规格':
            # 下一个非空 label 即尺寸串
            for j in range(i + 1, min(i + 4, len(labels))):
                nxt = labels[j].strip()
                if nxt and '*' in nxt and 'CM' in nxt.upper():
                    skus = [s.strip() for s in nxt.split(',') if s.strip()]
                    break
            break
    return skus


def extract_links(elems):
    return [{'label': (e.get('label') or '').strip()[:60], 'bounds': e.get('bounds')}
            for e in elems if e.get('role') == 'AXLink' and (e.get('label') or '').strip()]


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    path, mode = sys.argv[1], 'dump'
    for a in sys.argv[2:]:
        if a.startswith('--'):
            mode = a[2:]
    elems = load(path)
    if mode == 'products':
        ps = extract_products(elems)
        print(f"# 商品卡片 {len(ps)} 个")
        for p in ps:
            print(f"{p['price'] or '':>9} | {p['sold'] or '':<10} | {p['supplier'] or '':<18} | {p['title']}")
    elif mode == 'spec':
        ss = extract_spec(elems)
        print(f"# 件重尺表 {len(ss)} 行  (规格 -> [长,宽,高,体积,重量])")
        for s in ss:
            print(f"{s['spec']:<42} -> {s['nums']}")
    elif mode == 'sku':
        sk = extract_sku(elems)
        print(f"# SKU 尺寸 {len(sk)} 个")
        print(', '.join(sk))
    elif mode == 'links':
        for l in extract_links(elems):
            print(l)
    else:
        for t in dump_text(elems):
            print(t)


if __name__ == '__main__':
    main()
