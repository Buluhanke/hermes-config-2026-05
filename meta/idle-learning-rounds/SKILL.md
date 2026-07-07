---
name: idle-learning-rounds
description: 多方向 A→B→C→D 扫描的 idle_learning cron 任务模式 — 浏览器产线 / 论文 / 安全 / 执行层 4 个方向跑实际命令（不是只写日志），必须落地 fact_store，验证工具链 3 个工具的真实输出，产 3 行式大白话报告。Load when 收到任务含「idle_learning / A→B→C→D / 学到的必须安装并跑一遍 / 多方向扫描 / 浏览器产线+论文+安全+执行 / batch_facts_from_log / fact_decay」任意一条。
---

# idle-learning-rounds — A→B→C→D 多方向扫描落地模式

**核心定位**: cron 触发的多方向「学习+落地」轮次任务。区别于 `hermes-daily-learning-summary`（每日写 MEMORY.md），本 skill 是 **事实采集 + 落地 fact_store + 工具验证 + 3 行报告** 的标准化流水线。

**核心铁律（用户原话）**: 「学到的必须安装并跑一遍——光记日志不行」「每个方向完成后必须落地到 fact_store」「跑完后**必须**调用 batch_facts_from_log.py」。

---

## 一、4 方向标准流程（A→B→C→D 顺序固定）

每个方向都**跑实际命令**，不接受「只输出计划」。

| 方向 | 关注域 | 实际跑的命令 |
|---|---|---|
| **A 浏览器产线** | 浏览器识别 4 层链路健康度 | `lsof -i :9222 + pgrep -f cua-driver + ls ~/.hermes/node_modules/@sawyerhood/dev-browser + mcp_cua_driver_health_report` |
| **B 论文 / AI 知识** | AI 圈 24h 新动向 | `python3 ~/.hermes/scripts/ai_radar_brief.py`（643→585 簇聚类，Top 12 加权） |
| **C 安全 CVE** | 本机依赖漏洞 | `python3 ~/.hermes/scripts/cve_scan.py`（OSV.dev 公开 API，扫描 20 个关键包） |
| **D 执行层** | 动作多样性 / 触发链路 | `python3 ~/.hermes/scripts/action_diversity.py`（基于 `~/.hermes/state/script_router_history.jsonl`） |

**为什么是这 4 个方向**: 浏览器产线是 Hermes 最大杠杆（屏幕=眼 → 现在眼=浏览器识别 4 层 CDP/AX/视觉/OCR）；论文是知识保鲜；安全是负向 risk 面（v3.0 风险记忆）；执行层检测「做了多少事」+ 链路断裂。这是 `hermes-daily-learning-summary` 不覆盖的「实时+外部数据」面。

---

## 二、写入 fact_store — 强制步骤
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
- `新写入 = 0 + 跳过 > 0`：去重命中 OR 硬编码列表已 bootstrap 完，库稳定
- `新写入 = 0 + 跳过 = 0`：脚本可能扫错路径
- `新写入 > 0`：硬编码 FACTS 列表里有未落地的发现

**⚠️ 2026-06-30 关键发现**: 此脚本**不是从 `idle_learning_log.md` 动态解析**，而是内置硬编码 `FACTS_FROM_LOG` 常量列表。一次性 bootstrap 后就稳态 → 本轮新发现全部丢失。看到 0 新写时**必须检查本轮是否实际有新发现**，有则走 `references/fact-store-direct-write.md` 的 sqlite3 直写 fallback。
## 三、衰减检查 — 第二强制步骤

```bash
python3 ~/.hermes/scripts/fact_decay.py
```

输出 schema：
```
📊 fact_store 衰减统计 (N 条)
  ✅ 活跃 (trust > 0.15): 77
  ⚠️  低信任 (0.05 < trust ≤ 0.15): 0
  ❌ 已过期 (trust ≤ 0.05): 0
📈 平均 trust: 0.557
```

**健康判定**：活跃率 ≥ 95% + 平均 trust ≥ 0.4 = 健康。任一低于阈值要触发 `fact_decay --prune` 清理。

---

## 四、3 个工具实测验证（必须步骤）

不是「跑一遍看到 exit 0」就完，要看到**真实业务输出**：

