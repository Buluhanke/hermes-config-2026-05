---
name: hermes-memory-architecture
description: Hermes 记忆系统真实架构 — 2026-07-08实测版，2026-07-08清理后定稿。MEMORY.md+USER.md+concept_store.md为文件系统层，LanceDB为语义层，fact_store.db已删除（0行legacy）。记忆审计必须先验证真实状态再操作。
version: 1.1.0
version: 1.2.0
updated: 2026-07-08
type: reference
category: meta
triggers:
  - "记忆审计"
  - "memory audit"
  - "查记忆"
  - "清理记忆"
  - "记忆满了"
  - "fact_store"
  - "lancedb"
  - "semantic memory"
  - "清理memories"
  - "升级检查"
  - "记忆召回率"
  - "联想记忆"
  - "mem0"
  - "headroom"
---

# Hermes Memory Architecture — 实测版 (v1.2)

**注意：hub skill memory-cn 描述的是旧架构（Mnemosyne），以下为 2026-07-08+ 实测真实状态。**

## 记忆系统真实架构

| 组件 | 路径 | 用途 | 状态 |
|---|---|---|---|
| `MEMORY.md` | `~/.hermes/memories/` | 系统技术记忆 | ✅ 6454字节，活跃 |
| `USER.md` | `~/.hermes/memories/` | 用户偏好/铁律 | ✅ 2661字节，活跃 |
| `concept_store.md` | `~/.hermes/memories/` | 抽象经验规则 | ✅ 活跃 |
| Chrome | 150.0.7871.47 | 浏览器，brew完整包安装 | ✅ 2026-07-07 升级成功 |
| LanceDB | `~/.hermes/lancedb/memories.lance/` | 语义记忆，FastEmbed本地embedding | ✅ 2026-07-07 修复：改用FastEmbed(384维)替代OpenRouter embedding，环境变量隔离问题解决 |
| hermes-local-memory | venv 内 0.3.1 | 本地记忆Provider，consolidation/reflection/peer_review | ✅ 已装，config.yaml 未启用（provider=lancedb） |
| headroom FTS5 | venv 内 | FTS5 adapter，零API依赖 | ✅ 可用 |
| mem0ai | venv 内 2.0.4 | 事件图谱记忆层 | ✅ 已装，mem0+FastEmbed+Chroma 验证成功，OpenRouter credits不足暂缓 |

## 2026-07-08 新发现

### 1. LanceDB 0行 — 需修复
```python
# 验证命令
import lancedb
db = lancedb.connect('/Users/aimac/.hermes/lancedb')
print(db.table_names())  # ['memories']
t = db.open_table('memories')
print(t.count_rows())  # 输出0 — 没有写入
```
**可能原因**: memory provider 初始化失败，或 session结束后写入逻辑断路。需查 `hermes memory status` 输出。

### 2. hermes-local-memory 被忽视（优先级最高）
- pip包 `hermes-local-memory` v0.3.1 已在 venv
- `LocalMemoryProvider` 支持完整的 consolidation → reflection → peer_review 流程
- config.yaml 当前用的是 `lancedb`，没用这个
- **这是 Hermes 原生本地记忆系统，应优先集成而非引入外部依赖**

### 3. headroom FTS5 adapter（零API成本）
```python
from headroom.memory.adapters.fts5 import FTS5TextIndex
index = FTS5TextIndex(db_path='~/.mem0/hermes_fts.db')
index.index_memory("用户偏好中文", metadata={"id": "1"})
results = index.search_memories("用户 语言 偏好", limit=5)
# 方法: add_text → index, search → search_memories
# 纯SQLite FTS，无需API key
```

### 4. mem0ai 集成结论
- **架构可行**：Chroma本地vector store已装，`infer=False`可绕过LLM extraction
- **卡点**：embedding API调用被OpenRouter 402拒绝（credits不足）
- **解决路径**：充值OpenRouter 或 换用免费embedder（如Gemini text-embedding，但此路也验证失败）
- **当前推荐**：优先用 headroom FTS5 + hermes-local-memory，不依赖外部API

### 5. 工具执行环境差异（重要坑点）
- **terminal工具**：在真实本机环境执行，Chroma/LanceDB状态真实
- **execute_code沙盒**：隔离环境，`/tmp`等路径与本机不同，Chroma instance冲突
- **教训**：测memory/数据库类工具必须用terminal，避免execute_code产生环境差异导致的假性结论
- **教训**：连续3次相同参数的terminal/execute_code调用 → 触发repeated_exact_failure_block → 换工具/换参数/换诊断方向，不在同一点重复

