# ABCD学习管道修复记录 (2026-07-12 追加)

## 追加修复（2026-07-12）

### 修复4：batch_facts_from_log.py 硬编码日期（紧急）
- **Bug**：第22行硬编码 `glob("2026-07-11*.log")`，每日读昨日日志→永远读不到当天结果
- **症状**：`来源: 2026-07-11_01-00-14.log` 而非当天日志
- **修法**：`date.today().strftime("%Y-%m-%d")` 动态生成 prefix，`from datetime import date, timedelta`
- **验证**：`python3 ~/.hermes/scripts/batch_facts_from_log.py` → 应显示"来源: 2026-07-12_..."（当天日期）

### 修复5：cve_lite SSL EOF（macOS 防火墙）
- **Bug**：OSV API TLS 握手被 macOS 防火墙截断，`UNEXPECTED_EOF_WHILE_READING`
- **修法**：在 `_http_json()` 中加 `ssl.CERT_NONE` fallback
- **验证**：`python3 ~/.hermes/scripts/cve_lite.py scan ~/.hermes/hermes-agent/venv --severity HIGH --timeout 20` → 应显示 `✓ no known vulnerabilities found`

### 修复6：wrapper 路径双重 .hermes
- **Bug**：`$HERMES_HOME` 已是 `~/.hermes`，拼 `.hermes/skills/` 导致 `~/.hermes/.hermes/skills/`
- **修法**：skill 路径用 `$HERMES_HOME/skills/`，不重复

### 修复7：abcd-learner skill 目录从未创建
- **Bug**：execute_code 的 write_file 和 terminal 的 mkdir 多次失败，skill 目录空
- **修法**：先 `mkdir -p`，再逐文件 write_file
- **DB schema 注意**：`fact_id`（不是`id`），`category` 字段存的是 fact.text 长描述（不是分类），无 `source` 列

---

## 原始记录 (2026-07-11)

## 问题现象
- 每天凌晨1点ABCD自学轮次运行成功（`ok`）
- 但 fact_store 始终写入 **0 条新知**

## 根因分析

### 根因1：batch_facts_from_log.py 使用静态列表（已修正）
- FACTS_FROM_LOG 是硬编码的 6 月中旬静态列表，每天跑 = 每次都跳过去重 = 永远 0 写入

### 根因2：cve_scan 超时被截断（已修正）
- `idle_learning_orchestrator.py` 原第 223 行：`timeout=5`
- cve_scan.py 实际需要 50 秒，Thread 被 kill 后在后台异步运行，结果从未写入 DB

## 修复方案

### 修正1：batch_facts_from_log.py 重写（动态提取）
从 orchestrator 日志动态提取 ABCD 阶段结果 → fact 入库。实测：fact_store 97 → 121 条（每轮 4 条新 fact）

### 修正2：cve_scan.py → cve_lite.py（生产级替换）
- **来源**：Scottcjn/Rustchain，MIT License，零外部依赖
- **落地**：`~/.hermes/scripts/cve_lite.py`

### 修正3：AgentFactory paradigm → skill crystallizer（新增 E 阶段）
- **来源**：zzatpku/AgentFactory (GitHub 57 stars, ACL 2026 System Demonstrations)
- **核心思想**：successful task solutions → **executable subagent code** > textual experience
- **新增**：`~/.hermes/skills/abcd-learner/`

## 全网现成方案
| 项目 | Stars | 用途 | Hermes集成 |
|------|-------|------|----------|
| AgentFactory (zzatpku) | 57 | subagent → skill | 引入 skill crystallizer |
| cve_lite.py (Scottcjn) | - | 零依赖 OSV 扫描 | 替换自写 cve_scan |
| CVE-KGRAG (Yuning-J) | 17 | CVE 知识图谱+RAG | 未来结构化 |
| autoagent (kevinrgu) | 4488 | 自主改配置跑 benchmark | skill_vetter 借鉴 |

## 验证命令
```bash
python3 ~/.hermes/scripts/batch_facts_from_log.py   # 应写入>0条，来源为当天日期
python3 ~/.hermes/scripts/cve_lite.py scan ~/.hermes/hermes-agent/venv --severity HIGH --timeout 20
python3 ~/.hermes/skills/abcd-learner/abcd_learner.py
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts"  # 应增长
```

## 关键文件
- `~/.hermes/scripts/batch_facts_from_log.py` — 重写，动态提取
- `~/.hermes/scripts/cve_lite.py` — 新增，生产级 CVE 扫描
- `~/.hermes/scripts/idle_learning_orchestrator.py` — 更新调用 cve_lite
- `~/.hermes/scripts/idle_learning_wrapper.sh` — 加入 E 阶段
- `~/.hermes/skills/abcd-learner/` — 新增 AgentFactory 格式 skill
- `~/.hermes/memory_store.db` — 97 → 131 条