```bash
# 1. trust 分布（看最旧/最新条目的衰减轨迹）
python3 ~/.hermes/scripts/fact_decay.py --score
# 期望: 看到 N 条排序后的 trust 数据（如 30 条从高到低）

# 2. 视觉缓存统计（warm_cache.py stats）
python3 ~/.hermes/scripts/warm_cache.py stats
# 期望: entries / max_entries / ttl_seconds / hit_rate / error_rate 都有数值
# 注意: 实际脚本是 warm_cache.py（vision_cache.py 是旧名，已废弃）

# 3. 快照列表（rollback 触发证据）
python3 ~/.hermes/scripts/rollback_manager.py list
# 期望: 看到 N 个快照，含 ID + 名称 + 时间 + 已恢复状态
```

**判定标准**：每个工具的输出里必须有具体数字（N 条记录 / M 包 / X% 命中率），不能是「没数据就完事」。

---

## 五、3 行式大白话报告（v2.3 用户偏好）

**严格 3 行结构**，每行不超过 2 句话：

```markdown
🛠️ 本轮修了什么：<具体脚本名 + 文件名 + 关键改动>（不超过 100 字）

📊 fact_store 现状：活跃 X / 低信任 Y / 过期 Z，平均 trust=N.NNN。最旧/最新条目编号 + trust 值（衰减轨迹参考）

🎯 下次轮次该关注的 1-2 个新发现：<具体到一个 fact ID 或脚本名 + 为什么值得关注>
```

**反向案例**（违规）：6+ 行的详细 report、长段 markdown 解释、用 bullet 列表代替行内格式。这是用户已多次抱怨的「嘴炮模式」。

---

## 🚦 零新 → 静默门（2026-07-03 新增，最高优先级回调门）

**背景**：本 skill 对应的 cron（夜间ABCD自学轮次 + abcd-auto-fix）已跑 38 轮，**0 条有用 fact_store 知识落地**，用户质疑"到底学到东西了吗"。每次跑都消耗 LLM token 但产出为零。

### Gate A — 数据源变化检查（跑 ABCD 前必走）

```bash
# 自上次运行以来，以下有任何变化吗？
# 1. GitHub releases 有新 tag？（curl -I 304 = 无变化）
# 2. fact_store 自上次新增 > 0？
# 3. script_router_history.jsonl 自上次以来行数有变？
# 4. cve_scan 上一次检查 < 7 天？
→ 全部 NO → exit 0，不跑 LLM，不写报告，不推送
→ 有任何 YES → 才进入 ABCD 流程
```

### Gate B — 连续跳过自动降频

```sql
-- 在 fact_store 写一条 "idle_learning_skip: 2026-07-03 无变化跳过"
sqlite3 ~/.hermes/memory_store.db "INSERT OR IGNORE INTO facts (content, category, tags, trust_score, created_at, updated_at) VALUES ('idle_learning_skip: 2026-07-03 无变化跳过', 'idle-learning', '[\"automation\",\"skip\"]', 0.75, strftime('%s','now'), strftime('%s','now'))"
```

- **连续 3 次跳过** → 自动降频：每天 → 每 3 天 → 每周
- **连续 7 次跳过** → 自动建议用户删除此 cron

### Gate C — abcd-auto-fix token 门（每天 6am）

`abcd_auto_fix.py` 修复 LLM 调用方式（2026-07-08）：
- **旧方式**: `hermes "-z" prompt "chat"` — `hermes` CLI 不存在 `-z` 参数，subprocess 调用永远失败
- **新方式**: 通过 API server (`localhost:8642`) 调 LLM，用 `urllib.request` 走 `POST /v1/chat/completions`，API key 从 `.env` 加载
- `abcd_auto_fix.py --dry-run` 验证是否有 pending gap，无 gap 则 0 token 消耗

**Gate 逻辑**：
1. 先看 `abcd_auto_fix.py --dry-run` 是否有 pending gap
2. **有 gap** → 才调 LLM agent 修
3. **无 gap** → exit 0，0 个 API call
4. **连续 7 天无 gap** → 自动建议删除此 cron

### 报告规则（覆盖所有产出）

- **零新知识 **→ **静默**：不写 `daily_learning_20260703.md`，不推 Telegram，不走 report
- **本次确实有发现** → 才产 3 行式报告（五节格式）
- **判断标准**：`sqlite3 ~/.hermes/memory/fact_store.db "SELECT COUNT(*) FROM facts WHERE created_at > strftime('%s','now','-1 day');"` > 0 才能发报告