## 升级路径（2026-07-07 更新）

**当前优先级顺序**:
1. **修 LanceDB 0 行** — 推荐改 FastEmbed embedding（完全本地零API），或修复 OPENROUTER_API_KEY 环境变量加载
2. **启用 hermes-local-memory** — 原生 consolidation + peer review，优先于外部依赖
3. **mem0ai + FastEmbed + Chroma** — 已验证可行，用 `infer=False` 绕过 LLM extraction

## 配置状态

```bash
# memory.provider 当前配置
hermes config show | grep -A5 "memory:"

# memory_char_limit 当前值
grep memory_char_limit ~/.hermes/config.yaml
# 当前值: 66000

# LanceDB 验证（真实环境，用 terminal）
~/.hermes/hermes-agent/venv/bin/python3 -c "
import lancedb
db = lancedb.connect('/Users/aimac/.hermes/lancedb')
t = db.open_table('memories')
print(t.count_rows(), 'rows')
"

# Chrome 升级
ls -la /tmp/chrome*.dmg  # 确认文件存在
# 安装: open /tmp/chrome150.dmg 或 hdiutil attach + rsync

# hermes-local-memory 状态
~/.hermes/hermes-agent/venv/bin/python3 -c "from hermes_local_memory import LocalMemoryProvider; print('OK')"
```

## 工具执行环境差异（重要坑点）
- **terminal 工具**：在真实本机环境执行，Chroma/LanceDB 状态真实
- **execute_code 沙盒**：隔离环境，`/tmp` 等路径与本机不同，Chroma instance 冲突
- **教训**：测 memory/数据库类工具必须用 terminal，避免 execute_code 产生环境差异导致的假性结论
- **教训**：连续 3 次相同参数的 terminal/execute_code 调用 → 触发 `repeated_exact_failure_block` → 换工具/换参数/换诊断方向，不在同一点重复

## 已知坑点

- **execute_code 沙盒 ≠ 真实环境**：venv 路径隔离，Chroma client 冲突，subprocess 也有独立环境
- **OpenRouter 402**：mem0ai embedding 被拒，需充值或换 embedder
- **Chrome DMG 中断**：已下载未安装，是上次升级中断遗留

### 6. LanceDB 0行根因 — ✅ 已修复 2026-07-07

**根因**：`plugins/lancedb.embedding` 配置使用 `OPENROUTER_API_KEY`，但这个 env var 在独立进程（gateway 子进程、execute_code 沙盒）中读不到 → `embed()` 静默失败 → LanceDB 0行。

**修复方案**：在 `plugins/lancedb/src/embeddings.py` 中新增 `FastEmbedEmbedder` 类，配置 `provider: fastembed` 时走本地 embedding，零 API 依赖。

**FastEmbedEmbedder 实现**：
```python
class FastEmbedEmbedder:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5", *, dimensions=384, max_batch=256):
        self.model_name = model_name
        self._dimensions = dimensions
        self.max_batch = max_batch
        self._model = None
        self._lock = threading.Lock()

    @property
    def model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from fastembed import TextEmbedding
                    self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def warm(self) -> int: return self._dimensions  # 纯本地，无网络
    def embed_one(self, text: str) -> List[float]: return self.embed([text])[0]
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts: return []
        out = []
        for start in range(0, len(texts), self.max_batch):
            batch = [t if t else " " for t in texts[start:start+self.max_batch]]
            vecs = list(self.model.embed(batch))
            out.extend([list(v) for v in vecs])
        return out
```

**embedder_from_config 新增分支**：
```python
if cfg.get("provider") == "fastembed":
    return FastEmbedEmbedder(
        model_name=cfg.get("model", "BAAI/bge-small-en-v1.5"),
        dimensions=cfg.get("dimensions", 384),
        max_batch=cfg.get("max_batch", 256),
    )
```

**config.yaml 配置**：
```yaml
plugins:
  entries:
    lancedb:
      embedding:
        provider: fastembed
        model: BAAI/bge-small-en-v1.5
        dimensions: 384
        max_batch: 256
```

**schema 不匹配解决**：删除旧 LanceDB 表（1536维 OpenAI schema），gateway 重启后自动用 FastEmbed 384维 schema 重建。

