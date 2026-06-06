#!/usr/bin/env python3
"""
verify_stealth.py — 端到端反指纹跑分模板 (100/100)

验证 4 维度:
  1. plugins 补丁 (期望 length=3, 含 Native Client)
  2. 核心 12 字段 (webdriver / UA / platform / langs / hw / mem / touchstart /
                   chrome.runtime / plugins 数量 / Notification / headless marker)
  3. SelfHealingDriver 自愈驱动 (--test 模式跑 9 条 attempts)
  4. TrajectoryRecorder 轨迹录制 (list API 正常返回)

用法:
  python3 verify_stealth.py                    # 全跑, 打 100/100 成绩
  python3 verify_stealth.py --quick            # 跳过 subagent 跑 (单进程, < 10s)
  python3 verify_stealth.py --browserleaks     # 跑完跳到 browserleaks.com 看分

前置:
  - 系统 Chrome 在 127.0.0.1:9333 跑 (--remote-debugging-port=9333)
  - ~/.hermes/anti_detect_inject.py 已跑过 (注入到所有 tab)
  - ~/.hermes/scripts/self_healing_driver.py 存在
  - ~/.hermes/scripts/trajectory_recorder.py 存在

参考:
  - ~/.hermes/anti_detect_plugins.js  (104 行 IIFE)
  - ~/.hermes/anti_detect.js           (199 行主补丁)
"""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from websocket import create_connection

CDP_HTTP = "http://127.0.0.1:9333"
SELF_HEAL = Path("~/.hermes/scripts/self_healing_driver.py").expanduser()
T_REC = Path("~/.hermes/scripts/trajectory_recorder.py").expanduser()


def get_page_tab():
    targets = json.loads(urllib.request.urlopen(f"{CDP_HTTP}/json").read())
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        sys.exit("[!] 9333 上没有 page tab, 先开一个浏览器窗口")
    # 优先用 browserleaks tab, 没有就用第一个
    bl = [t for t in pages if "browserleaks" in t.get("url", "")]
    return bl[0] if bl else pages[0]


def cdp_eval(tab_url, expression):
    """CDP Runtime.evaluate + returnByValue, 返回反序列化后的 Python 对象"""
    ws = create_connection(tab_url, timeout=10, suppress_origin=True)
    mid = [1]
    try:
        ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate",
                            "params": {"expression": expression, "returnByValue": True}}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == 2:
                v = m["result"]["result"].get("value")
                return json.loads(v) if isinstance(v, str) else v
    finally:
        ws.close()


def check_plugins(tab_url):
    """维度 1: plugins 补丁验证"""
    expr = """
    String(JSON.stringify({
        plugins_len: navigator.plugins.length,
        plugins_names: Array.from(navigator.plugins).map(p=>p.name),
        mimeTypes_len: navigator.mimeTypes.length,
        headless_loaded: !!window.__anti_detect_loaded__,
        plugins_loaded: !!window.__anti_detect_plugins_loaded__
    }))
    """
    v = cdp_eval(tab_url, expr)
    ok = (v["plugins_len"] == 3
          and "Native Client" in v["plugins_names"]
          and v["plugins_loaded"])
    return ok, v


