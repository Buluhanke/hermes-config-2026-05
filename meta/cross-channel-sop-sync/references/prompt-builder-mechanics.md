# Hermes Prompt Builder 机制 — Skills 怎么注入到 System Prompt

## 总览

Hermes agent session 起手时，`prompt_builder.build_skills_system_prompt()`
被调用，返回一个**紧凑的 skills 索引**字符串，注入到 system prompt 末尾。
**所有渠道**（CLI / Telegram / QQBot / 飞书 / WeCom / Weixin / Discord /
Slack / Mattermost / Matrix / API Server / Webhook / Cron）走**同一个**
装配函数 → **改一个 skill = 全部渠道自动同步**。

源代码：`~/.hermes/hermes-agent/agent/prompt_builder.py` 第 1351 行

## 关键代码片段

```python
def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
    compact_categories: "frozenset[str] | None" = None,
) -> str:
    """Build a compact skill index for the system prompt."""
    skills_dir = get_skills_dir()  # ~/.hermes/skills/
    external_dirs = get_all_skills_dirs()[1:]  # 排除本地
    ...
    # Layer 1: in-process LRU cache
    # Layer 2: disk snapshot (~/.hermes/.skills_prompt_snapshot.json)
    # Falls back to full filesystem scan
```

**两层缓存**:
1. **In-process LRU** — `(skills_dir, tools, toolsets, hidden, platform_hint, disabled, compact_categories)` 复合 key
2. **Disk snapshot** — `~/.hermes/.skills_prompt_snapshot.json` 持久化

## Skills 怎么被发现

```python
# prompt_builder.py 1380+ 行
for entry in snapshot.get("skills", []):
    skill_name = entry.get("skill_name") or ""
    category = entry.get("category") or "general"
    frontmatter_name = entry.get("frontmatter_name") or skill_name
    platforms = entry.get("platforms") or []
    if not skill_matches_platform({"platforms": platforms}):
        continue
    if frontmatter_name in disabled or skill_name in disabled:
        continue
    if not _skill_should_show(entry.get("conditions") or {}, ...):
        continue
    skills_by_category.setdefault(category, []).append(
        (frontmatter_name, entry.get("description", ""))
    )
```

**过滤逻辑**:
- `platforms` 字段不匹配当前 platform → 跳过
- 在 `disabled` 列表里 → 跳过
- `conditions` 不满足 → 跳过
- 默认 `platforms: [macos, linux]` 在 macOS + Linux 上都出现

## 改完 skill 后是否需要 reload

**不需要手动 reload**。Disk snapshot 有 mtime 校验。

**验证方法**:
```bash
# 看 snapshot 是否含新建的 skill
grep "channel-universal-sop" ~/.hermes/.skills_prompt_snapshot.json

# 不含 → 删 snapshot 让 prompt_builder rebuild
rm ~/.hermes/.skills_prompt_snapshot.json
```

**注意**: In-process LRU cache (Layer 1) 在**当前 Python 进程**里持续有效。
**重启 gateway 后才生效**（或长 session 自然过期）。

## 跟 SOUL.md 注入的关系

```python
# prompt_builder.py 1687+ 行
def build_context_files_prompt(...):
    """Load SOUL.md / AGENTS.md / .hermes.md from HERMES_HOME and cwd."""
```

**SOUL.md 跟 skills 索引是分开装配的两段**:
- SOUL.md → 注入到 system prompt 靠前位置（身份段）
- Skills 索引 → 注入到 system prompt 靠后位置（能力段）
- **改 SOUL.md 也是跨渠道同步**（同样走 build_context_files_prompt）

**实际落地 (v3.1)**:
- SOUL.md 末尾加 v3.1 段落 → 全渠道身份段都有
- channel-universal-sop skill → 全渠道能力段索引都有
- 两者**互为补充**：SOUL.md 是核心铁律的简短回顾，skill 是详细 SOP

## Skill frontmatter 关键字段

```yaml
---
name: <unique-name>           # 必填
description: |                # 必填, multiline 时首行短摘要+下面详细
  ...
version: 1.0.0
author: ...
license: MIT
platforms: [macos, linux]     # 默认都出现, 显式列更稳
metadata:
  hermes:
    tags: [...]
    related_skills: [...]     # 关联 skill 列表
---
```

**`description` 字段的实战技巧**:
- **必须**包含用户原话关键句 (e.g. "成长之路必须落地")
- 让验证脚本能 `grep` 到
- 让 agent 加载时第一眼看到
- YAML literal block (`|`) 里 `#` 不是注释, 写 plain text

## 跟 channel_prompts 的区别

| 字段 | 范围 | 用途 | 跨渠道同步 |
|---|---|---|---|
| `channel_prompts` | per-channel / per-chat | 渠道/频道特定行为 | ❌ 单点 |
| SOUL.md | 全局 | 核心身份/铁律 | ✅ 全部渠道 |
| Skill (skills/) | 全局（按 platform/condition 过滤） | 详细 SOP / 工具 | ✅ 全部渠道 |

**结论**: 行为铁律 / SOP 走 **skill + SOUL.md**，**别碰 channel_prompts**。
channel_prompts 只用于渠道/频道**特定**的微调（e.g. 某群组附加规则）。