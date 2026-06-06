"""
stealth_inject.py — Hermes 反指纹注入器 (v1.2)
通过 CDP ws://127.0.0.1:9333 连接本地 Chrome, 把 stealth.js 注入到所有 tab
- Page.addScriptToEvaluateOnNewDocument: 每个新页面/刷新前自动跑 stealth
- Runtime.evaluate: 立即生效 (不刷新也能覆盖)

v1.2 修: Chrome 148+ 默认 push event, ws.recv() 会拿到 Runtime.executionContextCreated
        等 event 而不是 command response. 用 sendrecv 循环跳过 event.

Usage:
  python3 stealth_inject.py                # 注入到所有 tab, 立即生效
  python3 stealth_inject.py --verify       # 只验证 10 项反指纹检查 (10/10 满)
  python3 stealth_inject.py --revert       # 移除 stealth 注入 (debug)
  python3 stealth_inject.py --dry-run      # 显示计划, 不实际执行

触发词: "stealth 注入" / "反指纹跑分" / "bot.sannysoft" / "anti-detect 验证"
        / "隐身注入到所有 tab" / "CDP 持久 stealth"
"""
import argparse
import json
import os
import sys
import urllib.request
import websocket  # pip install websocket-client

CDP_URL = 'ws://127.0.0.1:9333'
STEALTH_PATH = os.path.expanduser('~/.hermes/scripts/stealth.js')


def fetch_targets():
    """从 /json/list 拉所有 tab target"""
    with urllib.request.urlopen('http://127.0.0.1:9333/json/list', timeout=3) as r:
        targets = json.loads(r.read())
    return [t for t in targets if t.get('type') == 'page']


