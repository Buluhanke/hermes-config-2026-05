# idle-learning-rounds 工具链参考

6 个标准工具的 CLI 参数、输出 schema、判定标准。所有路径在 `~/.hermes/scripts/` 下。

---

## 1. `fact_decay.py` — fact_store 衰减检查

**核心命令**：
```bash
python3 ~/.hermes/scripts/fact_decay.py            # 统计汇总
python3 ~/.hermes/scripts/fact_decay.py --score    # 逐条 trust 排序
python3 ~/.hermes/scripts/fact_decay.py --prune    # 清理过期
```

**输出 schema**（标准统计）：
```
📊 fact_store 衰减统计 (N 条)
  ✅ 活跃 (trust > 0.15): X
  ⚠️  低信任 (0.05 < trust ≤ 0.15): Y
  ❌ 已过期 (trust ≤ 0.05): Z
📈 平均 trust: N.NNN
```

**判定**：
- 健康：活跃 ≥ 95% 且 平均 trust ≥ 0.4
- 警告：平均 trust 0.2-0.4
- 不健康：活跃 < 90% 或 平均 trust < 0.2 → 触发 `--prune`

---

## 2. `vision_cache.py` — 视觉缓存统计

**核心命令**：
```bash
python3 ~/.hermes/scripts/vision_cache.py stats    # 统计 + 错误率
python3 ~/.hermes/scripts/vision_cache.py test     # 触发写入测试
```

**输出 schema**：
```
📊 视觉缓存统计:
  entries: N
  max_entries: 200
  ttl_seconds: 300
  hits: N
  misses: N
  hit_rate: N.N%
  total_size: XB
  cache_file: /Users/aimac/.hermes/cache/vision_cache.json
  rolling_window_size: 50
  recent_results_tracked: N
  error_rate: N.N%
  error_threshold: 30%
  error_exceeded: False
  error_warning: ✅ 错误率在正常范围内
```

**判定**：
- 缓存文件首次创建（"📦 缓存文件不存在, 首次创建"）是正常
- `error_rate < error_threshold (30%)` 为健康
- `entries=0` 可能是 screen_watcher 未启动，**不一定是 bug**，看 fact #60 的解释

---

## 3. `rollback_manager.py` — 系统快照管理

**核心命令**：
```bash
python3 ~/.hermes/scripts/rollback_manager.py list       # 列出所有快照
python3 ~/.hermes/scripts/rollback_manager.py snapshot   # 创建新快照
python3 ~/.hermes/scripts/rollback_manager.py rollback <id>  # 回滚
```

**输出 schema**（list）：
```
📸 快照列表 (N 个):
ID             名称                             时间                   已恢复
----------------------------------------------------------------------
<id>   <name>   <YYYY-MM-DD HH:MM:SS>   ⬜
```

**判定**：
- 快照少（< 5）正常：破坏性操作少
- 快照多（> 20）需审视：可能 rollback 被频繁触发

---

## 4. `batch_facts_from_log.py` — 批量入库

**核心命令**：
```bash
python3 ~/.hermes/scripts/batch_facts_from_log.py
```

**输出 schema**：
```
✅ 新写入 N 条 fact
⏭️  跳过 M 条（已存在）
📊 fact_store 总计: K 条
```

**判定**：
- `新写入 = 0 + 跳过 > 0`：去重命中，库稳定，**正常**
- `新写入 = 0 + 跳过 = 0`：日志没发现，**异常**（脚本可能扫错路径）
- `新写入 > 0`：有新发现落地

---

## 5. `ai_radar_brief.py` — 论文 / AI 圈扫描

**核心命令**：
```bash
python3 ~/.hermes/scripts/ai_radar_brief.py          # 24h 摘要
python3 ~/.hermes/scripts/ai_radar_brief.py --full   # 完整内容
```

**输出 schema**：
```
✓ 拉取 1706 KB (attempt 1)
📥 643 条 AI 强相关 (>=0.65)
🧩 聚类去重: 643 → 585 簇

📊 24h AI 圈 Top 12 (跨源加权 + 时间衰减)
数据时间: 2026-06-29T16:52:30.080113Z
```

**判定**：
- 拉取成功（KB > 100）+ 聚类比 < 90% = 健康
- 多源验证（"2 源 ✓ 多源验证"）越多越可信
- `ai_score < 0.65` 不计入，不在 Top 12

---

## 6. `cve_scan.py` — 依赖漏洞扫描

**核心命令**：
```bash
python3 ~/.hermes/scripts/cve_scan.py          # 扫描 20 个核心包
python3 ~/.hermes/scripts/cve_scan.py --json   # JSON 输出
```

**输出 schema**：
```
[cve_scan] 扫描 20 个包 (OSV.dev 公开 API)
[cve_scan] 完成。

============================================================
扫描结果: 20 包 | 总漏洞: N
============================================================

  ✅ <package>==<version>: 无已知漏洞
  ⚠️  <package>==<version>: <CVE-id> ...
```

**判定**：
- 总漏洞 = 0：依赖健康
- 总漏洞 > 0 但严重度低：观察
- 总漏洞 > 5 或有 critical：触发升级评估

---

## 7. `action_diversity.py` — 动作多样性

**核心命令**：
```bash
python3 ~/.hermes/scripts/action_diversity.py
```

**输出 schema**：
```
[action_diversity] 文件: /Users/aimac/.hermes/state/script_router_history.jsonl

[action_diversity] 最近 7 天无行动记录
# 或
[action_diversity] 最近 7 天: terminal 53%, UI < 8%, browser X%, ...
```

**判定**：
- 无记录（用户在家没执行）：**预期内**，不报错
- terminal 占比 > 50%：行动失衡（参见 fact #14）
- UI < 8%：观察，可能视觉产线没接上