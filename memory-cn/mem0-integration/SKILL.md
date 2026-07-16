---
name: mem0-integration
description: mem0ai 记忆层集成 — 第三记忆引擎，事件图谱+时间线+高召回，叠加在 fact_store+LanceDB 上增强联想能力
triggers:
  - mem0
  - 记忆增强
  - 联想记忆
  - recall boost
  - 记忆召回
---

# mem0-integration — mem0ai 记忆层集成

## 核心架构
mem0ai v2 (60K stars) 作为第三记忆引擎，叠加在现有架构上：
- L0: MEMORY.md（直觉/规则）
- L1: fact_store FTS5（精确检索）
- L2: LanceDB 向量（语义联想）
- **L3: mem0ai（事件图谱+时间线+高召回）** ← 新增

## 初始化配置
```python
import os
from mem0 import Memory
from mem0.configs.base import MemoryConfig, VectorStoreConfig

config = MemoryConfig(
    vector_store=VectorStoreConfig(
        provider='chroma',
        config={
            'path': os.path.expanduser('~/.mem0/chroma'),
            'collection_name': 'hermes_mem0',
        }
    ),
    version='v2'
)
m = Memory(config=config)
```

## embedder 配置（通过环境变量）
```bash
export OPENAI_API_KEY=<openrouter_key>
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

## 核心接口

### 记忆写入
```python
m.add(
    "用户叫Y Y，中文优先，不喜欢重复确认",
    user_id="hermes_owner",
    metadata={"source": "telegram", "session": "2026-07-07"}
)
```

### 记忆检索
```python
results = m.search(
    query="用户的语言偏好和沟通风格",
    user_id="hermes_owner",
    limit=5
)
# 返回: [{id, memory, score, metadata}, ...]
```

### 记忆关系图谱
```python
# mem0 v2 自动维护实体关系和时间线
# 查询相关记忆
m.history(user_id="hermes_owner", limit=10)
```

## 现有工具的增强映射
| 场景 | 原有方案 | 增强方案 |
|------|---------|---------|
| 跨标签模糊召回 | lancedb_recall | mem0.search |
| 实体关系推理 | — | mem0.history + 关系图 |
| 事件时间线 | — | mem0 v2 temporal graph |
| 技能关联发现 | 硬触发词 | mem0语义相似度 |

## 已知坑点
- mem0 默认用 Qdrant（需外部服务），必须指定 `provider='chroma'`
- GLM API Key 不能直接用于 embedding（格式不兼容 OpenAI embedding endpoint）
- `search()` 用 `filters={'user_id': '...'}` 而非顶层 `user_id=`
- LLM extraction 时 GLM 报 `1211 模型不存在` — 需确保模型名称正确，或 `infer=False` 绕过
- **mem0 ChromaConfig 导入**：不能用 `mem0.vector_stores.configs.ChromaConfig`（不存在），用 dict 形式 `{'provider': 'chroma', 'config': {...}}`
- mem0 的 `VectorStoreConfig` → `config` 字段传 dict，会自动实例化对应 provider 的 config 类

## FastEmbed 本地 embedding（2026-07-07 实测 ✅）

**FastEmbed 已在 venv（0.8.0），mem0 已集成，无需额外安装。**

```python
import os
from mem0 import Memory
from mem0.configs.base import MemoryConfig

# 读取 GLM key
glm_key = None
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.strip().startswith('GLM_API_KEY='):
            glm_key = line.strip().split('=', 1)[1].strip()
            break

chroma_path = os.path.expanduser('~/.hermes/mem0_chroma')
os.makedirs(chroma_path, exist_ok=True)

config = MemoryConfig(
    vector_store={
        'provider': 'chroma',
        'config': {
            'collection_name': 'hermes_memories',
            'path': chroma_path
        }
    },
    llm={
        'provider': 'openai',
        'config': {
            'api_key': glm_key,
            'openai_base_url': 'https://open.bigmodel.cn/api/paas/v4'
        }
    },
    embedder={
        'provider': 'fastembed',
        'config': {
            'model': 'BAAI/bge-small-en-v1.5',  # 384维，多语言
            'embedding_dims': 384
        }
    }
)

m = Memory(config)
m.add("记忆内容", user_id='hermes', infer=False)  # infer=False 跳过LLM extraction
results = m.search("内容", limit=3)
```

**可用 FastEmbed 模型（venv 已装，无需联网）：**
- `BAAI/bge-small-en-v1.5` (384维) — 最快，多语言
- `BAAI/bge-base-en-v1.5` (768维) — 更高精度
- `sentence-transformers/all-MiniLM-L6-v2` (384维) — 通用
- `jinaai/jina-embeddings-v2-base-zh` (768维) — 中文优化

**首次运行慢**（~100s下载模型），之后本地秒级。

## 推荐路径（2026-07-07 实测）
**当前卡在 OpenRouter 402，embedding 不可用。建议：**
1. 充值 OpenRouter credits，或
2. 换用 Ollama 本地 embedder（不耗 credits），或
3. 用 headroom FTS5 替代（零 API 成本，已在 venv）

**不要盲目装 mem0ai** — 先 `pip show mem0ai` 确认版本，再验证 embedding 能通。

## 验证步骤（infer=False 模式）
```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python3 << 'EOF'
import os
from mem0 import Memory
from mem0.configs.base import MemoryConfig, VectorStoreConfig

env_path = os.path.expanduser('~/.hermes/.env')
with open(env_path) as f:
    for line in f:
        if line.strip().startswith('OPENROUTER_API_KEY='):
            key = line.strip().split('=', 1)[1].strip()
            os.environ['OPENAI_API_KEY'] = key
            break
os.environ['OPENAI_BASE_URL'] = 'https://openrouter.ai/api/v1'

config = MemoryConfig(
    vector_store=VectorStoreConfig(provider='chroma', config={'path': '~/.mem0/chroma', 'collection_name': 'hermes_mem0'}),
    version='v1'
)
m = Memory(config=config)
result = m.add("test memory", user_id="hermes_owner", infer=False)
results = m.search("test", filters={"user_id": "hermes_owner"}, limit=3)
print('OK:', len(results.get('results', [])))
EOF
```
