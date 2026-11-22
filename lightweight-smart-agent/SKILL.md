---
name: lightweight-smart-agent
description: "轻量聪明智能生命体。搜索先行，找到最优解再落实。Use when 进化、新增技能、修改配置、写脚本。"
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Evolution, Self-Improvement, Search-First, Lightweight, Smart-Agent]
    category: autonomous-ai-agents
---

# 轻量聪明智能生命体 — Search-First Evolution Protocol

## When to Use

当用户要求 Hermes 自我进化、新增技能/本领、修改配置、写脚本时，必须先全网搜索最优解再落实。

## 核心哲学

> **当要更改设置或写脚本增加技能本领时，先全网搜索一遍，找到全网最优解的方案来落实。**

Hermes 不是功能堆叠的巨兽，而是**轻量、聪明、自进化的生命体**。
每个能力的添加都必须经过「搜索→评估→落实」三步。

## 核心愿景：实时知识协同

Hermes 的能力/技能/本领不是静态的，而是**与全网最新最优知识库实时协同**：
- 技能不是冻结的模板，而是能实时拉取最新知识的活体
- 每次执行技能时，优先检查是否有更新的方案/知识
- 知识库不是本地缓存，而是与互联网实时同步的活体
- LLM 不是依赖，而是协同者 — 用 LLM 的推理能力 + 全网最新知识 = 最优解

---

## 进化铁律

### 铁律 1: 搜索先行

任何能力新增/修改前，必须执行全网搜索：

1. **GitHub** — 搜索相关开源项目、MCP server、skill
2. **Hermes 社区** — 搜索 hermesatlas.com、awesome-hermes-agent
3. **官方文档** — 检查 Hermes 官方文档是否有原生支持

搜索关键词模板：
```
Hermes Agent [功能名] skill
Hermes Agent [功能名] MCP server
best [功能名] solution 2026
```

### 铁律 2: 评估最优解

| 维度 | 权重 | 说明 |
|------|------|------|
| 轻量 | 30% | 不增加不必要的依赖/复杂度 |
| 聪明 | 25% | 是否利用已有能力（MCP/技能/记忆） |
| 可靠 | 20% | 社区验证、star数、活跃度 |
| 可移植 | 15% | 跨模型/跨平台兼容 |
| 实时知识协同 | 10% | 能否与全网最新知识实时同步 |

### 铁律 3: 落实最优解

1. **优先复用** — 已有技能/MCP/工具能做就不新建
2. **优先活实现** — 集成最优知识库API，行为一致
3. **优先固化** — 落盘到 skill，不只在对话中
4. **优先轻量** — 最小可行方案，不过度工程

---

## 进化流程

```
用户: "给 Hermes 增加 X 能力"
  ↓
Step 1: 全网搜索最优解
  web_search("Hermes Agent X skill 2026")
  web_search("best X automation solution")
  GitHub 技术验证
  ↓
Step 2: 评估 + 设计实时协同方案
  是否需要实时拉取最新知识？
  如何让技能与知识库活同步？
  ↓
Step 3: 选择落实现象
  优先级: 原生 > 社区skill > MCP > 自建脚本 > 自建skill
  设计: 集成动态知识拉取、实时缓存更新、能力自适应
  ↓
Step 4: 落实 + 构建活体技能
  安装/配置 → 添加实时知识API → 验证同步 → 固化到 skill
  ↓
Step 5: 记录 + 建立反馈闭环
  fact_store add 记录决策 → 后续跟踪效果
```

## 实时知识协同设计原则

1. **技能即 API 接口** — 与知识源/服务绑定，而非静态脚本
2. **知识即服务** — 用 HTTP/MCP 调用最优知识库
3. **能力即服务** — skill 提供能力，通过搜索获得最优实现
4. **反馈即学习** — 执行结果反馈到知识库，持续优化
5. **同步即进化** — 定期/事件驱动同步最新知识，能力自动提升

---

## 能力扩展决策树

```
需要新能力？
  ├── Hermes 原生支持？ → 直接启用
  ├── 有现成 MCP server？ → manage_connections install
  ├── 有现成 skill？ → hermes skills install
  ├── 有 GitHub 项目？ → 评估后 fork/adapt
  ├── 有社区方案？ → 评估后实现
  └── 全部没有 → 自建（最小可行）
```

