---
name: installed-unused-tool-discovery
description: |
  定期扫系统里"装了但没用过"的工具/库/skill, 主动给用户呈现"是不是该激活" — 而不是用户问起来才发现盲区。
  6/5 SearXNG/DDGS 盲区就是这个类的: 装在系统里, 没用过, 知识库里"知道名字不知道用法"。
  Use when: hourly/daily 巡检 / 用户问"XX 你知道怎么用吗" / 评估 hermes 工具覆盖 / 工具盘点。
version: 1.0.0
triggers:
  - "装了没用"
  - "盲区扫描"
  - "工具盘点"
  - "installed but unused"
  - "didn't know how to use"
---

# 已装未用工具发现 — 防止盲区累积

## 根案例 (6/5 踩的)

Y Y 问"你是不是也不知道 SearXNG 和 DDGS 聚合搜索", 我承认:
- `/opt/homebrew/bin/searxng` 装了 (Python 脚本, MCP server)
- `ddgs 9.14.2` 装了 (Python CLI 库)
- `anysearch` skill 装了
- **都没用过, 不知道真用法**

**这是典型盲区**: "知道名字 + 知道大致功能" ≠ "知道怎么用"。**装在系统里 ≠ 知识库有真用法**。

## 主动扫描机制

### 1. 工具发现命令 (用 venv 里所有可执行 CLI)

```bash
# 列出 venv + 系统 + brew + npm 装的可能相关工具
ls ~/.hermes/hermes-agent/venv/bin/ | grep -E "^-rwx" | head
which -a ddgs anysearch searxng SearXNG ddg ddgr 2>/dev/null
npm list -g --depth=0 2>/dev/null | grep -iE "mcp|search"
brew list 2>/dev/null | head
```

### 2. 关键过滤: 装了但 0 次调用

```bash
# pip 装的, 但 hermes 没用过
~/.hermes/hermes-agent/venv/bin/python -c "
import importlib, pkgutil, sys
importlib.invalidate_caches()
# 简单版: 跟 main hermes import 对比
import hermes
hermes_mods = set(sys.modules)
# 这个不准, 真正的"用了什么"得查 .usage.json
"
# 实际更准: ~/.hermes/skills/.usage.json (skill 调用统计)
grep -E "\"uses\":\s*0" ~/.hermes/skills/.usage.json 2>/dev/null
```

### 3. 给用户报告模板

```
【盲区扫描 — YYYY-MM-DD】
• 装了 0 次用的 skill: <list>
• 装了 0 次用的 venv CLI: <list>
• 装了 0 次用的 brew formula: <list>
• 装了 0 次用的 npm MCP: <list>
建议激活的: <top 3>
```

## 接入位置 (建议)

- **hourly self_evolution 段**: 加 "盲区扫描" 段, 发现就写 fact (tag=blind_spot, trust=0.4)
- **daily_health_check 末尾**: 给用户列 "今天有 N 个装了没用的工具, 建议激活"
- **手动 trigger**: 用户问"XX 你知道怎么用吗"时, **先跑盲区扫描**再答

## 关键经验 (6/5 验证)

- **真盲区**比"不知道"更危险: 用户问"XX 是不是你也不知道"是**高价值信号**, 不要装懂
- **回答模板**: "知道名字知道大致功能, 没用过" + "装在哪 + 命令" + "现在要不要接"
- **让用户选**: 别自作主张接, 让用户在 daily_health 里看到候选, 自己拍

## 接入后预期效果

- 从"用户戳我才发现盲区" → "我主动告诉用户有哪些盲区"
- 评分增量: +0.3-0.5 分 (覆盖广度, 不止"会用得多")

## 相关引用

- `references/scan_commands.md` — 各场景的扫描命令清单
- `references/mcp-audit-2026-06-05.md` — 13 MCP 包盘点实录（npm 装了不等于 Hermes 配了）

## MCP 特殊审计 (6/5 新增)

MCP 包是**双盲区**的：

| 盲区层 | 怎么查 | 怎么暴露 |
|---|---|---|
| npm/pip 装没装 | `npm list -g \| grep -i mcp` / `pip3 list \| grep -i mcp` | `which mcp` 应该存在 |
| **Hermes 配没配** | `grep -A 3 'mcp_servers:' ~/.hermes/config.yaml` | **关键差异**：包在 ≠ 框架能用 |
| 包名是不是真存在 | `npm view <name> version` / `pip show <name>` | **关键差异**：猜的包名 ≠ 真的包名 |

**根案例 (6/5 22:30)**:
- 用户问"看看有没有可用的 mcp" → agent **被安全闸 BLOCKED**, 改用训练数据回答
- 推荐 filesystem / git / http fetch 三个 → 实际 filesystem **已装但未配**, git 不知道是不是真叫 mcp-server-git, **fetch 包名 agent 编的** (`mcp-server-fetch` 不是真包)
- 用户回"你仔细查一下" → 才 `npm list -g` 查到真相

**MCP 审计 4 步** (耗时 ~10 分钟):

