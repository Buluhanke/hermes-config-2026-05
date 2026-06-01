# 记忆系统使用规范 & 跨会话记忆连续性（2026-06-02 实测教训）

## 事故回顾

2026-06-02 会话：用户问"昨晚说关掉动态壁纸"，session_search 搜"动态壁纸 屏幕 主体"返回0结果。根因：FTS5 AND 查询要求所有词都命中，搜"壁纸"才能找到"动态壁纸"。

同时 MEMORY.md 有多处严重过时：
- "Docker/Colima在跑" → 6月1日凌晨已全部清空
- "Hindsight容器在跑" → Colima停了就不在
- "Ollama已卸载" → app残留进程每次重启都回来
- session_search 能搜到（搜对关键词），但重要结论没写进 MEMORY.md

## 记忆三层架构

| 层 | 存储 | 用途 | 失效后果 |
|----|------|------|---------|
| MEMORY.md | `~/.hermes/memories/MEMORY.md` 文本文件 | 注入 system prompt 的快照事实 | 跨会话丢失重要决策 |
| fact_store (holographic) | `~/.hermes/memory_store.db` SQLite FTS5 | 结构化推理，entity查询 | 跨会话找不到关键事实 |
| session_search | `~/.hermes/state.db` FTS5 | 搜索历史对话 | 搜不准就丢失 |

## FTS5 查询规律

```
搜"动态壁纸"  → 0结果（因为DB里存的是"动态壁纸"但AND模式要求精确）
搜"壁纸"      → 能找到（包含关系）
搜"CPU 教训"  → 能找到
搜"动态壁纸 CPU" → 0结果（AND模式）
```

**结论**：重要结论写进 MEMORY.md + fact_store，不能依赖跨会话 session_search。

## 记忆写入规范

### 何时必须写 MEMORY.md

1. 识别到系统级问题（CPU/内存/进程异常）
2. 重要决策或配置变更（如关闭某服务、删除某容器）
3. 用户明确说过要做的改进方向
4. 发现工具能力边界（如"xxx不适用于1688"）

### 如何写

```markdown
§
[日期] [简短标题]：
- [事实1]
- [事实2]
- [教训/注意]
```

### fact_store 补录条件

当发现 MEMORY.md 中没有、但 session_search 能搜到的结论时，立刻写 fact_store：
```python
fact_store(action='add', content='...', category='tool')
```

## Ollama 残留进程问题

Ollama.app 退出后进程不一定退出（`ollama serve` 独立运行）。
每次会话开始检查：
```bash
ps aux | grep -i ollama | grep -v grep
```
如有残留：`kill $(pgrep -f ollama)`

## 动态壁纸彻底关闭

`WallpaperAerialsExtension` 进程每次唤醒/切换 Space 都会重启。
系统设置 → 壁纸 → 换成静态图片。

## session_search 正确用法

- 搜"关键词"而不是"完整描述"
- 搜不到时换更短的词（"壁纸" 而不是 "动态壁纸"）
- 优先写 MEMORY.md，不要依赖 session_search 找回重要结论
