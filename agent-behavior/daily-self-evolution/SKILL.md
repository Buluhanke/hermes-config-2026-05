---
name: daily-self-evolution
description: Hermes每日自我进化闭环——记忆健康检查+技能沉淀+知识采集
---

# 每日自我进化闭环

## 触发条件
- cron定时：每天9:00
- 主动触发：用户说"进化"、"自检"、"运行进化"

## 执行步骤

### 1. 运行每日进化脚本
```bash
~/.hermes/scripts/daily_evolution.sh
```

会检查：
- MEMORY.md是否超过2200字符（超限自动压缩）
- skill目录统计
- 生成进化日志

### 2. 三文件体系
- **SOUL.md** — 人格定义（专业干练、真人化、主动执行）
- **USER.md** — 用户画像（偏好、雷区、环境）
- **AGENTS.md** — 行为逻辑（闭环优先级、自我反思机制）

### 3. 手动执行（如需）
```bash
# 立即跑一次
~/.hermes/scripts/daily_evolution.sh

# 查看最近日志
ls -t ~/.hermes/logs/ | head -3
```

## 进化闭环
```
每日9:00定时
    ↓
记忆压缩（2200字符限容）
    ↓
fact_store权重检查
    ↓
磁盘空间检查（3大目录监控）
    ↓
技能沉淀统计
    ↓
汇报结果到Telegram
```

### 磁盘健康监控（新增）
Mac mini M4 24GB，磁盘空间需要主动管理。检查以下目录：
```bash
du -sh ~/.hermes ~/Library/Application\ Support ~/Library/Caches 2>/dev/null
```
**预警阈值**：
- `~/.hermes` > 15G → 清理日志和截图
- `~/.hermes/logs/` > 2G → 轮替旧日志
- `~/.hermes/screenshots/` > 1G → 清理超过7天的截图
- `~/Library/Caches` > 15G → 提醒用户清理
- 总空闲 < 5G → 紧急告警

**清理命令**（非破坏性）：
```bash
# 清理15天前的日志
find ~/.hermes/logs -name "*.log" -mtime +15 -delete
# 清理7天前的截图
find ~/.hermes/screenshots -name "*.png" -mtime +7 -delete 2>/dev/null
```
详见 `references/disk-health-reference.md`

## 相关文件
- `~/.hermes/SOUL.md` — 人格定义
- `~/.hermes/USER.md` — 用户画像
- `~/.hermes/AGENTS.md` — 行为逻辑
- `~/.hermes/scripts/daily_evolution.sh` — 进化脚本
- `~/.hermes/logs/` — 每日进化日志