```bash
# 1. npm 全局 MCP
echo "=== npm -g MCP ==="; npm list -g --depth=0 2>/dev/null | grep -iE "mcp|@modelcontext"

# 2. pip 全局 MCP / SDK
echo "=== pip MCP ==="; pip3 list 2>/dev/null | grep -iE "mcp|fastmcp"

# 3. Hermes 实际配的 MCP
echo "=== hermes config mcp ==="; grep -A 20 'mcp_servers:' ~/.hermes/config.yaml

# 4. 验证每个包"装了且真存在"
for pkg in @modelcontextprotocol/server-filesystem mcp-chrome-bridge mcporter; do
  npm view "$pkg" version 2>/dev/null && echo "$pkg: real package" || echo "$pkg: NOT IN REGISTRY"
done
```

**给用户的 4 态报告**（每个 MCP 必须落在 4 态之一）:

| 状态 | 含义 | 该怎么办 |
|---|---|---|
| ✅ 已装 + 已配 | npm 在 + Hermes config 在 | 直接用 |
| ⚠️ 已装 + **未配** | npm 在 + Hermes 不知道 | 配 5 行 config.yaml |
| ❌ **未装** + 真包 | registry 里有 | `npm i -g` 装 |
| ❓ 未装 + **不确定** | 名字是我编的 / 不知道 | **先查** registry 再说 |

## Anti-patterns
- 推荐时**只列名不查 registry** (我编的 `mcp-server-fetch`)
- 把"npm 装在全局"和"Hermes 配好可用"混为一谈
- 跳过第 4 步 — 不查 registry 就断言"装上能用"

## 已知案例（2026-06-06 实战）— Skill 总数重数方法论 bug

### 触发场景
6/6 00:18 做"全部 skill 调研"任务，**先估 24 个**（昨晚 22:00 旧数据），**实测 176 个**——**误判 7.3 倍**。

### Bug 根因
原方法（"看顶层 `SKILL.md` 是否存在"）：
```bash
for d in .hermes/skills/*/; do
  if [ -f "$d/SKILL.md" ]; then
    REAL_SKILLS=$((REAL_SKILLS+1))
  else
    EMPTY_DIRS=$((EMPTY_DIRS+1))
  fi
done
```
**漏数**了**分类目录里嵌套的真 skill**（如 `apple/apple-notes/SKILL.md`）。

### 正确方法（递归）

```bash
# 真实 skill 总数（含分类目录下嵌套的）
find ~/.hermes/skills -name "SKILL.md" -type f | wc -l

# 顶层 skill 目录数（含分类目录）
find ~/.hermes/skills -maxdepth 1 -mindepth 1 -type d | wc -l

# 分类目录数（顶层无 SKILL.md 但子目录有）
find ~/.hermes/skills -maxdepth 1 -mindepth 1 -type d -exec sh -c \
  '[ ! -f "$1/SKILL.md" ] && find "$1" -name "SKILL.md" -type f | head -1 | grep -q . && echo "$(basename "$1")"' _ {} \;
```

### 4 态对账表（skill 调研必给）

| 状态 | 含义 | 例子（6/6 00:18 实测）|
|---|---|---|
| ✅ 顶层 skill | `~/.hermes/skills/<name>/SKILL.md` 存在 | `anysearch/SKILL.md` |
| ✅ 分类目录含 skill | 顶层无 SKILL.md，但 `<dir>/<sub>/SKILL.md` 存在 | `apple/apple-notes/SKILL.md` (6 个真 skill 在 `apple/` 下) |
| ⚠️ 分类目录但子目录全空 | 顶层无 SKILL.md，子目录也无 SKILL.md | `communication/email-drafter/SKILL.md` (1 个，但 `communication/` 顶层无) |
| ❌ 真空壳 | 顶层 + 子目录全无 SKILL.md | `gaming/` 整组（pokemon-player 等都没 SKILL.md） |

### 报告模板（skill 调研）

```
【Skill 调研 — YYYY-MM-DD】
- 顶层 skill 目录: N (含 M 个分类目录)
- 真实 SKILL.md 总数: X (用 `find ... -name SKILL.md | wc -l`)
- 按 4 态分:
  • ✅ 顶层 skill: <count>
  • ✅ 分类目录含 skill: <count>（聚合 Y 个真 skill）
  • ⚠️ 分类目录但子目录空: <count>
  • ❌ 真空壳: <count>
- 误判提醒: 之前估 Z, 实测 X, 差异 ±W 倍
```

### 触发条件

- 用户问"全部 skill 调研" / "skill 总数" / "skill 列表"
- 任何"盘点"类任务开始前
- 旧数据 > 24 小时（很可能过期）

### 教训

- **递归才数得全**——顶层 SKILL.md 存在与否 ≠ 真实 skill 数
- **分类目录不是空壳**——它们聚合多个真 skill
- **必须先 `find` 完再下结论**——不要凭"昨晚 22:00 说 24 个"继续往下说

**给用户的报告模板** (MCP 部分):
```
【MCP 审计 — YYYY-MM-DD】
npm 全局 MCP 包: N 个
pip 全局 MCP/SDK: M 个
Hermes config 里实际启用: K 个 (远少于 N+M)

按状态分:
• ✅ 已装+已配: <list>
• ⚠️ 已装+未配 (建议激活): <list>
• ❌ 未装但真包 (考虑): <list>
• ❓ 不确定 (需要查): <list>
```

**触发条件**: 用户说"看看 X 里有什么 MCP/工具能用" / "把全部 skill/MCP 接起来" / 任何 broad audit 类指令 → **必须先走 4 步**, 不许凭训练数据答。
