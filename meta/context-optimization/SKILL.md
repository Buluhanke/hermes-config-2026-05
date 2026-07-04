---
name: context-optimization
description: Hermes Agent 上下文优化 — AGENTS.md 高级用法、token 消耗控制、工具门控、模型路由、会话压缩、Response Truncated 5 因 5 修、memory 文件大小管理。涉及 Hermes 上下文管理 / token 优化 / AGENTS.md 配置 / 工具禁用 / 模型路由 / Response Truncated 必加载。
version: 1.1.0
created: 2026-07-01
updated: 2026-07-02
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [context, token, optimization, agnets-md, skills]
    category: meta
---

# Context Optimization — Hermes 上下文与 Token 优化

## 核心原则

Hermes 每次 API 调用有 **~13.9K tokens 的固定开销**（8K-10K 工具定义 + 2K-3K 系统提示 + 1K-5K 记忆文件 + 0-2K 活跃技能）。优化目标是**降低每轮成本**同时**保持执行质量**。

---

## 一、AGENTS.md 高级用法（10 条实战规则）

> 来源：2026-07-01 通过 chatglm.cn GLM-5.2 深度分析，结合官方文档验证。

### 1. AGENTS.md 是"项目级指令"不是 README
- 只写"怎么在这个项目里干活"，不写"历史背景"或"项目百科"
- 反面：把所有项目架构、API 说明、数据库 schema 都塞进去 → token 爆炸
- 正面：只写编码规范、测试命令、工具偏好、常见坑点

### 2. 项目规则文件只选一个，别堆叠
- 优先级：`.hermes.md` > `AGENTS.md` > `CLAUDE.md` > `.cursorrules`
- 命中第一个就停止搜索，**只加载一个**
- 不要在根目录放 AGENTS.md 又在子目录放 .hermes.md → 浪费 token

### 3. 控制上下文总量
- AGENTS.md + SOUL.md + MEMORY.md 总和影响每轮 token 开销
- 目标：combined < 3K tokens（约 12K-15K 字符）
- 定期审查：`wc -c ~/.hermes/SOUL.md ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md`

### 4. 分层加载策略
- 根目录 AGENTS.md：全局加载，每次会话注入
- 子目录 AGENTS.md：懒加载，只在 cd 到该目录时注入
- 利用这个特性：把项目特定的规则放子目录，减少全局上下文

### 5. 引导工具使用
- 在 AGENTS.md 中声明项目特定的工具偏好：
  - "优先用 rg 不用 grep"
  - "测试用 pytest 不用 unittest"
  - "代码格式化用 black 不用 yapf"
- 减少 agent 在工具选择上的推理成本

### 6. 与 Skill 系统协同
- AGENTS.md 写**通用规则**（编码规范、项目约定）
- Skill 写**复杂流程**（多步骤工作流、故障处理）
- **不要把 Skill 内容塞进 AGENTS.md** → 违反渐进式披露原则

### 7. 保持简洁
- 每条规则用一句话表达，不要长篇大论
- 用 bullet points 代替 paragraphs
- 去掉"为什么"只留"怎么做"（原因在 skill 里说明）

### 8. 利用上下文文件分工
| 文件 | 职责 | 加载时机 |
|------|------|----------|
| SOUL.md | 人格/风格 | 每次会话 |
| MEMORY.md | 关键事实/偏好 | 每次会话 |
| AGENTS.md | 项目规则 | 按目录加载 |
| Skill | 复杂流程 | 按需加载 |

### 9. 避免"记忆堆"模式
- ❌ "上次我们讨论了 X，结论是 Y，下次记得 Z..."
- ✅ "项目使用 PostgreSQL + Alembic 做迁移"
- 记忆类信息走 `memory` tool，AGENTS.md 只写规则

### 10. 定期清理
- 每月审查一次 AGENTS.md，删除不再适用的规则
- 被 skill 替代的规则 → 从 AGENTS.md 移到 skill
- 过期的约定 → 直接删

---

## 二、Token 消耗优化策略

### 策略 1：禁用不用的工具
每个工具定义占用 ~100-500 tokens。禁用不用的工具可减少 8-10K token 的工具定义开销。

```bash
# 查看已启用工具
hermes tools list

# 禁用不需要的工具
hermes tools disable browser_navigate browser_snapshot
hermes tools disable code_execute_python
hermes tools disable web_search
```

**注意**：禁用工具可能导致依赖它们的 skill 静默失败。

