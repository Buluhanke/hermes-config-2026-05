---
name: hermes-hindsight
description: "Hindsight 本地记忆引擎 — AI Agent 终身记忆系统，包裹LLM调用自动存储/检索语义记忆。部署在 Docker + Ollama，本地运行完全免费。"
---

# hermes-hindsight

**Hindsight** 是 vectorize-io 开源的本地记忆引擎（15k+ stars），通过 `retain/recall/reflect` 三个操作让 Agent 具备跨会话的语义记忆和自我进化能力。

## 架构

```
Hermes Agent
    ↓ retain/recall HTTP API
Hindsight API (Docker, 端口 8899)
    ↓ LLM 调用 (Ollama, 本地)
PostgreSQL (embedded pg0)
Embedding: nomic-embed-text / BAAI/bge-small-en-v1.5
```

## 部署状态

| 项目 | 值 |
|------|---|
| 容器名 | `hermes-hindsight` |
| API 端口 | `8899`（8888 被 searxng 占用） |
| LLM 模型 | `qwen2.5:1.5b` |
| Embedding | `nomic-embed-text:latest` |
| 版本 | v0.7.1 |

## 核心操作

```python
from hindsight_client import Hindsight
client = Hindsight(base_url="http://localhost:8899")

# 存记忆
client.retain(bank_id="hermes", content="记忆内容", tags=["标签"])

# 语义搜索
result = client.recall(bank_id="hermes", query="搜索词")
for r in result.results:
    print(f"[{r.type_}] {r.content[:80]}")

# 自我反思
insights = client.reflect(bank_id="hermes", query="我的偏好是什么？")
```

## 与 ChromaDB (hermes-memory-hpc) 的区别

| 维度 | Hindsight | ChromaDB (hermes-memory-hpc) |
|------|-----------|------------------------------|
| 存储 | PostgreSQL + 向量 | ChromaDB 向量数据库 |
| 语义层 | LLM 生成 Disposition（类人格）| 结构化 metadata 标签 |
| 触发 | 自动包裹 LLM 调用 | 手动调用函数 |
| 适用 | 非结构化对话/经验积累 | 供应商/产品结构化记录 |

**两者互补**：Hindsight 记对话经验，ChromaDB 记供应商数据。

## Docker 部署命令

```bash
docker run -d \
  --name hermes-hindsight \
  -p 8899:8888 \
  -p 9999:9999 \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
  -e HINDSIGHT_API_LLM_PROVIDER=ollama \
  -e HINDSIGHT_API_LLM_MODEL=qwen2.5:1.5b \
  -e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434/v1 \
  -e HINDSIGHT_API_EMBEDDING_MODEL=nomic-embed-text:latest \
  -e HINDSIGHT_API_EMBEDDING_BASE_URL=http://host.docker.internal:11434/v1 \
  -e HINDSIGHT_WAIT_FOR_DEPS=true \
  -e HINDSIGHT_RETRY_MAX=30 \
  -e HINDSIGHT_RETRY_INTERVAL=10 \
  --restart unless-stopped \
  ghcr.io/vectorize-io/hindsight:latest
```

## ⚠️ 关键坑点

### 模型速度决定响应时间
`qwen3-vl:2b` 太慢（30s+/次推理），每次 retain/recall 都调 LLM 生成。**用小模型**：`ollama pull qwen2.5:1.5b`

### API 请求格式（v0.7.1）
```bash
# 创建 bank
curl -X PUT "http://localhost:8899/v1/default/banks/hermes" \
  -H "Content-Type: application/json" \
  -d '{"bank_id":"hermes","name":"Hermes"}'

# 存记忆（POST items 数组）
curl -X POST "http://localhost:8899/v1/default/banks/hermes/memories" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"content":"记忆内容","tags":["标签"]}]}'

# 搜索
curl -X POST "http://localhost:8899/v1/default/banks/hermes/memories/recall" \
  -H "Content-Type: application/json" \
  -d '{"query":"搜索关键词"}'
```

### 8888 端口冲突
SearXNG 占用了 8888，用 `8899:8888` 映射。

## 运维

```bash
docker logs hermes-hindsight
docker restart hermes-hindsight
curl http://localhost:8899/health  # {"status":"healthy","database":"connected"}
```
