#!/usr/bin/env python3
"""
解析 computer_use(mode='ax') 落盘的 AX 树 JSON，抽取「字段→值」相邻结构。

用法:
  python3 parse_ax_tree.py <elements_json> [--keys k1,k2,...] [--context 6] [--max 80]

  <elements_json>   computer_use 返回的 elements_file 路径
  --keys            命中的关键词（逗号分隔）；命中即抓该节点及之后 --context 个非空 label
  --context         每个命中向后收集的 label 数（默认 6）
  --max             最多输出多少条（默认 80，0=不限）
  --role            只保留某 role（如 AXLink / AXStaticText），可选

输出去重后的「字段→值」片段，便于从 SKU 矩阵 / 件重尺 / 规格表里挖值。
"""
import json
import argparse


def load_elements(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "elements" in data:
        return data["elements"]
    raise SystemExit(f"无法识别的 AX JSON 结构: {type(data)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--keys", default="规格,材质,厚度,尺寸,外部尺寸,内部尺寸,颜色,硬度,起订,起批,价格,报价,库存,发货,长(cm),宽(cm),高(cm),体积,重量")
    ap.add_argument("--context", type=int, default=6)
    ap.add_argument("--max", type=int, default=80)
    ap.add_argument("--role", default=None)
    args = ap.parse_args  # placeholder, replaced below
    args = ap.parse_args()

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    elems = load_elements(args.json)
    labels = [(e.get("role", ""), e.get("label") or "") for e in elems]

    out = []
    seen = set()
    for i, (role, lab) in enumerate(labels):
        if args.role and role != args.role:
            continue
        if not any(k in lab for k in keys):
            continue
        chunk = []
        for j in range(i, min(i + 1 + args.context, len(labels))):
            t = labels[j][1].strip()
            if t and t not in chunk:
                chunk.append(t)
        sig = " | ".join(chunk)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(f"[{i}] {lab!r} -> {chunk}")

    if args.max:
        out = out[: args.max]

    print(f"total elements={len(elems)}  matched={len(out)}")
    for line in out:
        print(line)


if __name__ == "__main__":
    main()
