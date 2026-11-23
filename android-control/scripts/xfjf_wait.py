#!/usr/bin/env python3
"""学法减分考试：事件驱动等待器（短轮询 + 即时推进，零 LLM 依赖）。

配合 terminal(background=True, notify=True) 使用：完成瞬间收到通知，
不用长 sleep 空等。这是「长任务实时盯屏铁律」的落地脚本。

用法:
  ~/.hermes/venvs/u2/bin/python scripts/xfjf_wait.py unlock-start  --dev <IP>:5555
  ~/.hermes/venvs/u2/bin/python scripts/xfjf_wait.py face-pass     --dev <IP>:5555
  ~/.hermes/venvs/u2/bin/python scripts/xfjf_wait.py reexam-ready  --dev <IP>:5555
  ~/.hermes/venvs/u2/bin/python scripts/xfjf_wait.py final-auth    --dev <IP>:5555
"""
import sys, re, json, time, datetime, subprocess
import uiautomator2 as u2

ADB = '/Users/aimac/.local/bin/adb'

def log(msg):
    print(datetime.datetime.now().strftime('%H:%M:%S') + ' ' + str(msg), flush=True)

def dev_locked(dev):
    """锁屏判定唯一可靠来源：dumpsys trust 的 deviceLocked。
    绝不用页面文字里的'人脸'/'识别'判断——华为锁屏页自带'双击屏幕进行人脸识别'，
    会被误判成考试抓拍。"""
    out = subprocess.run([ADB, '-s', dev, 'shell', 'dumpsys', 'trust'],
                         capture_output=True, text=True).stdout
    m = re.search(r'deviceLocked=(\d)', out)
    return m.group(1) == '1' if m else True

def texts_of(xml):
    return re.findall(r'text="([^"]{2,})"', xml)

def find_click(d, label, xml):
    """按按钮文字取 bounds 中心点击——横竖屏坐标不同，绝不写死。"""
    pat = r'text="([^"]*' + re.escape(label) + r'[^"]*)"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"'
    for t, b in re.findall(pat, xml):
        n = [int(x) for x in re.findall(r'\d+', b)]
        d.click((n[0] + n[2]) // 2, (n[1] + n[3]) // 2)
        return t
    return None

def cmd_unlock_start(d, dev, timeout=240):
    log('WAIT_UNLOCK')
    end = time.time() + timeout
    while time.time() < end:
        if not dev_locked(dev):
            log('UNLOCKED')
            subprocess.run([ADB, '-s', dev, 'shell', 'input', 'keyevent', '224'])  # 点亮
            time.sleep(1)
            xml = d.dump_hierarchy()
            hit = find_click(d, '开始考试', xml)
            log('CLICKED_START=' + str(hit))
            time.sleep(3)
            xml = d.dump_hierarchy()
            q = re.search(r'text="(\d+、[^"]+)"', xml)
            print(json.dumps({'event': 'started', 'button': hit,
                              'face': '人脸' in xml or '正对摄像头' in xml,
                              'q': q.group(1) if q else '',
                              'texts': texts_of(xml)[:20]}, ensure_ascii=False), flush=True)
            return
        time.sleep(2)
    print(json.dumps({'event': 'timeout_unlock'}, ensure_ascii=False), flush=True)
    sys.exit(1)

def cmd_face_pass(d, dev, timeout=180):
    log('WAIT_FACE_PASS')
    end = time.time() + timeout
    while time.time() < end:
        if dev_locked(dev):   # 锁屏时不做人脸判断，避免假阳性
            log('LOCKED_SKIP')
            time.sleep(2); continue
        xml = d.dump_hierarchy()
        texts = texts_of(xml)
        if any('比对不通过' in t or ('剩余' in t and '次' in t) for t in texts):
            print(json.dumps({'event': 'face_fail', 'texts': texts[:20]}, ensure_ascii=False), flush=True)
            return
        q = re.search(r'text="(\d+、[^"]+)"', xml)
        face = '人脸' in xml or '正对摄像头' in xml or '置于屏幕中央' in xml
        if not face and q:
            print(json.dumps({'event': 'face_pass', 'q': q.group(1),
                              'texts': texts[:10]}, ensure_ascii=False), flush=True)
            return
        time.sleep(2)
    print(json.dumps({'event': 'timeout_face'}, ensure_ascii=False), flush=True)
    sys.exit(1)

def cmd_reexam_ready(d, dev, timeout=180):
    """点完「立即补考」后等题目页出现；人脸抓拍态单独报，不空等。"""
    log('WAIT_REEXAM')
    end = time.time() + timeout
    while time.time() < end:
        if dev_locked(dev):
            log('LOCKED_SKIP')
            time.sleep(2); continue
        xml = d.dump_hierarchy()
        texts = texts_of(xml)
        q = re.search(r'text="(\d+、[^"]+)"', xml)
        if q:
            print(json.dumps({'event': 'reexam_ready', 'q': q.group(1),
                              'texts': texts[:10]}, ensure_ascii=False), flush=True)
            return
        if any('人脸' in t or '正对摄像头' in t for t in texts):
            print(json.dumps({'event': 'face_wait', 'texts': texts[:15]}, ensure_ascii=False), flush=True)
            return
        time.sleep(2)
    print(json.dumps({'event': 'timeout_reexam'}, ensure_ascii=False), flush=True)
    sys.exit(1)


def cmd_final_auth(d, dev, timeout=300):
    """交卷后最终人脸认证监听：通过/失败/超时立刻报（限时5分钟）。"""
    log('WAIT_FINAL_AUTH')
    end = time.time() + timeout
    while time.time() < end:
        texts = texts_of(d.dump_hierarchy())
        joined = ' '.join(texts)
        if any(k in joined for k in ('考试通过', '成绩合格', '提交减分', '已为您提交')):
            print(json.dumps({'event': 'auth_pass', 'texts': texts[:25]}, ensure_ascii=False), flush=True)
            return
        if any(k in joined for k in ('认证失败', '比对不通过', '考试不通过', '不合格')):
            print(json.dumps({'event': 'auth_fail', 'texts': texts[:25]}, ensure_ascii=False), flush=True)
            return
        time.sleep(2)
    print(json.dumps({'event': 'timeout_auth'}, ensure_ascii=False), flush=True)
    sys.exit(1)


if __name__ == '__main__':
    argv = sys.argv[1:]
    dev = argv[argv.index('--dev') + 1] if '--dev' in argv else None
    if dev:
        i = argv.index('--dev'); argv = argv[:i] + argv[i + 2:]
    cmd = argv[0] if argv else 'unlock-start'
    if not dev:
        print('必须 --dev <设备IP:5555>', file=sys.stderr); sys.exit(2)
    d = u2.connect(dev)
    if cmd == 'unlock-start':
        cmd_unlock_start(d, dev)
    elif cmd == 'face-pass':
        cmd_face_pass(d, dev)
    elif cmd == 'reexam-ready':
        cmd_reexam_ready(d, dev)
    elif cmd == 'final-auth':
        cmd_final_auth(d, dev)
    else:
        print('未知命令: ' + cmd, file=sys.stderr); sys.exit(2)
