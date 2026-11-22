#!/usr/bin/env python3
"""step_verifier v2 端到端模拟：4 场景，纯本地 mock，不依赖屏幕/OCR/LLM。

运行：python3 <本文件>
通过标准：输出 4/4 passed，退出码 0。
场景：正常成功 / 陈旧目标零执行 / 异常转移上报 / web 证据否决。
"""
import sys
import os
import tempfile
import json
from pathlib import Path

MAIN_SCRIPTS = os.path.expanduser('~/.hermes/scripts')
if MAIN_SCRIPTS not in sys.path:
    sys.path.insert(0, MAIN_SCRIPTS)

from PIL import Image
import step_verifier as sv
import visual_verifier
import decision_engine as de

tmp = Path(tempfile.mkdtemp(prefix='v2sim_'))
a, b = tmp / 'a.png', tmp / 'b.png'
Image.new('RGB', (300, 200), 'white').save(a)
Image.new('RGB', (300, 200), 'black').save(b)
v = sv.StepVerifier(trace_path=str(tmp / 'trace.jsonl'))
orig_find, orig_ocr = de.find_element, visual_verifier._ocr
results = []


def fake_found(**kw):
    return {'found': True, 'path': 'l0',
            'element': {'title': 'Submit', 'role': 'button',
                        'x': 10, 'y': 20, 'w': 100, 'h': 40}}


# 1) 正常成功：guard 通过 + OCR 正向确认 + 无禁止信号
de.find_element = fake_found
visual_verifier._ocr = lambda p: [{'text': 'Success! Order placed'}]
calls = {'n': 0}


def act():
    calls['n'] += 1


r1 = v.run_step('sim1', '正常提交', {'title': 'Submit'},
                {'text_appears': ['Success'],
                 'unexpected_appears': ['captcha', 'login']},
                act, str(a), lambda: str(b),
                guard_spec={'title': 'Submit', 'box': [10, 20, 100, 40]},
                skip_precheck=False)
results.append(('正常成功', r1['ok'] is True and calls['n'] == 1, r1['path']))

# 2) 陈旧目标：guard 拒绝，危险动作零执行
de.find_element = lambda **kw: {
    'found': True, 'path': 'l0',
    'element': {'title': 'Delete Account', 'role': 'button',
                'x': 10, 'y': 20, 'w': 100, 'h': 40}}
calls2 = {'n': 0}
r2 = v.run_step('sim2', '危险动作拦截', {'title': 'Submit'}, {'fp_changed': True},
                lambda: calls2.__setitem__('n', calls2['n'] + 1),
                str(a), lambda: str(b),
                guard_spec={'title': 'Submit', 'box': [10, 20, 100, 40]},
                skip_precheck=False)
results.append(('陈旧目标拦截',
                r2['ok'] is False and calls2['n'] == 0 and
                'stale_target' in r2['precheck']['reason'],
                r2['precheck']['reason']))

# 3) 异常转移：禁止信号出现，重试后上报
de.find_element = fake_found
visual_verifier._ocr = lambda p: [{'text': 'Please verify you are human'}]
calls3 = {'n': 0}
r3 = v.run_step('sim3', '被风控拦截', {'title': 'Submit'},
                {'text_appears': ['Success'],
                 'unexpected_appears': ['verify you are human']},
                lambda: calls3.__setitem__('n', calls3['n'] + 1),
                str(a), lambda: str(b),
                guard_spec={'title': 'Submit'},
                skip_precheck=False, max_retries=1)
results.append(('异常转移检测',
                r3['ok'] is False and r3['path'] == 'postcheck_failed',
                r3['path']))

# 4) web 证据否决：失败网络请求压过正向 OCR
de.find_element = fake_found
visual_verifier._ocr = lambda p: [{'text': 'Success'}]
r4 = v.run_step('sim4', '支付请求失败', {'title': 'Submit'},
                {'text_appears': ['Success']},
                lambda: None, str(a), lambda: str(b),
                guard_spec={'title': 'Submit'}, skip_precheck=False,
                max_retries=1,
                verify_web_fn=lambda: {
                    'url_delta': '/cart -> /pay',
                    'console_errors': [],
                    'network_failures': [{'status': 500, 'url': 'POST /pay'}]})
results.append(('Web证据否决',
                r4['ok'] is False and
                r4['evidence']['web']['network_failures'][0]['status'] == 500,
                r4['path']))

de.find_element, visual_verifier._ocr = orig_find, orig_ocr
v.flush()
for name, ok, detail in results:
    print(('  PASS ' if ok else '  FAIL ') + f'{name}: {detail}')
print(f'{sum(1 for _, o, _ in results if o)}/{len(results)} passed')
json.dump([{'scene': n, 'ok': o, 'detail': d} for n, o, d in results],
          open(tmp / 'result.json', 'w'))
print('TRACE:', v.trace_path)
sys.exit(0 if all(o for _, o, _ in results) else 1)