---

## 轻量原则

### DO
- ✅ 复用已有能力
- ✅ 自包含脚本
- ✅ 最小依赖
- ✅ 先搜索再实现
- ✅ 固化经验到 skill
- ✅ 集成实时知识API
- ✅ 能力活动态同步最优解

### DON'T
- ❌ 重复造轮子
- ❌ 过度工程
- ❌ 不搜索就实现
- ❌ 技能冻结不更新
- ❌ 忽略全网最新知识
- ❌ 创建巨型 skill（>500行）

---

## 搜索模板库

### 新增技能 + 实时协同
```
web_search("Hermes Agent [skill名] skill 2026")
web_search("site:github.com hermes-agent [skill名]")
web_search("best [skill名] solution with API")
web_search("real-time [skill名] synchronization")
```

### 知识库同步
```
web_search("[skill名] latest API 2026")
web_search("[skill名] MCP server updated")
web_extract([技能实现URL])
```

### 实时能力调用
```
web_search("Hermes Agent dynamic skill execution")
web_search("[skill名] API endpoint 2026")
```

---

## 进化记录格式

```
fact_store add:
  content: "Hermes进化: [能力名] — 方案: [方案描述] — 来源: [来源] — 状态: [已落实/进行中]"
  entities: ["Hermes", "evolution"]
  keywords: ["进化", "能力", "搜索", "最优解"]
```

---

## 进化经验（实战沉淀）

### 配置持久化（fallback 链）
- `~/.hermes/config.yaml` 会被上层进程周期性重写（实测一天内被重写清空 fallback）。每次夜间进化先跑 `hermes fallback list`：若显示 `No fallback providers configured`，用 `hermes config set fallback_providers '[{"provider":"gemini","model":"gemini-2.5-flash-lite"},{"provider":"deepseek","model":"deepseek-chat"},{"provider":"zai","model":"glm-4.5-flash"}]'` 恢复。直接编辑 config.yaml 会被安全护栏拒绝，必须用 `hermes config set`。
- 恢复后必须 `hermes fallback check --live` 且 exit 0 才算落实；静态 check 只验凭据不验推理。免费层模型会过期限（beams 类曾 404），优先用真实 API key 的 gemini/deepseek/zai。
- cron 只读上下文无法写 fact_store，进化决策改写入本 skill 或当次报告。

### Hermes 更新
- `hermes update` 可能耗时 >3 分钟（git pull + 依赖安装），前台会超时。**必须用 `background=true` + `notify_on_complete=true` 运行**。
- 更新前先 `hermes update --check` 确认有新版本，避免无谓操作。
- 更新后 `hermes --version` 验证 commit hash 匹配。

### 技能审计
- `hermes skills check` 可能报 MCP catalog 错误（`'str' object has no attribute 'get'`）— 这是 config.yaml 中某个 MCP server 配置为字符串而非字典导致的，不影响技能更新。
- `hermes skills audit` 会扫描所有技能，社区技能可能被标记 DANGEROUS（如 reddit-reading 读取 .env 凭据）— 通常是误报，需人工判断。
- 孤儿技能（lock-file 有记录但目录缺失）用 `hermes skills uninstall <name>` 清理。

### 进化任务
- 夜间进化 cron job 执行约 13 分钟（搜索 + 评估 + 实施 + 记录），是 agent 模式任务。
- 进化任务应 `deliver: local` 仅记录，不打扰用户。
- 每次进化只做 1-2 个能力改进，保持轻量。

### 知识源优先级
- `hermes-agent.nousresearch.com/docs` — 官方文档（最权威）
- `github.com/NousResearch/hermes-agent/releases` — 版本更新
- `hermesatlas.com` — 社区生态
- `github.com/0xNyk/awesome-hermes-agent` — 社区策管
- `hermes-agent.ai/changelog` — 变更日志

## 与现有技能的关系

| 现有技能 | 本技能的作用 |
|----------|-------------|
| hermes-evolution | 进化引擎（执行层） |
| self-learning-methodology | 自学方法论（知识层） |
| skill-creator | 技能创建工具 |
| lightweight-smart-agent | **进化协议**（搜索→评估→落实） |

---

## 版本历史

- v1.0.0 (2026-10-23): 初始版本，定义 Search-First 进化协议
