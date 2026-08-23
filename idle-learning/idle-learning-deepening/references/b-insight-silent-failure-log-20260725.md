# B_insight 静默失败完整日志

**日期**: 2026-07-25
**触发**: 用户问"有没有深度学习啊"

## 问题现象

用户问"有没有深度学习啊"，答"没有"——因为 B_insight 依赖的 `MINIMAX_M3_API_KEY` 未配置，
LLM 洞察推理步骤静默跳过。

## 完整执行日志

```
=== idle_learning_wrapper 2026-07-25_16-58-02 ===
🌊 启动空闲学习 orchestrator
🛠  工具就位: {'fact_decay': True, 'vision_cache': True, 'rollback_manager': True, 'batch_facts': True}
  ✅ A_visual: 17 个 Hermes 相关进程
  ✅ B_paper: arXiv 8 篇（含摘要/分类/作者）
  ❌ C_safety: CVE 扫描已在 wrapper 中同步执行
  ✅ D_action: action_diversity 完成

B_insight: arXiv 论文 → LLM 洞察 → fact_store
  ⚠  MINIMAX_M3_API_KEY 未找到

E2: 反思消化（升级retrieval_count）:
  📖 5条新知识反思消化...

E: Skill 升华（retrieval_count>=1, trust>=0.65）:
  ✅ 升华 → Hermes/（含 hermes-model-health + hermes-tuning-playbook）
  ✅ 升华 → LLM-as-Judge/（fact_id=478）
  ✅ 创建: 2, 跳过: 3
```

## 关键诊断

```bash
# 1. 检查 env
grep MINIMAX ~/.hermes/.env        # 无输出 = key 不存在

# 2. 检查 fact 增长
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE category='arxiv-insight';"
# 跑前=跑后=0，说明本轮零新洞察
```

## 结论

- A 阶段本地扫描正常（17个进程）
- B_paper 缓存的 8 篇论文数据存在但未入库 fact_store
- B_insight 完全跳过，无新洞察
- E 升华消耗的是历史 fact（fact_id=478），不是本轮数据
- 真正需要配 key 才能激活深度学习

## 相关文件

- `~/.hermes/cron/output/idle_learning/2026-07-25_16-58-02.log` — 本轮完整日志
- `~/.hermes/scripts/idle_learning_wrapper.sh` — 主流水线
- `~/.hermes/scripts/b_insight.py` — B_insight 推理逻辑
