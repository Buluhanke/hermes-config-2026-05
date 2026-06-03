#!/usr/bin/env python3
"""macOS 内存分析脚本 — 正确处理 page size + RSS 分类汇总

⚠️ 关键陷阱：macOS vm_stat 的 page size 是 16384 字节（旧文档说 4096 是错的，
Apple Silicon M1/M2/M3/M4 都是 16384）。用 4096 算会少算 4 倍。

正确公式：
  实际字节数 = pages × 16384
  实际 GB = pages × 16384 / 1024 / 1024 / 1024

ps -A -o rss 输出单位是 KB（注意：man page 有时不准确，实测是 KB）。

用法：python3 macos-mem-report.py
输出：按分类汇总 + 总量 + 空闲内存
"""
import subprocess
from collections import defaultdict

# 抓取 ps 输出
out = subprocess.check_output(['ps', '-A', '-o', 'comm,rss'], text=True)
lines = out.strip().split('\n')[1:]

# 分类映射
def classify(comm):
    c = comm.lower()
    if 'chrome' in c: return 'Google Chrome'
    if 'webkit' in c: return 'WebKit (系统)'
    if 'node' in c: return 'Node.js'
    if 'python' in c: return 'Python'
    if 'npm' in c: return 'NPM'
    if 'mihomo' in c or 'clash' in c or 'verge' in c: return 'Clash Verge 代理'
    if 'warp' in c or 'cloudflare' in c: return 'Cloudflare WARP'
    if 'spotlight' in c or 'corespotlight' in c or 'knowledged' in c: return 'Spotlight 索引'
    if any(x in c for x in ['loginwindow','windowserver','dock','systemuiserver','sharingd','fontd']):
        return 'macOS 系统UI'
    if any(x in c for x in ['contactsd','calendar','reminders','notes','maps','mediaanalysis','mail','imagent']):
        return 'macOS 应用服务'
    if 'input' in c or 'scim' in c: return '输入法'
    if 'activity' in c: return 'Activity Monitor'
    if 'terminal' in c: return 'Terminal'
    if 'screenshot' in c: return 'Screenshot Helper'
    if 'cua-driver' in c: return 'CUA Driver (computer_use)'
    return comm

# 路径前缀分类（处理带 /Applications/ /System/Library/ 等的进程）
def classify_by_path(comm):
    if classify(comm) != comm:
        return classify(comm)
    if comm.startswith('/System/Library/'):
        return 'macOS 系统库 (6GB+)'
    if comm.startswith('/Applications/'):
        return '用户应用 (路径类)'
    if comm.startswith('/usr/libexec/'):
        return 'macOS 系统服务'
    if comm.startswith('/usr/sbin/'):
        return 'macOS 系统守护'
    if comm.startswith('/usr/'):
        return 'macOS 系统命令'
    if comm.startswith('/System/'):
        return 'macOS 系统组件'
    if comm.startswith('/Users/aimac/.hermes/'):
        return 'Hermes 自家组件'
    return classify(comm)

groups = defaultdict(lambda: {'count': 0, 'rss': 0, 'procs': []})
for line in lines:
    parts = line.split()
    if len(parts) < 2: continue
    comm = parts[0]
    try:
        rss_kb = int(parts[1])
    except (ValueError, IndexError):
        continue
    cat = classify_by_path(comm)
    g = groups[cat]
    g['count'] += 1
    g['rss'] += rss_kb
    if rss_kb > 50 * 1024:  # >50MB 记录详情
        g['procs'].append((comm, rss_kb / 1024))

# vm_stat 解析（正确使用 16384 page size）
vmstat = subprocess.check_output(['vm_stat'], text=True)
stats = {}
for line in vmstat.split('\n'):
    if ':' in line:
        k, v = line.split(':', 1)
        try:
            stats[k.strip()] = int(v.strip().rstrip('.'))
        except ValueError:
            pass

PAGE = 16384  # Apple Silicon 实际 page size
free_gb = stats.get('Pages free', 0) * PAGE / 1024 / 1024 / 1024
active_gb = stats.get('Pages active', 0) * PAGE / 1024 / 1024 / 1024
inactive_gb = stats.get('Pages inactive', 0) * PAGE / 1024 / 1024 / 1024
wired_gb = stats.get('Pages wired down', 0) * PAGE / 1024 / 1024 / 1024
compressed_gb = stats.get('Pages compressed', 0) * PAGE / 1024 / 1024 / 1024

total_mb = sum(g['rss'] for g in groups.values()) / 1024

print(f"{'分类':<32} {'个数':<6} {'占用':<12} {'占比'}")
print('-' * 70)
for cat, g in sorted(groups.items(), key=lambda x: -x[1]['rss']):
    mb = g['rss'] / 1024
    pct = mb / total_mb * 100
    print(f"{cat:<32} {g['count']:<6} {mb:>7.1f} MB  {pct:>4.1f}%")
    for proc, mb2 in sorted(g['procs'], key=lambda x: -x[1])[:2]:
        proc_name = proc.split('/')[-1] if '/' in proc else proc
        print(f"  └─ {proc_name}  {mb2:.0f} MB")
print('-' * 70)
print(f"{'进程 RSS 总和':<32} {'':6} {total_mb:>7.1f} MB  100.0%")
print()
print(f"=== macOS 内存统计 (page size = {PAGE}) ===")
print(f"Active (活跃):     {active_gb:>6.2f} GB")
print(f"Inactive (非活跃): {inactive_gb:>6.2f} GB  ← 文件缓存，可回收")
print(f"Wired (核心):      {wired_gb:>6.2f} GB")
print(f"Compressed (压缩): {compressed_gb:>6.2f} GB")
print(f"Free (空闲):       {free_gb:>6.2f} GB  ← 真正可用")
