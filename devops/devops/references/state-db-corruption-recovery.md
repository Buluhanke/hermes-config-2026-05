---
name: state-db-corruption-recovery
description: 2026-06-06 实战复盘 — state.db 414MB + database disk image is malformed 完整诊断与 3 种恢复路径
---

# state.db 损坏 — 诊断与恢复（实战复盘）

**发生时间**：2026-06-06 上午
**症状链**：用户问 "为什么没去使用这些功能会坏掉？昨晚配置好没问题的呢" → `session_search` 报 "database disk image is malformed" → 进程/端口/CDP 全正常 → 问题被掩盖

## 完整对账表（实测状态）

| 状态 | 项目 | 说明 |
|---|---|---|
| 🟢 正常 | Gateway PID 66063 | 14:47 起的，420MB 内存，正常 |
| 🟢 正常 | Webhook 9888 | 也在跑 |
| 🟢 正常 | Chrome CDP 9333 | 通 |
| 🔴 **坏** | state.db 414MB | "database disk image is malformed (11)" |
| 🟡 部分 | LaunchAgent | 只剩 `weekly-backup.plist` 一个（其它 cron 似乎没起来）|
| ❌ 找不到 | 9222 端口 | 已弃用，配置改用 9333 |

## 根因

state.db FTS5 索引损坏。可能原因：
- 写入过程中断电/强制 kill
- WAL 残骸
- 长期不清理导致 bloat（414MB 异常大，正常应该几十 MB）

## 3 种恢复路径（按风险递增）

### 路径 1：`.recover` 抢救（推荐先试）
```bash
sqlite3 ~/.hermes/state.db ".recover" | sqlite3 ~/.hermes/state_recovered.db
sqlite3 ~/.hermes/state_recovered.db "PRAGMA integrity_check;"
# ✅ 期望: ok
# 414MB 抢救可能耗时 5-15 分钟，丢部分损坏行
```

### 路径 2：直接重命名让 gateway 重建（最快）
```bash
mv ~/.hermes/state.db ~/.hermes/state.db.corrupt.$(date +%Y%m%d)
# gateway 启动时会自动建新的 state.db
# ⚠️ 历史 session 全部清零
```

### 路径 3：从备份恢复（如果有）
```bash
# 看最近的 weekly backup
ls -lat ~/.hermes/backups/ | head -5
hermes_restore_one.sh  # hermes-portable-backup skill 里的一键恢复脚本
```

## 经验法则

1. **先跑 integrity_check 再做判断** — 不要被"size 还在"的假象骗到
2. **414MB 是异常大小** — 任何 state.db > 200MB 都触发人工审视（可能 bloat）
3. **session_search 报错 = state.db 损坏第一信号** — 比 gateway 异常更早暴露
4. **恢复前先 `cp state.db state.db.bak.YYYYMMDD`** — 别覆盖原文件

## 防范（待做）

- 加 `state.db` 每周 integrity_check 到 `scheduled-task-audit`（devops 类）
- 414MB 阈值告警 — 接到 `macos-resource-debug` 流程
- nightly `VACUUM` + `REINDEX` 防止 bloat（待评估对 gateway 写入的影响）
