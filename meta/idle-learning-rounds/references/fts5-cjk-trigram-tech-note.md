# FTS5 CJK 搜索：trigram vs unicode61 技术笔记

## 背景
Hermes state.db 存储用户对话记录。session_search 依赖 SQLite FTS5 索引。
中文搜索低召回的原因是 **unicode61 tokenizer** 把连续 CJK 字符各自拆为单字符 token。

## 现状（Hermes state.db schema 2026-07-03）
**双 FTS5 索引共存**：
- `messages_fts` — tokenize='unicode61'（默认）
- `messages_fts_trigram` — tokenize='trigram'（已创建）
- 3 个 trigger 同步数据到 `messages_fts_trigram`（insert/delete/update）

```sql
-- 确认 trigram 存在
SELECT name, sql FROM sqlite_master 
WHERE type='table' AND name LIKE '%trigram%';

-- 确认 trigger 存在
SELECT name, sql FROM sqlite_master 
WHERE type='trigger' AND sql LIKE '%trigram%';
```

## trigram 原理
- 将文本切分为重叠的 3-gram（3 字符序列）
- 中文：每个汉字作为 Unicode 字符被 trigram 正确拆分
- 搜索"苹果"→ trigram 生成"苹果"本身（恰好 3 字）→ 精确命中
- 搜索"怀孕"→ trigram 匹配"怀孕"（2 字填充为 3-gram 的变体）→ 比 unicode61 的"怀"+"孕" token 更准确
- 英文也有效："apple"→ ["app","ppl","ple"]

## 与 tokenchars 对比
- `unicode61 tokenchars` — 把 CJK 字符视为 token 组成字符，实际效果是把整段中文粘成一个巨型 token，只支持精确完全匹配
- `trigram` — 产生重叠 3-gram，支持子串匹配和模糊匹配
- **trigram 完胜 tokenchars** for CJK

## 验证 trigram 是否在用的快速方法
```bash
sqlite3 ~/.hermes/state.db "SELECT count(*) FROM messages_fts_trigram;"
sqlite3 ~/.hermes/state.db "SELECT count(*) FROM messages_fts;"
```
两者计数应接近。如果 `messages_fts_trigram` 计数明显少，说明 trigger 可能滞后或某次重建遗漏。

## 来源
- 2026-07-03 idle 学习：查 state.db schema 发现 trigram 已存在
- ChatGLM 验证确认 trigram > unicode61+tokenchars for CJK
- memory-cn skill（clawhub）提供的 FTS5 中文分析
