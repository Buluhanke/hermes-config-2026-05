# ABCD学习管道修复记录 (2026-07-11)

## 问题现象
- 每天凌晨1点ABCD自学轮次运行成功（`ok`）
- 但 fact_store 始终写入 **0 条新知**
- batch_facts_from_log.py 输出：`✅ 新写入 0 条 fact` + `⏭️ 跳过 28 条（已存在）`

## 根因分析

### 根因1：batch_facts_from_log.py 使用静态列表（已修正）
- FACTS_FROM_LOG 是硬编码的 6 月中旬静态列表，每天跑 = 每次都跳过去重 = 永远 0 写入
- **纠正旧误判**：INSERT 列名和去重逻辑之前被认为是 bug，实测验证后两者都正常工作
- ABCD 四步的运行结果（进程数/arXiv 缓存/cve 状态/action 输出）**从未被解析为 fact**

### 根因2：cve_scan 超时被截断（已修正）
- `idle_learning_orchestrator.py` 原第 223 行：`timeout=5`（只等 5 秒）
- cve_scan.py 实际需要 50 秒，Thread 被 kill 后在后台异步运行，结果从未写入 DB

## 修复方案

### 修正1：batch_facts_from_log.py 重写（动态提取）
从 orchestrator 日志动态提取 ABCD 阶段结果 → fact 入库。实测：fact_store 97 → 121 条（每轮 4 条新 fact）

### 修正2：cve_scan.py → cve_lite.py（生产级替换）
- **来源**：Scottcjn/Rustchain，MIT License，零外部依赖
- **优点**：Python 标准库、支持 PyPI/npm/crates.io/Go 多生态、batch API 优化、CVSS 评分生产级
- **落地**：`~/.hermes/scripts/cve_lite.py`
- **验证**：`python3 ~/.hermes/scripts/cve_lite.py scan ~/.hermes/hermes-agent/venv --severity HIGH`
- orchestrator c_safety() 指向 cve_lite.py，超时 5s → 120s

### 修正3：AgentFactory paradigm → skill crystallizer（新增 E 阶段）
- **来源**：zzatpku/AgentFactory (GitHub 57 stars, ACL 2026 System Demonstrations)
- **核心思想**：successful task solutions → **executable subagent code** > textual experience
- **Hermes 落地**：fact 被检索 3 次以上 → 升华为 `~/.hermes/skills/` 下可执行 skill
- **新增**：`~/.hermes/skills/abcd-learner/` skill 目录
- **wrapper 更新**：`idle_learning_wrapper.sh` 在 orchestrator 之后加入 E 阶段

## 遗留问题
1. B方向 arXiv：缓存模式未解析 paper 标题/摘要入库
2. D方向 action_diversity：只输出状态，无结构化知识提取
3. skill crystallizer 目前只写 stub，需在 fact 检索 3+ 次时触发真正 skill 生成

## 验证命令
```bash
python3 ~/.hermes/scripts/batch_facts_from_log.py   # 应写入>0条
python3 ~/.hermes/scripts/cve_lite.py scan ~/.hermes/hermes-agent/venv --severity HIGH
python3 ~/.hermes/skills/abcd-learner/abcd_learner.py
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts"  # 应增长
```

## 关键文件
- `~/.hermes/scripts/batch_facts_from_log.py` — 重写，动态提取
- `~/.hermes/scripts/cve_lite.py` — 新增，生产级 CVE 扫描
- `~/.hermes/scripts/idle_learning_orchestrator.py` — 更新调用 cve_lite
- `~/.hermes/scripts/idle_learning_wrapper.sh` — 加入 E 阶段
- `~/.hermes/skills/abcd-learner/` — 新增 AgentFactory 格式 skill
- `~/.hermes/memory_store.db` — 97 → 121 条

## 全网现成方案
| 项目 | Stars | 用途 | Hermes集成 |
|------|-------|------|----------|
| AgentFactory (zzatpku) | 57 | subagent → skill | 引入 skill crystallizer |
| cve_lite.py (Scottcjn) | - | 零依赖 OSV 扫描 | 替换自写 cve_scan |
| CVE-KGRAG (Yuning-J) | 17 | CVE 知识图谱+RAG | 未来结构化 |
| autoagent (kevinrgu) | 4488 | 自主改配置跑 benchmark | skill_vetter 借鉴 |