### 策略 2：工具门控（Lazy Loading）
```bash
# 启用工具门控
hermes config set tools.gating.enabled true

# 轻量工具始终加载
hermes config set tools.gating.always_loaded '["shell", "filesystem", "send_message"]'

# 重量工具懒加载
hermes config set tools.gating.lazy '["browser", "code_execute", "web_search", "mcp_*"]'
```

### 策略 3：模型路由
- Routine 任务 → 便宜模型（OpenRouter Qwen3.5-7B ~$0.07/M tokens）
- 复杂推理 → 贵模型（Claude Sonnet / GPT-5）
- 在 SKILL.md frontmatter 声明：
```yaml
---
name: deep-code-review
model: heavy  # 自动路由到贵模型
---
```

### 策略 4：会话压缩
长会话积累大量上下文，用 `/compress` 压缩：
```
/compress           # 手动压缩当前会话
```
- 适用场景：50+ 轮对话后，或 agent 变慢时
- 风险：summary 丢失细节，避免过度使用
- 验证：压缩后用 `/usage` 检查 token 变化

### 策略 5：Memory 文件瘦身
- MEMORY.md 上限 ~2,200 字符（**理论值，实际可放宽**）
- USER.md 上限 ~1,375 字符
- 定期清理过期事实
- 命令：`"清理你的记忆"` 或手动压缩
- **2026-07-02 实战验证的 MEMORY.md 真实预算**：2,200ch 是官方保守文档值，但实际 soft cap 应该是 **~12KB（再硬些 14KB）**。本机从 14.8KB → 16.4KB（cron 多次 append 没压）→ 压缩到 6KB / 54 行。**经验值**：
  - **6-8KB / 50-60 行 = 健康**（每行价值密度高）
  - **10-12KB / 80-100 行 = 警戒**（下次 append 必压）
  - **>14KB = 必压**（影响 cron 启动时延，token 注入开销）
  - **压缩方法**：①`wc -l` 看整体 ② 找同日期 cron 块合并（按日期分块压缩成"速查"）③ `patch` 大块替换整段，不要逐条删。详见 `idle-learning-rounds` 的 pitfall「MEMORY.md 超 12KB 压缩 playbook」

### 6. 重复段检测（2026-07-03 02:00 cron 实战发现）
**症状**: MEMORY.md 涨到 11.5KB 时，发现 113-132 行 = 92-112 行的完整复制粘贴（"## 问AI的两条路"重复两次）。逐行 `read` 看不见，patch 操作时 `Found 2 matches` 才会暴露。
**3 步检测法**（`wc -c` 看到 10KB+ 立即跑）：
1. **`diff <(sed -n '50,80p' FILE) <(sed -n '100,130p' FILE)`** — 截取可疑重复区段，diff 看是否一致
2. **按章节标题扫**: `grep -n "^## " ~/.hermes/MEMORY.md | awk -F: '{print $1}'` 拿所有 H2 标题行号 → 人工扫一眼是否同一标题出现 ≥2 次
3. **`tail -50 FILE` 看末尾** — 重复段常被 append 到文件尾（"再加一份保险"是常见编辑本能）
**修法**: `patch` 一次性删整段重复块，**不**用 append 模式（直接 write_file 整文件重写 = 顺便走压缩 playbook）
**反向教训**: 仅看 `wc -c` 大小不暴露重复，必须 diff/grep 双重验证。11.5KB 看似只超 5 倍，实际有 ~3KB 是无意义复制

### 7. web_extract 头尾截断的兜底（2026-07-03 02:00 cron 实战）
**症状**: `web_extract(urls=[tips-page], char_limit=12000)` 返回 `Showing 8,948 chars (head) + 2,963 chars (tail)` 提示，全文 21,877 chars 写到本地 cache 文件，需要 `read_file` 拿中间段。
**修法 3 步**:
1. 第一次 `web_extract` 不带 char_limit（或用默认 15000）拿头部，**记录 `[TRUNCATED] + 完整路径`** 提示
2. **直接 `read_file(path=cache_file, offset=N, limit=M)`** 拿中间段，**不要二次 web_extract** 浪费 token
3. 如果 cache 路径不可见（被 `untrusted_tool_result` 屏蔽），降级到 `browser_console(expression='document.querySelector("article").innerText.substring(OFFSET, OFFSET+LIMIT)')` 分段提取
**判断信号**: web_extract 输出含 `──────── [TRUNCATED] ────────` 头饰 → 1 步切 read_file，不要盲加 char_limit 重试

