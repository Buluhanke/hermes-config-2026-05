# 两个学习流水线 — 独立暂停/静默指南

> 2026-07-03 生成（用户问"不是暂停了吗"后发现）

---

## 两条独立流水线

| Cron 名称 | 调度时间 | 功能 | 暂停状态 |
|-----------|----------|------|----------|
| `每日skill采集` | 03:00 | 从 hermes-skill-discovery / agentskills.io / GitHub 采 5 个 skill 并安装 | `enabled: false` ✅ 已暂停 |
| `knowledge-miner` | 07:00 | 扫描 GitHub 硬规则 / 中文社区 / 高频词，写入 `~/.hermes/logs/daily_learning_YYYYMMDD.md` | `enabled: true` ⚠️ **还在跑** |

两条流水线**完全独立**：
- 暂停 `每日skill采集` 不影响 `knowledge-miner`
- `knowledge-miner` 没有在 UI 上被暂停过
- 用户说"暂停"时，需要明确说"暂停 knowledge-miner"才能停掉它

---

## 暂停/静默命令

```bash
# 暂停 skill 采集（已暂停）
hermes cron pause 4862dc17ff7e

# 暂停 knowledge-miner（本次未执行）
hermes cron pause c5cad75593ba

# 暂停所有学习类 cron
hermes cron list | grep -E "skill|learning|knowledge|abcd|自学"
```

---

## 零新 → 静默原则（两条流水线都适用）

来自 `proactive-execution` Failure 62：

```
① 本次要检查的数据源自上次运行以来有变化吗？
   - 无变化 → exit 0，不跑 LLM，不写日志，不推任何东西
   - 有变化 → 才跑 LLM / 执行任务

② 如果必须跑脚本（no_agent=true），产出为空 → exit 0，不推送

③ 如果跑 LLM 后产出仍然为零 → 写 fact_store 标记"X已重复N次无变化"
   下次跑时看到这条事实直接跳过
```

---

## knowledge-miner 产出验证

```bash
# 检查最近产出
tail -20 ~/.hermes/logs/daily_learning_*.md

# 检查 cron 历史
hermes cron list | grep knowledge
```

本次（2026-07-03 09:30）：`新增: 0 条` → 按零新静默原则应该 exit 0 但实际每次都写报告推 origin。

---

## 修复方向

knowledge-miner wrapper 脚本（`knowledge_miner_wrapper.sh`）需要加「零新静默」gate：

```bash
#!/bin/bash
# 跑前检查：自上次运行以来有没有变化？
LAST_LOG=$(ls -t ~/.hermes/logs/daily_learning_*.md 2>/dev/null | head -1)
if [ -f "$LAST_LOG" ]; then
  NEW_COUNT=$(grep -c "新增:" "$LAST_LOG" | awk '{print $2}')
  if [ "$NEW_COUNT" = "0" ]; then
    # 无新内容，静默跳过
    exit 0
  fi
fi

# 有变化才跑
python3 ~/.hermes/scripts/knowledge_miner.py 2>&1 | tail -5
```
