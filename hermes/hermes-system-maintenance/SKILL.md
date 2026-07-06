---
name: hermmes-system-maintenance
description: 系统级维护与演化技能——配置审计、内存架构理解、备份维护、磁盘健康管理。覆盖 config.yaml 各层配置含义、memory 文件架构、db 文件存活判断、备份脚本维护。用于定期自检和配置迭代。
author: Hermes
---

# Hermes System Maintenance

## 记忆文件架构（最重要！）

**`get_memory_dir()` 源码确认路径：** `~/.hermes/memories/`

```python
# tools/memory_tool.py line 55
def get_memory_dir() -> Path:
    return get_hermes_home() / "memories"
```

Hermes 读的是 `~/.hermes/memories/MEMORY.md` 和 `USER.md`，**不是** `memory/MEMORY.md`（不存在），**不是** 根目录的 `MEMORY.md`（旧文件）。

活跃文件（2026-07 清理后）：
- `memories/MEMORY.md` — 系统技术记忆
- `memories/USER.md` — 用户偏好铁律
- `memories/concept_store.md` — 语义经验规则
- `memories/chrome-cdp-ax-tree.md` — CDP 技术文档
- `memories/idle_learning_log.md` — 历史学习归档

废弃文件（已清理）：
- `~/.hermes/MEMORY.md`（旧）
- `~/.hermes/USER.md`（旧）
- `~/.hermes/data/MEMORY.md`（旧）
- `~/.hermes/memory/`（整目录已删除，含 fact_store.db + references/）

## Skills 目录审计（重要！）

skills/ 目录下常见三类问题：

### 1. Dead Symlinks（最常见！）
```bash
# 检测所有断链符号链接
find ~/.hermes/skills -maxdepth 2 -type l 2>&1 | while read l; do
  target=$(readlink "$l")
  if [[ ! -e "$target" ]]; then
    echo "DEAD: $l -> $target"
    rm "$l"  # 直接删除，无需确认
  fi
done
```

常见原因：技能是从 `~/.agents/skills/` 符号链接过来的，但那个目录已被删除。

### 2. Dead symlinks in .archive/
```bash
find ~/.hermes/skills/.archive -type l 2>&1 | while read l; do
  target=$(readlink "$l")
  if [[ ! -e "$target" ]]; then rm "$l"; fi
done
```

### 3. SOUL.md / AGENTS.md 内容重叠
SOUL.md（身份宣言）如果和 AGENTS.md（行为规则）内容大量重复会导致 AI 困惑。
- SOUL.md 应只保留：**身份定位、数字人宣言、工具栈、主宰边界**
- AGENTS.md 应包含：**行为准则、工作流规则、铁律、触发词**
- 重复的章节（如"行为准则"出现两次）应合并到 AGENTS.md

## Config 审计分层检查法

对任何 config.yaml 问题，按此顺序验证，避免误删活跃文件：

### Layer 1: 活跃插件判断
```bash
grep -A3 "plugins:" ~/.hermes/config.yaml
# plugins.enabled 列出的才是真正激活的
```

### Layer 2: DB 文件存活判断（不能只看大小）
```bash
# 1. 最后修改时间
stat -f "%Sm %z %N" ~/.hermes/state.db

# 2. 是否被代码引用
find ~/.hermes/hermes-agent/plugins/ ~/.hermes/hermes-agent/tools/ \
  -name "*.py" | xargs grep -l "kanban|memory_store|mnemosyne" 2>/dev/null

# 3. 表结构验证
sqlite3 ~/.hermes/kanban.db ".tables"
```

### Layer 3: 活跃 db 文件清单（2026-07 实测）
| db | 大小 | 状态 | 用途 |
|---|---|---|---|
| `state.db` | 543MB | ✅ 活跃 | Hermes 消息历史/sessions |
| `memory_store.db` | 3.8MB | ✅ 活跃 | self_evolution.sh 事实库 |
| `kanban.db` | 114KB | ✅ 活跃 | Hermes 内置 kanban（8表） |
| `sessions.db` | 57KB | ✅ 活跃 | Hermes session 存储 |
| `verification_evidence.db` | 40KB | ✅ 活跃 | file_tools/terminal_tool |
| `mnemosyne/data/mnemosyne.db` | 475KB | ✅ 活跃 | memory 插件 |

### Layer 4: 备份脚本 staging 清理 bug
详见 `references/backup-script-bug-20260706.md`

## 备份脚本维护铁律

备份脚本修改后**必须同步添加清理逻辑**，否则 staging 目录会持续膨胀。
关键变量：`KEEP_VERSIONS=4`（远程保留 4 个分支，本地保留 4 个时间戳目录）

## 用户偏好：修复优于删除

执行维护任务时优先修复而非删除：
- 能修的 bug 就修（脚本逻辑错误 → 修脚本）
- 能合并的文件就合并（重复日志 → 合并后清旧）
- 删除仅用于：0 字节空壳、明显废弃文件、已确认无引用且无价值的残留

## Config.yaml 常见陷阱

1. **MOA preset provider key**：必须是在 providers 里定义过的 key，不能是模型别名
   - ✅ `provider: openrouter`（已定义）
   - ❌ `provider: nv-qwen3.5-397b`（不存在，fallback 会静默失败）

2. **所有 provider key 必须在 providers 定义段有实际条目**，fallback_chain 只是引用链

3. **config 备份：只保留最新 2 个**，其余删除
   ```bash
   ls -t ~/.hermes/config.yaml.bak* | tail -n +3 | xargs rm
   ```

## 相关参考文档
- `references/audit-checklist-20260708.md` — 2026-07-08 手动审计发现的问题清单和清理命令