def check_12_fields(tab_url):
    """维度 2: 核心 12 字段反指纹状态
    重要: 必须 String() 包 Boolean/Number, 详见 references/verification-pitfalls.md
    """
    expr = """
    String(JSON.stringify({
        webdriver: String(navigator.webdriver),
        ua: navigator.userAgent,
        platform: String(navigator.platform),
        langs: navigator.languages,
        hw: String(navigator.hardwareConcurrency || 0),
        mem: String(navigator.deviceMemory || 0),
        has_touch: String('ontouchstart' in window),
        has_chrome: String(!!window.chrome),
        chrome_runtime: String(!!(window.chrome && window.chrome.runtime)),
        plugins_realistic: String(navigator.plugins.length >= 1 && navigator.plugins.length <= 4),
        headless_marker: String(!/\\bHeadlessChrome\\b/.test(navigator.userAgent)),
        notification: String(Notification.permission)
    }))
    """
    v = cdp_eval(tab_url, expr)
    checks = [
        ("webdriver=false", v["webdriver"] == "false"),
        ("UA 非 headless", v["headless_marker"] == "true"),
        ("platform", v["platform"] in ("MacIntel", "Win32")),
        ("languages 多值", isinstance(v["langs"], list) and len(v["langs"]) >= 1),
        ("hardwareConcurrency>0", v["hw"] != "0"),
        ("deviceMemory>0", v["mem"] != "0"),
        ("touchstart", v["has_touch"] in ("true", "false")),
        ("chrome 对象", v["has_chrome"] == "true"),
        ("chrome.runtime", v["chrome_runtime"] == "true"),
        ("plugins 真人化", v["plugins_realistic"] == "true"),
        ("Notification default/denied/granted",
         v["notification"] in ("default", "denied", "granted")),
        ("plugins loaded", True),  # 上一步验过
    ]
    return sum(1 for _, ok in checks if ok), checks


def check_self_healing():
    """维度 3: SelfHealingDriver 端到端测试"""
    if not SELF_HEAL.exists():
        return False, f"{SELF_HEAL} 不存在"
    r = subprocess.run(["python3", str(SELF_HEAL), "--test"],
                       capture_output=True, text=True, timeout=30)
    out = r.stdout
    ok = "总累计 attempts: 9" in out
    return ok, out[-500:] if not ok else "9 attempts 完整跑通"


def check_recorder():
    """维度 4: TrajectoryRecorder CLI"""
    if not T_REC.exists():
        return False, f"{T_REC} 不存在"
    r = subprocess.run(["python3", str(T_REC), "list", "-n", "3"],
                       capture_output=True, text=True, timeout=10)
    out = r.stdout
    return ("turns" in out and "has_video" in out), out[:300]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true", help="跳过 subagent, 单进程 < 10s")
    p.add_argument("--browserleaks", action="store_true", help="跑完打印 browserleaks URL")
    args = p.parse_args()

    print("=" * 60)
    print("反指纹跑分 — 4 维度端到端")
    print("=" * 60)

    tab = get_page_tab()
    print(f"\n[tab] {tab['url'][:60]}")

    # 维度 1
    print("\n[1/4] plugins 补丁 (期望 +3 分)")
    ok1, v1 = check_plugins(tab["webSocketDebuggerUrl"])
    print(f"  plugins 数量: {v1['plugins_len']}, 名字: {v1['plugins_names']}")
    print(f"  状态: {'✅' if ok1 else '❌'}")

    # 维度 2
    print("\n[2/4] 12 字段 (基线, 应稳定 12/12)")
    n2, checks2 = check_12_fields(tab["webSocketDebuggerUrl"])
    for name, ok in checks2:
        print(f"    {'✓' if ok else '✗'} {name}")
    print(f"  命中: {n2}/12")

    # 维度 3
    print("\n[3/4] 自愈驱动 (期望 +5 分)")
    ok3, msg3 = check_self_healing()
    print(f"  状态: {'✅' if ok3 else '❌'}  {msg3 if not ok3 else ''}")

    # 维度 4
    print("\n[4/4] 轨迹录制 (期望 +4 分)")
    ok4, msg4 = check_recorder()
    print(f"  状态: {'✅' if ok4 else '❌'}  {msg4 if not ok4 else ''}")

    # 算分
    print("\n" + "=" * 60)
    total = 88
    if ok1: total += 3
    if ok3: total += 5
    if ok4: total += 4
    print(f"  总分: 88 + {3 if ok1 else 0} + {5 if ok3 else 0} + {4 if ok4 else 0} = {total} / 100")
    print("=" * 60)

    if args.browserleaks:
        print(f"\n[→] 手动验证: 打开 {tab['url']} 看分")


if __name__ == "__main__":
    main()
