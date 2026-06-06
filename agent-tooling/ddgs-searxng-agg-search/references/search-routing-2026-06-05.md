# 搜索路由决策记录 — 2026-06-05

## 路由演变过程

| 时间 | 方案 | 问题 |
|------|------|------|
| 早期 | ddgs 直调 | 中文查询自动翻译英文，结果垃圾 |
| 中期 | agg_search.py (ddgs + SearXNG) | SearXNG 公用实例全挂（429/404），实际只有 ddgs |
| 中期 | Firecrawl | 额度耗尽，已卸载 |
| 本次 | **anysearch** | 中文质量好，70+引擎，无需key |
| 本次 | **last30days** | 热点/舆情专用，HN + Reddit + Polymarket |

## 路由最终决策

```
用户指令: "搜索就只要 last30days 和 anysearch，话题按 Hermes 推荐走"

→ search.py 统一入口
  ├── 含 趋势/热点/社媒/舆情/过去N天/月 → last30days
  └── 其余 → anysearch
        └── 挂了 → agg_search.py (ddgs)
```

## anysearch 中文质量验证（2026-06-05 21:45）

```
查询: "九号平衡车 评测 2026"
结果: 3条
  1. 站长之家（chinaz.com）— 三大场景实测
  2. 搜狐汽车 — 九号L8对比评测
  3. IT之家 — 热门机型全盘点
耗时: 10s
质量: ✅ 全部中文优质来源
```

## last30days Python 3.12 问题（2026-06-05 22:00）

```bash
# 直接 python3 调用 → 报错
python3 last30days.py "AI agent" --quick
→ "last30days v3 requires Python 3.12+. Detected Python 3.11.15."

# 改用 python3.12 → 正常
/opt/homebrew/bin/python3.12 last30days.py "AI agent" --quick
→ ✅ 6 HN stories, 501 pts
```

**search.py 中的 PY312 常量**:
```python
PY312 = "/opt/homebrew/bin/python3.12"
```

## last30days 必须 --plan 参数

不加 `--plan` 会 DEGRADED RUN，源只有 HN 且结果被 demote：
```bash
# 正确
/opt/homebrew/bin/python3.12 last30days.py "话题" \
  --plan '{"intent":"话题","freshness_mode":"month","subqueries":["话题","话题 2026"]}'

# 错误（会降级）
/opt/homebrew/bin/python3.12 last30days.py "话题" --quick
```

## 不要做的事（2026-06-05 用户拍板）

- ❌ 单独用 ddgs 搜中文（自动翻译毁结果）
- ❌ 依赖 SearXNG 公用实例（全部挂了）
- ❌ 装 Docker 版 SearXNG（用户禁用）
- ❌ Firecrawl（额度耗尽，已卸载）
- ❌ 走框架内置 `web_search` 工具
- ❌ 手动选引擎（统一入口自动路由）