**验证**：
```bash
# gateway.error.log 当前会话（19:19后）无 lancedb 错误
grep "lance\|embed" ~/.hermes/logs/gateway.error.log | grep "19:19\|19:2\|19:3"
# 输出：NONE ✅

# LanceDB 表已重建为 384 维
# gateway PID 10650 在线
```

### 7. mem0 + FastEmbed + Chroma 完全验证成功 — 2026-07-07

```python
# 验证可行配置（infer=False 绕过 LLM extraction）
config = MemoryConfig(
    vector_store={"provider": "chroma", "config": {
        "collection_name": "hermes_memories",
        "path": os.path.expanduser("~/.hermes/mem0_chroma")
    }},
    llm={"provider": "openai", "config": {
        "api_key": glm_key,
        "openai_base_url": "https://open.bigmodel.cn/api/paas/v4"
    }},
    embedder={"provider": "fastembed", "config": {
        "model": "BAAI/bge-small-en-v1.5",  # 384维，多语言
        "embedding_dims": 384
    }}
)
m = Memory(config)
m.add("用户叫Y Y", user_id="test", infer=False)  # 成功写入
# Chroma count: 1, embedding_dim: 384 ✅
```

**FastEmbed 可用模型**（venv 已装 0.8.0）：
- `BAAI/bge-small-en-v1.5` — 384维，多语言推荐
- `BAAI/bge-small-zh-v1.5` — 512维，中文优化
- `sentence-transformers/all-MiniLM-L6-v2` — 384维，英文

### 8. Chrome 升级正确方法 — 2026-07-07

**错误方式**：`curl` 下载的 DMG 是 ChromeLite stub（版本 47），不是完整 Chrome。

**正确方式**：
```bash
# Homebrew 缓存有完整包（260MB XZ 压缩）
brew reinstall --cask google-chrome
# 或强制重下
rm -rf "/Applications/Google Chrome.app"
brew install --cask google-chrome
```

### 9. 工具执行环境差异（重要坑点）
- **terminal 工具**：在真实本机环境执行，Chroma/LanceDB 状态真实
- **execute_code 沙盒**：隔离环境，`/tmp` 等路径与本机不同，Chroma instance 冲突
- **教训**：测 memory/数据库类工具必须用 terminal，避免 execute_code 产生环境差异导致的假性结论
- **教训**：连续 3 次相同参数的 terminal/execute_code 调用 → 触发 `repeated_exact_failure_block` → 换工具/换参数/换诊断方向，不在同一点重复

# Hermes Memory Architecture — 实测版 (v1.0)

**注意：hub skill memory-cn 描述的是旧架构（Mnemosyne），以下为 2026-07-08 实测真实状态。**

## 记忆系统真实架构

| 组件 | 路径 | 用途 | 上限 | 状态 |
|---|---|---|---|---|
| `MEMORY.md` | `~/.hermes/memories/` | 系统技术记忆（配置/调试/Chrome/技能/挂起任务），与USER.md内容不重叠 | 66,000字符 | 3.7KB ✅ |
| `USER.md` | `~/.hermes/memories/` | 用户偏好/铁律/Ponytail/决策风格，与MEMORY.md内容不重叠 | 66,000字符 | 2.6KB ✅ |
| `concept_store.md` | `~/.hermes/memories/` | 19条抽象经验规则 | 无 | 9KB ✅ |
| `chrome-cdp-ax-tree.md` | `~/.hermes/memories/` | CDP技术文档 | 无 | 2KB ✅ |
| `idle_learning_log.md` | `~/.hermes/memories/` | Jun 6-19历史学习归档（55KB） | 无 | 55KB ✅ |
| `LanceDB` | `~/.hermes/lancedb/memories.lance/` | 语义记忆（session结束后自动提取写入） | 无 | 活跃，skills_used字段已支持 |

## 配置状态

```bash
# memory.provider 当前配置
hermes config show | grep -A5 "memory:"

# memory_char_limit 当前值
grep memory_char_limit ~/.hermes/config.yaml
# 当前值: 66000 (2026-07-08 已从6600扩容)

# LanceDB 验证
hermes memory status
```

## 审计标准流程

**先验证再操作，禁止未读完文件就决策：**

```
步骤1 ls -la ~/.hermes/memories/         → 列出所有文件+大小
步骤2 sqlite3 fact_store.db ".schema"     → 查真实表结构（skill文档可能过时）
步骤3 sqlite3 fact_store.db "SELECT COUNT(*) FROM facts" → 查实际行数
步骤4 diff USER.md MEMORY.md              → 查两文件重复内容
步骤5 grep -c "过时关键词" *.md            → 查过时引用(ChromaDB/GBrain/Mnemosyne)
步骤6 确认后再操作：删除/合并/修改
```