### 关联
- `proactive-execution` Failure 62（v1.17.0）— 本回调门的上层原则
- `hermes-daily-learning-summary` 第九节 delivery gate

---

## 六、踩过的坑

- **「skills/idle_learning/scanner.py 不存在」**: 用户 prompt 里常引用 `skills.idle_learning.scanner.scan_papers()`，尝试此方法会导致 `ModuleNotFoundError: No module named 'skills.idle_learning'`。**实际只有 `scripts/idle_learning_orchestrator.py`**。**修法**: 用 `scripts/ai_radar_brief.py` 替代 B 方向，路径在 `~/.hermes/scripts/`，不是 `skills/idle_learning/`。**不要试图创建 skills/idle_learning/ 目录**。
- **「action_diversity.py 报无记录是正常的」**: 用户不在家时没执行任务 → 7 天无数据。**不要因此报告失败**，明确说「预期内」。
- **「cve_scan.py 全 0 CVE 不代表扫描失败」**: OSV.dev API 命中即算成功，全 0 是当前依赖健康度的正面信号。
- **「vision_cache stats 报 0 entries 不要慌」**: 实际脚本是 `warm_cache.py`（vision_cache.py 是旧名，已废弃）。0 entries + max_entries=200 + error_rate=0% 已经是完整元数据输出，不代表缓存失效。
- **「batch_facts_from_log.py 0 新写 = 本轮发现丢失」**(**2026-06-30 关键发现**): 脚本**不是从 `idle_learning_log.md` 动态解析**, 而是内置一个硬编码的 `FACTS_FROM_LOG` 常量列表(~28 条历史发现快照)。脚本一次性 bootstrap 完就进入稳态。本轮新发现(A 方向 ollama 状态、B 方向 OSU-NLP 重抓论文、C 方向 OSV 全 0、D 方向周末无人值守)**全部不在硬编码列表里** → 0 新写 = 数据丢失。**修法**: 发现 `batch_facts_from_log.py` 报 0 新写 + 本轮确实有新发现时, **直接走 sqlite3 写 fact_store**, 不要就此收手。正确 DB: `~/.hermes/memory_store.db`, 表 `facts(fact_id, content, category, tags, trust_score, retrieval_count, helpful_count, created_at, updated_at)`。INSERT: `INSERT OR IGNORE INTO facts (content, category, tags, trust_score, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)`. 注意字段是 `content` 不是 `text`/`topic`。
- 「batch_facts_from_log.py 报 0 新写 ≠ 任务失败」: 脚本内置去重，28 跳过说明之前的发现已全部落地（**仅当本轮无新发现时适用**）。上面那条 pitfall 覆盖「本轮有新发现」的场景。

- 「browser 健康度检查命令缺失导致 A 方向挂起」(2026-07-02 本轮确认): 弃本地 VLM 后 A 方向脚本换 `lsof -i :9222 + pgrep -f cua-driver + mcp_cua_driver_health_report`，**前置依赖**: Chrome 启 --remote-debugging-port=9222 + cua-driver 安装并授权。**修法**: cron 跑前用 `command -v lsof && pgrep cua-driver` 探活，缺则标"暂停因 X 未配"不重试。

- 「batch_facts_from_log.py 0 新写 = 本轮发现丢失」(2026-07-02 确认): 脚本内置硬编码 `FACTS_FROM_LOG` 常量 (~28 条历史快照)，非动态解析 log。本轮新发现 (ollama 未安装/scanner.py 缺失/20 包 0 漏洞/周末无记录) **全不在硬编码列表** → 报 "✅ 新写入 0 条" = **数据丢失**。**修法**: 0 新写 + 本轮有新发现时，**直接 sqlite3 写 fact_store.db**，fallback snippet 见 `references/fact-store-direct-write.md`。
- **「rollback_manager list 只有 2 快照」**: 这是 2026-06-18 装 chrome-devtools-mcp 的回滚保护，**不是说 rollback 失效**，而是破坏性操作少。

