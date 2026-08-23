# Hermes 能力配置参考 — 2026-08-06更新

## 当前搜索Backend状态

| Backend | 状态 | 配置 | 费用 |
|---------|------|------|------|
| DDGS | ✅ 正常 | autodetected，无需配置 | 免费 |
| SearXNG | ❌ Docker未装 | 装好后一行配置 | 免费（自部署） |
| Firecrawl | ✅ via nous/tencent | nous portal | Nous Portal订阅 |
| Tavily | ❌ 未配置 | TA VILY_API_KEY | 付费 |

**配置路径**（~/.hermes/config.yaml）：
```yaml
web:
  search_backend: "searxng"     # Docker装好后切换
  extract_backend: "firecrawl"  # 当前走nous
```

**Docker安装SearXNG**（待执行）：
```bash
docker run -d -p 8888:8080 --name searxng \
  -v $(pwd)/searxng:/etc/searxng \
  searxng/searxng
```
然后设置 `SEARXNG_URL=http://localhost:8888`

---

## Skill自我优化配置

### 阈值（~/.hermes/.env）：
```
HERMES_LEARNING_LOOP_CONFIDENCE_THRESHOLD=0.7  # 默认，可调
HERMES_SKILL_RETRIEVAL_THRESHOLD=0.85
HERMES_LEARNING_LOOP_ENABLED=true
```

### Skill写入条件（同时满足）：
- 5+ tool calls 或 错误恢复 或 用户纠正
- confidence ≥ 0.7
- 过去10次无相同skill

### 更新规则：
- 发现更好方法 → `patch` 不是 `edit`（保守更新）
- 自我测试验证泛化，失败则丢弃

---

## 渐进披露架构

- system prompt：仅存skill名称+一行摘要（~630 tokens/50skills）
- 全文：通过 `skill_view` 按需加载
- 效果：50skills ≈ 630 tokens vs 全量内联25K+ tokens

---

## 8层时间循环（Luong Hong Thuan解析）

| 层级 | 频率 | 关键机制 |
|------|------|---------|
| L1 执行 | 每次任务 | 干活 |
| L2 目标 | 跨会话 | 追求长期目标 |
| L3 Skill写 | 任务后 | 固化流程 |
| L4 Curator | 每周六 | 修剪低质量skill，防止腐烂 |
| L5 记忆 | 持续 | fact_store + MEMORY.md |
| L6 Kanban | 并行 | 多任务同时跑 |
| L7 压缩 | 上下文满时 | 提炼关键信息 |
| L8 子agent | 并行 | delegate_task并行工作 |

**Curator是防止skill腐烂的关键**：30天未用→移备份；重叠→合并；过时→删除。

---

## deep-research skill（GitHub可装）

```bash
hermes skills install official/research/deep-research
```

多agent并行→结构化JSON→报告，适合系统性研究任务。

---

## Skill Bundle

多条skill可以bundle加载：
```bash
hermes skills install category/research/deep-research
```
同category skill可bundle，一条命令加载多个。
