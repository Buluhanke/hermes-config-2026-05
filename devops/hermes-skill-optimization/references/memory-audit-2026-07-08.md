# 记忆系统审计记录 (2026-07-08)

## 发现的关键问题

### 1. memory-cn skill 内容过时（hub skill，无法patch）
**问题**：
- skill 描述 Mnemosyne 作为 P2 层，已被 LanceDB 取代
- skill 内写 fact_store 列名为 `topic/text/trust`，实际是 `key/value/confidence`
- skill 描述 6 个记忆层，但实际 fact_store.db 0行未启用

**现状**：
- `memory.provider: lancedb` 已激活（不是 mnemosyne）
- LanceDB 工具已注册：`lancedb_recall/remember/read/forget`
- 存储路径：`~/.hermes/lancedb/memories.lance`
- 依赖：`OPENAI_API_KEY`（text-embedding-3-small，1536维）
- 旧 fact_store.db 0行，实际未启用

**教训**：审计记忆时，第一件事是 `sqlite3` 查真实列名，不要信任 skill 里的描述。

### 2. 记忆文件重复严重
| 文件对 | 重叠内容 |
|---|---|
| USER.md ↔ human-core-memory.md | 数字人原则/能力优先级/学习路径完全重复 |
| concept_store.md ↔ fact_store.md | concept_store 引用的 "ChromaDB/GBrain" 已废弃 |

**处理**：合并去重，human-core-memory.md 仅保留 USER.md 没有的"能力优先级"和"学习路径"章节。

### 3. 备份文件堆积
- `MEMORY.md.bak.*` 18个 + `USER.md.bak.*` 10个
- `archive/` 空目录

**处理**：全部删除。

## 真实记忆层（2026-07-08）
```
1. MEMORY.md        → 3.7KB 系统级记忆
2. USER.md          → 2.6KB 用户偏好/铁律
3. human-core...    → 1.2KB 能力优先级（与USER.md不重叠部分）
4. concept_store.md  → 9KB 抽象规则（已修正ChromaDB引用）
5. chrome-cdp-ax-tree.md → 2KB CDP技术文档
6. LanceDB语义记忆  → 0行（新库，session结束后自动写入）
```

## 审计流程（经验沉淀）
```
1. ls -la ~/.hermes/memories/          # 列出所有文件及大小
2. sqlite3 fact_store.db ".schema"       # 查真实表结构
3. sqlite3 fact_store.db "SELECT COUNT(*) FROM facts"  # 查行数
4. diff USER.md human-core-memory.md     # 查重复
5. grep "过时技术名" *                    # 查废弃引用
6. ls *.bak*                            # 查备份垃圾
```
