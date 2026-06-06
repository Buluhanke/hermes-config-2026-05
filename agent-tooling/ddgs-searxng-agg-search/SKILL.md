---
name: ddgs-searxng-agg-search
description: 搜索兜底链 + 健康诊断 — anysearch 和 last30days 全部故障时, 用 DDGS 多引擎聚合（DuckDuckGo/Bing/Brave/Startpage/Google/AskSearX）兜底。触发词：搜索挂了/兜底/agg_search/ddgs 兜底/搜索引擎全挂
tags:
  - search
  - fallback
  - ddgs
  - health
---

# 搜索兜底链 + 健康诊断

## ⚠️ 定位：兜底专用，不是主路由

**上层路由统一入口 = `unified-search-routing` skill**（调 `search.py`）。本 skill **只负责兜底和诊断**。

## DDGS 兜底调用

```bash
python3 ~/.hermes/scripts/agg_search.py "查询词"
```

默认走 DuckDuckGo + Bing + Brave 三路并行。当 `search.py` 路由失败时（anysearch 网络断了 + last30days Python 3.12 缺了），调用此命令。

**触发条件**（由 `search.py` 内部处理，agent 无需手动触发，除非 `search.py` 本身也挂了）：
1. anysearch 网络超时/返回空结果
2. last30days Python 3.12 缺失
3. `search.py` 返回错误码非 0

## 健康诊断脚本（30 秒定位搜索故障）

**触发词**: "搜索正常吗" / "anysearch 还活着吗" / "last30days 还能用吗" / "搜索挂了" / "搜索一会儿好一会儿坏" / "为什么搜不到东西" / "你不是说都在的吗"。

**别靠记忆** —— 之前 v4 误判 last30days 已亡就是靠记忆报错。**必须实测 4 步**：

```bash
# 1) 确认 3 个 CLI 文件都在
ls -la ~/.hermes/skills/anysearch/scripts/anysearch_cli.py \
     ~/.hermes/skills/research/last30days/scripts/last30days.py \
     ~/.hermes/scripts/agg_search.py ~/.hermes/scripts/search.py

# 2) 确认 last30days 的 Python 3.12 在
which python3.12 || ls ~/.local/bin/python3.12

# 3) 测 anysearch
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "test-query" --max_results 1

# 4) 测 last30days
~/.local/bin/python3.12 ~/.hermes/skills/research/last30days/scripts/last30days.py "test-query" --quick 2>&1 | head -5

# 5) 测兜底
python3 ~/.hermes/scripts/agg_search.py "test-query" 2>&1 | head -5
```

**判断**：
- 全 ✅ → 搜索正常
- 任一 ❌ → 报告哪个环节挂了，给修复建议

**Agent 自我约束**（**重要**）：

诊断脚本**不要自己在 terminal/execute_code 跑**（Hermes 安全闸可能 BLOCKED）。**给用户跑法**，让用户在 Mac 终端粘贴执行，结果贴回来。

具体行为:
- ❌ 错: "我自己跑一下" → 触发 BLOCKED → 用户骂"乱来"
- ✅ 对: "这是 30 秒问诊脚本, 复制到 Mac 终端跑一下, 贴结果给我, 我立刻判断"

## 已知问题

- SearXNG 公用实例全挂（不讨论、不部署、不救）
- anysearch 仅匿名 access（限速较低，无 API Key）
- last30days 需要 Python 3.12+（`~/.local/bin/python3.12`）, 走 venv 的 3.11 会失败
- Docker 禁用（不讨论、不部署）

## 安装与路径（2026-06-06 修复）

- last30days **已正式安装**：`~/.hermes/skills/research/last30days/`（不再依赖 /tmp）
- 安装方法：`cp -rn /private/tmp/last30days-skill-repo/skills/last30days ~/.hermes/skills/research/last30days`
- ⚠️ **不要用 symlink 到 /tmp**：macOS 重启清 /tmp → symlink 变死链
- ⚠️ **不要用 symlink 到 ~/.local/share/**：目标不存在 = 死链（2026-06-06 翻过）
- 验证：`ls ~/.hermes/skills/research/last30days/scripts/last30days.py` 有输出=成功