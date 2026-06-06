# mem_patrol v1.0 误杀实战（2026-06-05 真实反例）

## 事件经过

执行 `~/.hermes/scripts/mem_patrol.sh` v1.0 第一次跑，**误杀 4 个进程**：
- ToDesk PID=1537（2MB）
- Claude Helper PID=23400（11MB）
- Claude Helper PID=23402（11MB）
- Claude Helper PID=23405（19MB）

**真相**：当前系统实际有 **16.7 GB 空闲内存**（已用 31%），完全不紧张。

## 根因（两个坑叠在一起）

### 坑 1：`vm_stat | Pages free` 单值当总空闲

```bash
# v1.0 错误写法
FREE_PAGES=$(vm_stat | awk '/Pages free/ {print $3}' | tr -d '.')
INACTIVE_PAGES=$(vm_stat | awk '/Pages inactive/ {print $3}' | tr -d '.')
PAGE_SIZE=16384
FREE_MB=$(( (FREE_PAGES + INACTIVE_PAGES) * PAGE_SIZE / 1024 / 1024 ))
# 算出来: 749 MB ← 把空闲低估 22 倍
```

macOS 上 `Pages free` 是 kernel 主动标记的"完全空闲页"，**不包含**大量 inactive 页（系统可按需 swap out）。`Pages free + Pages inactive` 还差一项 `Pages speculative`（已清零未回收，可立即用）。

**正确**：
```python
avail_pages = free + inactive + speculative
free_mb = (avail_pages * 16384) // (1024 * 1024)
# 算出来: 16950 MB ← 真实空闲
```

### 坑 2：BSD `paste` 在 macOS 上参数顺序反了

```bash
# v1.0 想用 paste 拼数字
vm_stat | awk '/Pages free|Pages inactive/ {print $3}' | tr -d '.' | paste -sd+ | bc
# 输出: usage: paste [-s] [-d delimiters] file ...
```

**BSD paste 期望 `-d` 在 `-s` 前**，GNU paste 习惯反过来。脚本里 `paste -sd+` 直接报错，FREE_MB 算成 0 → 比 1GB 阈值还低 → 触发紧急杀进程。

## v1.1 修复（3 个核心改动）

1. **改用 python 算内存**（绕过 BSD 工具链兼容性问题）
2. **`free + inactive + speculative` 三项求和**（真实可用内存）
3. **杀进程前重新算一遍**（杀一个就检查，够 1.5GB 就停）

```python
import subprocess
o = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
PAGE = 16384
def parse(k):
    for l in o.splitlines():
        if l.startswith(k):
            return int(l.split(':')[1].strip().rstrip('.'))
    return 0
avail_pages = parse('Pages free') + parse('Pages inactive') + parse('Pages speculative')
free_mb = (avail_pages * PAGE) // (1024 * 1024)
```

## 教训（写入 macos-process-lifecycle）

1. **macOS 内存计算必须用 python**（BSD 工具链兼容性 + 三项求和复杂度）
2. **"Pages free" 单值 = 误导**（Mem Graph 顶部数字是三项求和）
3. **杀进程脚本必须有"杀一个重算"循环**（不能假设"杀完所有就够"）
4. **静态分析不能完全替代 dry-run** — v1.0 静态看脚本"逻辑正确"，但 BSD paste 错位只在真实运行才暴露

## 复现/验证命令

```bash
# 看当前真实空闲
python3 -c "
import subprocess
o = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
PAGE = 16384
def parse(k):
    for l in o.splitlines():
        if l.startswith(k):
            return int(l.split(':')[1].strip().rstrip('.'))
    return 0
avail = parse('Pages free') + parse('Pages inactive') + parse('Pages speculative')
print(f'可用: {(avail * PAGE) // (1024*1024)}MB')
"
# 期望: 8000+ MB（Mac mini 24GB 平时空闲 12-17GB）

# 验证 BSD paste 错位
echo "1" "2" "3" | paste -sd+
# macOS 输出: usage: paste [-s] [-d delimiters] file ...
```

## 适用范围

任何 macOS 上的"内存巡逻 / 杀进程 / 自动清理"脚本**都必须**走 v1.1 的 python 公式。Linux 上 systemd/slab 模型不同，可以放心用 `free -m` 单值。