- **「搜索引擎全失败时别死磕」**（2026-07-01 cron 经验）：任务「搜索社区最新技巧」时，SearXNG 默认 `general` 类目可能 0 结果，换 categories=['general','news'] 仍空，web_search DuckDuckGo 后端也报 `No results found`。**修法**: 0 思考直接 fallback 到 `web_extract` 抓官方文档/仓库 URL：`https://<project>.nousresearch.com/docs`、`https://github.com/<org>/<repo>`、`https://github.com/<org>/<repo>/releases`。官方 docs 通常 LLM-summarize 后 5k 字内含足够干货，再叠加 `releases` 页面抓最近 1-2 个版本的 highlights，足够喂 3 条技巧到 MEMORY.md。**踩坑信号**: 同一个 query 跨 2 个搜索引擎 + 2 个 query 变体都 0 结果 → 立刻切官方源，不要再换 query 词。

- **「SearXNG MCP 不等于 web_search」**（**2026-07-02 08:01 cron 第三次确认，强制 1-call 切换**）：5-7 个并行 `mcp_searxng_web_search` 调用**全 0 返回空字符串**（连错误都没有），同样的 query 在 `web_search` 立刻命中 10 条。**根因**：SearXNG 实例未启用/默认类目空/限流/MCP 包装吞 error。**强制修法**：harvest 类任务（每日 skill 采集 / 联网搜索找方案 / 找社区技巧）**永远首选 `web_search`**，把 `mcp_searxng_web_search` 视为完全不可用——本会话验证 4 次全是空字符串零反馈。**判断标准**：1 个 `mcp_searxng_web_search` 返回空字符串 → 0 思考立刻切 `web_search`，**不要再加第 2 个 SearXNG 调用**。1 call 即切，不是 3 次才切。

- **「SPA 类 skill hub 站（agentskills.io 类）curl 抓不到元数据」**（2026-07-01 cron 经验，Ponytail 真值）：任务「去 agentskills.io 找对应 skill 安装」时，`curl https://agentskills.io/` 返回 107KB HTML，但里面只有 `_next/static/chunks/*.js` 加载逻辑和 `404 NEXT_HTTP_ERROR_FALLBACK`，**没有 skill 列表、没有标题、没有描述**——Next.js SPA 内容由客户端 JS 渲染，server-side HTML 是空的。`web_extract` 同样返回空内容（HTML 体积大但全是 JS）。**修法**：0 思考跳过 SPA hub，直接走 Ponytail rung 4 已知方案：`web_search query + "site:github.com"`，或 `https://github.com/<org>/<repo>` 拿 README + releases。GitHub raw README 是纯 markdown，curl 一次拿到全部信息。**判断信号**：`curl <url> | grep -c "skill\|SKILL"` 命中 < 5 → SPA，站本身没有 SSR，跳过。**反例**: skillhub.cn / cocoloop hub / mcp.so 这类纯 SSR 站仍可 `curl + grep` 拿索引。

- **「AI 咨询站点 (chat.deepseek.com / chatglm.cn) 走 browser_navigate 必撞登录墙**（2026-07-01 12:00 cron idle 学习经验，工具调用前置约束）：任务里要求「打开 chat.deepseek.com 或 chatglm.cn 提问」时，`browser_navigate https://chat.deepseek.com/` 返回 sign_in 页，chatglm.cn 超时。**根因**：`browser_navigate` 是 Browserbase 远程代理，**不带本地浏览器登录态**——浏览器在远端跑，cookies/session 是 Browserbase 那个容器的新 profile，不是用户 Mac 上的 Chrome。**SOUL.md 列的"已登录 Gemini/Doubao/ChatGLM/DeepSeek/Grok/ChatGPT"指本地 Chrome profile**，Browserbase 完全用不上。**修法三步走**（按 Ponytail 决策梯）：① **首选**：直接 `web_extract` 抓官方 docs / GitHub README / `/releases`，纯 markdown 无登录墙——问的问题（"X 命令怎么用"）官方文档 99% 已答；② **次选**：用已登录的本地浏览器（`mcp_chrome_devtools_mcp_*` 连本地 9222 端口），但要 Gemini/Doubao/ChatGPT 这种 SOUL 标"已登录"的站点，不要指望 deepseek/chatglm；③ **兜底**：self-reasoning，ponytail rung 1 YAGNI——问的问题如果是"哪个 skill 该用"，agent 自己的 fact_store + 已有 skill 已经够答，**别为提问而提问**。**判断信号**：`browser_navigate <ai-chat-url>` 返回的 snapshot 含 `textbox "請輸入手機號碼/電郵地址"` / `button "登入"` / 含 `sign_in` 的 URL → 立刻 abort，不要尝试输入手机号/密码（绕过登录 = 安全违规 + 用户没授权）。**反向教训**：不要在登录墙耗 ≥2 个 tool call，ponytail 哲学下"绕不开就别绕"，1 call 试不通立刻换路径。

