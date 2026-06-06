# Complete Entity Deletion Checklist

> 删除 Hermes 中的任意实体（plugin / skill / 集成）时的标准化流程

## 适用场景

- 彻底删除某个插件（firecrawl、某个 provider 等）
- 清理已废弃的 skill 及所有残留引用
- 清理 MCP server 残留

## 五步删除法

### Step 1 — 定位所有实体位置

```bash
# 插件实体（两个标准路径）
ls ~/.hermes/hermes-agent/plugins/web/<entity>/
ls ~/.hermes/hermes-agent/plugins/browser/<entity>/

# Skill 及 profile 副本
ls ~/.hermes/skills/<category>/references/<entity>*
ls ~/.hermes/profiles/default/skills/<category>/references/<entity>*
```

### Step 2 — 删除实体文件

```bash
rm -rf ~/.hermes/hermes-agent/plugins/web/<entity>
rm -rf ~/.hermes/hermes-agent/plugins/browser/<entity>
rm -f ~/.hermes/skills/.../references/<entity>*
rm -f ~/.hermes/profiles/default/skills/.../references/<entity>*
```

### Step 3 — 清理技能库中对实体的引用

```bash
# 扫描所有 skill .md 文件中的字符串引用
grep -r "<entity-name>" ~/.hermes/skills --include="*.md"
```

常见残留位置：
- `SKILL.md` 正文中的 "见 references/..." 链接
- `references/*.md` 中的配置示例（`backend: <entity>`）
- `references/*.md` 中的注释（`# 不是 xxx（需付费）`）

### Step 4 — 清除 config / .env 中的引用

```bash
grep -r "<entity>" ~/.hermes --include="*.yaml" --include="*.yml" --include="*.json" --include="*.env" --include="*.toml" -l
```

### Step 5 — 最终验证

```bash
# 无任何残留
grep -r "<entity>" ~/.hermes/skills --include="*.md"
find ~/.hermes/hermes-agent/plugins -type d -name "*<entity>*"
echo "Clean"
```

## 实际案例：Firecrawl 删除（2026-06-05）

| 位置 | 类型 | 状态 |
|---|---|---|
| `plugins/web/firecrawl/` | 插件目录 | ✅ 已删除 |
| `plugins/browser/firecrawl/` | 插件目录 | ✅ 已删除 |
| `skills/idle_learning/references/firecrawl*.md` | 参考文档 | ✅ 已删除 |
| `profiles/default/skills/idle_learning/references/firecrawl*.md` | Profile 副本 | ✅ 已删除 |
| `idle_learning/SKILL.md`（正文引用） | Skill 正文 | ✅ 已清除 |
| `proactive-self-evolution/references/web-search-backend-config.md`（配置示例） | 参考文档 | ✅ 已清除 |
| `web-agent-os/SKILL.md`（配置示例） | Skill 正文 | ✅ 已清除 |

**关键教训**：Profile 目录 (`profiles/default/skills/`) 是独立副本，必须单独清理，不能假设主 skills 目录删了 profile 就跟着删。
