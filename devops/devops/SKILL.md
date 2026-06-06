---
name: devops
description: "Mac mini 运维技能：系统健康检查、进程/端口管理、日志清理、资源监控、cron 管理、venv 维护"
triggers:
  - "给hermes来个大体检"
  - "系统健康检查"
  - "内存清理"
  - "清理垃圾"
  - "cleanup/free memory/资源管理"
  - "进程检查"
  - "端口检查"
  - "日志清理"
  - "cron job 管理"
version: 2026-06-06
---

# DevOps — Mac mini 运维技能

## 快速诊断流程（体检清单）

当用户说"体检"/"健康检查"/"清理"/"cleanup"时，按以下步骤执行：

### 第一步：系统大盘（30 秒）
```python
import psutil, subprocess, os
# 内存 + swap + CPU 负载 + 磁盘 + 运行时间
mem = psutil.virtual_memory()
swap = psutil.swap_memory()
load = os.getloadavg()
disk = psutil.disk_usage('/')
```

**阈值**：
- 内存 >80% → 告警
- Swap >50% → 黄色预警
- 磁盘可用 <10% → 告警

### 第二步：核心模块存活
```bash
pgrep -f 'hermes_cli.main gateway'  # ✅ PID
pgrep -f 'hermes_cli.main dashboard'
curl -s http://127.0.0.1:9333/json/version  # Chrome CDP
lsof -iTCP -sTCP:LISTEN -P -n  # 监听端口
```

### 第二步 B：state.db 完整性探测（2026-06-06 新增）
**为什么**：state.db 损坏会直接瘫痪 `session_search`（"database disk image is malformed"），但其它功能照常跑——症状隐蔽。**size 还在 ≠ 完整**。414MB 的 state.db 不保证健康。
```bash
# 必须跑！光看 size 没用
sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;" 2>&1
# ✅ 期望: "ok"
# ❌ 坏: "database disk image is malformed (11)" → 见 references/state-db-corruption-recovery.md

# 同时看 size（异常基线：>200MB 触发人工审视）
ls -la ~/.hermes/state.db
```

**触发场景**：用户说 "session_search 不工作" / "X 昨晚还好" / "X 功能突然没了" → 第一件事就查这个，比查 gateway 优先级更高。

### 第三步：Config 验证
```bash
wc -l ~/.hermes/config.yaml  # 行数检查
wc -l ~/.hermes/.env         # .env 完整性
grep -n 'model:' ~/.hermes/config.yaml  # 检查硬编码
```

### 第四步：清理检查
```bash
ls ~/.hermes/scripts/ | grep -E 'test_|\.bak|_v1|_v2'  # 冗余文件
ls ~/.hermes/skills/*/  # 空目录
du -sh ~/.hermes/logs/*  # 日志大小
```

### 第五步：内存大户
```bash
ps aux --sort=-%mem | head -12
top -l 1 -n 0 -o MEM  # 详细
```

## 清理操作

### 安全清理（无需授权）
1. 删除 `.bak` 备份文件
2. 删除 `test_*.py` 测试脚本（scripts/ 目录下）
3. 删除旧版 `_v1`/`_v2` 变体
4. 删除空壳技能目录（0KB）
5. 删除 `.gz` 日志归档
6. 删除空的 `.log` 文件
7. 删除旧报告 `.md`

### 需要授权
- 删除 Ollama 模型（`ollama rm`）
- 清理 __pycache__
- 删除 venv

## 已知故障模式

### 1. Fallback 模型不可用
**症状**：日志中 `unknown provider 'xxx'` / `Fallback to xxx failed: provider not configured`
**原因**：`fallback_chain` 引用了 `custom_providers` 或 `fallback_providers` 中未注册的 provider name
**修复**：检查 config 中 provider 注册名称与 fallback_chain 是否一致；或检查 `.env` 中 `${VAR}` 是否能被 gateway 加载

### 2. QQBot 频繁超时
**症状**：`WebSocket closed: code=4009 reason=Session timed out` 每 30 分钟一次
**原因**：QQBot API 的 session 30 分钟过期，需要 gateway 自动 rejoin
**修复**：属于 gateway 适配层，需要改源码，不在运维范围