- **「chatglm.cn 提交后卡 '思考' 按钮 145s+ 不返回」**（2026-07-01 13:00 cron idle 学习经验，AI 站点另一类卡点）：任务要求"去 chatglm.cn 提问"但**已登录态仍卡死**——`browser_type` + `browser_click(e46 提交)` 后页面状态变成"思考"，等了 145s 仍无响应，3 次 `browser_snapshot` 返回相同 DOM。**根因推断**: GLM-5.2 长 reasoning chain 偶发不返回（rate limit / 后端 bug / 长上下文卡死） / Browserbase 代理超时断开 websocket 但前端无重连。**修法**: ① **不要死等 AI 站点响应** — cron job 没有"等回复"语义，最多等 60s；② **首选立刻换站点**: Gemini / Doubao / ChatGPT (SOUL 标已登录, 本地 Chrome profile 可用) 重新发问；③ **次选 self-reasoning**: Ponytail rung 1 YAGNI — 问"X 命令怎么用 / Y 问题根因"，agent 自己的 fact_store + 已有 skill + 官方 docs 已经有答案, 别为提问而提问；④ **兜底写半成品**: 如果问题确实是 agent 知识盲区, 立即把"我知道的 70% 答案"写出来 + 标注"未确认部分", 不阻塞 cron。**判断信号**: 同一 AI 站点 snapshot 3 次返回相同 DOM + 按钮文字为"思考" → abort, 不等第 4 次。**反向教训**: 之前 12:00 cron 已经踩过"登录墙"坑, 13:00 这次踩"提交后卡死"坑 — **两类都是 AI 站点不可靠信号**, 应一并 fallback 到 web_extract 官方 docs。

- **「hermesagent.org.cn/forum 是腾讯频道私密群，不可抓取」**（**2026-07-02 cron 社区巡逻确认**）：`browser_navigate hermesagent.org.cn/forum` 返回的页面只有二维码 + 4 条论坛说明段落，没有公开讨论内容。实际论坛在腾讯频道（微信/QQ 扫码加入）。**修法**：搜索中文社区内容时，跳过 forum 页面（它是死路），用 `web_search + 中文 query` 直接抓知乎/CSDN 等公共站点的 Hermes 文章。**判断信号**：页面 snapshot 只显示 "微信 / QQ 扫码进入腾讯频道" + 二维码图片 → 没有再往下抓的必要，直接切 web_search。

- **「MEMORY.md 超 12KB 压缩 playbook」**（**2026-07-02 08:01 cron 本轮踩坑，4 步变体步骤4实战 SOP**）：本轮做完 step1-3 后追加条目，wc -c 显示 16.4KB（之前压缩完的"14KB ok"也没守住）。**绝不能简单 append**，必须先压。**3 步压缩法**：
  1. **`wc -l` 看行数 + `head/tail` 读首尾**：先看整体结构（54 行 vs 160 行差异巨大）
  2. **找同质化 cron 块合并**：多个 `[2026-06-30 cron]` / `[2026-07-01 cron]` 段单条信息互相重复 → 按日期分块压缩成 1-2 行"速查"格式，每个原段保留 1 个最高价值 bullet。**判断标准**：每条 bullet 是否能独立引用？还是只是同一主题的变体？独立引用保留，变体合并
  3. **`patch` 工具大块替换**：用 `patch mode='replace' old_string="<整段>" new_string="<压缩版>"`，**不要逐条删除**（大 patch 比多次小 patch 快 5x 且更安全）
  - **目标大小**：6-8KB / 50-60 行。14KB 是"还行"但容易"再 append 一次就爆"。**硬上限 12KB**，超出必压
  - **保留判定**：压缩时问 3 个问题——①这是 fact（环境/偏好）还是 log（具体会话过程）？→ log 删 / fact 留 ②半年内还会被引用吗？→ 否就删 ③能浓缩成 1 行速查吗？→ 是就压、否就删
  - **本轮实证**：160 行/16KB → 54 行/6KB，删了 4 个冗余 cron 段+skill-manage 安装细节+装法代码块，**保留全部 5 条关键规则（spec 约束/name mismatch/kanban/ollama 守护/spec 验证命令）**