---

## 三、配置优化

### 关闭非必需功能
```bash
# 关闭不必要的自动化
hermes config set memory.reflection_enabled false
hermes config set evaluation.enabled false
hermes config set skills.auto_create false
```

### 预算控制
- Provider 级别：在 OpenRouter/OpenAI 设账户预算
- Hermes 级别：软熔断（配置 `model.max_cost_per_session`）

---

## 四、成本监控

### 每日成本查询
```sql
sqlite3 ~/.hermes/state.db "
  SELECT date(created_at) as day, model, COUNT(*) as calls,
         SUM(input_tokens) as in_tok, SUM(output_tokens) as out_tok
  FROM messages
  WHERE created_at > date('now', '-7 days')
  GROUP BY day, model
  ORDER BY day"
```

### 技能级成本分析
```sql
sqlite3 ~/.hermes/state.db "
  SELECT skills, AVG(input_tokens), COUNT(*)
  FROM messages
  WHERE skills IS NOT NULL
  GROUP BY skills
  ORDER BY AVG(input_tokens) DESC"
```

---

## 六、Response Truncated Debugging（必读）

最常见的"Token 优化失败"场景是 `Response truncated (finish_reason='length')` — 模型输出被截断。**不是模型问题，是配置没跟上。** 5 种原因从最常见到最隐蔽排列：

### Cause 1：config.yaml 的 max_tokens 被静默忽略（bug #4404）
**现象**: 设了 `model.max_tokens: 8192`，但请求走出去时带的是 provider 默认（2048/4096）。
**修复**: 设环境变量覆盖 —— `echo 'HERMES_MAX_TOKENS=8192' >> ~/.hermes/.env`
**验证**: `hermes chat -q "write 300 words" --verbose` 看实际请求日志

### Cause 2：Provider 默认输出限制太低（尤其 Ollama）
**现象**: Ollama 默认 `num_ctx=2048` — 系统 prompt + history 占完就没空间给输出了。
**修复**: Modelfile 强制设定 —— `PARAMETER num_ctx 8192` + `PARAMETER num_predict 1024`

### Cause 3：Context-window 数学错误
**现象**: 系统 prompt + 历史记录 + 工具定义加起来接近 context window 上限，模型拿到 0 输出空间。
**修复**: `context_length` 必须匹配模型实际值。Ollama 模型用 `/api/show` 查 `context_length` 字段；非 Ollama 模型查官方文档。

### Cause 4：压缩系统 Bug（#14690）
**现象**: `/compress` 命令无法正常触发，handoff/summary 函数中的 math 计算有 bug。
**修复**: `hermes update` 到最新版。2026 年 6 月此 bug 仍有残留报告（#26425）。

### Cause 5：OpenRouter 信用预留（#22879）
**现象**: OpenRouter 账户提前锁定 output token 量，信用不足时截断。
**修复**: 换无信用限制的 provider，或给 OpenRouter 账户充值。

### 诊断快捷命令
```bash
# 1. 检查实际发送的 max_tokens
hermes chat -q "write 100 words" --verbose 2>&1 | grep -i "max_tokens"

# 2. 检查 Ollama 模型上下文窗口
ollama show <model> | grep -i context

# 3. 检查 .env 是否有 HERMES_MAX_TOKENS
grep HERMES_MAX_TOKENS ~/.hermes/.env

# 4. 验证版本
hermes --version | head -1
```

### 引用的 context-compression skill
已装 `sickn33/antigravity-awesome-skills@context-compression` 到 `~/.hermes/skills/context-compression/`（1.1K★）。提供 3 种生产级压缩策略缓解上下文压力：
- Anchored Iterative（98.6% 压缩，推荐）
- Opaque（99.3% 压缩，顶级 token 节省）
- Regenerative（98.7% 压缩，可读性最好）

**使用时机**: 压缩系统 bug 修好 + config 配对后，仍频繁触发 `/compress` 也救不回 long session → 加载此 skill 实施结构化迭代压缩。详见 `references/response-truncated-5-causes.md`。

---

## 七、相关 Skill 联动

| Skill | 关系 |
|-------|------|
| `hermes-agent` | 权威文档源，本 skill 补充实战优化技巧 |
| `proactive-execution` | 本 skill 是"省钱"维度的支撑 |
| `hermes-runtime-fortress` | 内存保护与本 skill 的"资源控制"互补 |
| `ponytail-decision-ladder` | 本 skill 是 Ponytail 哲学的"优化"维度 |
