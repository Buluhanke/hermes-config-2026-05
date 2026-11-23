#!/usr/bin/env python3
"""12123 学法减分快速答题助手 - 用 uiautomator2 常驻连接提速

## 为什么快
裸 `adb shell uiautomator dump` 每次冷启动 JVM + 等 1 秒 idle = 2.8 秒/次。
uiautomator2 常驻设备端服务，dump 只要 0.2 秒（实测 13x），click 0.23 秒。
加上去掉多余的 sleep，单题从 ~5s 压到 ~1s。

## 环境
python3 -m venv ~/.hermes/venvs/u2
~/.hermes/venvs/u2/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uiautomator2
首次 connect 会自动 push u2.jar 到设备并拉起服务（需 USB 调试已授权）。

## 用法
# 读当前题（题干+题型+选项+坐标），一行 JSON 输出，模型据此判断答案
./xfjf_fast.py read

# 答一题：点选答案字母 + 下一题 + 返回下一题题干
./xfjf_fast.py ans A          # 单选/判断(Y=正确 N=错误)；多选传多字母 ./xfjf_fast.py ans ACD
./xfjf_fast.py ans Y
./xfjf_fast.py submit ACD     # 最后一题：选完直接交卷

# 批量模式（答案由外部传入，如题库API匹配结果），一次跑完不等模型
./xfjf_fast.py batch 'A,N,Y,ABC,D,...'   # 逗号分隔，每题一个答案串

# 状态（是否抓拍/结果页）
./xfjf_fast.py status
"""
import sys, json, re, time
import uiautomator2 as u2

d = None  # 主入口里按 --dev 连接

def tap_text(label):
    """按文字找按钮取 bounds 中心点击——坐标随横竖屏翻转，绝不写死。"""
    xml = d.dump_hierarchy()
    for t, b in re.findall(r'text="([^"]*' + re.escape(label) + r'[^"]*)"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"', xml):
        n = [int(x) for x in re.findall(r'\d+', b)]
        d.click((n[0]+n[2])//2, (n[1]+n[3])//2)
        return True
    return False

def parse(xml):
    q = re.search(r'text="(\d+、[^"]+)"', xml)
    typ = re.findall(r'text="\(([^)]+)\)"', xml)
    opts = []
    for t, b in re.findall(r'text="([ABCDYN][：:][^"]+)"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"', xml):
        n = [int(x) for x in re.findall(r'\d+', b)]
        opts.append({'label': t.split('：')[0].split(':')[0], 'text': t,
                     'xy': [(n[0]+n[2])//2, (n[1]+n[3])//2]})
    has_img = 'ImageView' in xml or 'image' in xml.lower()
    face = '人脸' in xml or '置于屏幕中央' in xml or '识别' in xml
    result = '考试通过' in xml or '考试不通过' in xml or '合格' in xml
    submit = 'text="交卷"' in xml
    return {'q': q.group(1) if q else '', 'type': typ[0] if typ else '',
            'options': opts, 'has_image': has_img, 'face': face,
            'result': result, 'submit': submit,
            'texts': re.findall(r'text="([^"]{4,})"', xml)[:3]}

def dump():
    return parse(d.dump_hierarchy())

def click_opts(letters, info):
    m = {o['label']: o['xy'] for o in info['options']}
    for L in letters:
        if L in m:
            d.click(*m[L]); time.sleep(0.12)

def next_q(submit=False):
    # 按钮文字「下一题」/「交卷」，按文字取 bounds——横竖屏坐标不同，绝不用固定点
    if not tap_text('交卷') and not tap_text('下一题'):
        raise RuntimeError('找不到下一题/交卷按钮')
    time.sleep(0.45)

def cmd_read():
    print(json.dumps(dump(), ensure_ascii=False))

def cmd_ans(letters, submit=False):
    info = dump()
    if info['face']:
        print(json.dumps({'error': '人脸抓拍中，需本人刷脸', 'info': info}, ensure_ascii=False)); return
    click_opts(letters, info)
    next_q(submit)
    print(json.dumps(dump(), ensure_ascii=False))

def cmd_batch(answers):
    for i, a in enumerate(answers.split(',')):
        info = dump()
        if info['face'] or info['result']:
            print(json.dumps({'stop': i, 'reason': 'face' if info['face'] else 'result', 'info': info}, ensure_ascii=False)); return
        if not info['q']:
            print(json.dumps({'stop': i, 'reason': 'no_question', 'info': info}, ensure_ascii=False)); return
        letters = [c for c in a.strip().upper() if c in 'ABCDYN']
        click_opts(letters, info)
        last = (i == len(answers.split(',')) - 1) or info['submit']
        next_q(last)
        print(f'[{i+1}] {info["q"][:30]} -> {a}', flush=True)
    print(json.dumps(dump(), ensure_ascii=False))

def cmd_status():
    info = dump()
    print(json.dumps({'q': info['q'], 'face': info['face'], 'result': info['result'],
                      'texts': info['texts']}, ensure_ascii=False))

if __name__ == '__main__':
    argv = sys.argv[1:]
    DEV = argv[argv.index('--dev')+1] if '--dev' in argv else None
    if '--dev' in argv:
        i = argv.index('--dev'); argv = argv[:i] + argv[i+2:]
    global_d = u2.connect(DEV) if DEV else u2.connect()
    d = global_d
    c = argv[0] if argv else 'read'
    a1 = argv[1] if len(argv) > 1 else ''
    if c == 'read': cmd_read()
    elif c == 'ans': cmd_ans(a1)
    elif c == 'submit': cmd_ans(a1, True)
    elif c == 'batch': cmd_batch(a1)
    elif c == 'status': cmd_status()
    else: print('未知命令', c)
