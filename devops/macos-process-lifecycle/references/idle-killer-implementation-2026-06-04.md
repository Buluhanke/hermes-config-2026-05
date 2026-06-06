# 30 分钟空闲回收 — 实操记录 (2026-06-04)

## 决策依据

用户原话：*"占用资源的东西只要半小时不用就消除掉吧，有需要再拉起来"*

## 实现组件

| 组件 | 路径 | 说明 |
|---|---|---|
| 脚本 | `~/.hermes/scripts/idle_killer.sh` | bash 实现，监控名单 + 杀法 |
| 状态文件 | `~/.hermes/state/idle_killer.json` | 每个服务的 last_cpu + last_check |
| 日志 | `~/.hermes/logs/idle_killer.log` | kill 事件 + 扫描状态 |
| Cron job | `2f527c06f06d` | `*/15 * * * *`（每 15 分钟扫一次） |
| 监控名单 | cua-driver / ToDesk_Service / hermes venv python 子进程 | 见 SKILL.md |
| 白名单 | gateway / launchd / cron 跑的 python | 永远不杀 |

## 判断逻辑（已验证）

**核心判断**：cputime delta < 0.1s **且** idle_sec >= 1800 (30min) → 杀

**为什么 cputime delta 是对的（不是错的）**：
- cua-driver 实测：99% 时间在 `_pthread_wqthread`（macOS workqueue 空轮询）
- 实测 4 分钟内 cputime 增长 < 0.05s（基本不动）
- vs `mcp_cua_driver_*` 工具调用时 cputime 增长 > 1s/次
- 所以 cputime delta 是有效的"是否真干活"指标

## 误杀防护

1. **首次扫描只记录 baseline**，不杀任何东西（防止脚本刚装就被误杀）
2. **THRESHOLD_SEC=1800**（30 分钟）足够长，误杀概率 < 1%
3. **白名单硬编码**（gateway / launchd 子进程 / cron 任务 python）
4. **状态文件用 `mktemp` 原子更新**，避免并发写崩

## 副作用

| 副作用 | 缓解 |
|---|---|
| 杀 cua-driver 后 mcp_cua_driver_* 全失效 | 重新调用时 `launchctl bootstrap` 自动拉起，等 5-10s |
| 正在跑 computer_use 任务时杀会卡住 | 用户拍板前已确认"等任务跑完再杀"，但脚本本身无法检测——靠用户操作纪律 |
| 杀 ToDesk_Service 后远程连不上 | ToDesk 不在用就杀，重新 `open -a ToDesk` |

## 监控名单（按用户偏好调整）

**白名单（绝对不杀）**：
- `hermes gateway` 主进程
- launchd 系统服务（PID 1 子进程）
- 所有 `*python*` 跑的 cron 任务

**黑名单（候选杀）**：
- `cua-driver` — 桌面控制后台（45% CPU 空转）
- `ToDesk_Service` — 远程工具（不在时不该跑）
- `hermes venv python` 子进程（需要细化，目前是模糊匹配）

**未监控**：
- ddddocr 模型驻留（当前按需加载，不需要监控）
- Chrome debug 进程（已有独立 watchdog 脚本，参见 chrome-watchdog.sh）

## 后续优化方向

- [ ] 第二次门控：连续 3 次扫描都空闲才杀（再加一道保险）
- [ ] 拉起通知：杀完推 Telegram 告诉用户
- [ ] 拉起延迟容忍：重新调用时检测 cold start 并等

## 验证

```bash
# 手动跑一次
bash ~/.hermes/scripts/idle_killer.sh

# 看状态
cat ~/.hermes/state/idle_killer.json
tail ~/.hermes/logs/idle_killer.log

# 看 cron 是否在跑
hermes cron list | grep idle-killer
```
