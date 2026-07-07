# 记忆系统升级调研 — 2026-07-08

## 任务目标
提升记忆检索召回率、技能关联推理、短期→长期记忆转化、主动预判能力。

## 方案评估

### 方案A: mem0ai v2（60K stars）
- **状态**: ✅ 已安装 2.0.4，Chroma ✅ 已装
- **架构**: 事件图谱 + 时间线 + 高召回
- **卡点**: OpenRouter credits 不足（402错误），embedding API 必须调用
- **测试结果**:
  - `Memory()` 初始化 ✅（env vars 正确配置后）
  - `m.add(infer=False)` ✅ 绕过LLM extraction，但embedding仍需API
  - `m.search()` v2 API：`filters={"user_id": "..."}` 而非 `user_id=` 参数级
  - Chroma collection 创建 ✅，但 0 条记录（因embedding失败）
- **结论**: 架构正确，需解决 API credits 后可用

### 方案B: headroom FTS5 adapter
- **状态**: ✅ 已在 venv（路径 `headroom.memory.adapters.fts5`）
- **优势**: 纯 SQLite FTS5，零 API 依赖
- **接口**: `FTS5TextIndex`，方法 `index_memory()` / `search_memories()`（非 `add_text()`）
- **局限**: 纯关键词搜索，无语义向量能力
- **结论**: ✅ 可立即作为关键词召回增强层

### 方案C: hermes-local-memory
- **状态**: ✅ 已装 v0.3.1，pip 包名 `hermes-local-memory`
- **关键类**: `LocalMemoryProvider` + `LocalMemoryStore`
- **流程**: consolidation → reflection → peer_review → candidate_review
- **问题**: config.yaml 用的是 `lancedb`，这个被完全忽视了
- **结论**: 🔴 优先级最高，应启用替代 lancedb

### 方案D: 修 LanceDB 0行
- **状态**: LanceDB 表存在但 0 行
- **可能原因**: provider 初始化失败 / session_end 写入逻辑断路
- **验证**: `hermes memory status`
- **结论**: 需查 provider 日志

## 关键坑点

### 坑点1: terminal vs execute_code 环境差异
- **现象**: execute_code 沙盒中 Chroma 报 "instance already exists with different settings"
- **原因**: 沙盒 `/tmp` 与本机 `/tmp` 不同，Chroma 是持久化进程级单例
- **教训**: memory/数据库类测试必须用 terminal，避免 execute_code 假性结论

### 坑点2: OpenRouter embedding 402
- **原因**: OpenRouter 免费账户 embedding 调用需要 credits
- **测试**: `text-embedding-3-small` 直接调 OpenAI API 成功（dim: 1536）
- **mem0 内部**: 默认用 `text-embedding-3-small`（dim 1536），通过 OpenRouter 代理

### 坑点3: mem0 search API 变化
- **旧**: `m.search(query, user_id="...")`
- **新**: `m.search(query, filters={"user_id": "..."})`
- **来源**: v2 API breaking change

### 坑点4: 工具调用循环（repeated_exact_failure_block）
- **触发**: 相同参数 terminal 调用 3 次失败
- **处理**: 换工具（execute_code）、换参数、换诊断方向
- **教训**: 不在同一点重复，换路不换方法

## API Key 配置（实测）
```
OPENROUTER_API_KEY=sk-or-...(73 chars)
OPENAI_BASE_URL=https://openrouter.ai/api/v1
GEMINI_API_KEY=AQ.Ab8R...(可用但embedding endpoint格式不兼容)
```

## 推荐行动项
1. `hermes memory status` — 查 LanceDB 0行原因
2. 启用 hermes-local-memory — 替代 lancedb
3. headroom FTS5 — 即插即用，零成本关键词召回
4. mem0ai — 充值 OpenRouter 后再集成