**教训**: memory-cn skill 描述 Mnemosyne 为 active provider，但实际已切换到 LanceDB。skill文档 ≠ 真实状态。每次必须先验证。

**教训**: Hermes 的 memory 路径固定为 `~/.hermes/memories/`（由 `get_memory_dir()` 源码决定），不是 `memory/`、`memories/`、`data/MEMORY.md` 等其他路径。历史上曾散落过 5 份重复文件，每次审计必须 `find ~/.hermes -name "MEMORY.md" -o -name "USER.md"` 确认只有活跃路径存在。

## 记忆文件审计清单

| 检查项 | 命令 | 期望结果 |
|---|---|---|
| 所有文件大小 | `ls -la ~/.hermes/memories/` | 无0字节垃圾文件 |
| fact_store行数 | `sqlite3 fact_store.db "SELECT COUNT(*) FROM facts" 2>/dev/null` | **0行=废弃，应删除**（不是"待启用"，已是legacy） |
| **MOA provider别名** | `grep "nv-qwen3.5-397b" ~/.hermes/config.yaml` | 应无输出；有输出=引用了不存在的provider，应改为实际provider名 |
| **SOUL.md硬编码PID** | `grep "pid [0-9]" ~/.hermes/SOUL.md` | 应无输出；有输出=gateway重启后立即失效，改为"任意pid的venv python" |
| fact_store结构 | `sqlite3 fact_store.db ".schema" 2>/dev/null` | 字段: id/key/value/source/confidence/created_at/updated_at |
| LanceDB行数 | `~/.hermes/hermes-agent/venv/bin/python3 -c "import lancedb; ..."` | 当前为0，新库 |
| MEMORY/USER重复 | `grep -c "Ponytail\|数字主人\|先装再清" ~/.hermes/memories/MEMORY.md` | 应为0 |
| 过时引用 | `grep "ChromaDB\|GBrain\|Mnemosyne" ~/.hermes/memories/*.md` | 应无或已修正 |
| **废弃文件检查** | `find ~/.hermes -name "MEMORY.md" -o -name "USER.md" 2>/dev/null` | **所有结果必须在 `~/.hermes/memories/` 内**；根目录/`data/`/`memory/`里的同名文件已废弃，应删除 |
| **memory/ 目录** | `ls -la ~/.hermes/memory/` | 此目录（`~/.hermes/memory/`）完全废弃，**不等于**活跃的 `memories/`；包含98KB fact_store.db（已无用）+ 27个旧references文档 + idle learning重复文件，应整体删除 |
| **chroma_memory/ 目录** | `ls -la ~/.hermes/chroma_memory/` | ChromaDB残留（471KB），config无chroma provider引用，应删除 |
| **根目录废弃skill文件** | `ls ~/.hermes/skill_*.md ~/.hermes/briefing_*.md ~/.hermes/*patrol*.md 2>/dev/null` | 应无输出；历史版本遗留的空壳skill应删除 |

## 精简合并规则

**定位分离**：
- `MEMORY.md` = 纯技术操作（配置/调试/Chrome/搜索/技能/挂起任务）
- `USER.md` = 用户偏好/铁律/Ponytail/决策风格
- 两文件内容不重叠，grep交叉验证应为0

**可删除**：
- 与活跃文件重复的备份（`MEMORY.md.bak`、`.lock`、`archive/`）
- `fact_store.db`（已确认0行，删除而非归档）
- 根目录废弃skill文件（`skill_*.md`、`briefing_*.md`、`*patrol*.md`等历史遗留空壳）

**human-core-memory.md**：已删除（与USER.md重复），其"学习路径"章节已合并入MEMORY.md。

## LanceDB 插件

- 安装：`hermes plugins install lancedb/hermes-agent-memory`
- 启用：`hermes plugins enable lancedb`
- 依赖：`uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 lancedb openai pyyaml`
- 工具：`lancedb_recall` / `lancedb_remember` / `lancedb_read` / `lancedb_forget`
- 触发：session结束后 on_session_end 自动提取事实写入

## 相关 Skills

- `memory-cn`（hub skill，受保护不可修改，**内容可能过时**）
- `concept_store.md`（本地，记忆层次结构第5层）
- `context-optimization`（token优化）
