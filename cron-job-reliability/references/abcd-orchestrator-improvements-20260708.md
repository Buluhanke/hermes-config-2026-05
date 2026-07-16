# ABCD 扫描 + Orchestrator 改进记录（2026-07-08）

## 问题诊断

### 问题1：cron job LLM 偷懒
- **现象**：夜间ABCD自学轮次 cron output 全是 Markdown 报告，没有实际命令执行
- **根因**：cron job 只有 prompt 没有 script → Hermes 启动 LLM agent → LLM 写报告不执行
- **修复**：no_agent=true + script=idle_learning_wrapper.sh

### 问题2：orchestrator 里 ABCD 是假的
- **现象**：orchestrator 没有真正跑 A/B/C/D 扫描的逻辑
- **根因**：ABCD 扫描写在 cron prompt 里，LLM 不会认真执行
- **修复**：idle_learning_orchestrator.py 新增 run_abcd_scan()，每方向独立超时

### 问题3：subprocess 卡死
- **现象**：cve_scan 493 个包 × API 调用，同步阻塞 orchestrator
- **修复**：C 方向 5s 超时，超时标记"后台扫描中"继续

### 问题4：arXiv API 限速
- **现象**：urllib 连接 arXiv 超时 30s+
- **修复**：缓存优先（1h TTL）+ 降级读过期缓存 + curl --max-time 6s

### 问题5：vision_cache.py 引用错误
- **修复**：引用改为 warm_cache.py

## 修复后的阶段顺序

```
阶段 0: ABCD scan (新增，并行)
阶段 1: batch_facts_from_log
阶段 2: fact_decay (先 stage 后 fact_stats)
阶段 3: rollback_list
阶段 4: skill_resonance (fact_stats 之后)
```

## 验证命令

```bash
# ABCD 扫描
python3 -c "
from idle_learning_orchestrator import run_abcd_scan
r = run_abcd_scan()
for k,v in r.items():
    print(f'{k}: {v.get(\"status\")} | {v.get(\"summary\",\"\")}')
"

# 完整 orchestrator
bash ~/.hermes/scripts/idle_learning_wrapper.sh | grep -E "A_visual|B_paper|C_safety|D_action|fact_store|4/4"

# wrapper 可执行性
for s in idle_learning abcd_auto_fix daily_skill_intake knowledge_miner auto_skill_scan self_model_update; do
    f="$HOME/.hermes/scripts/${s}_wrapper.sh"
    [ -x "$f" ] && echo "✅ $f" || echo "❌ $f"
done
```
