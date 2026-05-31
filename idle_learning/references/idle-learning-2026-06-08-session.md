# Idle Learning 2026-06-08 Session

## 方向 B — 理解层巡检 + 产线 Bug 修复

### 系统状态

| 检查项 | 状态 |
|--------|------|
| screen_watcher 进程 | 已死（上次截图 6/1 00:39，7天 stale） |
| Handler lock 残留 | 无（未阻塞） |
| Ollama 进程 | ✅ 运行中（serve + runner） |
| 本地模型 | qwen2.5:1.5b (0.92GB) + qwen3-vl:2b (1.76GB) |
| Dry-run 记录 | 617 条总数 |
| 场景分布 | unknown 49% / browser 38% / desktop 7% / other 5% |
| gateway.log 污染 | 1352 条 screen_watch 记录（占日志 26%） |

### Handler 紧急权重误区

**症状**：screen_analysis.log 中所有 `other` 场景被标记 `[urgent]`，即使分析结果为"没有需要处理的内容或异常"。

**根因分析**：
- 代码中对 `unknown`/`other` 场景使用 CRITICAL_KEYWORDS 降级匹配
- `CRITICAL_KEYWORDS` 包含 "异常"
- "没有需要处理的内容或**异常**" 中 "异常" 在否定上下文中被误匹配
- 结果：100% 的 other/unknown 场景被标记 urgent

**修复**：
1. 从 CRITICAL_KEYWORDS 移除 "异常"（太泛，否定上下文匹配率高）
2. 增加否定词检测：关键词前 12 字符内出现 "没有/无/未/不" 时跳过

### Broken Hook 污染 Gateway 日志

**症状**：gateway.log 含有 1352 条 `screen_watch` 记录，其中 1332 条是 "model not found"。

**根因**：
- `~/.hermes/hooks/screen_watch/` 硬编码旧 smolvlm2 模型（已下线）
- 依赖已删除的 `humanization_core`
- 1332 次模型查找尝试写入 gateway.log

**修复**：`HOOK.yaml` events 置空，hook 不再触发。

**诊断命令**：
```bash
# 检查污染程度
grep -c "screen_watch" ~/.hermes/logs/gateway.log

# 检查污染来源分布
grep "screen_watch" ~/.hermes/logs/gateway.log | sed 's/.*\] //' | sort | uniq -c | sort -rn

# 列出所有 hooks 并检查是否健康
ls -lt ~/.hermes/hooks/
for h in ~/.hermes/hooks/*/; do
  echo "=== $(basename $h) ==="
  cat "$h/HOOK.yaml" 2>/dev/null | head -5
done
```

### 联网学习结果

- Ollama 远程库：gemma4:31b / qwen3.5:397b >24GB，无新 M4 可用视觉模型
- InsiderLLM 最新讨论：qwen3.6 量化相关，需 ≥22GB + 非 Ollama 部署
- qwen3-vl:2b 仍是 M4 24GB 最佳视觉模型

### 已实装改进
1. ✅ handler 紧急权重否定检测
2. ✅ screen_watch hook 废弃禁用

### 下次方向
C — 决策操作（dry-run 场景分布优化 + handler action 扩展）
