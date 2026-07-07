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
| `MEMORY.md` | `~/.hermes/memories/` | 系统技术记忆 | ✅ 活跃 |
| `USER.md` | `~/.hermes/memories/` | 用户偏好/铁律 | ✅ 活跃 |
| `concept_store.md` | `~/.hermes/memories/` | 抽象经验规则 | ✅ 活跃 |
| **`memory_store.db`** | `~/.hermes/memory_store.db` | **fact_store 主库**，自 学脚本全写这里 | ✅ **71条facts，2026-07-08修复路径后恢复写入** |
| `LanceDB` | `~/.hermes/lancedb/memories.lance/` | 语义记忆 | ✅ 活跃 |
| Chrome | 150.0.7871.47 | 浏览器 | ✅ 2026-07-07 升级成功 |

**⚠️ 路径铁律（2026-07-08 修正）**：
- 正确：`~/.hermes/memory_store.db`
- 错误：`~/.hermes/memory/fact_store.db`（不存在）、`~/.hermes/memories/fact_store.md`（是文件不是DB）
- 教训：脚本路径必须先 `sqlite3 <path> "SELECT COUNT(*)"` 验证存在，grep 搜到路径≠文件存在

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

### 6. fact_store 路径断路 — ✅ 已修复 2026-07-08

**断路现象**：knowledge_miner / batch_facts_from_log / fact_decay 三个脚本各自写不同路径。

**真实 DB**：`~/.hermes/memory_store.db`（71条facts）
**历史错误路径**：
- `~/.hermes/memory/fact_store.db` — 不存在
- `~/.hermes/memories/fact_store.md` — 是 Markdown 文件不是 DB

**根因**：所有自学脚本的 DB_PATH 配置互相不一致，都没先验证文件是否存在。

**修复**：统一改为 `~/.hermes/memory_store.db`，字段映射 `content`（不是 `text`/`topic`），timestamp 处理加 `_parse_timestamp()` 兼容字符串和 float。

**教训**：grep 搜到路径 ≠ 文件存在。必须 `sqlite3 <path> "SELECT 1"` 验证。
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
步骤1 ls -la ~/.hermes/memories/       → 列出所有文件+大小
步骤2 sqlite3 ~/.hermes/memory_store.db ".schema"     → 查真实表结构（skill文档可能过时）
步骤3 sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts" → 查实际行数（当前71条）
步骤4 diff USER.md MEMORY.md            → 查两文件重复内容
步骤5 grep -c "过时关键词" *.md          → 查过时引用(ChromaDB/GBrain/Mnemosyne)
步骤6 确认后再操作：删除/合并/修改
```

**教训**: memory-cn skill 描述 Mnemosyne 为 active provider，但实际已切换到 LanceDB。skill文档 ≠ 真实状态。每次必须先验证。

**教训**: Hermes 的 memory 路径固定为 `~/.hermes/memories/`（由 `get_memory_dir()` 源码决定），不是 `memory/`、`memories/`、`data/MEMORY.md` 等其他路径。历史上曾散落过 5 份重复文件，每次审计必须 `find ~/.hermes -name "MEMORY.md" -o -name "USER.md"` 确认只有活跃路径存在。

## 记忆文件审计清单

| 检查项 | 命令 | 期望结果 |
|---|---|---|
| 所有文件大小 | `ls -la ~/.hermes/memories/` | 无0字节垃圾文件 |
| **fact_store路径** | `sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts"` | **71条=正常；0行=legacy废弃** |
| fact_store schema | `sqlite3 ~/.hermes/memory_store.db ".schema"` | 字段: fact_id/content/category/tags/trust_score/retrieval_count/helpful_count/created_at/updated_at |
| **废弃路径检查** | `ls ~/.hermes/memory/fact_store.db 2>/dev/null` | 不存在=正确；存在=历史上遗留的废弃路径 |
| LanceDB行数 | `~/.hermes/hermes-agent/venv/bin/python3 -c "import lancedb; ..."` | 当前为0，新库 |
| MEMORY/USER重复 | `grep -c "Ponytail\|数字主人\|先装再清" ~/.hermes/memories/MEMORY.md` | 应为0 |
| 过时引用 | `grep "ChromaDB\|GBrain\|Mnemosyne" ~/.hermes/memories/*.md` | 应无或已修正 |

## fact_store DB Schema（2026-07-08 实测）

```sql
CREATE TABLE facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,   -- ← 注意是 content 不是 text/topic
    category        TEXT DEFAULT 'general',
    tags            TEXT DEFAULT '',         -- JSON 字符串
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 字符串 "2026-06-03 16:46:17"
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hrr_vector      BLOB
);
```

**写入时注意**：
- `created_at`/`updated_at` 在 SQLite INSERT 不指定时自动填当前时间字符串
- Python `time.time()` 写入是 float，查询时需 `_parse_timestamp()` 转换
- 正确字段：`content`（不是 `text`/`topic`），`trust_score`（不是 `trust`/`original_trust`）
- 自学脚本写入字段顺序：`content, category, tags, trust_score, created_at, updated_at`（6个）

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
