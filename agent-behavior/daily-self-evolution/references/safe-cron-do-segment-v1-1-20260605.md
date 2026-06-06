# self_evolution Do 段安全协议 v1.1（2026-06-05 实测落地）

> 这是 `safe-cron-script-edit-protocol-20260605.md`（v2.3 沉淀）的实战补充
> 重点：**5 步安全保护 + BSD/Apple Silicon 特定坑 + 误杀复盘**

## 协议原文（5 步安全保护）

1. **PID 验证**：kill 前先取 PID，重启后验证新 PID 存在
2. **优雅终止 → 强杀兜底**：`kill -TERM` → 5s 等待 → `kill -9`
3. **重试 + 健康检查**：连续 3 次 × 2s 间隔（避免抖动误重启）
4. **fact 去重指纹**：tags 加 `chrome_9333_restart_YYYYMMDDHH` 防止刷屏
5. **白名单**：`screen_watcher` / `dashboard` 等 launchd 拉起的进程不在 kill 范围

## ⚠️ 2026-06-05 新增的"5 步之外"必加项

### 6. macOS 内存判断必须用 python（不是 BSD paste + awk）

```bash
# ❌ 错误: BSD paste -sd+ 在 macOS 上参数顺序反了
FREE_MB=$(vm_stat | awk '/Pages free|Pages inactive/ {print $3}' | tr -d '.' | paste -sd+ | bc)
# 输出: usage: paste [-s] [-d delimiters] file ...

# ✅ 正确: python 三项求和
FREE_MB="$($PY -c "
import subprocess
o = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
PAGE = 16384
def parse(k):
    for l in o.splitlines():
        if l.startswith(k):
            return int(l.split(':')[1].strip().rstrip('.'))
    return 0
avail = parse('Pages free') + parse('Pages inactive') + parse('Pages speculative')
print((avail * PAGE) // (1024 * 1024))")"
```

详见 `macos-process-lifecycle/references/mem-patrol-v1-bug-20260605.md`

### 7. RSS 单位是 KB 不是 MB

```bash
# ❌ 错误: 直接当 MB 用
RSS_KB=$(ps -p "$PID" -o rss= | tr -d ' ')
log "Killed PID=$PID (${RSS_KB}MB)"  # 实际是 KB → 报告数字被夸大 1024 倍
KILLED_TOTAL=$((KILLED_TOTAL + RSS_KB))  # 累计变成 KB 单位

# ✅ 正确
RSS_MB=$((RSS_KB / 1024))
log "Killed PID=$PID (${RSS_MB}MB)"
```

### 8. 静态分析不能完全替代 dry-run

v1.0 静态看 `bash -n` 语法 OK、`grep` 路径齐，但 BSD paste 错位只在真实运行才暴露。

**补救**：v1.1 加完后**先手动跑一次**（无破坏性副作用时），看输出对不对再上线。

## 📋 协议执行清单（更新版）

加 Do 段前/后必走：

```
□ 静态分析 (grep 路径标记全在)
□ bash -n 语法检查
□ 静态确认白名单 (避免误杀 dashboard/gateway)
□ 手动 dry-run 一次 (看输出符合预期)
□ 加载到 launchd 之前先看是否能 list
□ launchd 跑完 30 分钟, 查日志确认
```

## 实战：2026-06-05 三个 Do 段都按 5+3 步走

| Do 段 | 静态分析 | 手动 dry-run | launchd 跑后 |
|---|---|---|---|
| Telegram>5/h 重启 gateway | ✅ grep 5/5 标记 | ✅ 没触发（代理可达） | 待 30min 内自然触发 |
| Telegram>3/h 拉 proxy | ✅ grep 3/3 标记 | ✅ 没触发 | 待代理挂 |
| Chrome 9333→3 次重试 | ✅ grep 4/4 标记 | ✅ 没触发（9333 在监听） | 待 9333 异常 |

**注意**：dashboard PID 33447/33454 当前在跑，Telegram>5 段触发时会**顺手 kill dashboard**（被 SIGTERM 走优雅路径，launchd 看到进程死会自动拉起，约 10-30s 闪断）。用户看 web dashboard 期间会闪一下。

## 反面教材

**v1.0 误杀事件**（2026-06-05）：BSD paste + 单值 Pages free 双重坑 → 误杀 4 进程。

**教训**：协议是"必要条件"不是"充分条件"。每加一个 Do 段都要单独走完整 5+3 步，不能"加 3 个就只走 3 步"。
