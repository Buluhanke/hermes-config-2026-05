# 2026-07-04 实测状态（perception-decision-engine 纠错记录）

## 背景

skill_view 返回的 SKILL.md 中有一处错误声明：
> `fact_store.db`: ❌ 0字节，表结构丢失

这是错误报告——实际上 `fact_store.db` 有两个文件：
- `~/.hermes/fact_store.db` → **0 字节**（旧文件，可忽略）
- `~/.hermes/memory/fact_store.db` → **94KB，90 条事实** ✅

skill 文档将两者混淆导致误判。

## 实测命令（必用，不要相信文档）

```bash
# 查 fact_store 事实数量（两个路径都要查）
sqlite3 ~/.hermes/fact_store.db "SELECT COUNT(*) FROM facts;" 2>/dev/null
sqlite3 ~/.hermes/memory/fact_store.db "SELECT COUNT(*) FROM facts;" 2>/dev/null

# 查表结构
sqlite3 ~/.hermes/memory/fact_store.db ".schema" 2>/dev/null | head -20
```

## 教训

**汇报前必须实测**：
- 文档说"0字节" → 实际有两个路径，只查了一个
- 路径 A 0字节 ≠ 路径 B 也是 0字节
- 涉及 DB/文件/进程状态的声称，必须有 `sqlite3` / `ls -la` / `ps` 实际输出作为证据
