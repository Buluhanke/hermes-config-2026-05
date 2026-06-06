# SearXNG 实例存活状态 — 已归档（2026-06-05 22:00）

> **⚠️ 本文档已归档**：SearXNG 已从 Hermes 全部移除（代码/配置/.env）。本文件仅作历史记录，**不再更新、不再参考**。如需新搜索后端，参见 SKILL.md 主文档。

## 测试方法
```bash
for url in "https://searx.party" "https://searxng.org" "http://127.0.0.1:8888"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url/search?q=ai&format=json&limit=1")
  echo "$url → $code"
done
```

## 实测结果（2026-06-05）

| 实例 | 状态 | 错误 |
|------|------|------|
| `http://127.0.0.1:8888` | ❌ Connection refused | localhost 未部署（Docker 被用户禁用） |
| `https://searx.party` | ❌ 429 | Too Many Requests，持续，排队也过不去 |
| `https://searxng.org` | ❌ 404 | Not Found，已下线 |

## 2026-06-02 历史记录（参考）
```
searx.be         → 403 Forbidden（JSON 不通）
searx.party      → 429 Too Many Requests（持续）
searxng.vern.cc  → 429
searx.li         → 404
searx.tuxcloud.net → 429
searxng.org      → 404
searx.ddot.cc    → 530
searx.lynL.org   → 429
searx.trom.tf     → 429
其余 40+        → 000 超时
```

## 结论
公开 SearXNG 实例不可依赖。脚本里保留多实例 fallback 逻辑是正确设计，但实际只有 ddgs 单独工作。

**最终方案（2026-06-05 22:00 落地）**：不走自建 SearXNG，**改用 anysearch 作为真聚合首选**（70+ 引擎，匿名免 key，中英文都好）。
