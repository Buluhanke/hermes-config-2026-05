# Orphan Audit Results — 2026-07-16 (ACTUAL)

## Actual Numbers
- Archive: 137 skills | Active: 72 skills | True orphans: 116
- Recovered: **26 skills** | Archived permanently: ~90

## ✅ Recovered Skills (26)

### From large orphans (>5KB, substantive content):
`secrets-management` `memory-cn` `siyuan` `perception-decision-engine` `memray-memory-profiler` `subagent-driven-development` `skill-creator` `writing-skills` `browser-use` `3-statement-model` `context-compression` `dcf-model` `agent-rdp`

### From wondelai-skills (8):
`clean-code` `refactoring-patterns` `software-design-philosophy` `pragmatic-programmer` `working-with-legacy-code` `system-design` `clean-architecture` `team-topologies`

### From research/skills (2):
`qmd` `scrapling`

### From other orphans (3):
`courier-notification-skills` `open-source-skill-harvesting` `kepano-defuddle→defuddle`

### Pattern: archive dir ≠ skill name (needed multi-level find):
Some archived skills buried 3 levels deep (e.g., `note-taking/obsidian`, `hermes-evolution/open-source-skill-harvesting`, `core/web-search-default`).

## ❌ Archived Permanently (~90)

**Placeholder pattern** — body=title, no runnable steps, all <2KB:
- `cve-lite-py替换cve-scan-py` (594B)
- `screen-watcher-handler触发链路断裂` (474B)
- `ai代理-工作流知识化` (541B)
- `star-4d-学习循环` (551B)
- `launchd启动Python脚本cwd` (457B)
- `chrome-cdp端口异常` 系列 (534-565B)
- `telegram-pool-timeout` 系列 (558-613B)
- `ddgs-cli损坏` (453B)
- `模型优化/知识架构/评测垂直化` 系列 (576-735B)
- `失败驱动记忆进化/坑点检索飞轮/反思式增量` 系列 (598-706B)
- `hard-rule-6种方式已全确认` (706B)

**14x duplicate:** "小时工具错误聚集-XX次" — identical format, different day number

## ⚠️ Skipped (needs fresh assessment)
- `afrexai-observability-engine` (46KB) — overlaps with `hermes-observability`
- `agent-browser` — overlaps with `browser-use`
- `kepano-defuddle` — duplicates recovered `defuddle`

## Size ≠ Substance

| Bytes | Placeholder likelihood | Action |
|-------|----------------------|--------|
| <500 | ~95% | Skip |
| 500-1KB | ~80% | Read 5 lines |
| 1-3KB | ~50/50 | Read 20 lines |
| 3-10KB | ~70% substantive | Read 20 lines |
| >10KB | ~90% substantive | Check for raw dumps |

**Counter-examples:** `prism-3way` (2.8KB) real, `agentmail` (4KB) real, `perception-decision-engine` (12KB) richest decision framework.