- **「`patch` tool 重复失败时立刻切 `write_file`」**（2026-07-03 cron 实证，4 步变体步骤 4 实战）：cron 跑「写入 MEMORY.md」时，`patch mode='replace' old_string="..." new_string="..."` 报 `Found 2 matches for old_string. Provide more context to make it unique, or use replace_all=True.` → 加上下文重试 → 还是 2 matches → 第 4 次触发 `same_tool_failure_halt` 强制中断整个 patch 路径。**根因**：MEMORY.md 已 11.5KB（远超 2200 字符 5 倍），`旧字符串 + 末尾 3 行上下文` 这种片段在文件里出现 ≥2 次完全可能（多个章节结尾同格式）。**3 步修法**：① **第 1 次 `Found N matches` 就换路径**，不要加 context 重试——同一个文件重复同模式串的概率随 KB 增长陡升；② **首选 `read_file` 拿文件最后 ~20 行** → `terminal` 用 `cat >> ~/.hermes/MEMORY.md << 'EOF'\n...新内容...\nEOF` append（heredoc 不会撞 unique-match 问题）；③ **兜底 `write_file` 整文件重写**（MEMORY.md 大于 12KB 时正好顺便走压缩 playbook）。**判断信号**：连续 2 次 `patch` 都报 `Found N matches` → 0 思考切 `write_file` 或 `cat >> heredoc`，不再试第 3 次 patch。**反向教训**：本次踩坑烧了 4 个 tool call 才被 `same_tool_failure_halt` 强停，下个 cron 1 次撞 `Found N matches` 就切。

- **「`mcp_chrome_devtools_mcp_*` (本地 9222 CDP) 是 SOUL 已登录 AI 站点的正确入口」**（2026-07-03 cron 实证，4 步变体步骤 3 实战）：上次 cron 12:00/13:00 已经踩过 `browser_navigate` (Browserbase) 撞登录墙 + 卡思考——这次发现 `mcp_chrome_devtools_mcp_navigate_page("https://chatglm.cn/...")` 直接进了已登录会话（GLM-5.2 在工作、显示"升级"按钮 = 登录态），`mcp_chrome_devtools_mcp_press_key("Enter")` 提交也成功，~20s 出答案。**根因对比**：`browser_navigate` 走 Browserbase 远端代理（无本地 cookies），`mcp_chrome_devtools_mcp_*` 走本地 Chrome `--remote-debugging-port=9222` CDP（带本地 profile 登录态）。**修法**：4 步变体步骤 3「Ask AI site」重新排序：① **首选 `mcp_chrome_devtools_mcp_*` 访问 SOUL.md 标已登录的 6 个站点**（ChatGPT/Gemini/Doubao/ChatGLM/DeepSeek/Grok）—— 直接拿到登录态，免登录墙；② 撞登录墙才 fallback 到 `web_extract` 抓官方 docs 或 self-reasoning；③ **永不**用 `browser_navigate` 访问 AI 站点（Browserbase 无登录态 = 100% 撞墙）。**判断信号**：`mcp_chrome_devtools_mcp_list_pages` 返回 ≥1 个本地 Chrome tab = 连接 OK，可直接 `navigate_page` + `type_text` + `press_key Enter` 走完整 4 步对话。**反向教训**：之前 6 节 pitfall 只覆盖 `browser_navigate` 撞墙，没提"换 `mcp_chrome_devtools_mcp_*` 就解了"——是本次 cron 的关键补全。

