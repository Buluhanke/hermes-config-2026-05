# macOS 内存/CPU 计算公式（Apple Silicon）

## 关键陷阱：page size

macOS Apple Silicon (M1/M2/M3/M4) 的 `vm_stat` 输出 `page size of 16384 bytes`。
**不是**旧 x86/macOS 的 4096。

错误用 4096 会把空闲内存低估 4 倍：
- 报告 1.37 GB 空闲 → 实际 5.31 GB

## 标准公式

### ❌ 错误: 单取 `Pages free`（v1.0 mem_patrol 踩这个坑）

```bash
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')  # 数字
# → 749 MB，但实际系统有 16.7 GB 空闲
# → 把空闲低估 22 倍 → 误判"紧急" → 误杀 ToDesk + 3 个 Claude Helper
```

**根因**：`Pages free` 是 kernel 主动标记的"完全空闲页"，macOS 会把大量 inactive 页留在那供按需 swap out → 不算进 free。如果脚本只看 `Pages free`，会以为内存紧张。

### ✅ 正确: `free + inactive + speculative` 三项求和

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

**为什么三项**：
- `Pages free` — 完全空闲页，零成本立即可用
- `Pages inactive` — 最近用过但已无引用，**macOS 会按需 swap out**（几乎零成本）
- `Pages speculative` — 已清零但还没回收，**同样可立即用**

**三项相加才是真正的"可用内存"**。Mem Graph/Activity Monitor 顶部那个数字就是这么算的。

### ⚠️ BSD `paste` 在 macOS 上参数顺序反了（v1.0 第二个坑）

```bash
# 错误 (GNU paste 习惯):
free_mb=$(vm_stat | awk '/Pages free|Pages inactive/ {print $3}' | tr -d '.' | paste -sd+ | bc)
# → usage: paste [-s] [-d delimiters] file ...
# → BSD paste 期望 -d 在 -s 前，且 stdin 流行为不同
```

**解决**：所有 macOS 内存计算用 python，别用 BSD paste 拼。`paste -sd+` 在 Linux 写得通，移植到 macOS 直接报错。

### 各类内存（GB）
```bash
vm_stat | grep -E "Pages free|active|inactive|wired|compressor" | awk -F'[:.]' '{
  pages=$2; gsub(/^ */,"",pages); gsub(/\..*$/,"",pages); gsub(/ /,"",pages);
  printf "  %-30s %.2f GB\n", $1, pages * 16384 / 1024 / 1024 / 1024
}'
```

### Swap 使用
```bash
sysctl vm.swapusage
# 输出: total = 2048.00M  used = 646.69M  free = 1401.31M
```

**判断压力**：Swapouts > Swapins 持续为真 → 内存压力。绝对值大不代表压力，要看趋势。

### CPU 负载
```bash
sysctl -n vm.loadavg
# 输出: { 1min 5min 15min }
# 4 核 Mac mini: < 2.5 = 健康；> 4.0 = 紧张
```

### 内存压力
```bash
memory_pressure | head -10
# 需要 sudo 才有完整 page-out stats
```

### 进程 RSS
```bash
ps -A -o pid,rss,command | sort -k2 -rn | head -10
# RSS 单位是 KB，要除以 1024 才得 MB
# mb=$((rss/1024))
```

## 系统服务判断

```bash
# 父进程 = launchd (PID 1) → 系统服务，不杀
ps -A -o pid,ppid,command | awk '$2 == 1 {print}'

# 僵尸进程（STAT = Z）→ 不杀，让父进程回收
ps -A -o pid,stat,command | awk '$2 ~ /Z/ {print}'
```

## 前台窗口检测

```bash
# 当前可见 App
osascript -e 'tell application "System Events" to get name of every process whose visible is true'
# 返回: "Finder, Safari, ..."
```

## 参考

- Apple 官方 vm_stat 文档（man vm_stat）
- Hermes memory 已确认 16384 page size
- 案例 2026-06-04：从 2.97 GB → 4.56 GB 释放验证
- 案例 2026-06-05：mem_patrol v1.0 误杀（"Pages free" 749 MB ≠ 真实空闲 16.7 GB）→ v1.1 改 python 三项求和修好
