# Skills 深度审计记录 — 2026-07-16

## 背景

用户要求「所有技能要一个不落在最前面文件夹」，推动了一次全面深度检查。

## 发现的问题

### 1. `agent-human-level-computer-use/` — 伞包套伞包（depth 3-4）

**来源：** 从 `hermes-export.tar.gz` 的 `engineering/` 目录安装时带入
**结构：**
```
agent-human-level-computer-use/
  SKILL.md                  ← depth=2（自身是 skill）
  apple/                    ← 伞包子分类
    apple-notes/SKILL.md    ← depth=3
    apple-reminders/SKILL.md
    findmy/SKILL.md
    imessage/SKILL.md
  creative/                 ← 同上
    ascii-art/SKILL.md
    baoyu-infographic/SKILL.md
    ...
  autonomous-ai-agents/
    opencode/SKILL.md
  email/
    himalaya/SKILL.md
  github/
    codebase-inspection/SKILL.md
  ...
```

**问题：** 子分类 apple/creative/email 等在本次整理前已全部提升到顶层，这个伞包里的全是冗余副本。同时伞包自身是独立 skill。

**处理：**
1. 将 `agent-human-level-computer-use/SKILL.md` 提升到 `~/.hermes/skills/agent-human-level-computer-use/SKILL.md`（作为独立 skill）
2. 删掉所有冗余子分类（apple/、creative/、email/ 等）
3. 删整个空伞包目录

### 2. `node-inspect-debugger/` — 嵌套副本（depth 3）

**来源：** `hermes-export.tar.gz` 安装时带入
**结构：**
```
node-inspect-debugger/
  SKILL.md                        ← depth=2（正确）
  node-inspect-debugger/          ← 多余层
    SKILL.md                      ← depth=3（副本）
```

**处理：** 删掉嵌套的 `node-inspect-debugger/node-inspect-debugger/` 目录

## 最终验证命令

```bash
# depth>2 违例检查
find ~/.hermes/skills -mindepth 3 -name 'SKILL.md' | grep -v '/.hub/' | \
  grep -v '/.curator_backups/' | wc -l
# 结果为 0 = 无违例

# 有 SKILL.md 的 skill 总数
find ~/.hermes/skills -maxdepth 1 -type d | while read d; do
  [ -f "${d}/SKILL.md" ] && basename "$d"
done | wc -l
# 结果应为 176

# Hermes 在线索引数
hermes skills list 2>&1 | grep -c '│'
```

## 经验总结

1. **来源包中的伞包最危险**：`engineering/` 目录里可能有完整伞包结构，安装时要特别检查
2. **嵌套副本的来源**：从压缩包装入 skill 时，如果 skill 名称和上层目录名相同，容易产生嵌套副本
3. **验证必须用精确 depth 命令**：不能只看 `hermes skills list` 是否正常，因为 depth>2 的 skill Hermes 仍会索引但用户可能搜不到
4. **处理顺序**：先找违例 → 确认伞包来源 → 提升 skill 自身 → 删冗余子目录 → 验证

## 备份

- 原始 skills 备份：`~/.hermes/skills.bak.20260716_173142/`（49 MB）
- 被删伞包副本：`/tmp/skills_orphan_174252/`（504 KB）