- **「大 skill 仓库最小子集安装（obra/superpowers 类）」**（2026-07-03 cron 实证，4 步变体步骤 2 实战）：`obra/superpowers` 244k stars + 13 个 skill 子目录（brainstorming / systematic-debugging / verification-before-completion / TDD / plans / subagent-driven-development 等），但原作不直支持 Hermes 工具调用；`Labhund/hermes-superpowers` 衍生版 20 stars / 6 commits / 3 月前最后更新，活跃度过低。**GLM-5.2 决策**：装原作做参考底本 + **只取需要的 1-2 个 skill 目录**手动改写进 `~/.hermes/skills/<category>/<name>/`，不引整框架。**3 步修法**：① **`git clone --depth=1 https://github.com/<org>/<repo>.git /tmp/<probe>`**（depth=1 省 90% 时间 + 流量，不读历史 commits）；② `ls /tmp/<probe>/<subdir>/` 找到目标子目录，`head -40 <subdir>/SKILL.md` 看 frontmatter + HARD-GATE 段落确认质量；③ `mkdir -p ~/.hermes/skills/<category>/<name> && cp -r /tmp/<probe>/<subdir>/* ~/.hermes/skills/<category>/<name>/ && rm -rf /tmp/<probe>`。**关键检查**：`head -5 ~/.hermes/skills/<category>/<name>/SKILL.md` 必须有完整 frontmatter（`name:` + `description:`），且 `name` 字段 = 目录名（spec 强制）。**资源红线**：`/tmp/probe` 用完必删，否则下次 idle cron 又 clone 一次占用磁盘。**对比之前 "ClawHub skill inspect/install 解析失败，需走 GitHub clone" pitfall**：那次是 install 管道失败 fallback；这次是**有 install 路径但不完美 + 仓库太大**时的主动最小子集提取策略。两者互补。：跑「搜索社区最新技巧」类 cron 时，搜索引擎全部超时（SearXNG 0 返回 + DuckDuckGo 报 `error sending request timed out`）→ fallback 抓官方 docs (`https://hermes-agent.nousresearch.com/docs` + GitHub README) → 抓到 v0.17.0+ 关键技巧 `/learn` 命令。**正确做法**: 抓回官方 docs → 不要只写进 MEMORY.md 当 log → **立即 `/learn <docs-url>`** 把它固化为一个可复用的 skill (走 `skill_manage` tool, 全平台可用). 三个层次的落库: ① MEMORY.md (本日学习摘要) → ② fact_store (新事实条目) → ③ **新 skill (从 docs 提炼的工作流)**. 只做 ① 是浪费数据. **修法**: 抓到有价值的 docs → 0 思考 `/learn` → 写完 `ls ~/.hermes/skills/<new>/SKILL.md` 验证 → 才认为本轮 cron 真的产生价值. 详见 `hermes-skill-optimization/references/learn-command.md`.

- **「4 步 idle 学习流中途停止」**: 收到「空闲时做 X」任务时，只执行了第 1 步（搜社区）就停止，**未继续安装skill、问AI站点、写MEMORY** 的后续步骤。**这是严重违反 v3.1 铁律的行为**。**修法**: 一旦进入 4 步流程（search→install→ask→write），必须完成所有 4 步才能结束。**不允许在任意中间节点停止或询问「要不要继续」**。如果第 1 步搜不到有用技巧，应立刻转向官方 docs 或内置功能（如 `/learn` 命令）寻找可落地的知识点，而不是放弃任务。\n\n### 变体流程技巧来源参考文件

- `references/official-tips-guide-annotated.md` — Hermes 官方 Tips & Best Practices 页面注释版 (2026-07-01 采集)，含 12 个技巧的用法笔记、终端兼容性、价值评级。变体步骤 1「Search 社区」时优先参考此文件，命中即可跳过搜索引擎。
- `references/tips-from-official-page-2026-07-02.md` — 官方 Tips 页面后半部分技巧 13-31 (2026-07-02 采集)，含 memory/skills 管理、性能优化、通讯技巧、安全配置。配合上一文件覆盖全部 31 个官方技巧。
- `references/community-research-sources.md` — 2026-07-02 社区巡逻经验，SSR/SPA/不可抓取来源矩阵，含中文搜索关键词建议、各来源可靠性验证。变体步骤 1 行动前快速决策用。
- `references/fts5-cjk-trigram-tech-note.md` — (2026-07-03 采集) FTS5 trigram vs unicode61 中文搜索技术笔记。Hermes state.db 内置 messages_fts_trigram 索引 + 3 trigger 同步，session_search 已具备 CJK 搜索能力。涉及 `sqlite_master` schema 检查、trigram 原理、验证 SQL。
- `references/tips-from-v018-release-notes.md` — Hermes v0.18.0 "Judgment Release" (2026-07-01) 关键新特性实战档案：`/learn <anything>` 自动提炼 skill / `/journey` 时间轴 / `/goal` 完成契约 / `/undo` / MoA 一等公民 provider / 后台 fan-out 子 agent。含 2026-07-02 18:00 cron 完整 5-call 4 步流水线 (search→install→ask→write) 验证记录。变体步骤 1「搜社区」时优先加载本文件, 命中 `/learn` / `/goal` 即可跳过 90% 提炼工作。

