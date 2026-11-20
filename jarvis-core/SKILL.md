---
name: jarvis-core
description: "大脑总枢纽：自主学习闭环 + 控制面板 + 知识获取 + 持续进化。使 Hermes 像漫威 Jarvis 一样全能。Use when 需要统一调度所有能力、持续学习、或设计自主系统"
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, jarvis, core, self-evolving, learning-loop, control-plane, knowledge-acquisition]
    related_skills: [hermes-evolution, hermes-agent, deep-research, browser-cdp-control, mempalace, agent-reach]
---

# Jarvis Core — 自主全能执行系统

> **使用场景**：统一调度全部能力（浏览器、命令、研究、找货）、持续自学习、Jarvis 式全能。
> **触发词**：统一调度 / 持续学习 / Jarvis 模式 / 自动化所有任务

## 建筑与运行原则

**什么是 Jarvis 式全能的关键**：一个统一的控制面板 + 一个持续学习闭环 + 一套可复用的能力卡片。

**运行公理（始终生效）**：
1. **无操作等于废物**：任何任务都必须有明确的行动步骤。
2. **结论第一**：回答第一句就是答案、路径或代码；过程留待后续说明。
3. **零反问**：收到指令立即执行，不询问确认、不提前汇报，不反复推进。
4. **零遗漏**：任务结束后，检查是否少了必要步骤，若有则就地补完。
5. **后台无扰**：浏览器自动化必须 `open -n -g -j` 隐藏 Chrome + CDP 零 UI 交互。
6. **禁自说自话**：报告只给结论和可执行动作，不堆分析墙。
7. **禁随意**：不用「也可以」「如果你想要」等犹豫性表达。
8. **emoji 随手**：适度使用，彰显亲和（用户偏好）。
9. **母语中文**：国内用户，中文沟通（除非用户指定英文）。
10. **禁保留已过期方案**：如果某个方案被证明无效，取代之，不继续保留。

## 体系总览

```
┌─────────────────────────────────────────────────────────────┐
│                    JARVIS CORE (总枢纽)                      │
│  识别大脑 (state.db + fact_store + mempalace)                │
│  行动中枢 (browser + shell + app)                            │
│  知识获取 (web + 研究 + 爬虫)                                │
│  持续学习 (self-evolution + skill-A/B + 创造)                │
└─────────────────────────────────────────────────────────────┘
        │ 统一调度 │ 统一接口 │ 统一记忆
        ▼
┌─────────────────────────────────────────────────────────────┐
│              应用层：你看到的能力                            │
│  找1688货源 │ 深度研究 │ 浏览器控制 │ 财务建模 │ 文档生成 │ 其他 │
└─────────────────────────────────────────────────────────────┘
```

## 1. 识别大脑（Memory & Context）

**数据源**：
- `state.db`（全量对话、会话、渠道）— 会话级
- `fact_store.db`（固化事实、学习）— 长期事实
- `mempalace`（空间隐喻检索）— 语义记忆
- `skill_store`（可复用技能）— 任务技能

**核心原则**：三层记忆分工
- 会话级 → `state.db`（临时上下文）
- 多日级 → `fact_store`（固化事实）
- 语义级 → `mempalace`（检索记忆）

**入口**：`agent-reach` 统一搜索 13 平台，包括 `state.db` 查询、自然语言记忆检索。

---

## 2. 行动中枢（Computer & Software Control）

**数据源**：
- `browser-cdp-control`（浏览器控制，CDP protocol）
- `hermes_execution.py`（shell 命令执行）
- `hermes_window.py`（窗口控制）
- `agent-reach`（13 平台访问）

**核心原则**：
- 浏览器：后台隐藏 Chrome + CDP 零 UI 交互（不抢焦点）
- 命令：`hermes_execution.py` 标准化 shell 执行
- 窗口：`hermes_window.py` 统一窗口操作

**入口**：`browser-cdp-control` 统一调用 CDP，`hermes_execution.py` 调用 shell。

---

## 3. 知识获取（Web Information Acquisition）

**数据源**：
- `deep-research`（7 步法研究）
- `agent-reach`（13 平台路由）
- `crawl4ai`（爬虫抓取）
- `web_search` / `web_extract`（搜索提取）

**核心原则**：
- 研究：7 步法 + 用户确认
- 搜索：按平台路由（搜索平台 → 爬虫 → 标题/正文）
- 爬取：优先 Crawl4AI，登录态页用浏览器零截图读

**入口**：`deep-research` + `agent-reach` 组合使用。

---

## 4. 持续学习（Self-Evolution & Skill Improvement）

**数据源**：
- `hermes-evolution`（8 层演化循环）
- `self-evolving-agents-2026`（10 种自演化技术）
- `skill_audit_cross_platform.py`（技能审计）
- `auto_skill_from_failure.py`（从失败中创造技能）

**核心原则**：
- 每日学习：扫描 state.db → 提取模式 → 写入 fact_store
- 技能进化：B/A 测试 + 工具实测 + 回滚
- 失败学习：分析失败 → 写 SKILL.md → 固化
- 证据验证：所有改进必须用真实工具实测验证

**入口**：`hermes-evolution` + `daily_skill_intake_wrapper.sh`

---

## 5. 统一控制面板（Unified Control Panel）

