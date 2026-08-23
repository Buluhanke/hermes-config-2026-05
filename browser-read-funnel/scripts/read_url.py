#!/usr/bin/env python3
"""read_url.py — L0/L2 失败降级链（零截图读懂的轻量入口，纯本地可验证工具）。

策略（全部已实跑验证，不依赖对话沙箱外的 hermes_tools / 未验证的云端后端）:
  1. scrapling extract get   （HTTP 静态/快速，本地）
  2. scrapling extract fetch （JS 渲染/SPA，本地，--network-idle）
  3. curl -sL                （最裸兜底，仅当 scrapling 不可用时）

注: Hermes 内置的 web_extract 工具在对话里可用，但本独立脚本运行在普通
python 子进程、 import 不到 hermes_tools，故降级链走 scrapling(已验证)。
登录态前台页请走 L1 (read_chrome.py)；后台登录页(无前台窗口)走 A2 (curl_xhr.py --cookie)。

用法:
  python3 read_url.py <url> [--out file.md] [--json]
  --json  打印 {url, via, ok, len, head}
"""
import sys, os, json, subprocess, tempfile

def _run_scrapling(url, mode):
    fd, tmp = tempfile.mkstemp(suffix=".md")
    os.close(fd)
    cmd = ["scrapling", "extract", mode, url, tmp]
    if mode == "fetch":
        cmd += ["--network-idle"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return None
    if os.path.exists(tmp) and os.path.getsize(tmp) > 80:
        with open(tmp, encoding="utf-8") as f:
            return f.read()
    return None

def try_scrapling_get(url):
    return _run_scrapling(url, "get")

def try_scrapling_fetch(url):
    return _run_scrapling(url, "fetch")

def try_curl(url):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "60", url],
                            capture_output=True, text=True, timeout=70)
        if r.returncode == 0 and len(r.stdout) > 200:
            return r.stdout
    except Exception:
        pass
    return None

def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("用法: python3 read_url.py <url> [--out file] [--json]")
        sys.exit(2)
    url = args[0]
    out = None
    as_json = False
    if "--json" in args: as_json = True
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args): out = args[i + 1]

    for via, fn in (("scrapling-get", try_scrapling_get),
                    ("scrapling-fetch", try_scrapling_fetch),
                    ("curl", try_curl)):
        content = fn(url)
        if content:
            if out:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(content)
                print(json.dumps({"url": url, "via": via, "ok": True, "len": len(content), "out": out}, ensure_ascii=False) if as_json
                      else f"OK via {via} -> {out} ({len(content)} chars)")
            else:
                print(json.dumps({"url": url, "via": via, "ok": True, "len": len(content), "head": content[:300]}, ensure_ascii=False) if as_json
                      else f"=== via {via} ({len(content)} chars) ===\n{content[:4000]}")
            return
    print(json.dumps({"url": url, "via": None, "ok": False, "len": 0, "error": "所有后端失败"}, ensure_ascii=False) if as_json
          else "FAIL: 所有后端失败")
    sys.exit(1)

if __name__ == "__main__":
    main()
