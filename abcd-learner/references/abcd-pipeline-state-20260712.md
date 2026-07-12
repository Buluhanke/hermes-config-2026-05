# ABCD Pipeline — 2026-07-12 State

## 当前五阶段状态

| 阶段 | 脚本 | 状态 | 产出 |
|------|------|------|------|
| A_visual | orchestrator | ✅ 正常 | 进程数写入 fact |
| B_paper | orchestrator → fact_store | ✅ 正常 | arXiv 8篇/次，含标题+摘要+作者+分类+日期，摘要写独立 fact |
| C_safety | wrapper → cve_lite.py | ✅ 正常 | venv 扫描，0 漏洞 |
| D_action | orchestrator | ✅ 正常 | action_diversity 状态输出 |
| E_skill | abcd_learner.py | ✅ 正常 | retrieval_count≥3 时升华 skill |
| batch_facts | batch_facts_from_log.py | ✅ 正常 | 从日志提取 ABCD 元认知写入 fact_store |

## B_paper 写入 fact_store 的结构（2026-07-12 重写验证）

每次运行写入 2N 条 fact（N=新论文数）：
- **标题 fact**: `content=论文标题`, `category=arXiv AI | 日期 | 作者`, `tags=[分类列表 + arXiv/paper/ai/idle-learning]`, `trust=0.65`
- **摘要 fact**: `content=[摘要] 摘要前200字`, `category=arXiv摘要 | 日期`, `tags=[分类 + arxiv/abstract]`, `trust=0.60`

## MiniMax LLM 洞察（B_insight）

- **目标**: 读 DB 中 arXiv 论文 → LLM 推理 → 写洞察到 DB
- **API 端点**: `http://123.56.67.77:9100/v1/chat/completions`
- **Key 位置**: `~/.hermes/.env` → `MINIMAX_M3_API_KEY="sk-290...6e18"`
- **状态**: 从 sandbox 调用超时（网络隔离），gateway 进程内调用正常
- **Gateway AI server**: 端口 8642，`/v1/chat/completions` 返回 401 Unauthorized（需要 Bearer token）

## 关键脚本路径

```
~/.hermes/scripts/
  idle_learning_wrapper.sh      # 主流水线编排
  idle_learning_orchestrator.py # ABCD orchestrator（B_paper 在此）
  batch_facts_from_log.py       # 日志→fact 提取
  cve_lite.py                  # CVE 扫描（Rustchain/Scottcjn, 552行标准库）
  restart_gw.sh                # Gateway 重启
~/.hermes/skills/abcd-learner/
  abcd_learner.py              # E 阶段 skill 升华
~/.hermes/memory_store.db      # fact_store（SQLite）
```

## 验证命令

```bash
# 跑完整流水线
bash ~/.hermes/scripts/idle_learning_wrapper.sh

# 查 fact_store 总数
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts"

# 查最新 arXiv facts
sqlite3 ~/.hermes/memory_store.db "SELECT content, category FROM facts WHERE tags LIKE '%arxiv%' ORDER BY created_at DESC LIMIT 6"

# 查按 tag 分布
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*), tags FROM facts GROUP BY tags"
```

## 踩坑记录（2026-07-12）

- **Gateway 端口变更**: health 检查从 3847 变为 8642（`curl localhost:8642/health` 返回 `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}`）
- **b_paper 崩溃**: `run_abcd_scan()` 返回 `None` → 重写 orchestrator 后解决（外层函数缩进导致嵌套函数定义不返回）
- **MiniMax key**: sandbox 拿不到 gateway 进程环境的 key，需从 `~/.hermes/.env` 读
- **B_insight LLM**: 从 sandbox 调用 MiniMax API 超时，需在 gateway 进程内调用