### 3. CDP Chrome 无响应
**症状**：`curl http://127.0.0.1:9333/json` 无输出或 0 tabs
**诊断**：
- `/json/version` 能响应 → CDP 正常，只是没有 tab 注册（正常状态）
- `/json` 返回 0 tabs → Chrome 可能在另一个 Space 上或有极少 tab 打开，**不是故障**
- 两个都无响应 → Chrome 未启动或端口不对
**修复**：Chrome 可能需要重新打开窗口或使用 `--new-window` 启动。验证用 `/json/version` 而不是 `/json`。

### 5. Fallback chain 日志垃圾
**症状**：每 30 分钟 20+ 条 `provider not configured` / `fallback failed` 错误日志，但主模型正常运行
**原因**：`fallback_chain` 引用了不存在的 provider name（未在 `fallback_providers` 或 `custom_providers` 注册）
**修复**：`hermes config set model.fallback_chain ''` 清空（或 `hermes config set model.fallback_chain "[]"` 置空列表）。重启 gateway：`hermes gateway restart`。
**注意**：`fallback_chain` 是 string 类型（YAML 中的逗号分隔 provider name 列表），不是 list。空字符串 `''` 即可。
### 5. Swap 偏高
**症状**：`swap_usage: 58%` 但当前内存压力 <60%
**原因**：历史内存峰值导致 swap 写入，当前不活跃
**修复**：不影响性能可不管；想降 swap 需重启或清理 Ollama

## 参考文件
- `references/hermes-health-check-2026-05-27.md` — 完整 9 步体检流程 + 故障等级 + 修复优先级
- `references/state-db-corruption-recovery.md` — state.db 损坏 3 种恢复路径（2026-06-06 实战）
- `references/skill-broken-invocation.md` — Skill 文件在磁盘但无法调用的诊断流程（两种故障模式：路径错位/缺失 cron）

## 故障模式：Skill 在磁盘但不能调用

**触发场景**：`skill_view` 能加载 SKILL.md，但 CLI 执行失败或 cron 静默不跑。

**两种模式（见 references/skill-broken-invocation.md）：**
1. **路径错位** — `runtime.conf` 指向的路径与实际文件位置不一致（例：last30days 主脚本在根目录而非 `scripts/`）
2. **Cron 丢失** — 技能文件完整但 jobs.json 未恢复（备份/迁移时只存了部分配置）

**快速诊断流程：**
```bash
# 1. 文件在？ ls ~/.hermes/skills/<name>/SKILL.md
# 2. CLI 通？cd ~/.hermes/skills/<name> && python3 scripts/<script> --help
# 3. runtime.conf 对？cat ~/.hermes/skills/<name>/runtime.conf
# 4. 环境变量有？env | grep -i <KEY>
# 5. Cron 有？cronjob(action='list')
```

**注意**：`cronjob(action='list')` 返回 ≠ skill 能跑 — 必须 CLI 烟测通过才算数。

## 诊断实际生效的模型 provider（不只看 config.yaml）

config.yaml 里写的 provider 可能被运行时环境变量或会话覆盖，导致**实际跑的 provider ≠ 配置的 provider**。正确做法：

### 第一步：读 agent.log

```bash
grep 'base_url=.*model=.*provider=' ~/.hermes/logs/agent.log | tail -5
```

找含 `model=<model_name>` 和 `base_url=` 的行，确认实际请求的目标。

### 第二步：API 测试 + 响应头分析

```bash
# 从 config.yaml 提取 provider 的 base_url 和 api_key
# 用 http.client 发请求，关键看响应头
```

**关键响应头**：
| 头名 | 含义 |
|------|------|
| `X-Litellm-Key-Spend` | 实际扣费（0.0=免费） |
| `X-Litellm-Response-Cost-Original` | 模型原成本 |
| `X-Litellm-Response-Cost-Margin-Percent` | 加价百分比 |
| `X-RateLimit-*` 或 `RateLimit-*` | 限流信息（有则有限速/配额） |
| `cf-cache-status` | Cloudflare 缓存状态（MISS=DYNAMIC=实时请求） |
| `Server-Timing` | 后端延迟分解（cfEdge / cfOrigin） |

### 第三步：验证

- 免费模型：`Key-Spend: 0.0` + `Response-Cost-Original: 0.0`
- 受限模型：有 `RateLimit-*` 头 → 记录限额、剩余、重置时间
- 不限流：无 `RateLimit-*` 头 → 不限流（但可能是 soft limit 不暴露头）
- 旧版参考也保留在 `hermes-evolution-context/references/hermes-health-check-2026-05-27.md`
