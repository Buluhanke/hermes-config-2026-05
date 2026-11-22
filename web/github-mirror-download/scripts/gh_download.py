#!/usr/bin/env python3
"""
gh_download.py — GitHub 资源多镜像智能下载器
从 Komi Store 逆向提炼的镜像加速能力，做成零依赖 CLI。

策略（复刻 Komi Store）：
  1. 拉取 Komi 动态镜像目录 (api.github-store.org/v1/mirrors/list)，失败则用内置列表兜底
  2. 按官方延迟排序，跳过 status=down 的镜像
  3. 可选 --probe 用真实 HEAD 请求现场测速（冷12s/热5s，2次取最快，并发6）
  4. 依次尝试每个镜像下载，第一个成功的胜出；全失败退回直连
  5. 断点续传：支持 -C -，配合多次重试对抗 0 字节限速

用法：
  gh_download.py <github_url> [-o 输出路径] [--probe] [--list] [--timeout 秒] [--tries N]

示例：
  gh_download.py https://github.com/owner/repo/releases/download/v1/app.dmg -o ~/Downloads/app.dmg
  gh_download.py https://github.com/owner/repo/archive/refs/heads/main.tar.gz -o repo.tar.gz
  gh_download.py --list                       # 只列出当前镜像健康状态
  gh_download.py <url> --probe                # 现场测速后用最快镜像

设计原则：零第三方依赖（仅 stdlib）、零 LLM、零 GUI、可被 agent 直接 subprocess 调用。
"""
import argparse
import json
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

MIRROR_API = "https://api.github-store.org/v1/mirrors/list"
PROBE_URL = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"

