# macOS `vm_stat` 字段差异与解析模板

## 背景

`vm_stat` 的字段名随 macOS 版本变化，shell 脚本按老字段名匹配会**静默返空**（awk 没匹配上 → 变量空字符串 → 算出来的内存百分比 = 0%，触发假阴性）。这种 bug 不会报错，只会让监控永远不告警。

## 字段差异速查

| 字段用途 | 旧版（≤ macOS 12） | 新版（macOS 13+ / 14+） |
|---|---|---|
| 物理页空闲 | `Pages free:` | `Pages free:` |
| 活跃页 | `Pages active:` | `Pages active:` |
| 非活跃页 | `Pages inactive:` | `Pages inactive:` |
| **已锁定页** | **`Pages wired:`** | **`Pages wired down:`** ← 字段名变了 |
| 压缩存储 | `Pages occupied by compressor:` | `Pages stored in compressor:`（新版可能没这字段） |

**page size 始终 = 16384 字节**（Apple Silicon 不变）。

## 内存占用 % — 兼容解析（bash）

公式：`used / total × 100`，其中 `used = (active + wired) × 16384`，`total = (free + active + inactive + wired + compressed) × 16384`。

```bash
vmstat=$(vm_stat 2>/dev/null)
p_free=$(echo "$vmstat" | awk '/Pages free:/ {gsub(/\./,"",$3); print $3+0}')
p_active=$(echo "$vmstat" | awk '/Pages active:/ {gsub(/\./,"",$3); print $3+0}')
p_inactive=$(echo "$vmstat" | awk '/Pages inactive:/ {gsub(/\./,"",$3); print $3+0}')
p_wired=$(echo "$vmstat" | awk '/Pages wired down:/ {gsub(/\./,"",$4); print $4+0}')
p_compressed=$(echo "$vmstat" | awk '/Pages stored in compressor|Pages occupied by compressor/ {gsub(/\./,"",$NF); print $NF+0; exit}')
p_compressed=${p_compressed:-0}
page_size=16384
total=$(( (p_free + p_active + p_inactive + p_wired + p_compressed) * page_size ))
used=$(( (p_active + p_wired) * page_size ))
pct=$(( used * 100 / total ))
```

## CPU 占用 — load average 归一化

```bash
# 1-min load average / 逻辑核数 × 100
# 比 ps 累加更稳定（不抖动），更能反映"系统卡顿"
cores=$(sysctl -n hw.logicalcpu)
load1=$(sysctl -n vm.loadavg | awk '{print $2}')
pct=$(awk -v l="$load1" -v c="$cores" 'BEGIN { if (c>0) printf "%d", (l/c)*100; else print 0 }')
```

## 关键坑

1. **`set -u` + awk 空匹配 = 崩**：`print $3+0` 让 awk 在没匹配时返 0，避免下游 unbound variable。**或直接拿掉 `set -u` 改用 `set -o pipefail`**——vm_stat 解析是 I/O 重外部命令，不适合 strict mode。
2. **awk 字段索引随字段名变**："Pages wired down" 是第 **4** 个字段（不是第 3）——多了个 "down" 词。直接看 `vm_stat | cat -A` 确认空格数最稳。
3. **`gsub` 后必须 `+0`**：`gsub(/\./,"",$3)` 只去点号，`$3+0` 强制转数字。少了 `+0` 时字符串做算术会得到奇怪的 0。
4. **压缩页字段可能不存在**：新 macOS 不一定有 compressor 字段，必须 `${p_compressed:-0}` 兜底。直接写 `awk` 找不到会静默返 0（这里 OK），但有 `set -u` 就会崩。

## 验证

跑完解析后用 `Activity Monitor` 或 `top -l 1` 对比——24GB Mac mini 满载时 `wired` 通常 300-400K pages，活跃 `active` 400-600K pages，相加 / 24GB ≈ 70-85%。如果脚本算出来 < 5%，基本就是字段没匹配上。

## 实测现场

2026-06-05 Mac mini M4 24GB 空闲状态：
- `Pages free: 68052`（≈ 1.04 GB）
- `Pages active: 553100`（≈ 8.4 GB）
- `Pages inactive: 495479`（≈ 7.6 GB）
- `Pages wired down: 331834`（≈ 5.1 GB）
- 无 compressor 字段
- → 内存占用 ≈ (553100 + 331834) / (68052 + 553100 + 495479 + 331834) = **46%**

## 相关

- 完整监控脚本模板：`templates/resource_monitor.sh`
- 自动定时监控模式（SOP）：`mac-resource-cleanup/SKILL.md` 的"自动定时监控"节