- `hermes-daily-learning-summary` — 姐妹 skill（每日 MEMORY.md 写入，24h 数据汇总），本 skill 是「外部数据扫描 + fact_store 落地 + 工具验证」的**实时面**，两者输出目标不同（MEMORY.md vs fact_store + tool reports）
- `verification-before-reporting` — 验证原则（exit code / 文件存在 / API 响应 / 实际测量值）
- `proactive-execution` — 主动执行铁律（不反问 / 不等授权 / 失败 1 次换方法）
- `cross-channel-sop-sync` — 「在家不推送」跨渠道铁律 v2.6：cron 触发的本会话只在回报，不推 Telegram

## 十、orchestrator-first 关键路径（2026-07-03 cron 验证）

`idle_learning_orchestrator.py` 是 **5 阶段流水线** 的单一入口：

1. batch_facts_from_log.py
2. fact_decay.py
3. vision_cache（健康检查）
4. rollback_manager（健康检查）
5. action_diversity

**反模式**: cron 消息把 batch_facts_from_log + fact_decay 列为手动步骤 → 跑完 orchestrator 后**又手动跑一遍** batch_facts → 第二次输出"新写入 0 条 fact, fact_store 总计 87 条"看起来"失败"。

**正路**: 0 思考先跑 `python3 ~/.hermes/scripts/idle_learning_orchestrator.py`（一次 exit=0, ~0.06s）→ 它的 stdout **已经包含** batch_facts 结果 + fact_decay 衰减统计 → 不要再手动跑这两个脚本。**手动步骤只保留** A/B/C/D 4 方向扫描 + 3 工具验证。

**2026-07-03 实证 baseline**: orchestrator 跑完输出 `fact_store 总计: 87 条 / 活跃 87 / 低信任 0 / 过期 0 / 平均 trust 0.522`。下次 cron 跑前对照这个数字，差太大说明 fact_decay 公式或硬编码 FACTS 列表变了。

## 十一、A 方向「0 进程 = 健康」判定（2026-07-03 cron 验证）

`ps aux | grep -iE 'ollama|screen_watcher|trigger_handler' | grep -v grep` 跑出 **0 行** = 视觉产线全卸载状态 = **healthy**。与 fact #114 "ollama 卸载 → 4 层浏览器方法论" 自洽：

- 屏幕 UI grounding 走浏览器原生 a11y（trust=0.921）
- 24GB Mac mini 永远云端 VLM > 本地 VLM（trust=0.921）
- vision_cache.py stats 0 entries + max_entries=200 + error_rate=0% = 缓存元数据完整

**反判定**: 如果 `pgrep ollama` 返回 PID → 立即 fact_decay 触发检查 + memory_watchdog 评估是否要 OLLAMA_KEEP_ALIVE=0 卸载（fact #108 vision_cache 保护条款）。

## 八、参考文件 / 脚本

- `references/fact-store-direct-write.md` — `batch_facts_from_log.py` 报 0 新写 + 本轮有发现时的 sqlite3 直写 fallback（schema / snippet / trust 区间 / 2026-06-30 案例）
- `references/toolchain-reference.md` — 6 个工具的 CLI 参数表（fact_decay / spatial_memory / rollback_manager / batch_facts_from_log / ai_radar_brief / cve_scan）
- `references/sample-output-snippets.md` — 2026-06-30 实跑样本输出，4 方向 + 3 工具 + 报告原文，可作 baseline 对照
- `references/hermes-self-evolution-gepa.md` — NousResearch/hermes-agent-self-evolution (DSPy+GEPA) 安装 + 跑 SOP + 适用判断。2026-07-02 采集，**未本地安装**，下次 cron 可真跑 `evolve_skill --skill hermes-see-act --eval-source sessiondb` 试水
- `references/community-skill-installation-patterns.md` — 社区 skill 安装模式汇总表：sources/installation-methods/security-scanner-verdicts/blocked-vs-installed 对照 (2026-07-03 采集)。变体步骤 2「找 skill 安装」时优先参考此文件，命中 direct install 命令即可跳过全搜索流程。
- `scripts/idle_round_runner.sh` — 一键跑完 A→B→C→D + fact_store + 3 工具验证 + 健康判定（exit code = 健康度：0=健康, 1=失败, 2=fact_store 不达标）。**首次使用前需 `chmod +x`**，或直接用 `bash idle_round_runner.sh` 调用（不依赖 +x 位）

<!-- 变体流程已移至 references/idle-learning-variant.md -->