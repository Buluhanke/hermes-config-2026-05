---
name: abcd-learner
description: Hermes 自主学习系统 — ABCDE五阶段 orchestrator，日志解析，fact入库，skill结晶化。来源：AgentFactory(ACL2026)+cve_lite(Rustchain)。触发：凌晨1点cron自动跑，或 idle_learning_wrapper.sh 手动触发。
entry_file: abcd_learner.py
---

# abcd-learner

## Description

Hermes 自主学习系统的核心 orchestrator。执行五阶段学习循环，把每日运行结果转化为可累积的知识资产。

**Problem Category**: Autonomous learning & knowledge discovery for AI agents
**Trigger**: 每天凌晨 1:00 cron，或手动 `bash ~/.hermes/scripts/idle_learning_wrapper.sh`

## 五阶段闭环

| 阶段 | 内容 | 工具 |
|------|------|------|
| A | 视觉产线进程检查 | `ps aux` |
| B | arXiv 论文扫描（缓存优先） | curl → `~/.hermes/cache/arxiv_papers.json` |
| C | CVE 安全扫描（SSL fallback） | `cve_lite.py scan --severity HIGH` |
| D | action_diversity 执行层检查 | `action_diversity.py` |
| E | Skill crystallizer（fact→skill） | `abcd-learner.py` |
| 后处理 | 日志→fact 动态提取 | `batch_facts_from_log.py` |

## 关键文件

| 文件 | 作用 |
|------|------|
| `~/.hermes/scripts/idle_learning_wrapper.sh` | 入口：五阶段顺序执行 |
| `~/.hermes/scripts/idle_learning_orchestrator.py` | A/B/D 线程并行（5s超时），C/E在wrapper同步 |
| `~/.hermes/scripts/batch_facts_from_log.py` | 解析orchestrator日志→fact写入DB |
| `~/.hermes/scripts/cve_lite.py` | 零依赖CVE扫描（MIT，Rustchain） |
| `~/.hermes/skills/abcd-learner/abcd_learner.py` | Skill crystallizer：fact检索3次→skill |

## 已知坑（每次跑前必查）

1. **CVE SSL EOF**：`ssl.SSLError UNEXPECTED_EOF_WHILE_READING` → cve_lite.py 已加 CERT_NONE fallback
2. **batch_facts 0写入**：FACTS_FROM_LOG 静态列表已饱和 → 依赖ABCD动态提取
3. **线程超时崩溃**：daemon线程超时不设 results[key] → orchestrator 拿None崩溃 → C已移出线程
4. **skill crystallizer 空输出**：retrieval_count < 3 → 需等累积

## AgentFactory 范式（E阶段核心）

当 fact 被检索 ≥ 3 次（retrieval_count ≥ 3）， crystallize 为可执行 skill：

```
fact 内容 + tags → ~/.hermes/skills/fact_<id>_<name>/
  SKILL.md         # 元数据
  <name>.py       # executable stub
```

参考：`references/research.md` / `references/run-log.md`

## 依赖

- `~/.hermes/memory_store.db`（fact_store）
- `~/.hermes/cron/output/idle_learning/*.log`（orchestrator日志）
- OSV.dev API（cve_lite，SSL fallback已处理）
- arXiv API（网络限速，缓存降级）