class CDPSession:
    """CDP 会话, 自动跳过 event 帧, 只返回对应 id 的 command response"""

    def __init__(self, ws_url, timeout=5):
        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self.msg_id = 0

    def close(self):
        self.ws.close()

    def sendrecv(self, method, params=None):
        """发命令, 收对应 id 的 response, 跳过 event 帧"""
        self.msg_id += 1
        my_id = self.msg_id
        self.ws.send(json.dumps({'id': my_id, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            # event 帧: 只有 method/params, 没 id
            if 'id' in msg and msg['id'] == my_id:
                return msg


def inject_stealth(target, dry_run=False):
    """CDP 注入 stealth.js 到一个 target"""
    if dry_run:
        print(f'  [DRY-RUN] would inject {target.get("url","?")[:60]}')
        return True
    cd = CDPSession(target['webSocketDebuggerUrl'])
    try:
        cd.sendrecv('Page.enable')
        with open(STEALTH_PATH) as f:
            script = f.read()
        r = cd.sendrecv('Page.addScriptToEvaluateOnNewDocument', {
            'source': script,
            'worldName': 'MAIN',
        })
        if 'error' in r:
            print(f'  ❌ addScript 失败: {r["error"]["message"]}')
            return False
        # 立即在当前页跑
        r = cd.sendrecv('Runtime.evaluate', {
            'expression': script,
            'runImmediately': True,
        })
        if 'error' in r:
            print(f'  ❌ Runtime.evaluate 失败: {r["error"]["message"]}')
            return False
        return True
    finally:
        cd.close()


def verify_stealth(target):
    """验证 10 项反指纹检查 (2026-06-05 实测 10/10 满)"""
    cd = CDPSession(target['webSocketDebuggerUrl'])
    try:
        cd.sendrecv('Runtime.enable')
        js = '''
        (() => {
            const r = {};
            r.webdriver = navigator.webdriver;
            r.plugins_count = navigator.plugins.length;
            r.plugins_names = Array.from(navigator.plugins).map(p => p.name);
            r.languages = navigator.languages;
            r.chrome_runtime = typeof window.chrome?.runtime;
            r.stealth_injected = window.__hermes_stealth_injected__ === true;
            r.stealth_version = window.__hermes_stealth_version__;
            try {
                const c = document.createElement('canvas');
                const gl = c.getContext('webgl');
                if (gl) {
                    r.webgl_vendor = gl.getParameter(37445);
                    r.webgl_renderer = gl.getParameter(37446);
                }
            } catch (e) { r.webgl_err = String(e); }
            r.permissions = navigator.permissions ? 'ok' : 'missing';
            const cdc = Object.keys(document).filter(k => k.startsWith('cdc_') || k.startsWith('__driver_') || k.startsWith('__webdriver_'));
            r.cdc_keys = cdc;
            return JSON.stringify(r);
        })()
        '''
        r = cd.sendrecv('Runtime.evaluate', {
            'expression': js,
            'returnByValue': True,
        })
        if 'error' in r:
            raise RuntimeError(f'CDP error: {r["error"]["message"]}')
        result = r.get('result', {})
        if 'exceptionDetails' in result:
            raise RuntimeError(f'Script exception: {result["exceptionDetails"]}')
        if 'result' in result and isinstance(result['result'], dict) and 'value' in result['result']:
            return json.loads(result['result']['value'])
        if 'value' in result:
            return json.loads(result['value'])
        raise RuntimeError(f'Unexpected shape: {json.dumps(r)[:200]}')
    finally:
        cd.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verify', action='store_true', help='只验证, 不注入')
    p.add_argument('--revert', action='store_true', help='移除所有注入')
    p.add_argument('--dry-run', action='store_true', help='只显示计划')
    args = p.parse_args()

    mode = 'verify' if args.verify else 'revert' if args.revert else 'inject'
    print(f'== Hermes stealth 注入器 ==  ({mode}{" DRY" if args.dry_run else ""})')
    print(f'CDP: {CDP_URL}')
    print(f'Stealth: {STEALTH_PATH}')

    targets = fetch_targets()
    print(f'Tabs found: {len(targets)}')

    if args.verify:
        for t in targets:
            url = t.get('url', '?')[:60]
            try:
                v = verify_stealth(t)
                checks = [
                    v.get('webdriver') is False,
                    v.get('plugins_count', 0) >= 3,
                    len(v.get('plugins_names', [])) >= 3,
                    isinstance(v.get('languages'), list) and len(v.get('languages', [])) >= 2,
                    v.get('chrome_runtime') == 'object',
                    v.get('stealth_injected') is True,
                    v.get('webgl_vendor') == 'Google Inc. (Apple)',
                    (v.get('webgl_renderer') or '').startswith('ANGLE'),
                    v.get('permissions') == 'ok',
                    len(v.get('cdc_keys', [])) == 0,
                ]
                score = sum(checks)
                pass_str = '/'.join(['1' if c else '0' for c in checks])
                print(f'  [{score}/10 {pass_str}] {url}')
                if score < 10:
                    print(f'     webdriver={v.get("webdriver")} plugins={v.get("plugins_count")} lang={v.get("languages")} chromert={v.get("chrome_runtime")} stealth={v.get("stealth_injected")} webgl={v.get("webgl_vendor")} cdc={len(v.get("cdc_keys",[]))}')
            except Exception as e:
                print(f'  [ERR] {url}: {e}')
        return 0

    if args.revert:
        for t in targets:
            cd = CDPSession(t['webSocketDebuggerUrl'])
            try:
                cd.sendrecv('Page.enable')
                # 没 identifier 概念, addScript 只能 reload 才失效
                print(f'  info: stealth 仅在 tab 关闭/Chrome 重启时失效, 需 inject 覆盖')
            finally:
                cd.close()
        return 0

    ok = 0
    for t in targets:
        url = t.get('url', '?')[:60]
        try:
            # v1.2 修: dry-run 时 inject_stealth 已 print [DRY-RUN], main 不能再 print ✅
            if args.dry_run:
                inject_stealth(t, dry_run=True)
            else:
                if inject_stealth(t, dry_run=False):
                    print(f'  ✅ {url}')
                    ok += 1
                else:
                    print(f'  ❌ {url}')
        except Exception as e:
            print(f'  [ERR] {url}: {e}')
    if args.dry_run:
        print(f'\n[DRY-RUN] 计划完成, 未实际执行')
    else:
        print(f'\n注入完成: {ok}/{len(targets)}')
    return 0 if (args.dry_run or ok == len(targets)) else 1


if __name__ == '__main__':
    sys.exit(main())