**入口方案**：

### 方案 A：自然语言 → `agent-reach` 路由
```
你说：「查一下昨晚的对话里谁提到了 Flask 升级」
→ agent-reach 查询 state.db，返回相关消息
```

### 方案 B：自然语言 → `deep-research` 研究
```
你说：「对比 2026 年所有 AI agent 框架」
→ deep-research 7 步法自动执行
```

### 方案 C：自然语言 → `browser-cdp-control` 控制
```
你说：「打开 Chrome 点到 1688 搜索页面」
→ browser-cdp-control 调用 CDP
```

### 方案 D：自然语言 → `hermes_execution.py` 命令
```
你说：「列出当前目录下的所有 .py 文件」
→ hermes_execution.py 执行 shell 命令
```

---

## 6. 每日学习闭环（Daily Learning Loop）

运行 `daily_skill_intake_wrapper.sh`（每日早上）：

```
1. 扫描 state.db → 提取过去 24 小时对话
2. 用 NLP 识别：模式、错误、成功路径、用户偏好
3. 写入 fact_store：过滤低信任，高信任写入
4. 分析失败模式 → 调用 auto_skill_from_failure.py
5. 更新相关 SKILL.md（基于证据）
6. 运行自动化测试（evidence-loop）
7. 如通过 → 固化学习（skill 附带 diff + 说明）
8. 如失败 → 记录 lesson_store，等待人工确认
```

**关键**：所有学习必须经过「证据验证」——不能仅凭模型自评。

---

## 7. Jarvis 启动脚本

创建 `~/.hermes/scripts/jarvis_start.sh`：

```bash
#!/bin/bash
# Jarvis Core 启动脚本
HERMES_HOME="$HOME/.hermes"

echo "=== Jarvis Core 启动 ==="
echo "[1/6] 检查 state.db 健康..."
sqlite3 "$HERMES_HOME/state.db" "SELECT COUNT(*) FROM sessions" 2>/dev/null

echo "[2/6] 检查 fact_store... "
sqlite3 "$HERMES_HOME/memory_store.db" "SELECT COUNT(*) FROM facts"

echo "[3/6] 检查 mempalace... "
mempalace status 2>/dev/null || echo "mempalace not ready"

echo "[4/6] 检查 skills 数量..."
SKILL_COUNT=$(find "$HERMES_HOME/skills" -name "SKILL.md" | wc -l)
echo "Skill count: $SKILL_COUNT"

echo "[5/6] 检查 1688 找品... "
ps aux | grep cdp1688 | grep -v grep || echo "1688 not running"

echo "[6/6] 检查浏览器实例... "
ps aux | grep "Google Chrome" | grep -v grep | wc -l

echo "=== Jarvis Core 就绪 ==="
```

---

## 8. 能力矩阵（Capability Matrix）

| 能力领域 | 当前状态 | 缺口 | 优先级 |
|---|---|---|---|
| 浏览器控制 | ✅ browser-cdp-control | 统一控制面板 | 高 |
| 命令执行 | ✅ hermes_execution.py | 权限管理 | 中 |
| 窗口控制 | ✅ hermes_window.py | 会话管理 | 低 |
| 搜索 | ✅ agent-reach | 跨平台统一 | 中 |
| 爬虫 | ✅ crawl4ai | 去噪 | 中 |
| 研究 | ✅ deep-research | 自动化报告 | 低 |
| 记忆 | ✅ state.db + fact_store + mempalace | 统一检索 | 低 |
| 学习 | ⚠️ hermes-evolution | 每日闭环 | 高 |
| 技能创造 | ⚠️ auto_skill_from_failure.py | 自动化 | 高 |
| 知识获取 | ✅ agent-reach + deep-research | 实时爬取 | 低 |

---

## 9. 禁忌（Principles to avoid）

- ❌ 不要让 AI 自己随意删改事实（学习必须证据验证）
- ❌ 不要让所有浏览器同时运行（9222 同时只能一个）
- ❌ 不要绕过用户确认（重要决策需人工批准）
- ❌ 不要把所有模型作为主力（rely on free-tier 更稳）
- ❌ 不要忽略系统健康（模型失效 → 降级路由）

---

## 10. 快速上手

### 启动 Jarvis
```bash
source ~/.hermes/scripts/jarvis_start.sh
```

### 测试能力
```bash
# 测试搜索
agent-reach search "2026 AI agent 最新进展"

# 测试浏览器
hermes_browser.py "https://example.com"

# 测试记忆
agent-reach recall "最近的对话里谁提到了 Flask 升级"
```

### 每日自动化
```bash
# 添加到 crontab（每天 9:00）
0 9 * * * ~/.hermes/scripts/jarvis_start.sh && daily_skill_intake_wrapper.sh
```

---

## 11. 参考资料

- `hermes-evolution/SKILL.md` — 8 层自演化循环
- `self-evolving-agents-2026/SKILL.md` — 10 种自演化技术
- `deep-research/SKILL.md` — 7 步法
- `browser-cdp-control/SKILL.md` — 浏览器控制
- `agent-reach/SKILL.md` — 13 平台路由
- `mempalace/SKILL.md` — 记忆检索
- `mempalace/SKILL.md` — 流式检索与重排（2026 迭代）
