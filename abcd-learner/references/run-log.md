# abcd-learner 运行日志

## 最新运行（2026-07-12 00:17）

```
A: ✅ 31个Hermes相关进程
B: ❌ arXiv缓存(1m前)
C: ✅ cve_lite同步完成（SSL fallback生效，venv无CVE）
D: ✅ action_diversity完成
E: ✅ skill crystallizer（无retrieval_count≥3的fact）
batch_facts: ✅ 4条知识提取，跳过已存在
fact_store: 活跃121条，低信任0条
```

## 已知问题

### CVE扫描 SSL EOF
**现象**：`OSV API unavailable: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING]>`
**原因**：macOS 防火墙/代理截断 TLS 握手
**修复**：cve_lite.py `_http_json()` 已加 SSL CERT_NONE fallback
**状态**：✅ 已修复，2026-07-12 验证通过

### skill crystallizer 空输出
**现象**：E 阶段无输出（无文件写入）
**原因**：当前无 retrieval_count ≥ 3 的 fact，无法触发 crystallize
**预期**：随每日 ABCD 运行，retrieval_count 累积，下轮触发

### batch_facts 0 新写入
**现象**：每轮写入 0 条（已存在于 DB）
**原因**：FACTS_FROM_LOG 静态列表已全部入库，ABCD 动态提取 4 条也已在昨天写入
**改善**：ABCD 方向需要有真实新知识发现（不只是状态检查）

## fact_store 当前状态（2026-07-12）
- 总计：121 条
- 活跃（trust > 0.15）：113 条
- 低信任（0.05 < trust ≤ 0.15）：8 条
- 过期（trust ≤ 0.05）：0 条
