---
name: hermes-systematic-audit
description: Hermes 系统性配置与存储审计 SOP — 定期执行，检测配置漂移、孤立文件、路由断裂、存储泄漏。适用于「感觉哪里不对」后的主动排查，或每月的例行清理。触发词：「检查配置 / 审计 / 系统性排查 / 清理Hermes house / hermes哪里有问题 / 检查记忆文件 / 清理垃圾文件」。
---

# Hermes 系统性配置与存储审计 SOP

## 审计分层（从外到内）

### Layer 1：记忆文件路径验证（先确认 Hermes 读哪）
```bash
# Hermes 实际从 ~/.hermes/memories/ 读取（不是 memory/ 不是根目录）
ls -la ~/.hermes/memories/
# 有效文件：MEMORY.md, USER.md, concept_store.md, chrome-cdp-ax-tree.md, idle_learning_log.md
# 如果发现 ~/.hermes/MEMORY.md 或 ~/.hermes/data/MEMORY.md → 旧文件，删除
```

### Layer 2：孤立数据库检查
```bash
# 查所有 .db 文件（排除 Chrome/CodeGraph）
find ~/.hermes -name "*.db" -not -path "*/chrome-*" -not -path "*/Profile*" -not -path "*/GPU*" -not -path "*/.codegraph/*" -exec ls -la {} \;
```
**常见孤立 DB（可安全删除）：**
| 文件 | 特征 | 判断方法 |
|---|---|---|
| `chroma_memory/` | ChromaDB 残留 | config 无 `provider: chromadb` 引用 |
| `memory/fact_store.db` | 旧 SQLite fact 库 | 0 行，已被 LanceDB 替代 |
| `memory/references/` | 27 个旧参考文档 | 无代码引用 |
| `根目录 fact_store.db` | 0 字节空壳 | `ls -la` 确认大小 = 0 |
| `hermes-memory.db` | 0 字节空壳 | 同上 |
| `hermes.db` | 0 字节空壳 | 同上 |

**活跃 DB（不删）：**
| 文件 | 大小 | 最后修改 | 说明 |
|---|---|---|---|
| `state.db` | ~544MB | 今天 | Hermes 主状态库，54652 条消息，正在写入 |
| `sessions.db` | 57KB | Jun 6 | 会话历史 |
| `memory_store.db` | 3.8MB | Jul 5 | self_evolution.sh 事实库，代码活跃引用 |
| `kanban.db` | 114KB | Jul 3 | Hermes 内置任务看板（8表：tasks/task_runs/task_events/task_comments等） |
| `perception_memory.db` | 57KB | Jun 29 | decision_engine.py + perception_health_check.py 活跃引用；element_cache(GUI坐标缓存) + task_recall 表；由 cua-driver 的 GUI 自动化流程调用 |
| `verification_evidence.db` | 40KB | 今天 | file_tools/terminal_tool 验证事件记录（当前 0 条但 schema 正常，属初始空状态） |

### TCC 权限诊断的正确方法（重要勘误）

**⚠️ TCC.db 查询不可靠。** macOS 14+ 将 Screen Recording/Full Disk Access 等权限存在 `/Library/TCC/` 和内存中，TCC.db 里查不到不等于没有权限。**必须用实际功能测试。**

```bash
# Screen Recording（hermes venv python）
/Users/aimac/.hermes/hermes-agent/venv/bin/python -c "
import Quartz
windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
print('窗口数:', len(windows) if windows else 0)
"

# screencapture 测试
screencapture -x /tmp/test.png && echo "ScreenCapture: OK"

# Full Disk Access - 测关键路径
python3 -c "
import os
for p in ['/Library/Mail', '/Volumes', '/System/Library/Extensions', '/private/var/db']:
    try: print('✅', p, len(os.listdir(p)), 'items')
    except: print('❌', p)
"
```

**真正需要 sudo 才能操作的只有** `/etc/sudoers`（root-only）。这是预期行为，无法自己修。

