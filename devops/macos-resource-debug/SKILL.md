---
name: macos-resource-debug
description: macOS (Apple Silicon) 资源/性能诊断 — 内存/CPU/Swap/进程分析、慢响应根因定位、Hermes 进程健康检查。当用户问"卡死了吗"、"为什么慢"、"查内存"、"查CPU"、"卡顿"、"吃内存"、"为什么没反应"、"stuck/slow" 时触发。涵盖单次 vm_stat 抓取、跨 session 并发竞争诊断、按 RSS 排查找隐藏内存大户的标准流程。
triggers:
  - "卡死"
  - "为什么慢"
  - "为什么没反应"
  - "查内存"
  - "查CPU"
  - "吃内存"
  - "卡顿"
  - "stuck"
  - "slow"
  - "检查资源"
  - "mac占用"
  - "内存清理"
---

# macOS 资源诊断与 Hermes 卡顿根因分析

## 何时使用

- 用户在 Telegram/QQ/任何渠道报告"卡死/慢/没反应"
- 用户主动要求查内存/CPU/Swap
- 用户说"系统变卡"
- 同一 session 出现异常延迟（>30s）

**不要**用于：网络问题（用 `hermes-multi-host-debug`），代码 bug（用 `systematic-debugging`）。

## 关键陷阱：Apple Silicon page size 是 16384

**macOS vm_stat 的 page size 在 Apple Silicon (M1/M2/M3/M4) 是 16384 字节，不是 4096。** 用 4096 算会低估内存 4 倍。`memory_pressure` 输出已明确说明 page size。

```bash
# 正确：用 16384 算空闲 GB
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')
python3 -c "print(round($free_pages * 16384 / 1024 / 1024 / 1024, 2))"  # GB
```

| 旧 macOS / x86 | Apple Silicon |
|---|---|
| 4096 | **16384** |
| 1GB ≈ 262144 pages | 1GB ≈ 65536 pages |

`ps -A -o rss` 的单位是 **KB**（注意是 1024，不是字节也不是 page）。

## 关键陷阱：`Pages free` 单值会**严重低估**真实可用内存（2026-06-05 mem_patrol 误杀实战）

macOS 内存压力图顶部那个"可用 XX GB"数字 = `Pages free + Pages inactive + Pages speculative` **三项求和**，不是只看 `Pages free`。`Pages free` 单值经常只有几百 MB（kernel 主动标记的"完全空闲页"），**但 inactive 和 speculative 随时可被 OS 自动回收**，加起来才是真实可用。

**任何拿 vm_stat 算"够不够"做决策的脚本（杀进程/告警/触发清理）都必须用三项求和。** 否则会误判"内存压力"→ 误杀无辜进程。

```python
# 唯一可靠的 macOS 内存计算公式（2026-06-05 mem_patrol v1.1 沉淀）
import subprocess
o = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
PAGE = 16384
def parse(key):
    for l in o.splitlines():
        if l.startswith(key):
            return int(l.split(':')[1].strip().rstrip('.'))
    return 0
avail = parse('Pages free') + parse('Pages inactive') + parse('Pages speculative')
free_mb = (avail * PAGE) // (1024 * 1024)
# 24GB 机器平时 12-17 GB 空闲正常，< 8GB 才算紧张
```

**配套坑**：macOS BSD `paste` 命令的 `-s` / `-d` 参数顺序与 GNU 相反。**`vm_stat | ... | paste -sd+ | bc` 在 macOS 上必报错**（输出 `usage: paste [-s] [-d delimiters] file ...`），算出来是 0，**会让任何以"空闲 < 阈值"为触发条件的脚本立刻误杀**。直接用 python 算，绕开。

**反面案例（2026-06-05 真实发生）**：`mem_patrol.sh` v1.0 用 `Pages free` 单值 + `paste` 算内存，算出 0MB → 触发"紧急"→ 误杀 ToDesk PID 1537 + 3 个 Claude Helper。实际当时系统有 16.7GB 空闲，完全不紧张。完整复现/修复见 `macos-process-lifecycle/references/mem-patrol-v1-bug-20260605.md`。

**杀进程前必走 2 步**：
1. 用上面的 python 公式确认**真实空闲** < 阈值
2. 杀一个 → 重算 → 够了就停（**不要预设"杀完所有候选就够"** — 阈值波动大，循环里少杀几个比多杀安全）

## 标准诊断流程（4 步）

### Step 1: 系统级快照（5 秒）

```bash
# 内存
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')
echo "Free: $(python3 -c "print(round($free_pages * 16384 / 1024 / 1024 / 1024, 2))") GB"
sysctl vm.swapusage  # 一定要看 used vs free

# CPU 负载
sysctl -n vm.loadavg   # 返回 { 1min 5min 15min }
```

判断标准：
- 24GB 机器空闲 < 2GB = 紧张
- Swapouts > Swapins（净换出）= 历史上有过内存压力
- loadavg > CPU 核数 = 有排队

### Step 2: 进程 top 榜（按 RSS 排序）

