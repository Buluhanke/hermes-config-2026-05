#!/usr/bin/env python3
"""OCR 交叉核对：macOS Vision + 百度 OCR 并行；有原生 VLM 转录时以其为准挑更准者。

用法:
  python3 ocr_crosscheck.py <图片路径> [--reference 参考文本文件或直接文本]
无 --reference 时退回启发式（中文占比、符号保真、长度一致性）。
纯 stdlib + 本机已有脚本，无 LLM 依赖。
"""
import argparse
import difflib
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

HOME = os.path.expanduser('~')
BAIDU = HOME + '/.hermes/scripts/baidu_ocr.py'
VISION = HOME + '/.hermes/scripts/macos_vision_ocr.swift'
SYMBOL_FIXES = [('￥', '¥'), ('✕', '×'), ('X', '×'), ('x', '×'), ('土', '±'), ('（', '('), ('）', ')')]


def norm(s):
    s = re.sub(r'\s+', '', s or '')
    for a, b in SYMBOL_FIXES:
        s = s.replace(a, b)
    return s


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (r.stdout or '').strip()
        return out if out and not out.startswith('ERROR') else ''
    except Exception:
        return ''


def heuristic(text):
    if not text:
        return -1e9
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    digits = len(re.findall(r'\d', text))
    bad = sum(text.count(a) for a, _ in SYMBOL_FIXES)
    return cn * 2 + digits + len(text.strip()) * 0.3 - bad * 8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--reference', default='', help='原生 VLM 转录文本，或包含该文本的文件路径')
    args = ap.parse_args()
    if not os.path.exists(args.image):
        raise SystemExit('image not found: ' + args.image)
    ref = args.reference
    if os.path.exists(ref):
        ref = open(ref, encoding='utf-8').read()
    with ThreadPoolExecutor(max_workers=2) as ex:
        baidu = ex.submit(run, ['python3', BAIDU, args.image])
        vision = ex.submit(run, ['swift', VISION, args.image])
        baidu, vision = baidu.result(), vision.result()
    print('=== macOS Vision ===')
    print(vision or '(unavailable)')
    print('\n=== 百度 OCR ===')
    print(baidu or '(unavailable)')
    if ref:
        nref = norm(ref)
        def sim(t):
            return difflib.SequenceMatcher(None, nref, norm(t)).ratio() if t else 0
        sb, sv = sim(baidu), sim(vision)
        mode = '原生VLM转录为参照'
    else:
        sb, sv = heuristic(baidu), heuristic(vision) + 10  # 实测 Vision 中文误识率更低，沿用原并行脚本的 +10 优势分
        mode = '启发式评分（无参照，Vision +10）'
    print(f'\n评分({mode}): Vision={sv:.4f}  Baidu={sb:.4f}')
    if sv >= sb and vision:
        print('\n✅ 采用 macOS Vision')
        print(vision)
    elif baidu:
        print('\n✅ 采用百度 OCR')
        print(baidu)
    else:
        print('\n⚠ 两个引擎都不可用')


if __name__ == '__main__':
    main()
