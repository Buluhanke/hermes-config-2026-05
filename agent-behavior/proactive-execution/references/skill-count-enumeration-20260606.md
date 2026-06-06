# Skill 库真实数量对账方法 (2026-06-06 实战)

**症状**：用户问"我们有多少 skill"，初看 66 个目录，看着 24 个 `SKILL.md`，习惯性估 "24 个可用"。

**真相**（实测）：**66 个顶层目录** + **40 个是分类目录**（下面挂子 skill）+ 真实 `SKILL.md` 总数 = **176 个**。

**关键误判**：把"没有顶层 SKILL.md" = "空壳"。**但实际是分类目录**（如 `apple/`、`productivity/`、`browser-automation/`），子目录里有真 skill。

## 30 秒对账脚本

```python
import os
from collections import defaultdict

root = '/Users/aimes/.hermes/skills'  # 注意改成你路径
by_top = defaultdict(list)
empty = []

for entry in sorted(os.listdir(root)):
    p = os.path.join(root, entry)
    if not os.path.isdir(p):
        continue
    if os.path.exists(os.path.join(p, 'SKILL.md')):
        by_top[entry].append(entry)
    else:
        # 分类目录：找子目录里的 SKILL.md
        sub_skills = []
        for root_d, _, files in os.walk(p):
            for f in files:
                if f == 'SKILL.md':
                    rel = os.path.relpath(os.path.join(root_d, f), p)
                    sub_skills.append(rel.replace('/SKILL.md', ''))
        if sub_skills:
            for s in sub_skills:
                by_top[entry].append(f"{entry}/{s}")
        else:
            empty.append(entry)

total = sum(len(v) for v in by_top.values())
print(f"顶层分类数: {len(by_top)}")
print(f"SKILL.md 总数: {total}")
print(f"真空壳目录: {len(empty)}")
print()
print("── Top 5 分类（按子目录数）──")
for top, subs in sorted(by_top.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"  {top:30} {len(subs):3} 个 skill")
```

## 关键判断

| 你看到的 | 实际是什么 | 数量级 |
|---|---|---|
| 顶层有 `SKILL.md` | 真 skill | 24 |
| 顶层没 `SKILL.md` + 子目录有 `SKILL.md` | 分类目录 + 子 skill | 40 个分类 + ~150 个子 skill |
| 顶层没 `SKILL.md` + 整个目录递归都没 `SKILL.md` | 真空壳 | 0-5 个 |

**总数**：24 + 150 = **~176 个真 skill**（不是 24 个）

## 何时跑这个脚本

- 用户问 "有多少 skill / 哪些用得上 / 装了啥"
- 写"全部 skill 调研"类任务前（避免漏报）
- `installed-unused-tool-discovery` skill 配套使用
- `skill-library-management` 决策树输入

## 配套

- `installed-unused-tool-discovery` skill — 扫"装了但 0 用"的 skill
- `skill-library-management` — 装/删决策
- `proactive-execution` 规则 27（盲区自扫）

## 反面教材（6/6 凌晨真实事件）

我之前在别的 session 说"我们 24 个真实可用 skill"——**完全错**，实际是 176 个（7.3 倍）。把 40 个分类目录当空壳，**漏报 150+ 个真 skill**。

修正：**任何"盘点 skill"任务，先跑这个对账脚本**，再列清单。
