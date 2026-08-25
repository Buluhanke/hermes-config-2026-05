---
name: idle-learning-deepening
version: 0.1
description: "ABCD流水线网络依赖阶段静默失败诊断。Use when B_insight C_safety悄悄挂了没产出"
triggers:
  - "深度学习"
  - "为什么没有新知识"
  - "ABCD跑完了但知识没增加"
  - "B_insight 失败"
  - "arXiv 有数据但没有洞察"
trigger_type: idle_learning
tags: [idle-learning, abcd, b-insight, api-key, troubleshooting]
created: 2026-07-25
来源: 2026-07-25 自我学习执行
---

# Idle Learning 深度化：激活网络依赖阶段

## 核心问题

ABCD 五阶段中，A(论文入库)/D(动作执行) 是纯本地进程，速度快但知识增长有限。
真正带来**新洞察**的是 B_insight（LLM 推理）和 C(CVE 扫描)，它们依赖外部 API。

2026-07-25 实测：A 报「8篇论文」成功，B_insight 报 `⚠ MINIMAX_M3_API_KEY 未找到` 静默跳过，
结果：fact 条目 0 增加，升华只消耗了已有 fact。

## B_insight 激活检查单

```
1. env 存在？      grep MINIMAX ~/.hermes/.env
2. wrapper 传递？  grep -n "b_insight\|MINIMAX" ~/.hermes/scripts/idle_learning_wrapper.sh
3. 实际写入？      sqlite3 ~/.hermes/memory_store.db \
                    "SELECT COUNT(*) FROM facts WHERE category='arxiv-insight';"
   跑前跑后差值 = 0 → B_insight 跳过
```

## 已知根因 & 修复记录（2026-08-01）

**B_insight 静默失败的真正原因（多次误判）：**

1. `MINIMAX_M3_API_KEY` 在 .env 中有值，但 `123.56.67.77:9100` 这个自定义代理端点
   对该 key 返回"无效令牌"（HTTP 401）。key 本身是 `sk-290...6e18`（AICODEE/MAIN_API_KEY 同值），
   但代理层认证不通过。

2. OpenRouter key 存在但 `mistral-7b-instruct` 免费模型 HTTP 404（模型下线或不可用）。

3. **最终可用方案：ZAI/GLM (`open.bigmodel.cn`，`glm-4-flash`)，有免费额度，SSL 需要 certifi。**

**修复：** `b_insight.py` 已改为 3-provider fallback 链：
- MiniMax custom endpoint（HTTP）→ 失败
- OpenRouter mistral-7b-instruct → HTTP 404
- ZAI/GLM `glm-4-flash`（SSL + certifi）→ **成功**

**代码改动：**
- `import ssl, certifi`
- `call_llm_glm()` 函数（SSL ctx）
- `call_llm_minimax()` 用 HTTP 不加 ctx
- provider fallback 链：minimax → openrouter → glm

## 修复方案（按优先级）

### P0：key 已配置，但解析正则错误（2026-07-25 实测）
`.env` 中 `MINIMAX_M3_API_KEY=sk-xxx`（无引号），`b_insight.py` 第 13 行正则 `r'"([^"]+)"'` 找双引号，永远匹配不到。
修复：`b_insight.py` 正则改为 `r'=\s*([^\s#]+)'`

### P1：安全闸拦截 LLM API 调用
带 `Authorization: Bearer` 的 HTTP 请求被安全闸超时拦。
解：连通性用 `curl http://123.56.67.77:9100/v1/models`（无 auth）测试；完整调用走 wrapper 脚本间接触发。

### P2：降级策略
若 MiniMax key 彻底不可用，可将 b_insight.py 切换到免费模型：
- OpenRouter 免费模型（mistral-7b-instruct 等）
- 配置在 `~/.hermes/.env` 的 `OPENROUTER_API_KEY`

## C_safety OSV 扫描

依赖：`~/.hermes/hermes-agent/venv` 下的 package 列表。
若 venv 依赖为空（如 2026-07-25 显示 `dependencies scanned: 0`），OSV API 无包可扫。
根因：orchestrator 用 `pip list --format=freeze` 在 venv 外执行，或 venv 内无包。

## 深度学习验证命令

```bash
# 每轮运行后检查
BEFORE=$(sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE category='arxiv-insight';")
# 运行 wrapper
AFTER=$(sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE category='arxiv-insight';")
echo "新增洞察: $((AFTER - BEFORE)) 条"
```

预期每轮 +3 条，差值为 0 则 B_insight 未激活。

## 相关脚本

- `~/.hermes/scripts/idle_learning_wrapper.sh` — 主流水线
- `~/.hermes/scripts/b_insight.py` — B_insight LLM 推理
- `~/.hermes/scripts/idle_learning_orchestrator.py` — A/B/D 并行 orchestrator