```bash
# 内存大户（注意 RSS 单位是 KB）
ps -A -o pid,rss,command | sort -k2 -rn | head -10 | awk '{printf "  PID %s: %.0f MB  %s\n", $1, $2/1024, $3}'

# CPU 大户
ps -A -o pid,pcpu,command | sort -k2 -rn | head -8
```

**重点关注**：
- bash-language-server（VS Code LSP，常驻 600MB+）
- mediaanalysisd（系统图片索引，~300MB，不可杀但可重启）
- Chrome Helper Renderer（每 tab 100-200MB）
- Hermes gateway（应 < 400MB）

### Step 3: 慢响应根因（"为什么慢"场景专用）

当用户说"卡死了"，实际可能是"另一个 session 占了模型"，**不要凭直觉说没卡死**：

```bash
# 查 gateway.log 看同一时刻的 session
grep -E "00:35:58|00:36:" ~/.hermes/logs/gateway.log | head -15

# 查 agent.log 看 API call 延迟
grep "API call" ~/.hermes/logs/agent.log | tail -10
# 关键字段：latency=、cache=、api_calls=N
```

**核心判断逻辑**：
- 多个 session 共享一个模型 → API call 排队 → 看起来"卡死"实则正常
- API call latency 5-7s 是 MiniMax-M2.7 正常值，不是卡死
- terminal 跑了 8s+ 不一定是 hang，可能是 grep 大文件

### Step 4: 主动清理动作

按风险从低到高：

| 动作 | 命令 | 释放量 | 风险 |
|------|------|--------|------|
| 杀 LSP 服务 | `kill <bash-language-server-pid>` | 600MB | VS Code 需重新连接 LSP |
| sync 释放缓存 | `sync` | 几十MB | 无 |
| sudo purge | `sudo purge` | 可观 | 需要 sudo |
| 杀 mediaanalysisd | `sudo killall mediaanalysisd` | 300MB | 照片 App 重新索引 |
| 重启 Chrome | `killall "Google Chrome"` | 1-2GB | 所有 tab 关闭，登录态保留 |

**Hermes 自家进程不能杀**：
- `hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace`
- `screen_watcher.py`
- `screen_trigger_handler.py`（30 分钟 cron）

### Step 5: 清理后验证

```bash
# 关键进程守护检查
ps -p <gateway-pid> > /dev/null 2>&1 && echo "✅ Gateway 正常" || echo "❌ Gateway 没了"
ps -p <screen_watcher-pid> > /dev/null 2>&1 && echo "✅ screen_watcher 正常" || echo "❌ 没了"
ps -p <chrome-pid> > /dev/null 2>&1 && echo "✅ Chrome 正常" || echo "❌ Chrome 没了"
```

**不要**杀掉 Hermes 自家进程，会触发 auto-restart 然后留下更多问题。

## 输出格式（用户偏好）

用户偏好结构化对比表（已在多 session 验证）：

```
| 指标 | 清理前 | 清理后 | 变化 |
|------|--------|--------|------|
| 空闲内存 | X GB | Y GB | +Z GB ✅ |
| Swap | ... | ... | ... |
| 关键进程 | 全部存活 | 全部存活 | ✅ |
```

不要长篇解释，**用表格 + 1-2 句结论**。

## Pitfalls

- ❌ 不要假设 page size 是 4096（Apple Silicon 是 16384）
- ❌ 不要假设用户"卡死" = 系统卡死（可能是 model 排队、另一 session 占用、terminal grep 慢）
- ❌ 不要手动 kill `defunct` 进程（父进程会自动回收，强行 SIGCHLD 无效）
- ❌ 不要碰 `mediaanalysisd` 除非用户授权（照片索引会重建，耗 CPU）
- ❌ 不要给 `purged` 数字兴奋（它是历史累计，不是当前可用）
- ❌ **不要看到进程 CPU 高就 kill**——99% 在 idle event loop 是正常的。先 `sample <pid> 2 1` 看 call graph
- ❌ 不要 `launchctl unload` `efilogin-helper`（会卡死系统），用 `pkill -9` 让系统自动重启归 0
- ❌ 不要盲杀 cua-driver（Hermes 桌面控制基础设施），详见 `macos-process-lifecycle/references/cua-driver-idle-pattern.md`
- ✅ swapouts > swapins 是历史值，重启后归零，不要去"清 swap"

## 进程级 CPU 异常诊断（2026-06-04 实战案例）

**用户问**："现在电脑的 CPU 和内存用掉多少了，仔细查一下" → 下一步多半是"这个进程为啥这么高"。

### 步骤 1: 抓 Top 5 CPU 进程

```bash
ps aux -r | awk 'NR>1 {printf "%5.1f%%  %6.1fMB  %s\n", $3, $6/1024, $11}' | sort -rn | head -5
```

### 步骤 2: 判断是否真在干活

**进程 CPU 高 ≠ 进程在干活**。要 `sample` 看 call graph 才知道：

```bash
sample <pid> 2 1 | grep -E "main-thread|thread_start" | head
```