# Komi Store 内置镜像 (BundledMirrors.kt)，{url} 模板
BUILTIN = [
    ("direct", None),                                    # 直连永远兜底
    ("fastly_jsdelivr", "https://fastly.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}"),
    ("ghfast_top", "https://ghfast.top/{url}"),
    ("gh_proxy_com", "https://gh-proxy.com/{url}"),
    ("moeyy_xyz", "https://github.moeyy.xyz/{url}"),
    ("ghps_cc", "https://ghps.cc/{url}"),
    ("gh_99988866_xyz", "https://gh.api.99988866.xyz/{url}"),
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch_mirror_catalog(timeout=10):
    """拉 Komi 动态镜像目录，返回 [(id, template, latency_ms, status)]，失败返回 []。"""
    try:
        req = urllib.request.Request(MIRROR_API, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
            data = json.loads(r.read().decode())
        out = []
        for m in data.get("mirrors", []):
            out.append((m.get("id", ""), m.get("url_template"),
                        m.get("latency_ms"), m.get("status", "unknown")))
        return out
    except Exception:
        return []


def apply_template(tpl, url):
    """镜像 URL 模板展开。只支持 {url} 形式（raw 文件的 {owner}/{repo}/{ref}/{path}
    需要分解路径，release 资产一律走 {url}）。"""
    if not tpl:
        return url
    if "{url}" in tpl:
        return tpl.replace("{url}", url)
    if "{owner}" in tpl:
        # raw.githubusercontent.com/owner/repo/ref/path -> 分解
        parts = url.split("raw.githubusercontent.com/", 1)
        if len(parts) == 2:
            seg = parts[1].strip("/").split("/", 3)
            if len(seg) >= 4:
                owner, repo, ref, path = seg[0], seg[1], seg[2], seg[3]
                return (tpl.replace("{owner}", owner).replace("{repo}", repo)
                           .replace("{ref}", ref).replace("{path}", path))
    return None


def probe_one(item):
    """现场测速单个镜像：HEAD 探 PROBE_URL，返回 (id, latency_ms) 或 None。"""
    mid, tpl, _, status = item
    if status == "down":
        return None
    target = apply_template(tpl, PROBE_URL)
    if not target:
        return None
    best = None
    for _ in range(2):  # 2 次取最快
        t0 = time.time()
        try:
            req = urllib.request.Request(target, method="HEAD", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as r:
                r.read(1)
                if 200 <= r.status < 400:
                    dt = int((time.time() - t0) * 1000)
                    best = dt if best is None else min(best, dt)
                    continue
        except Exception:
            pass
        break  # 本次失败则不再试第二次
    return (mid, best) if best is not None else None


def build_candidates(catalog, do_probe):
    """构造下载候选 URL 列表，按优先级排序。"""
    # 合并动态目录 + 内置列表（去重）
    entries = {}
    for mid, tpl in BUILTIN:
        entries[mid] = [mid, tpl, None, "unknown"]
    for mid, tpl, lat, status in catalog:
        if mid in entries:
            entries[mid][2] = lat
            entries[mid][3] = status
        else:
            entries[mid] = [mid, tpl, lat, status]

    items = list(entries.values())
    # direct 排最前作为兜底？不——镜像优先，direct 最后。所以分两组。
    mirrors = [e for e in items if e[0] != "direct"]
    direct = [e for e in items if e[0] == "direct"]

    if do_probe:
        with ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(probe_one, mirrors))
        lat = {r[0]: r[1] for r in results if r}
        mirrors = [(mid, tpl, lat.get(mid), st) for mid, tpl, _, st in mirrors
                   if lat.get(mid) is not None]
        mirrors.sort(key=lambda e: e[2])
    else:
        # 按目录延迟排序，down 的排最后但仍保留（目录可能过期）
        def key(e):
            st, lat = e[3], e[2]
            if st == "down":
                return (2, 0)
            if lat is None:
                return (1, 0)
            return (0, lat)
        mirrors.sort(key=key)

    return mirrors + direct


def download_one(url, out, timeout, tries, label):
    """用单个 URL 下载，支持断点续传与重试。成功返回 True。"""
    for attempt in range(1, tries + 1):
        cmd = ["curl", "-sSL", "--retry", "1", "--connect-timeout", "10",
               "--max-time", str(timeout), "-A", UA]
        if os.path.exists(out) and os.path.getsize(out) > 0:
            cmd += ["-C", "-"]
        cmd += ["-o", out, url]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout + 15)
            size = os.path.getsize(out) if os.path.exists(out) else 0
            if r.returncode == 0 and size > 0:
                print(f"    ✓ {label} 成功 ({size} bytes)", flush=True)
                return True
            # 0 字节或失败，删掉半成品重试
            if size == 0 and os.path.exists(out):
                try: os.remove(out)
                except Exception: pass
        except subprocess.TimeoutExpired:
            pass
        if attempt < tries:
            time.sleep(1.5 * attempt)
    return False


def main():
    ap = argparse.ArgumentParser(description="GitHub 资源多镜像智能下载器")
    ap.add_argument("url", nargs="?", help="GitHub 资源 URL")
    ap.add_argument("-o", "--output", help="输出文件路径")
    ap.add_argument("--probe", action="store_true", help="现场测速镜像（更准但慢）")
    ap.add_argument("--list", action="store_true", help="只列出镜像健康状态")
    ap.add_argument("--timeout", type=int, default=180, help="单镜像总超时秒数")
    ap.add_argument("--tries", type=int, default=2, help="每镜像重试次数")
    args = ap.parse_args()

    catalog = fetch_mirror_catalog()
    if args.list:
        print("Komi 动态镜像目录:")
        if catalog:
            for mid, tpl, lat, st in catalog:
                print(f"  {mid:20s} status={st:8s} latency={lat}ms")
        else:
            print("  (目录不可达，使用内置列表)")
        print("\n内置镜像:")
        for mid, tpl in BUILTIN:
            print(f"  {mid:20s} {tpl or '直连'}")
        return 0

    if not args.url:
        ap.error("需要 URL（或用 --list）")

    out = args.output or os.path.basename(args.url.split("?")[0]) or "download.bin"
    out = os.path.expanduser(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    candidates = build_candidates(catalog, args.probe)
    print(f"候选镜像 {len(candidates)} 个，目标: {out}", flush=True)

    for mid, tpl, lat, st in candidates:
        target = apply_template(tpl, args.url)
        if not target:
            continue
        label = f"{mid}" + (f" ({lat}ms)" if lat else "")
        print(f"  尝试 {label} ...", flush=True)
        # 部分镜像对 release 资产不支持，探测阶段就能筛掉；这里直接尝试
        if download_one(target, out, args.timeout, args.tries, label):
            print(f"完成 → {out}")
            return 0

    print("所有镜像失败，请检查 URL 或稍后重试", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