**可删 DB（已验证无引用）：**
| 文件 | 大小 | 特征 | 删除方法 |
|---|---|---|---|
| `response_store.db` | 20KB | 表为空（0 条），accessed_at 全 NULL，无代码引用 | ✅ 直接删（2026-07-06 已删除） |
| `chroma_memory/` | 471KB | ChromaDB 残留，config 无 `provider: chromadb` | ✅ 直接删 |
| `根目录 0 字节空壳` | 0B × 3 | fact_store.db / hermes-memory.db / hermes.db | ✅ 直接删 |

**已删除插件（2026-07-06 确认）：**
| 插件 | 删除原因 |
|---|---|
| `plugins/mnemosyne/` + `mnemosyne/data/`（~500KB） | ✅ 已删除（2026-07-06）— config 未启用 `provider: mnemosyne`，无 cron/skill 引用，最后访问 Jun 29 |

### Layer 3：config.yaml 路由完整性检查
```bash
# 1. 检查 fallback_chain 中所有 provider:model 是否在 providers 里有定义
grep "^fallback_chain:" -A1 ~/.hermes/config.yaml

# 2. 检查 MOA preset 里的 provider key 是否在 providers 段存在
grep -n "provider:" ~/.hermes/config.yaml | grep -v "provider: auto\|provider: $"
# 对比：provider key 必须匹配 providers 段第一行的 key（如 openrouter, groq, glm）

# 3. 检查所有 env var 引用是否在 .env 里有值
grep -oE '\$\{[A-Z_]+\}' ~/.hermes/config.yaml | sort -u
```

**常见 config 断裂模式：**
- MOA preset 引用 `provider: nv-qwen3.5-397b`（不存在）→ 应改为 `provider: openrouter`
- fallback_chain 引用 `ollama-cloud/xxx` 但该 provider 的 base_url 或 api_key 未配置
- 硬编码的旧 PID（891/879/875）在文档里 → 应改为泛指

### Layer 4：活跃插件引用检查
```bash
# 列出 config plugins.enabled
grep -A5 "plugins:" ~/.hermes/config.yaml

# 对每个 enabled 插件，检查目录是否存在
ls ~/.hermes/plugins/<name>/
```

### Layer 5：磁盘占用大户
```bash
du -sh ~/.hermes/.backups/       # staging/ 可能很大（github 备份）
du -sh ~/.hermes/logs/            # 日志 md 文件
du -sh ~/.hermes/state-snapshots/ # 快照
du -sh ~/.hermes/.codegraph/      # 代码图数据库
```

**清理阈值：**
- `.backups/staging/` > 1GB → 评估是否需要（注意：hermes_backup_github_push.sh 有 bug——本地 staging 从不清理，每次跑脚本残留新 chunk，需手动加清理逻辑）
- `logs/*.md` > 100 个 → 合并归档
- `.codegraph/codegraph.db` > 500MB → 可删，会重建

### Layer 6：根目录 .md 污染检查
```bash
ls ~/.hermes/*.md
# 只有 AGENTS.md 和 SOUL.md 是有效的
# 其他 skill_*.md / briefing_*.md / ai_patrol_*.md → 废弃
```

## DB 活跃度验证命令集

**判断 DB 活跃度的标准三连：**
```bash
sqlite3 <db_path> ".tables"
sqlite3 <db_path> ".schema" | head -60
# Python 查时间戳（已知字段名时）
python3 -c "import sqlite3,time; conn=sqlite3.connect('<db>'); ..."
```

详细 TCC 权限现状、LaunchAgents 状态、Unix 时间戳换算见 `references/hermes-permissions-tcc-2026-07-06.md`。

---

## 审计执行流程

1. **Layer 1 先走** — 确认 Hermes 读哪，防止删错活跃文件
2. **Layer 2 其次** — 孤立 DB 是最大磁盘泄漏源
3. **Layer 3 第三** — config 断裂会影响实际路由
4. **Layer 4 第四** — 插件孤立但不一定需要删
5. **Layer 5 最后** — 磁盘大户单独决策
6. **Layer 6 收尾** — 根目录 md 污染

**每次审计后写记忆：**
```
【日期 hermes审计】发现X个问题，已清理Y，剩余Z（决策待定）
```