| 主线程/子线程在干啥 | 含义 | 能不能杀 |
|---|---|---|
| 99% `-nextEventMatchingMask:untilDate:inMode:dequeue` | AppKit 事件循环，**正常 idle** | ❌ 不能盲杀 |
| 99% `parking_lot::condvar` 等 | tokio/async 池 idle | ❌ 不能盲杀 |
| 99% 实际业务代码（NSWindow update / VLM 推理） | 真在跑 | ⚠️ 先停任务再杀 |
| 99% 系统调用（`__workq_kernreturn`） | 等系统 | ✅ 可杀 |

### 步骤 3: 已知坑

#### `efilogin-helper` 94% CPU（系统 EFI 登录辅助）
- **症状**：用户空间 PID，名字像系统组件但 CPU 飙到 94%
- **真相**：卡在固件登录流程的某个状态，正常应 < 1%
- **解法**：`pkill -9 efilogin-helper` —— 系统会自动重启它归 0
- **不要**：尝试 `launchctl unload`（会卡死系统）

#### `cua-driver` 45% CPU（Hermes 桌面控制）
- **症状**：Hermes 基础设施进程，平时 45% CPU
- **真相**：99% 时间在 `_pthread_wqthread` 等任务，**不能盲杀**
- **杀前必停任务**：详见 `macos-process-lifecycle/references/cua-driver-idle-pattern.md`
- **30 分钟空闲回收规则**：不能用 cputime delta 判断（cputime 永远在涨），要按 Hermes 工具调用时间戳

#### `WindowServer` / `loginwindow` 高 CPU
- **真相**：GUI 事件循环，**正常**
- **不要**：尝试 kill，杀了会黑屏/退出登录
- ✅ 24GB 机器留 3GB 空闲是健康基线
- ✅ swapouts > swapins 是历史值，重启后归零，不要去"清 swap"

## 复现脚本

详见 `scripts/mac-resource-report.sh` —— 一键跑完上述 4 步，输出结构化报告。

## 全栈体检（大体检）—— 10+ 维度系统健康评估

当用户说"大体检"、"全身体检"、"全面检查"、"system health check"时触发。覆盖硬件、进程、配置、日志、技能库、脚本、平台连接、cron 等 10+ 维度。

### 标准体检流程（10 步）

```
Step 1: 硬件大盘 (内存/CPU/磁盘/进程数/运行时间)
Step 2: 核心模块状态 (Gateway/Dashboard/Chrome/CDP/Redis/Ollama/Clash/平台)
Step 3: 监听端口清单 (lsof -iTCP)
Step 4: 配置检查 (config.yaml 行数/字段合规性/.env keys)
Step 5: 日志分析 (agent.log/errors.log/gateway.log 行数/大小/最近错误)
Step 6: 技能库统计 (数量/大小/空壳目录)
Step 7: 脚本目录 (数量/大小/重复变体)
Step 8: Cronjob 检查 (Hermes cron / launchd plists)
Step 9: 平台连接 (已连的 platform 列表)
Step 10: 汇总评级 + 问题优先级排序
```

### 健康度评级标准

| 评级 | 条件 |
|---|---|
| 🟢 健康 | 核心模块全活, 内存<70%, 无 critical 错误 |
| 🟡 需关注 | 模块正常但某指标偏高 (swap/CDP/技能数/脚本数) |
| 🔴 需修理 | 模块不活/关键 API key 泄漏/关键连接断开 |

### 输出模板

按严重程度排序，每个问题标注等级 + 影响 + 建议：

```
🔴 问题 1: 问题描述
   影响: ...
   建议: ...

🟡 问题 2: ...
   影响: ...
   建议: ...

✅ 做得好的:
   1. ...
```

### 实战经验（2026-06-06 首次体检沉淀）

1. **CDP Chrome 监听但 curl 无响应** — Chrome 可能在 9333 端口监听了但 CDP 协议需要 ws:// 而非 HTTP。不要直接报"CDP 挂了"，用 `curl -s http://127.0.0.1:9333/json/version` 或检查 ws:// 连接。
2. **config.yaml 硬编码 API key** — 用户的 config.yaml 里可能写死了 `sk-xxx`、`nvapi-xxx`，违反 `script-provider-independence` 规则（不写模型/API key）。这是一个常见的配置卫生问题。
3. **Fallback chain 全挂** — `fallback_chain` 里的模型 provider 不在 `fallback_providers` 里注册（或环境变量未注入），会导致 3 次重试后 503。检查 gateway.log 的 `resolve_provider_client: unknown provider` 即可定位。
4. **Scripts 目录臃肿** — 100+ 脚本很常见，其中大量是重复变体（`hermes_web_bot.py` vs `_v2` vs `_cdp` vs `_ws`）。这是"技术债务"类问题，不需要立即修但体检时应该记录。
5. **空壳技能目录** — 0KB 的 skill 目录说明"装了但没内容"或"冗余分类"，超硬约束（30-40 个）时建议清理。

### 配套文件

- 本章节的体检模板：`references/system-health-check-template.md`（一键复制即用）
