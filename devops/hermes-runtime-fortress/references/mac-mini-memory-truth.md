# Mac mini 24GB 内存字段真实含义（2026-06-28 实测）

## vm_stat 输出字段对照

```
Mach Virtual Memory Statistics (page size of 16384 bytes)
Pages free:                          136035.      # 真空闲（页数）
Pages active:                        625756.      # 正在用（不可回收）
Pages inactive:                      597239.      # 已用但可回收 ← 关键
Pages speculative:                    30341.
Pages throttled:                          0.
Pages wired:                            28.      # ⚠ macOS 26 这里读不准
Pages purgeable:                        92.
"Translation faults":         12345678901.
"Pages copy-on-write":         123456789.
"Pages zero filled":           123456789.
"Pages reactivated":                 12345.
"Pages purged":                    1234567.
"File-backed pages":                 12345.
"Anonymous pages":                  123456.
```

**单位换算**: pages × 16384 bytes / 1024^3 = GB

## 关键概念

### Pages free ≠ 可用内存

`free` 只是"真空闲、未被任何东西用"。但 macOS 的 inactive 是**已用但可回收**——这部分可以快速被新进程复用。

**所以**:
- 看 `free` 数值小（1-2GB）≠ 内存爆了
- 看 `free + inactive` 才接近"理论最大可用"

### Pages inactive 的角色

类似 Linux 的 page cache / buff/cache:
- macOS 用 inactive 缓存最近访问过的文件页
- 新进程需要内存时，macOS 自动从 inactive 回收（毫秒级）
- 用户感知是"内存一直被吃光"——其实不是

### Pages wired 在 macOS 26 的坑

老版本叫 `Pages wired`，macOS 26 变成 `Pages wired down`。
很多脚本（包括早期版本的 memory_watchdog.py）读 wired=0，导致计算 used 偏低。

**修法**: 不依赖单一字段，用 `active + wired + compressed` 兜底。

## 正确计算可用内存

```python
import subprocess

def get_memory_state():
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    state = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            try:
                pages = int("".join(c for c in v if c.isdigit()))
                state[k.strip()] = pages * 16384 / 1024 / 1024 / 1024  # GB
            except: pass

    free = state.get("Pages free", 0)
    active = state.get("Pages active", 0)
    inactive = state.get("Pages inactive", 0)
    wired = state.get("Pages wired", 0) + state.get("Pages wired down", 0)
    compressed = state.get("Pages occupied by compressor", 0)

    used = active + wired + compressed       # 真实占用
    available = free + inactive              # 理论可用
    used_pct = used / 24.0 * 100             # 24GB 总内存

    return {"free": free, "active": active, "inactive": inactive,
            "wired": wired, "compressed": compressed,
            "used": used, "available": available, "used_pct": used_pct}
```

## 实测数据（2026-06-28 24GB Mac mini）

| 场景 | used | available | used% |
|---|---|---|---|
| 空闲（开机） | ~5GB | ~17GB | ~20% |
| Chrome 5 tab + Ollama 加载 | ~12GB | ~10GB | ~50% |
| Chrome 5 tab + Ollama + Claude | ~17GB | ~5GB | ~70% |
| 危险线 | 18GB | 4GB | 75% |
| 临界线 | 20GB | 2GB | 85% |

## Swap

macOS 在内存满时会用 SSD 当 swap（`dynamic_pager`）。
Swap 一旦开始用，**性能立刻崩**（SSD 读写 100-1000x 慢于 RAM）。

**健康状态**: `sysctl vm.swapusage` 显示 `used = 0.00M`。

## 内存压力命令（GUI 等价）

```bash
# 终端看内存压力（与活动监视器一致）
top -l 1 -s 0 -n 0 | head -10 | grep PhysMem

# 输出示例: PhysMem: 10G used (2.5G wired), 7.5G unused.
# 这里 inactive 被算进 "used"，所以读起来吓人
```

## 推荐工具

- **活动监视器** → 内存标签，看"已使用的交换"（非零就危险）
- **iStat Menus** → 实时监控 + 内存压力圆环
- **`memory_pressure`** 命令（macOS 自带，给出"系统级"压力评估，比 raw vm_stat 准）

```bash
memory_pressure
# 输出: System-wide memory free percentage: 35%
#       System-wide memory status: 1 (warning)
#       System-wide memory page-in count: 12345
```

status: 1 = warning, 2 = critical, 4 = normal. **warning 出现就该手动查**。